"""
Mean Reversion Trading Bot - Pybit Version
Timeframe: 5m
Entry: Price deviation from mean (Z-score)
TP: 2.5% | SL: 1.5%
"""
import os
import time
import logging
from datetime import datetime
from pybit.unified_trading import HTTP
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/bybit_bots/mean_reversion_bot.log')
    ]
)
logger = logging.getLogger('mean_reversion_bot')

# Config
SYMBOL = 'BTCUSDT'
TIMEFRAME = '5'
LEVERAGE = int(os.getenv('LEVERAGE', '3'))
POSITION_SIZE_USDT = float(os.getenv('POSITION_SIZE_USDT', '50'))  # Fixed $50 per position
TP_PCT = 2.5
SL_PCT = 1.5
LOOKBACK = 50
Z_THRESHOLD = 2.0

class MeanReversionBot:
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        self.session = HTTP(testnet=False, api_key=self.api_key, api_secret=self.api_secret)
        
    def get_klines(self, limit=100):
        """Fetch OHLCV data."""
        try:
            resp = self.session.get_kline(
                category='linear',
                symbol=SYMBOL,
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
            return df.iloc[::-1].reset_index(drop=True)
        except Exception as e:
            logger.error(f"Failed to fetch klines: {e}")
            return None
    
    def calculate_z_score(self, df):
        """Calculate Z-score for mean reversion."""
        df['sma'] = df['close'].rolling(window=LOOKBACK).mean()
        df['std'] = df['close'].rolling(window=LOOKBACK).std()
        df['z_score'] = (df['close'] - df['sma']) / df['std']
        return df
    
    def get_signal(self, df):
        """Check for mean reversion signals."""
        if df is None or len(df) < LOOKBACK + 5:
            return None
        
        df = self.calculate_z_score(df)
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Long: Price far below mean (negative Z-score)
        if current['z_score'] < -Z_THRESHOLD and prev['z_score'] < current['z_score']:
            # Z-score is improving (reverting to mean)
            logger.info(f"Mean Reversion LONG signal | Price: {current['close']:.2f} | Z-score: {current['z_score']:.2f}")
            return 'Buy'
        
        # Short: Price far above mean (positive Z-score)
        if current['z_score'] > Z_THRESHOLD and prev['z_score'] > current['z_score']:
            # Z-score is improving (reverting to mean)
            logger.info(f"Mean Reversion SHORT signal | Price: {current['close']:.2f} | Z-score: {current['z_score']:.2f}")
            return 'Sell'
        
        return None
    
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
    
    def get_position(self):
        """Check if position exists."""
        try:
            resp = self.session.get_positions(category='linear', symbol=SYMBOL)
            for p in resp['result']['list']:
                size = float(p.get('size', 0) or 0)
                if size != 0:
                    return p
            return None
        except Exception as e:
            logger.error(f"Failed to get position: {e}")
            return None
    
    def calculate_position_size(self):
        """Calculate position size - fixed $50 USD per position."""
        ticker = self.session.get_tickers(category='linear', symbol=SYMBOL)
        price = float(ticker['result']['list'][0].get('lastPrice', 70000))
        amount = POSITION_SIZE_USDT / price  # Fixed $50 position
        return max(0.001, round(amount, 3))
    
    def place_order(self, side, qty):
        """Place market order with TP/SL."""
        try:
            # Get current price
            ticker = self.session.get_tickers(category='linear', symbol=SYMBOL)
            entry = float(ticker['result']['list'][0].get('lastPrice', 0))
            
            if side == 'Buy':
                tp = entry * (1 + TP_PCT / 100)
                sl = entry * (1 - SL_PCT / 100)
            else:
                tp = entry * (1 - TP_PCT / 100)
                sl = entry * (1 + SL_PCT / 100)
            
            order = self.session.place_order(
                category='linear',
                symbol=SYMBOL,
                side=side,
                orderType='Market',
                qty=str(qty),
                takeProfit=str(round(tp, 2)),
                stopLoss=str(round(sl, 2)),
                tpTriggerBy='MarkPrice',
                slTriggerBy='MarkPrice'
            )
            
            if order['retCode'] == 0:
                logger.info(f"Mean Reversion {side} opened | Qty: {qty} | Entry: {entry:.2f} | TP: {tp:.2f} | SL: {sl:.2f}")
                return order
            else:
                logger.error(f"Order failed: {order}")
                return None
        except Exception as e:
            logger.error(f"Place order error: {e}")
            return None
    
    def run(self):
        """Main trading loop."""
        logger.info("=" * 50)
        logger.info("Mean Reversion Bot Started")
        logger.info(f"Symbol: {SYMBOL} | Timeframe: {TIMEFRAME}m")
        logger.info(f"TP: {TP_PCT}% | SL: {SL_PCT}% | Z-threshold: {Z_THRESHOLD}")
        logger.info("=" * 50)
        
        iteration = 0
        while True:
            try:
                iteration += 1
                logger.info(f"--- Iteration {iteration} ---")
                
                logger.info("Checking position...")
                position = self.get_position()
                logger.info(f"Position: {'Yes' if position else 'No'}")
                
                if not position:
                    logger.info("Fetching klines...")
                    df = self.get_klines()
                    logger.info(f"Klines: {len(df) if df is not None else 'None'} candles")
                    
                    signal = self.get_signal(df)
                    logger.info(f"Signal: {signal}")
                    
                    if signal:
                        qty = self.calculate_position_size()
                        logger.info(f"Qty: {qty}")
                        if qty > 0:
                            self.place_order(signal, qty)
                else:
                    logger.info(f"Active: {position['side']} {position['size']}")
                
                logger.info("Sleeping 60s...")
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    bot = MeanReversionBot()
    bot.run()
