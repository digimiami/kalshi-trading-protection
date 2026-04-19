"""
Bybit Scalping Bot - RSI + Bollinger Bands Strategy
Timeframe: 1m
Entry: RSI oversold/bought + BB bounce
TP: 0.8% | SL: 0.5% | Max hold: 15-20 minutes
"""
import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import ccxt
import config  # Loads .env
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scalping_bot')

class ScalpingBot:
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        self.symbol = os.getenv('TRADING_SYMBOL', 'ETH/USDT:USDT')
        self.leverage = int(os.getenv('LEVERAGE', '5'))
        self.position_size_pct = float(os.getenv('POSITION_SIZE_PCT', '5'))
        self.tp_pct = float(os.getenv('TP_PCT', '0.8'))
        self.sl_pct = float(os.getenv('SL_PCT', '0.5'))
        self.max_hold_minutes = int(os.getenv('MAX_HOLD_MINUTES', '20'))
        self.rsi_period = int(os.getenv('RSI_PERIOD', '14'))
        self.bb_period = int(os.getenv('BB_PERIOD', '20'))
        self.bb_std = float(os.getenv('BB_STD', '2.0'))
        
        self.exchange = ccxt.bybit({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'options': {'defaultType': 'swap'}
        })
        self.position = None
        self.entry_time = None
        
    def fetch_ohlcv(self, limit: int = 100) -> pd.DataFrame:
        """Fetch 1-minute OHLCV data."""
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, '1m', limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std: float = 2.0):
        """Calculate Bollinger Bands."""
        sma = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()
        upper_band = sma + (rolling_std * std)
        lower_band = sma - (rolling_std * std)
        return upper_band, sma, lower_band
    
    def get_signal(self, df: pd.DataFrame) -> Optional[str]:
        """
        Generate trading signal based on RSI and Bollinger Bands.
        Returns: 'long', 'short', or None
        """
        if len(df) < self.bb_period + 5:
            return None
            
        df['rsi'] = self.calculate_rsi(df['close'], self.rsi_period)
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.calculate_bollinger_bands(
            df['close'], self.bb_period, self.bb_std
        )
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Long signal: RSI oversold (< 30) and price bounces off lower BB
        if (current['rsi'] < 30 and 
            prev['close'] <= prev['bb_lower'] and 
            current['close'] > current['bb_lower']):
            return 'long'
            
        # Short signal: RSI overbought (> 70) and price rejects from upper BB
        if (current['rsi'] > 70 and 
            prev['close'] >= prev['bb_upper'] and 
            current['close'] < current['bb_upper']):
            return 'short'
            
        return None
    
    def get_balance(self) -> float:
        """Get USDT balance."""
        balance = self.exchange.fetch_balance()
        return balance['USDT']['free'] if 'USDT' in balance else 0
    
    def get_position(self) -> Optional[Dict]:
        """Get current position."""
        positions = self.exchange.fetch_positions([self.symbol])
        for pos in positions:
            if float(pos.get('contracts', 0)) != 0:
                return pos
        return None
    
    def calculate_position_size(self) -> float:
        """Calculate position size - fixed $50 USD per position."""
        position_value = float(os.getenv('POSITION_SIZE_USDT', '50'))  # Fixed $50
        ticker = self.exchange.fetch_ticker(self.symbol)
        price = ticker['last']
        amount = position_value / price
        return max(0.001, round(amount, 3))  # Minimum 0.001 BTC for Bybit
    
    def open_position(self, side: str):
        """Open a new position."""
        try:
            # Set leverage (ignore if already set)
            try:
                self.exchange.set_leverage(self.leverage, self.symbol)
            except Exception as e:
                if 'leverage not modified' in str(e).lower() or '110043' in str(e):
                    logger.debug("Leverage already set, continuing...")
                else:
                    raise
            
            # Calculate position size
            amount = self.calculate_position_size()
            
            # Calculate TP/SL prices
            ticker = self.exchange.fetch_ticker(self.symbol)
            entry_price = ticker['last']
            
            if side == 'long':
                tp_price = entry_price * (1 + self.tp_pct / 100)
                sl_price = entry_price * (1 - self.sl_pct / 100)
            else:  # short
                tp_price = entry_price * (1 - self.tp_pct / 100)
                sl_price = entry_price * (1 + self.sl_pct / 100)
            
            # Place market order
            order = self.exchange.create_market_order(
                self.symbol,
                side,
                amount,
                params={
                    'takeProfit': tp_price,
                    'stopLoss': sl_price
                }
            )
            
            self.position = side
            self.entry_time = datetime.now()
            
            logger.info(f"Opened {side} position | Size: {amount:.4f} | Entry: {entry_price:.2f} | TP: {tp_price:.2f} | SL: {sl_price:.2f}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to open position: {e}")
            return None
    
    def close_position(self):
        """Close current position."""
        try:
            pos = self.get_position()
            if not pos:
                logger.info("No position to close")
                return
                
            side = 'sell' if pos['side'] == 'long' else 'buy'
            amount = abs(float(pos['contracts']))
            
            order = ccxt_side = 'buy' if side == 'long' else 'sell'
            order = self.exchange.create_market_order(self.symbol, ccxt_side, amount)
            
            self.position = None
            self.entry_time = None
            
            logger.info(f"Closed position | Side: {side} | Amount: {amount:.4f}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return None
    
    def check_time_limit(self) -> bool:
        """Check if position has exceeded max hold time."""
        if not self.entry_time:
            return False
        elapsed = datetime.now() - self.entry_time
        return elapsed > timedelta(minutes=self.max_hold_minutes)
    
    def run(self):
        """Main trading loop."""
        logger.info(f"Scalping bot started | Symbol: {self.symbol} | Leverage: {self.leverage}x")
        
        while True:
            try:
                # Check for existing position
                current_pos = self.get_position()
                
                if current_pos:
                    # Check time limit
                    if self.check_time_limit():
                        logger.info("Max hold time reached - closing position")
                        self.close_position()
                    else:
                        logger.info("Position active - monitoring...")
                else:
                    # Look for new entry
                    df = self.fetch_ohlcv()
                    signal = self.get_signal(df)
                    
                    if signal:
                        logger.info(f"Signal detected: {signal}")
                        self.open_position(signal)
                    else:
                        logger.debug("No signal")
                
                # Sleep before next iteration
                time.sleep(60)  # 1 minute
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == '__main__':
    bot = ScalpingBot()
    bot.run()
