#!/usr/bin/env python3
"""
RSI + Moving Average Trading Bot for Bybit
Pairs: BTC, ETH, SOL, BNB, NEAR, LINK, DOGE
Strategy: Buy on RSI < 30 or price above MA20 + uptrend
         Sell on RSI > 70
"""
import os
import time
import logging
from datetime import datetime

# Load environment
env_path = '/root/.openclaw/workspace/skills/bybit-trading/scripts/.env'
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from pybit.unified_trading import HTTP
import pandas as pd
import numpy as np

# Configuration
PAIRS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'NEARUSDT', 'LINKUSDT', 'DOGEUSDT']
TIMEFRAME = '5'
RSI_PERIOD = 14
MA_PERIOD = 20
MAX_POSITIONS = 3
POSITION_SIZE_PCT = 10
TP_PCT = 2.5
SL_PCT = 2.5
TRAILING_PCT = 1.0
TRAILING_ACTIVATION_PCT = 1.0

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/bybit_bots/rsi_ma_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('rsi_ma_bot')

class RSIMaBot:
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        self.session = HTTP(testnet=False, api_key=self.api_key, api_secret=self.api_secret)
        
    def get_klines(self, symbol, limit=100):
        """Fetch OHLCV data."""
        try:
            resp = self.session.get_kline(
                category='linear',
                symbol=symbol,
                interval=TIMEFRAME,
                limit=limit
            )
            data = resp['result']['list']
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['open'] = df['open'].astype(float)
            df['volume'] = df['volume'].astype(float)
            return df.iloc[::-1].reset_index(drop=True)  # Reverse to chronological order
        except Exception as e:
            logger.error(f"Failed to fetch klines for {symbol}: {e}")
            return None
    
    def calculate_rsi(self, df, period=RSI_PERIOD):
        """Calculate RSI."""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_ma(self, df, period=MA_PERIOD):
        """Calculate Moving Average."""
        return df['close'].rolling(window=period).mean()
    
    def get_positions(self):
        """Get current positions."""
        positions = []
        for pair in PAIRS:
            try:
                resp = self.session.get_positions(category='linear', symbol=pair)
                for p in resp['result']['list']:
                    if float(p.get('size', 0)) != 0:
                        positions.append(p)
            except Exception as e:
                logger.error(f"Failed to get position for {pair}: {e}")
        return positions
    
    def get_open_position_count(self):
        """Count open positions."""
        return len(self.get_positions())
    
    def get_balance(self):
        """Get available USDT balance."""
        try:
            resp = self.session.get_wallet_balance(accountType='UNIFIED', coin='USDT')
            for acc in resp['result']['list']:
                for coin in acc.get('coin', []):
                    if coin['coin'] == 'USDT':
                        avail = coin.get('availableToWithdraw', '0') or '0'
                        return float(avail) if avail else 0
            return 0
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0
    
    def should_buy(self, df):
        """Check if buy conditions are met."""
        if df is None or len(df) < MA_PERIOD + 5:
            return False, None
        
        df['rsi'] = self.calculate_rsi(df)
        df['ma20'] = self.calculate_ma(df)
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Condition 1: RSI oversold
        rsi_oversold = current['rsi'] < 30
        
        # Condition 2: Price above MA20 with uptrend
        above_ma = current['close'] > current['ma20']
        trend_up = current['ma20'] > prev['ma20']
        ma_condition = above_ma and trend_up
        
        if rsi_oversold:
            return True, 'RSI oversold'
        elif ma_condition:
            return True, 'Above MA20 + uptrend'
        
        return False, None
    
    def should_sell(self, df):
        """Check if sell conditions are met."""
        if df is None or len(df) < RSI_PERIOD + 5:
            return False
        
        df['rsi'] = self.calculate_rsi(df)
        current = df.iloc[-1]
        
        return current['rsi'] > 70
    
    def place_order(self, symbol, side, qty):
        """Place market order."""
        try:
            resp = self.session.place_order(
                category='linear',
                symbol=symbol,
                side=side,
                orderType='Market',
                qty=str(qty)
            )
            logger.info(f"Order placed: {side} {qty} {symbol} - OrderID: {resp['result'].get('orderId', 'N/A')}")
            return resp
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return None
    
    def set_tp_sl(self, symbol, entry_price, side):
        """Set TP/SL with trailing stop."""
        try:
            if side == 'Buy':
                tp_price = round(entry_price * (1 + TP_PCT / 100), 4)
                sl_price = round(entry_price * (1 - SL_PCT / 100), 4)
                trailing = round(entry_price * TRAILING_PCT / 100, 4)
            else:
                tp_price = round(entry_price * (1 - TP_PCT / 100), 4)
                sl_price = round(entry_price * (1 + SL_PCT / 100), 4)
                trailing = round(entry_price * TRAILING_PCT / 100, 4)
            
            self.session.set_trading_stop(
                category='linear',
                symbol=symbol,
                takeProfit=str(tp_price),
                stopLoss=str(sl_price),
                trailingStop=str(trailing),
                activePrice=str(round(entry_price * (1 + TRAILING_ACTIVATION_PCT / 100), 4)) if side == 'Buy' else str(round(entry_price * (1 - TRAILING_ACTIVATION_PCT / 100), 4)),
                tpslMode='Full',
                tpTriggerBy='MarkPrice',
                slTriggerBy='MarkPrice'
            )
            logger.info(f"TP/SL set for {symbol}: TP={tp_price}, SL={sl_price}, Trailing={trailing}")
        except Exception as e:
            logger.error(f"Failed to set TP/SL: {e}")
    
    def get_position_size(self):
        """Calculate position size based on 10% of balance."""
        balance = self.get_balance()
        return round((balance * POSITION_SIZE_PCT / 100), 3)
    
    def run(self):
        """Main trading loop."""
        logger.info("=" * 50)
        logger.info("RSI + MA Bot Started")
        logger.info(f"Pairs: {', '.join(PAIRS)}")
        logger.info(f"Max Positions: {MAX_POSITIONS}")
        logger.info(f"TP: {TP_PCT}% | SL: {SL_PCT}% | Trailing: {TRAILING_PCT}%")
        logger.info("=" * 50)
        
        while True:
            try:
                # Check current positions
                positions = self.get_positions()
                open_count = len(positions)
                position_symbols = {p['symbol'] for p in positions}
                
                logger.info(f"Open positions: {open_count}/{MAX_POSITIONS}")
                
                # Check sell conditions for existing positions
                for pos in positions:
                    symbol = pos['symbol']
                    df = self.get_klines(symbol)
                    if df is not None and self.should_sell(df):
                        logger.info(f"Sell signal for {symbol}: RSI overbought")
                        qty = pos['size']
                        self.place_order(symbol, 'Sell', qty)
                
                # Look for buy opportunities if under max positions
                if open_count < MAX_POSITIONS:
                    for symbol in PAIRS:
                        if symbol in position_symbols:
                            continue
                        
                        df = self.get_klines(symbol)
                        should_buy, reason = self.should_buy(df)
                        
                        if should_buy:
                            qty = self.get_position_size()
                            if qty > 0:
                                logger.info(f"Buy signal for {symbol}: {reason}")
                                resp = self.place_order(symbol, 'Buy', qty)
                                if resp:
                                    entry = float(resp['result'].get('avgPrice', df.iloc[-1]['close']))
                                    self.set_tp_sl(symbol, entry, 'Buy')
                            break  # Only one trade per cycle
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(30)

if __name__ == '__main__':
    bot = RSIMaBot()
    bot.run()
