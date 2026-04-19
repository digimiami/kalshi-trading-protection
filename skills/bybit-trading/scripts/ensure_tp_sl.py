"""
Ensure TP/SL - Guardian script that verifies all positions have TP/SL set
Uses pybit which works with subaccounts
"""
import os
import sys
import time
import logging

# Load .env file
env_path = '/root/.openclaw/workspace/skills/bybit-trading/scripts/.env'
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from pybit.unified_trading import HTTP

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/bybit_bots/tpsl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('tp_sl_guardian')

class TPSLGuardian:
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        
        self.session = HTTP(
            testnet=False,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )
        
        self.default_tp_pct = float(os.getenv('TP_PCT', '0.8'))
        self.default_sl_pct = float(os.getenv('SL_PCT', '0.5'))
    
    def get_positions(self):
        """Get all open positions across all symbols."""
        try:
            all_positions = []
            symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT']
            
            for symbol in symbols:
                try:
                    resp = self.session.get_positions(category='linear', symbol=symbol)
                    positions = resp['result']['list']
                    for p in positions:
                        if float(p.get('size', 0)) != 0:
                            all_positions.append(p)
                except Exception as e:
                    logger.error(f"Failed to fetch {symbol}: {e}")
                    continue
            
            return all_positions
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            return []
    
    def has_tp_sl(self, position):
        """Check if position has TP and SL set."""
        tp = position.get('takeProfit', '0')
        sl = position.get('stopLoss', '0')
        has_tp = tp and float(tp) != 0
        has_sl = sl and float(sl) != 0
        return has_tp, has_sl
    
    def set_tp_sl(self, position):
        """Set TP/SL for a position."""
        try:
            symbol = position['symbol']
            # Use avgPrice (entry price) as base for TP/SL calculation
            mark_price = float(position.get('markPrice', 0))
            avg_price = float(position.get('avgPrice', 0))
            entry_price = float(position.get('entryPrice', 0))
            
            # Use avgPrice (actual entry) first, fall back to entryPrice
            if avg_price > 0:
                base_price = avg_price
                price_source = 'avgPrice'
            elif entry_price > 0:
                base_price = entry_price
                price_source = 'entryPrice'
            else:
                base_price = mark_price
                price_source = 'markPrice'
            
            side = position['side']
            
            logger.info(f"[DEBUG] {symbol}: side={side}, base_price={base_price} (from {price_source}), mark={mark_price}, avg={avg_price}, entry={entry_price}")
            logger.info(f"[DEBUG] TP%={self.default_tp_pct}, SL%={self.default_sl_pct}")
            
            if side == 'Buy':
                # For Buy (long): TP above entry, SL below entry
                tp_price = round(base_price * (1 + self.default_tp_pct / 100), 2)
                sl_price = round(base_price * (1 - self.default_sl_pct / 100), 2)
            else:  # Sell/Short
                # For Sell (short): TP below entry, SL above entry
                tp_price = round(base_price * (1 - self.default_tp_pct / 100), 2)
                sl_price = round(base_price * (1 + self.default_sl_pct / 100), 2)
            
            logger.info(f"[DEBUG] Calculated: TP={tp_price}, SL={sl_price}")
            
            self.session.set_trading_stop(
                category='linear',
                symbol=symbol,
                takeProfit=str(tp_price),
                stopLoss=str(sl_price),
                tpTriggerBy='MarkPrice',
                slTriggerBy='MarkPrice',
                positionIdx=0
            )
            
            logger.info(f"✅ Set TP/SL for {symbol} | TP: {tp_price} | SL: {sl_price}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set TP/SL: {e}")
            return False
    
    def check_all_positions(self):
        """Check all positions and ensure TP/SL is set."""
        positions = self.get_positions()
        
        if not positions:
            logger.info("No open positions to monitor")
            return
        
        for pos in positions:
            symbol = pos['symbol']
            has_tp, has_sl = self.has_tp_sl(pos)
            
            if has_tp and has_sl:
                logger.info(f"{symbol}: TP/SL already set ✓ (TP: {pos.get('takeProfit')}, SL: {pos.get('stopLoss')})")
                continue
            
            if not has_tp:
                logger.warning(f"{symbol}: Missing TP!")
            if not has_sl:
                logger.warning(f"{symbol}: Missing SL!")
            
            self.set_tp_sl(pos)
    
    def run(self):
        """Main loop."""
        logger.info("TP/SL Guardian started - monitoring positions...")
        
        while True:
            try:
                self.check_all_positions()
                time.sleep(30)
            except Exception as e:
                logger.error(f"Error in guardian loop: {e}")
                time.sleep(30)

def main():
    guardian = TPSLGuardian()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        print("🛡️ TP/SL Guardian Check - Running once...")
        guardian.check_all_positions()
        print("✅ Check complete. See /tmp/bybit_bots/tpsl.log for details.")
    else:
        guardian.run()

if __name__ == '__main__':
    main()
