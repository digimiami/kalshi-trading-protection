"""
Statistical Arbitrage Bot for Bybit
Trades correlation breakdowns between correlated pairs
"""
import os
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
import ccxt
import config
import pandas as pd
import numpy as np
from scipy import stats

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('arbitrage_bot')

class ArbitrageBot:
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        
        # Primary pair and hedge pair
        self.primary_symbol = os.getenv('ARB_PRIMARY', 'BTC/USDT:USDT')
        self.hedge_symbol = os.getenv('ARB_HEDGE', 'ETH/USDT:USDT')
        
        self.leverage = int(os.getenv('LEVERAGE', '3'))
        self.position_size_pct = float(os.getenv('POSITION_SIZE_PCT', '5'))
        self.lookback_period = int(os.getenv('ARB_LOOKBACK', '100'))
        self.zscore_threshold = float(os.getenv('ZSCORE_THRESHOLD', '2.0'))
        self.exit_zscore = float(os.getenv('EXIT_ZSCORE', '0.5'))
        self.correlation_min = float(os.getenv('CORR_MIN', '0.7'))
        
        self.exchange = ccxt.bybit({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'options': {'defaultType': 'swap'}
        })
        
        self.active_trade = None
        
    def fetch_prices(self, symbol: str, limit: int = 100) -> pd.Series:
        """Fetch price history."""
        ohlcv = self.exchange.fetch_ohlcv(symbol, '15m', limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df['close'].astype(float)
    
    def calculate_spread(self, series1: pd.Series, series2: pd.Series) -> Tuple[float, float, float]:
        """
        Calculate spread statistics.
        Returns: (current_zscore, correlation, hedge_ratio)
        """
        # Calculate correlation
        correlation = series1.corr(series2)
        
        # Calculate hedge ratio (beta)
        covariance = np.cov(series1, series2)[0][1]
        variance = np.var(series2)
        hedge_ratio = covariance / variance if variance != 0 else 1
        
        # Calculate spread
        spread = series1 - (hedge_ratio * series2)
        
        # Calculate Z-score
        spread_mean = spread.mean()
        spread_std = spread.std()
        current_spread = spread.iloc[-1]
        zscore = (current_spread - spread_mean) / spread_std if spread_std != 0 else 0
        
        return zscore, correlation, hedge_ratio
    
    def get_signal(self) -> Optional[Dict]:
        """
        Generate arbitrage signal.
        Returns: {'side': 'long_spread'/'short_spread', 'hedge_ratio': float} or None
        """
        try:
            primary_prices = self.fetch_prices(self.primary_symbol, self.lookback_period)
            hedge_prices = self.fetch_prices(self.hedge_symbol, self.lookback_period)
            
            if len(primary_prices) < self.lookback_period or len(hedge_prices) < self.lookback_period:
                return None
            
            zscore, correlation, hedge_ratio = self.calculate_spread(primary_prices, hedge_prices)
            
            logger.info(f"Z-Score: {zscore:.2f} | Correlation: {correlation:.2f} | Hedge Ratio: {hedge_ratio:.3f}")
            
            # Check if correlation is strong enough
            if abs(correlation) < self.correlation_min:
                logger.info(f"Correlation too weak: {correlation:.2f} (min: {self.correlation_min})")
                return None
            
            # Long spread: Primary undervalued vs hedge (Z-score < -2)
            if zscore < -self.zscore_threshold:
                return {'side': 'long_spread', 'hedge_ratio': hedge_ratio, 'zscore': zscore}
            
            # Short spread: Primary overvalued vs hedge (Z-score > 2)
            if zscore > self.zscore_threshold:
                return {'side': 'short_spread', 'hedge_ratio': hedge_ratio, 'zscore': zscore}
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating signal: {e}")
            return None
    
    def get_balance(self) -> float:
        balance = self.exchange.fetch_balance()
        return balance['USDT']['free'] if 'USDT' in balance else 0
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        positions = self.exchange.fetch_positions([symbol])
        for pos in positions:
            if float(pos.get('contracts', 0)) != 0:
                return pos
        return None
    
    def open_positions(self, signal: Dict):
        """Open pair trade."""
        try:
            balance = self.get_balance()
            position_value = balance * (self.position_size_pct / 100)
            
            # Get current prices
            primary_ticker = self.exchange.fetch_ticker(self.primary_symbol)
            hedge_ticker = self.exchange.fetch_ticker(self.hedge_symbol)
            
            primary_price = primary_ticker['last']
            hedge_price = hedge_ticker['last']
            
            # Calculate position sizes
            primary_amount = position_value / primary_price
            hedge_amount = (position_value * signal['hedge_ratio']) / hedge_price
            
            primary_amount = max(0.001, round(primary_amount, 3))
            hedge_amount = max(0.001, round(hedge_amount, 3))
            
            # Set leverage
            try:
                self.exchange.set_leverage(self.leverage, self.primary_symbol)
                self.exchange.set_leverage(self.leverage, self.hedge_symbol)
            except:
                pass
            
            # Execute trades
            if signal['side'] == 'long_spread':
                # Long primary, short hedge
                self.exchange.create_market_buy_order(self.primary_symbol, primary_amount)
                self.exchange.create_market_sell_order(self.hedge_symbol, hedge_amount)
                logger.info(f"⚖️ LONG SPREAD | Long {self.primary_symbol} @ ${primary_price:.2f}, Short {self.hedge_symbol} @ ${hedge_price:.2f}")
            else:
                # Short primary, long hedge
                self.exchange.create_market_sell_order(self.primary_symbol, primary_amount)
                self.exchange.create_market_buy_order(self.hedge_symbol, hedge_amount)
                logger.info(f"⚖️ SHORT SPREAD | Short {self.primary_symbol} @ ${primary_price:.2f}, Long {self.hedge_symbol} @ ${hedge_price:.2f}")
            
            self.active_trade = {
                'side': signal['side'],
                'hedge_ratio': signal['hedge_ratio'],
                'entry_zscore': signal['zscore'],
                'primary_price': primary_price,
                'hedge_price': hedge_price
            }
            
        except Exception as e:
            logger.error(f"Failed to open positions: {e}")
    
    def check_exit(self):
        """Check if spread has converged."""
        if not self.active_trade:
            return
        
        try:
            primary_prices = self.fetch_prices(self.primary_symbol, self.lookback_period)
            hedge_prices = self.fetch_prices(self.hedge_symbol, self.lookback_period)
            
            zscore, _, _ = self.calculate_spread(primary_prices, hedge_prices)
            
            logger.info(f"Exit check | Current Z: {zscore:.2f} | Entry Z: {self.active_trade['entry_zscore']:.2f}")
            
            # Exit when spread reverts
            if abs(zscore) < self.exit_zscore:
                logger.info("Spread converged - closing positions")
                self.close_all_positions()
                
        except Exception as e:
            logger.error(f"Error checking exit: {e}")
    
    def close_all_positions(self):
        """Close all positions."""
        try:
            for symbol in [self.primary_symbol, self.hedge_symbol]:
                pos = self.get_position(symbol)
                if pos:
                    side = 'sell' if pos['side'] == 'long' else 'buy'
                    amount = abs(float(pos['contracts']))
                    self.exchange.create_market_order(symbol, side, amount, {'reduceOnly': True})
            
            self.active_trade = None
            logger.info("All positions closed")
            
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
    
    def run(self):
        logger.info(f"⚖️ Arbitrage bot started | {self.primary_symbol} vs {self.hedge_symbol}")
        
        while True:
            try:
                if self.active_trade:
                    self.check_exit()
                else:
                    signal = self.get_signal()
                    if signal:
                        self.open_positions(signal)
                    else:
                        logger.debug("No arbitrage signal")
                
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    bot = ArbitrageBot()
    bot.run()
