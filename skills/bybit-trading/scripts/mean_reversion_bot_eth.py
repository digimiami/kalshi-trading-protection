"""
Mean Reversion Trading Bot
Timeframe: 5m/15m
Entry: Price deviation from mean
TP: 2-3% | SL: 1.5%
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
logger = logging.getLogger('mean_reversion_bot')

class MeanReversionBot:
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        self.symbol = os.getenv('TRADING_SYMBOL', 'ETH/USDT:USDT')
        self.timeframe = os.getenv('TIMEFRAME', '5m')
        self.leverage = int(os.getenv('LEVERAGE', '3'))
        self.position_size_pct = float(os.getenv('POSITION_SIZE_PCT', '10'))
        self.tp_pct = float(os.getenv('TP_PCT', '2.5'))
        self.sl_pct = float(os.getenv('SL_PCT', '1.5'))
        self.deviation_threshold = float(os.getenv('DEVIATION_THRESHOLD', '2.0'))
        self.lookback_period = int(os.getenv('LOOKBACK_PERIOD', '50'))
        
        self.exchange = ccxt.bybit({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'options': {'defaultType': 'swap'}
        })
        self.position = None
        
    def fetch_ohlcv(self, limit: int = 100) -> pd.DataFrame:
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    
    def calculate_indicators(self, df: pd.DataFrame):
        """Calculate mean reversion indicators."""
        df['sma'] = df['close'].rolling(window=self.lookback_period).mean()
        df['std'] = df['close'].rolling(window=self.lookback_period).std()
        df['z_score'] = (df['close'] - df['sma']) / df['std']
        df['bb_upper'] = df['sma'] + (df['std'] * 2)
        df['bb_lower'] = df['sma'] - (df['std'] * 2)
        return df
    
    def get_signal(self, df: pd.DataFrame) -> Optional[str]:
        if len(df) < self.lookback_period:
            return None
            
        df = self.calculate_indicators(df)
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Long: Price significantly below mean (z-score < -2)
        if (current['z_score'] < -self.deviation_threshold and 
            prev['close'] < prev['bb_lower'] and 
            current['close'] > current['bb_lower']):
            return 'long'
            
        # Short: Price significantly above mean (z-score > 2)
        if (current['z_score'] > self.deviation_threshold and 
            prev['close'] > prev['bb_upper'] and 
            current['close'] < current['bb_upper']):
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
        price = ticker['last']
        amount = position_value / price
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
            
            self.position = side
            logger.info(f"Mean Reversion {side} | Entry: {entry_price:.2f} | TP: {tp_pct:.2f} | SL: {sl_price:.2f}")
            return order
        except Exception as e:
            logger.error(f"Open position failed: {e}")
            return None
    
    def close_position(self):
        try:
            pos = self.get_position()
            if not pos:
                return
            side = 'sell' if pos['side'] == 'long' else 'buy'
            amount = abs(float(pos['contracts']))
            order = ccxt_side = 'buy' if side == 'long' else 'sell'
            order = self.exchange.create_market_order(self.symbol, ccxt_side, amount)
            self.position = None
            logger.info(f"Closed Mean Reversion position")
            return order
        except Exception as e:
            logger.error(f"Close position failed: {e}")
            return None
    
    def run(self):
        logger.info(f"Mean Reversion bot started | {self.symbol} | {self.timeframe}")
        while True:
            try:
                current_pos = self.get_position()
                if not current_pos:
                    df = self.fetch_ohlcv()
                    signal = self.get_signal(df)
                    if signal:
                        self.open_position(signal)
                time.sleep(300)  # 5 minutes
            except Exception as e:
                logger.error(f"Loop error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    bot = MeanReversionBot()
    bot.run()
