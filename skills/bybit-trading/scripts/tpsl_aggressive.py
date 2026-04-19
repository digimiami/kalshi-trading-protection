#!/usr/bin/env python3
"""
AGGRESSIVE TP/SL Guardian - Fixes ETH protection issues
Checks every 10 seconds, immediately re-applies TP/SL if missing
"""
import os
import sys
import time
import logging
from pybit.unified_trading import HTTP

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/bybit_bots/tpsl_aggressive.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('tpsl_aggressive')

# Track position sizes to detect changes
position_tracker = {}

def get_session():
    with open('/root/.openclaw/workspace/skills/bybit-trading/scripts/.env') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v
    
    return HTTP(
        testnet=False,
        api_key=os.getenv('BYBIT_API_KEY'),
        api_secret=os.getenv('BYBIT_API_SECRET'),
    )

def check_and_fix_position(session, symbol):
    """Check position and fix TP/SL if missing"""
    global position_tracker
    
    try:
        resp = session.get_positions(category='linear', symbol=symbol)
        
        for p in resp['result']['list']:
            size = float(p.get('size', 0))
            
            if size == 0:
                # Position closed, clear tracker
                if symbol in position_tracker:
                    del position_tracker[symbol]
                continue
            
            side = p['side']  # 'Buy' = LONG, 'Sell' = SHORT
            entry = float(p.get('avgPrice') or p.get('entryPrice') or 0)
            tp = p.get('takeProfit', '')
            sl = p.get('stopLoss', '')
            
            has_tp = tp and float(tp) > 0
            has_sl = sl and float(sl) > 0
            
            # Check if position size changed (pyramiding)
            size_changed = symbol in position_tracker and position_tracker[symbol] != size
            position_tracker[symbol] = size
            
            if not has_tp or not has_sl or size_changed:
                if size_changed:
                    logger.warning(f'{symbol}: Position size changed ({position_tracker.get(symbol, 0)} -> {size}), TP/SL cleared!')
                else:
                    logger.warning(f'{symbol}: Missing TP/SL - Entry: {entry}, Size: {size}')
                
                # Calculate TP/SL based on side
                if side == 'Buy':  # LONG
                    tp_price = round(entry * 1.02, 2)  # +2%
                    sl_price = round(entry * 0.985, 2)  # -1.5%
                else:  # SHORT
                    tp_price = round(entry * 0.98, 2)  # -2%
                    sl_price = round(entry * 1.015, 2)  # +1.5%
                
                # Apply TP/SL
                try:
                    session.set_trading_stop(
                        category='linear',
                        symbol=symbol,
                        takeProfit=str(tp_price),
                        stopLoss=str(sl_price),
                        tpTriggerBy='MarkPrice',
                        slTriggerBy='MarkPrice',
                        positionIdx=0
                    )
                    logger.info(f'✅ {symbol}: TP/SL SET | TP: {tp_price} | SL: {sl_price}')
                    return True
                except Exception as e:
                    logger.error(f'❌ {symbol}: Failed to set TP/SL - {e}')
                    return False
            else:
                logger.debug(f'{symbol}: Protected | TP: {tp} | SL: {sl}')
                
    except Exception as e:
        logger.error(f'Error checking {symbol}: {e}')
        return False
    
    return True

def main():
    logger.info('🛡️ AGGRESSIVE TP/SL GUARDIAN STARTED')
    logger.info('Checking every 10 seconds...')
    
    session = get_session()
    symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']
    
    while True:
        try:
            for symbol in symbols:
                check_and_fix_position(session, symbol)
            
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            logger.error(f'Main loop error: {e}')
            time.sleep(5)

if __name__ == '__main__':
    main()
