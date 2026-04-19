"""
Breakout Trading Bot for Bybit
Detects and trades breakouts from support/resistance with volume confirmation
"""
import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Optional, List
import ccxt
import config
import pandas as pd
import pandas_ta as ta
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('breakout_bot')

class BreakoutBot:
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        self.symbol = os.getenv('TRADING_SYMBOL', 'BTC/USDT:USDT')
        self.leverage = int(os.getenv('LEVERAGE', '3'))
        self.position_size_pct = float(os.getenv('POSITION_SIZE_PCT', '5'))
        self.tp_atr_multiplier = float(os.getenv('TP_ATR_MULT', '2.0'))
        self.sl_atr_multiplier = float(os.getenv('SL_ATR_MULT', '1.0'))
        self.lookback_period = int(os.getenv('LOOKBACK_PERIOD', '20'))
        self.volume_threshold = float(os.getenv('VOLUME_THRESHOLD', '1.5'))
        self.atr_period = int(os.getenv('ATR_PERIOD', '14'))
        
        self.exchange = ccxt.bybit({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'options': {'defaultType': 'swap'}
        })
        self.position = None
        
    def fetch_ohlcv(self, timeframe='15m', limit=100) -> pd.DataFrame:
        """Fetch OHLCV data."""
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = df.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': float})
        return df
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()
    
    def detect_support_resistance(self, df: pd.DataFrame, period: int = 20) -> tuple:
        """Detect support and resistance levels."""
        highs = df['high'].tail(period)
        lows = df['low'].tail(period)
        
        resistance = highs.max()
        support = lows.min()
        
        # Add buffer
        resistance_buffer = resistance * 1.002
        support_buffer = support * 0.998
        
        return support_buffer, resistance_buffer
    
    def get_signal(self, df: pd.DataFrame) -> Optional[str]:
        """
        Detect breakout signals.
        Returns: 'long', 'short', or None
        """
        if len(df) < self.lookback_period + 5:
            return None
            
        # Calculate indicators
        df['atr'] = self.calculate_atr(df, self.atr_period)
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        
        support, resistance = self.detect_support_resistance(df, self.lookback_period)
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Long breakout: Close above resistance with volume
        if (current['close'] > resistance and 
            prev['close'] <= resistance and
            current['volume'] > current['volume_sma'] * self.volume_threshold):
            return 'long'
            
        # Short breakout: Close below support with volume
        if (current['close'] < support and 
            prev['close'] >= support and
            current['volume'] > current['volume_sma'] * self.volume_threshold):
            return 'short'
            
        return None
    
    def get_balance(self) -> float:
        balance = self.exchange.fetch_balance()
        return balance['USDT']['free'] if 'USDT' in balance else 0
    
    def get_position(self) -> Optional[Dict]:
        positions = self.exchange.fetch_positions([self.symbol])
        for pos in positions:
            if float(pos.get('contracts', 0)) != 0:
                return pos
        return None
    
    def calculate_position_size(self) -> float:
        balance = self.get_balance()
        position_value = balance * (self.position_size_pct / 100)
        ticker = self.exchange.fetch_ticker(self.symbol)
        price = ticker['last']
        amount = position_value / price
        return max(0.001, round(amount, 3))
    
    def open_position(self, side: str):
        try:
            # Set leverage (ignore if already set)
            try:
                self.exchange.set_leverage(self.leverage, self.symbol)
            except:
                pass
                
            amount = self.calculate_position_size()
            
            # Get ATR for TP/SL
            df = self.fetch_ohlcv()
            atr = self.calculate_atr(df).iloc[-1]
            ticker = self.exchange.fetch_ticker(self.symbol)
            entry_price = ticker['last']
            
            if side == 'long':
                tp_price = entry_price + (atr * self.tp_atr_multiplier)
                sl_price = entry_price - (atr * self.sl_atr_multiplier)
            else:
                tp_price = entry_price - (atr * self.tp_atr_multiplier)
                sl_price = entry_price + (atr * self.sl_atr_multiplier)
            
            ccxt_side = 'buy' if side == 'long' else 'sell'
            
            order = self.exchange.create_market_order(
                self.symbol,
                ccxt_side,
                amount,
                params={
                    'takeProfit': tp_price,
                    'stopLoss': sl_price
                }
            )
            
            self.position = side
            logger.info(f"🔥 BREAKOUT {side.upper()} | Entry: ${entry_price:.2f} | TP: ${tp_price:.2f} | SL: ${sl_price:.2f} | ATR: ${atr:.2f}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to open position: {e}")
            return None
    
    def close_position(self):
        try:
            pos = self.get_position()
            if not pos:
                return
            side = 'sell' if pos['side'] == 'long' else 'buy'
            amount = abs(float(pos['contracts']))
            order = self.exchange.create_market_order(self.symbol, side, amount, {'reduceOnly': True})
            self.position = None
            logger.info(f"Closed position")
            return order
        except Exception as e:
            logger.error(f"Failed to close: {e}")
    
    def run(self):
        logger.info(f"🔥 Breakout bot started | Symbol: {self.symbol} | Leverage: {self.leverage}x")
        
        while True:
            try:
                current_pos = self.get_position()
                
                if current_pos:
                    logger.info("Position active - monitoring...")
                else:
                    df = self.fetch_ohlcv()
                    signal = self.get_signal(df)
                    
                    if signal:
                        logger.info(f"🔥 BREAKOUT SIGNAL: {signal.upper()}")
                        self.open_position(signal)
                    else:
                        logger.debug("No breakout signal")
                
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    bot = BreakoutBot()
    bot.run()
