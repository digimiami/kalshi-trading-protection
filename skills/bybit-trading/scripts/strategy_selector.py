"""
Strategy Selector - Market Regime Detection
Automatically selects best strategy based on market conditions
"""
import os
import time
import logging
from datetime import datetime
from typing import Dict, Optional
import ccxt
import config
import pandas as pd
import pandas_ta as ta
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('strategy_selector')

class StrategySelector:
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        self.symbol = os.getenv('TRADING_SYMBOL', 'BTC/USDT:USDT')
        
        self.exchange = ccxt.bybit({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'options': {'defaultType': 'swap'}
        })
        
        self.current_regime = None
        self.recommended_strategy = None
        
    def fetch_ohlcv(self, timeframe='1h', limit: int = 100) -> pd.DataFrame:
        """Fetch OHLCV data."""
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = df.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': float})
        return df
    
    def detect_market_regime(self, df: pd.DataFrame) -> Dict:
        """
        Detect current market regime.
        Returns: {
            'regime': 'trending_up'/'trending_down'/'ranging'/'volatile',
            'strength': 0-100,
            'volatility': 'low'/'medium'/'high',
            'recommended_strategy': str
        }
        """
        # Calculate indicators
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # ADX for trend strength
        adx = ta.adx(df['high'], df['low'], df['close'], length=14)
        if adx is not None:
            df['adx'] = adx['ADX_14']
        else:
            df['adx'] = 20
        
        # ATR for volatility
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        df['atr_pct'] = df['atr'] / df['close'] * 100
        
        # Bollinger Bands width
        bb = ta.bbands(df['close'], length=20, std=2.0)
        if bb is not None:
            df['bb_width'] = (bb['BBU_20_2.0'] - bb['BBL_20_2.0']) / df['close'] * 100
        else:
            df['bb_width'] = 5
        
        # RSI
        df['rsi'] = ta.rsi(df['close'], length=14)
        
        latest = df.iloc[-1]
        
        # Determine trend
        trend_up = latest['close'] > latest['sma_20'] and latest['sma_20'] > latest['sma_50']
        trend_down = latest['close'] < latest['sma_20'] and latest['sma_20'] < latest['sma_50']
        adx_value = latest['adx']
        
        # Determine volatility
        atr_pct = latest['atr_pct']
        if atr_pct < 1.5:
            volatility = 'low'
        elif atr_pct < 3.0:
            volatility = 'medium'
        else:
            volatility = 'high'
        
        # Classify regime
        if adx_value > 25:
            # Strong trend
            if trend_up:
                regime = 'trending_up'
                strength = min(100, int(adx_value * 2))
                recommended = 'momentum'  # Trend following
            elif trend_down:
                regime = 'trending_down'
                strength = min(100, int(adx_value * 2))
                recommended = 'momentum'  # Trend following (short)
            else:
                regime = 'trending'
                strength = min(100, int(adx_value * 2))
                recommended = 'breakout'  # Breakout trading
        elif volatility == 'high':
            regime = 'volatile'
            strength = min(100, int(atr_pct * 20))
            recommended = 'scalping'  # Quick in/out
        elif latest['bb_width'] < 5:
            regime = 'ranging'
            strength = 50
            recommended = 'mean_reversion'  # Buy low, sell high
        else:
            regime = 'uncertain'
            strength = 30
            recommended = 'grid'  # Grid trading
        
        return {
            'regime': regime,
            'strength': strength,
            'volatility': volatility,
            'atr_pct': round(atr_pct, 2),
            'adx': round(adx_value, 1),
            'rsi': round(latest['rsi'], 1) if not np.isnan(latest['rsi']) else 50,
            'recommended_strategy': recommended
        }
    
    def get_strategy_allocation(self, regime_data: Dict) -> Dict:
        """
        Get portfolio allocation across strategies based on regime.
        """
        recommended = regime_data['recommended_strategy']
        
        allocations = {
            'scalping': 0,
            'mean_reversion': 0,
            'momentum': 0,
            'grid': 0,
            'breakout': 0,
            'arbitrage': 0,
            'ml': 10  # Always keep some ML running
        }
        
        if recommended == 'momentum':
            allocations['momentum'] = 50
            allocations['breakout'] = 25
            allocations['ml'] = 15
            allocations['scalping'] = 10
        elif recommended == 'mean_reversion':
            allocations['mean_reversion'] = 50
            allocations['grid'] = 30
            allocations['ml'] = 10
            allocations['scalping'] = 10
        elif recommended == 'scalping':
            allocations['scalping'] = 60
            allocations['ml'] = 20
            allocations['momentum'] = 10
            allocations['grid'] = 10
        elif recommended == 'breakout':
            allocations['breakout'] = 50
            allocations['momentum'] = 30
            allocations['ml'] = 20
        elif recommended == 'grid':
            allocations['grid'] = 60
            allocations['mean_reversion'] = 20
            allocations['ml'] = 10
            allocations['scalping'] = 10
        else:
            # Balanced
            allocations['momentum'] = 25
            allocations['mean_reversion'] = 25
            allocations['grid'] = 20
            allocations['ml'] = 20
            allocations['scalping'] = 10
        
        return allocations
    
    def analyze_all_pairs(self) -> Dict:
        """Analyze all trading pairs."""
        pairs = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'XRP/USDT:USDT']
        results = {}
        
        for pair in pairs:
            try:
                ohlcv = self.exchange.fetch_ohlcv(pair, '1h', limit=100)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df = df.astype({'close': float, 'high': float, 'low': float, 'volume': float})
                
                regime_data = self.detect_market_regime(df)
                results[pair] = regime_data
            except Exception as e:
                logger.error(f"Error analyzing {pair}: {e}")
        
        return results
    
    def generate_report(self) -> str:
        """Generate strategy recommendation report."""
        results = self.analyze_all_pairs()
        
        report = []
        report.append("=" * 70)
        report.append("📊 MARKET REGIME ANALYSIS & STRATEGY RECOMMENDATIONS")
        report.append("=" * 70)
        report.append("")
        
        for pair, data in results.items():
            report.append(f"📈 {pair}:")
            report.append(f"   Regime: {data['regime'].upper()}")
            report.append(f"   Trend Strength: {data['strength']}/100")
            report.append(f"   Volatility: {data['volatility'].upper()} ({data['atr_pct']}%)")
            report.append(f"   ADX: {data['adx']}")
            report.append(f"   RSI: {data['rsi']}")
            report.append(f"   ➤ Recommended: {data['recommended_strategy'].upper()}")
            
            allocation = self.get_strategy_allocation(data)
            active_strats = [f"{k}({v}%)" for k, v in allocation.items() if v > 0]
            report.append(f"   Allocation: {', '.join(active_strats)}")
            report.append("")
        
        report.append("=" * 70)
        return "\n".join(report)
    
    def run(self):
        """Main loop - analyze and report."""
        logger.info("📊 Strategy Selector started - Monitoring market regimes")
        
        while True:
            try:
                report = self.generate_report()
                logger.info("\n" + report)
                
                # Save to file
                os.makedirs('/tmp/bybit_bots', exist_ok=True)
                with open('/tmp/bybit_bots/regime_report.txt', 'w') as f:
                    f.write(report)
                
                time.sleep(3600)  # Analyze every hour
                
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(300)

if __name__ == '__main__':
    selector = StrategySelector()
    selector.run()
