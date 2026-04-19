"""
BTC Short-Only Bybit Futures Agent
Shorts BTC with 5x leverage, auto TP/SL, strict risk management
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
import ccxt
import pandas as pd
import pandas_ta as ta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/tmp/bybit_bots/btc_short_agent.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
SYMBOL = "BTC/USDT:USDT"
LEVERAGE = 5
RISK_PCT = 0.015  # 1.5% of balance per trade
TP_PCT = 0.04     # 4% take profit
SL_PCT = 0.02     # 2% stop loss
MIN_SCORE = 3     # Minimum signal score to trade (out of 5)
LOOP_INTERVAL = 900  # 15 minutes
MAX_DAILY_DD = 0.10  # Stop trading if down 10% today
MAX_CONSEC_LOSSES = 3  # Stop after 3 consecutive losses

class BybitShortClient:
    """Bybit API wrapper for short-only trading."""
    
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        
        self.exchange = ccxt.bybit({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'options': {'defaultType': 'swap'}
        })
        
        log.info(f"Bybit client initialized | Testnet: {self.exchange.testnet}")
    
    def set_leverage(self):
        """Set leverage to 5x."""
        try:
            self.exchange.set_leverage(LEVERAGE, SYMBOL)
            log.info(f"Leverage set to {LEVERAGE}x")
        except Exception as e:
            log.warning(f"Leverage already set or error: {e}")
    
    def get_balance(self) -> float:
        """Get USDT balance."""
        balance = self.exchange.fetch_balance()
        usdt = balance.get('USDT', {})
        total = usdt.get('total', 0)
        log.info(f"Account balance: ${total:.2f}")
        return total
    
    def get_price(self) -> float:
        """Get current BTC price."""
        ticker = self.exchange.fetch_ticker(SYMBOL)
        return ticker['last']
    
    def get_klines(self, timeframe='15m', limit=250) -> pd.DataFrame:
        """Fetch OHLCV data."""
        ohlcv = self.exchange.fetch_ohlcv(SYMBOL, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = df.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': float})
        return df
    
    def get_funding_rate(self) -> float:
        """Get current funding rate."""
        try:
            funding = self.exchange.fetchFundingRate(SYMBOL)
            return funding['fundingRate']
        except:
            # Fallback: try to get from ticker
            ticker = self.exchange.fetch_ticker(SYMBOL)
            return ticker.get('fundingRate', 0)
    
    def get_open_position(self) -> Optional[Dict]:
        """Check for open position."""
        positions = self.exchange.fetch_positions([SYMBOL])
        for pos in positions:
            contracts = float(pos.get('contracts', 0))
            if contracts != 0:
                return pos
        return None
    
    def place_short_market(self, qty: float) -> Dict:
        """Place short market order."""
        order = self.exchange.create_market_sell_order(SYMBOL, qty)
        log.info(f"SHORT placed | qty={qty} | order={order.get('id')}")
        return order
    
    def place_tp_sl(self, tp_price: float, sl_price: float):
        """Set TP and SL on open position."""
        try:
            # Bybit unified trading - set trading stop
            self.exchange.set_position_mode(True, SYMBOL)  # Hedge mode
            
            # Set TP/SL using edit_position or trading_stop
            params = {
                'takeProfit': tp_price,
                'stopLoss': sl_price,
                'tpTriggerBy': 'MarkPrice',
                'slTriggerBy': 'MarkPrice'
            }
            
            # Try to set TP/SL
            self.exchange.private_post_v5_position_trading_stop({
                'category': 'linear',
                'symbol': SYMBOL.replace('/', '').replace(':USDT', ''),
                'takeProfit': str(round(tp_price, 2)),
                'stopLoss': str(round(sl_price, 2)),
                'tpTriggerBy': 'MarkPrice',
                'slTriggerBy': 'MarkPrice',
                'positionIdx': 0
            })
            
            log.info(f"TP/SL set | TP={tp_price:.2f} | SL={sl_price:.2f}")
        except Exception as e:
            log.error(f"Failed to set TP/SL: {e}")
            raise
    
    def close_position(self, qty: float):
        """Market close position."""
        order = self.exchange.create_market_buy_order(SYMBOL, qty, {'reduceOnly': True})
        log.info(f"Position CLOSED | qty={qty}")
        return order


class SignalEngine:
    """Technical analysis and signal generation."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._compute_indicators()
    
    def _compute_indicators(self):
        """Calculate technical indicators."""
        self.df['ema200'] = ta.ema(self.df['close'], length=200)
        self.df['rsi'] = ta.rsi(self.df['close'], length=14)
        macd = ta.macd(self.df['close'])
        if macd is not None:
            self.df['macd'] = macd['MACD_12_26_9']
            self.df['macd_signal'] = macd['MACDs_12_26_9']
        else:
            self.df['macd'] = 0
            self.df['macd_signal'] = 0
    
    def evaluate(self, funding_rate: float) -> Dict:
        """Evaluate short entry conditions."""
        last = self.df.iloc[-1]
        prev = self.df.iloc[-2] if len(self.df) > 1 else last
        price = last['close']
        
        conditions = {
            'below_ema200': price < last['ema200'] if pd.notna(last['ema200']) else False,
            'rsi_bearish': last['rsi'] < 55 and last['rsi'] < prev['rsi'] if pd.notna(last['rsi']) else False,
            'near_resistance': self._near_resistance(price),
            'funding_positive': funding_rate > 0.0001,
            'macd_bearish': last['macd'] < last['macd_signal'] if pd.notna(last['macd']) else False,
        }
        
        score = sum(conditions.values())
        
        return {
            'price': price,
            'ema200': last['ema200'],
            'rsi': last['rsi'],
            'funding': funding_rate,
            'conditions': conditions,
            'score': score,
        }
    
    def _near_resistance(self, price: float, window: int = 50, tolerance: float = 0.005) -> bool:
        """Check if price is near recent resistance."""
        if len(self.df) < window:
            return False
        highs = self.df['high'].tail(window)
        recent_high = highs.max()
        return abs(price - recent_high) / recent_high < tolerance


def calc_position_size(balance: float, entry: float, sl: float, confidence: float = 1.0) -> float:
    """Calculate position size based on risk."""
    risk_amount = balance * RISK_PCT * confidence
    price_risk = abs(entry - sl)
    
    if price_risk == 0:
        price_risk = entry * SL_PCT  # Fallback
    
    qty = (risk_amount / price_risk) * LEVERAGE
    qty = max(0.001, round(qty, 3))
    
    log.info(f"Position size: {qty} BTC | Risk: ${risk_amount:.2f} | Price risk: ${price_risk:.2f}")
    return qty


class TradeLogger:
    """Log trades to JSON file."""
    
    def __init__(self, filepath="/tmp/bybit_bots/btc_trades.json"):
        self.filepath = filepath
        self.trades = self._load()
    
    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath) as f:
                return json.load(f)
        return []
    
    def log(self, trade: Dict):
        trade['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        self.trades.append(trade)
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as f:
            json.dump(self.trades, f, indent=2)
    
    def consecutive_losses(self) -> int:
        closed = [t for t in self.trades if t.get('result') in ('SL_HIT', 'MANUAL_CLOSE')]
        count = 0
        for t in reversed(closed):
            if t['result'] == 'SL_HIT':
                count += 1
            else:
                break
        return count
    
    def daily_pnl(self) -> float:
        today = datetime.utcnow().strftime('%Y-%m-%d')
        return sum(
            t.get('pnl_usdt', 0) for t in self.trades 
            if t.get('timestamp', '').startswith(today)
        )


class BTCShortAgent:
    """Main trading agent."""
    
    def __init__(self):
        self.bybit = BybitShortClient()
        self.logger = TradeLogger()
        self.bybit.set_leverage()
    
    def run_cycle(self):
        """Execute one trading cycle."""
        log.info("=" * 60)
        log.info("Starting trading cycle")
        
        # ── Safety checks ──────────────────────────────────────────
        balance = self.bybit.get_balance()
        daily_pnl = self.logger.daily_pnl()
        consec_losses = self.logger.consecutive_losses()
        
        if balance < 100:
            log.warning(f"Balance ${balance:.2f} below minimum. Stopping.")
            return False
        
        if daily_pnl < -(balance * MAX_DAILY_DD):
            log.warning(f"Daily drawdown limit hit (${daily_pnl:.2f}). Stopping.")
            return False
        
        if consec_losses >= MAX_CONSEC_LOSSES:
            log.warning(f"{consec_losses} consecutive losses. Pausing for review.")
            return False
        
        # ── Check open position ─────────────────────────────────────
        position = self.bybit.get_open_position()
        if position:
            unrealized = float(position.get('unrealizedPnl', 0))
            entry = float(position.get('entryPrice', 0))
            size = float(position.get('contracts', 0))
            current = self.bybit.get_price()
            
            log.info(f"Position open | Size: {size} BTC | Entry: ${entry:.2f} | Current: ${current:.2f} | PnL: ${unrealized:.2f}")
            
            # Check for sharp reversal (>3% pump)
            if current > entry * 1.03:
                log.warning("Sharp reversal detected! Emergency closing position.")
                self.bybit.close_position(size)
                self.logger.log({
                    'action': 'CLOSE',
                    'result': 'MANUAL_CLOSE',
                    'reason': 'Emergency - sharp reversal',
                    'entry': entry,
                    'exit': current,
                    'pnl_usdt': unrealized
                })
            return True
        
        # ── Fetch data & compute signals ────────────────────────────
        df = self.bybit.get_klines(timeframe='15m', limit=250)
        funding_rate = self.bybit.get_funding_rate()
        
        engine = SignalEngine(df)
        signal = engine.evaluate(funding_rate)
        
        log.info(f"Signal | Price=${signal['price']:.2f} | EMA200=${signal['ema200']:.2f} "
                 f"| RSI={signal['rsi']:.1f} | Funding={signal['funding']*100:.4f}% "
                 f"| Score={signal['score']}/5")
        
        for name, val in signal['conditions'].items():
            log.info(f" {'✅' if val else '❌'} {name}")
        
        # ── Entry decision ──────────────────────────────────────────
        if signal['score'] < MIN_SCORE:
            log.info(f"Score {signal['score']}/5 — below threshold. No trade.")
            return True
        
        # Don't short if funding is negative (we'd pay to hold)
        if funding_rate < 0:
            log.info("Funding rate negative — shorts would pay. No trade.")
            return True
        
        confidence = 1.0 if signal['score'] >= 4 else 0.5
        entry_price = signal['price']
        tp_price = round(entry_price * (1 - TP_PCT), 2)
        sl_price = round(entry_price * (1 + SL_PCT), 2)
        qty = calc_position_size(balance, entry_price, sl_price, confidence)
        
        log.info(f"Entering SHORT | Entry=${entry_price:.2f} | TP=${tp_price:.2f} | SL=${sl_price:.2f} | Qty={qty} BTC")
        
        # ── Execute ─────────────────────────────────────────────────
        try:
            order = self.bybit.place_short_market(qty)
            time.sleep(1)  # Wait for fill
            self.bybit.place_tp_sl(tp_price, sl_price)
            
            self.logger.log({
                'action': 'SHORT',
                'entry': entry_price,
                'tp': tp_price,
                'sl': sl_price,
                'size': qty,
                'leverage': LEVERAGE,
                'score': signal['score'],
                'confidence': confidence,
                'balance': balance,
                'funding': signal['funding'],
                'rsi': signal['rsi'],
                'conditions': signal['conditions'],
                'order_id': order.get('id'),
                'result': 'OPEN'
            })
            
            log.info("✅ Trade executed and logged successfully.")
            
        except Exception as e:
            log.error(f"❌ Order execution failed: {e}")
        
        return True
    
    def run(self):
        """Main loop."""
        log.info("🤖 BTC Short Agent STARTED")
        log.info(f"Symbol: {SYMBOL} | Leverage: {LEVERAGE}x | Interval: {LOOP_INTERVAL}s")
        log.info(f"TP: {TP_PCT*100:.0f}% | SL: {SL_PCT*100:.0f}% | Min Score: {MIN_SCORE}/5")
        
        while True:
            try:
                if not self.run_cycle():
                    log.warning("Stopping agent due to safety condition.")
                    break
            except Exception as e:
                log.error(f"Cycle error: {e}")
            
            log.info(f"Sleeping {LOOP_INTERVAL}s until next cycle...")
            time.sleep(LOOP_INTERVAL)


def main():
    """Entry point."""
    agent = BTCShortAgent()
    agent.run()


if __name__ == '__main__':
    main()
