"""
Grid Trading Bot
Places buy/sell orders at regular intervals
"""
import os
import time
import logging
from typing import List, Dict, Optional
import ccxt
import config  # Loads .env

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('grid_bot')

class GridBot:
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        self.symbol = os.getenv('TRADING_SYMBOL', 'ETH/USDT:USDT')
        self.leverage = int(os.getenv('LEVERAGE', '3'))
        self.grid_levels = int(os.getenv('GRID_LEVELS', '10'))
        self.grid_spacing = float(os.getenv('GRID_SPACING', '1.0'))  # % between grids
        self.position_size = float(os.getenv('POSITION_SIZE_USDT', '50'))  # Fixed $50 per grid level
        
        self.exchange = ccxt.bybit({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'options': {'defaultType': 'swap'}
        })
        self.active_orders = []
        self.grid_prices = []
        
    def get_current_price(self) -> float:
        ticker = self.exchange.fetch_ticker(self.symbol)
        return ticker['last']
    
    def calculate_grid(self, center_price: float) -> List[float]:
        """Calculate grid price levels."""
        grids = []
        half_levels = self.grid_levels // 2
        
        for i in range(-half_levels, half_levels + 1):
            price = center_price * (1 + (i * self.grid_spacing / 100))
            grids.append(price)
        
        return sorted(grids)
    
    def cancel_all_orders(self):
        """Cancel all open orders."""
        try:
            self.exchange.cancel_all_orders(self.symbol)
            logger.info("All orders cancelled")
        except Exception as e:
            logger.error(f"Cancel failed: {e}")
    
    def place_grid_orders(self):
        """Place buy and sell orders at grid levels."""
        try:
            self.cancel_all_orders()
            
            current_price = self.get_current_price()
            self.grid_prices = self.calculate_grid(current_price)
            
            # Calculate amount per grid - ensure minimum 0.001 BTC
            amount = (self.position_size / current_price) / self.leverage
            amount = max(0.001, round(amount, 3))  # Minimum 0.001 BTC for Bybit
            
            for price in self.grid_prices:
                if price < current_price:
                    # Place buy order below current price
                    try:
                        order = self.exchange.create_limit_buy_order(
                            self.symbol, amount, price
                        )
                        logger.info(f"Grid buy order placed @ {price:.2f}")
                    except Exception as e:
                        logger.error(f"Buy order failed @ {price}: {e}")
                        
                elif price > current_price:
                    # Place sell order above current price
                    try:
                        order = self.exchange.create_limit_sell_order(
                            self.symbol, amount, price
                        )
                        logger.info(f"Grid sell order placed @ {price:.2f}")
                    except Exception as e:
                        logger.error(f"Sell order failed @ {price}: {e}")
            
            logger.info(f"Grid initialized with {len(self.grid_prices)} levels around {current_price:.2f}")
            
        except Exception as e:
            logger.error(f"Grid placement failed: {e}")
    
    def get_open_orders(self) -> List[Dict]:
        """Get list of open orders."""
        try:
            return self.exchange.fetch_open_orders(self.symbol)
        except Exception as e:
            logger.error(f"Fetch orders failed: {e}")
            return []
    
    def rebalance_grid(self):
        """Check if grid needs rebalancing."""
        try:
            current_price = self.get_current_price()
            open_orders = self.get_open_orders()
            
            # If price moved significantly or too few orders, rebuild grid
            if len(open_orders) < self.grid_levels * 0.7:
                logger.info("Grid depleted - rebalancing...")
                self.place_grid_orders()
                
        except Exception as e:
            logger.error(f"Rebalance failed: {e}")
    
    def run(self):
        """Main loop."""
        logger.info(f"Grid bot started | {self.symbol} | {self.grid_levels} levels")
        
        # Initial grid setup
        self.place_grid_orders()
        
        while True:
            try:
                self.rebalance_grid()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Loop error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    bot = GridBot()
    bot.run()
