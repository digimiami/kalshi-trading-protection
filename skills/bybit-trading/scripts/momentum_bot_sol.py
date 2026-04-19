"""
Momentum Trading Bot
Timeframe: 15m/1h
Entry: Breakout with volume confirmation
TP: 5-8% | SL: 2-3%
"""
import os
import time
import logging
from datetime import datetime
from typing import Optional, Dict
import ccxt
import config  # Loads .env
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('momentum_bot')

class MomentumBot:
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        self.symbol = os.getenv('TRADING_SYMBOL', 'SOL/USDT:USDT')
        self.timeframe = os.getenv('TIMEFRAME', '15m')
        self.leverage = int(os.getenv('LEVERAGE', '4'))
        self.position_size_pct = float(os.getenv('POSITION_SIZE_PCT', '8'))
        self.tp_pct = float(os.getenv('TP_PCT', '6'))
        self.sl_pct = float(os.getenv('SL_PCT', '2.5'))
        self.lookback = int(os.getenv('LOOKBACK_PERIOD', '20'))
        self.volume_multiplier = float(os.getenv('VOLUME_MULTIPLIER', '1.5'))
        
        self.exchange = ccxt.bybit({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'options': {'defaultType': 'swap'}
        })
        
    def fetch_ohlcv(self, limit: int = 100) -> pd.DataFrame:
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()
    
    def get_signal(self, df: pd.DataFrame) -> Optional[str]:
        if len(df) < self.lookback + 5:
            return None
            
        # Calculate indicators
        df['high_max'] = df['high'].rolling(window=self.lookback).max()
        df['low_min'] = df['low'].rolling(window=self.lookback).min()
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['atr'] = self.calculate_atr(df)
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Long breakout: Close above recent high with volume
        if (current['close'] > prev['high_max'] and 
            current['volume'] > current['volume_sma'] * self.volume_multiplier and
            current['atr'] > df['atr'].rolling(10).mean().iloc[-1]):
            return 'long'
            
        # Short breakout: Close below recent low with volume
        if (current['close'] < prev['low_min'] and 
            current['volume'] > current['volume_sma'] * self.volume_multiplier and
            current['atr'] > df['atr'].rolling(10).mean().iloc[-1]):
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
        """Calculate position size - fixed $50 USD per position."""
        position_value = float(os.getenv('POSITION_SIZE_USDT', '50'))  # Fixed $50
        ticker = self.exchange.fetch_ticker(self.symbol)
        amount = position_value / ticker['last']
        return max(0.001, round(amount, 3))  # Minimum 0.001 for Bybit
    
    def open_position(self, side: str):
        try:
            # Set leverage (ignore if already set)
            try:
                self.exchange.set_leverage(self.leverage, self.symbol)
            except Exception as e:
                if 'leverage not modified' in str(e).lower() or '110043' in str(e):
                    logging.debug("Leverage already set, continuing...")
                else:
                    raise
            amount = self.calculate_position_size()
            ticker = self.exchange.fetch_ticker(self.symbol)
            entry_price = ticker['last']
            
            if side == 'long':
                tp_price = entry_price * (1 + self.tp_pct / 100)
                sl_price = entry_price * (1 - self.sl_pct / 100)
            else:
                tp_price = entry_price * (1 - self.tp_pct / 100)
                sl_price = entry_price * (1 + self.sl_pct / 100)
            
            order = self.exchange.create_market_order(
                self.symbol, side, amount,
                params={'takeProfit': tp_price, 'stopLoss': sl_price}
            )
            logger.info(f"Momentum {side} | Entry: {entry_price:.2f} | TP: {tp_price:.2f}")
            return order
        except Exception as e:
            logger.error(f"Open failed: {e}")
            return None
    
    def close_position(self):
        try:
            pos = self.get_position()
            if not pos:
                return
            side = 'sell' if pos['side'] == 'long' else 'buy'
            amount = abs(float(pos['contracts']))
            ccxt_side = 'buy' if side == 'long' else 'sell'
            order = self.exchange.create_market_order(self.symbol, ccxt_side, amount)
            logger.info("Momentum position closed")
        except Exception as e:
            logger.error(f"Close failed: {e}")
    
    def run(self):
        logger.info(f"Momentum bot started | {self.symbol} | {self.timeframe}")
        while True:
            try:
                if not self.get_position():
                    df = self.fetch_ohlcv()
                    signal = self.get_signal(df)
                    if signal:
                        self.open_position(signal)
                time.sleep(900)  # 15 minutes
            except Exception as e:
                logger.error(f"Loop error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    bot = MomentumBot()
    bot.run()
