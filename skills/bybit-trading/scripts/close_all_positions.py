"""
Close all open positions on Bybit
Usage: python close_all_positions.py [--symbol SYMBOL]
"""
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('close_positions')

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import ccxt

def close_all_positions(symbol=None):
    """Close all open positions or a specific symbol."""
    
    # Initialize exchange
    exchange = ccxt.bybit({
        'apiKey': os.getenv('BYBIT_API_KEY'),
        'secret': os.getenv('BYBIT_API_SECRET'),
        'enableRateLimit': True,
        'options': {
            'defaultType': 'linear',
        }
    })
    
    try:
        # Fetch positions
        positions = exchange.fetch_positions()
        
        if symbol:
            positions = [p for p in positions if p['symbol'] == symbol and p['contracts'] != 0]
        else:
            positions = [p for p in positions if p['contracts'] != 0]
        
        if not positions:
            logger.info("No open positions found.")
            return
        
        logger.info(f"Found {len(positions)} open position(s)")
        
        for pos in positions:
            symbol = pos['symbol']
            side = pos['side']
            contracts = abs(pos['contracts'])
            pnl = pos.get('unrealizedPnl', 0)
            
            logger.info(f"Closing {symbol} {side} position: {contracts} contracts (PnL: {pnl:.2f} USDT)")
            
            # Determine order side (opposite of position)
            close_side = 'sell' if side == 'long' else 'buy'
            
            try:
                order = exchange.create_market_order(
                    symbol=symbol,
                    side=close_side,
                    amount=contracts,
                    params={'reduceOnly': True}
                )
                logger.info(f"✅ Closed {symbol} position - Order ID: {order['id']}")
            except Exception as e:
                logger.error(f"❌ Failed to close {symbol}: {e}")
        
        logger.info("All positions closed.")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == '__main__':
    symbol = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == '--symbol' else None
    close_all_positions(symbol)
