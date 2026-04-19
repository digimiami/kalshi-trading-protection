"""
Auto-Parameter Adjuster
Real-time parameter tuning based on market conditions and performance
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Optional
import pandas as pd
import numpy as np
from pybit.unified_trading import HTTP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('auto_adjuster')

class AutoParameterAdjuster:
    """
    Automatically adjusts bot parameters in real-time based on:
    - Market volatility
    - Recent win rate
    - Trend strength
    - Time of day (market session)
    """
    
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        
        self.session = HTTP(
            testnet=False,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )
        
        self.params_file = '/tmp/bybit_bots/dynamic_params.json'
        self.adjustment_history = []
        
        # Base configurations
        self.base_configs = {
            'scalping': {
                'rsi_entry_long': 30,
                'rsi_entry_short': 70,
                'tp_pct': 0.8,
                'sl_pct': 0.5,
                'position_size_pct': 5.0
            },
            'grid': {
                'grid_levels': 10,
                'grid_spacing': 1.0,
                'grid_position_size': 500
            },
            'breakout': {
                'lookback_period': 20,
                'volume_threshold': 1.5,
                'atr_multiplier_tp': 2.0,
                'atr_multiplier_sl': 1.0
            }
        }
        
        self.current_configs = self.load_configs()
    
    def load_configs(self) -> Dict:
        """Load current configurations"""
        if os.path.exists(self.params_file):
            with open(self.params_file, 'r') as f:
                return json.load(f)
        return self.base_configs.copy()
    
    def save_configs(self):
        """Save configurations"""
        with open(self.params_file, 'w') as f:
            json.dump(self.current_configs, f, indent=2)
    
    def get_market_conditions(self, symbol: str = 'BTCUSDT') -> Dict:
        """Get current market conditions"""
        try:
            resp = self.session.get_kline(
                category='linear',
                symbol=symbol,
                interval='15',
                limit=96  # 24 hours of 15m candles
            )
            
            data = resp['result']['list']
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df = df.astype({'close': float, 'high': float, 'low': float, 'volume': float})
            
            # Volatility (ATR %)
            tr1 = df['high'] - df['low']
            tr2 = abs(df['high'] - df['close'].shift())
            tr3 = abs(df['low'] - df['close'].shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(14).mean()
            volatility = (atr / df['close'] * 100).iloc[-1]
            
            # Trend
            df['sma20'] = df['close'].rolling(20).mean()
            trend = (df['close'].iloc[-1] / df['sma20'].iloc[-1] - 1) * 100
            
            # Volume
            volume_ratio = df['volume'].iloc[-1] / df['volume'].rolling(20).mean().iloc[-1]
            
            return {
                'volatility': volatility,
                'trend': trend,
                'volume_ratio': volume_ratio,
                'hour': datetime.now().hour
            }
        except Exception as e:
            logger.error(f"Error getting market conditions: {e}")
            return {'volatility': 2.0, 'trend': 0, 'volume_ratio': 1.0, 'hour': 12}
    
    def calculate_adjustments(self, conditions: Dict) -> Dict:
        """Calculate parameter adjustments based on conditions"""
        adjustments = {}
        
        volatility = conditions['volatility']
        trend = conditions['trend']
        volume = conditions['volume_ratio']
        hour = conditions['hour']
        
        # === SCALPING ADJUSTMENTS ===
        scalping_adj = {}
        
        # High volatility = wider TP/SL
        if volatility > 3.0:
            scalping_adj['tp_pct'] = 1.2  # Increase from 0.8
            scalping_adj['sl_pct'] = 0.8  # Increase from 0.5
            scalping_adj['position_size_pct'] = 3.0  # Reduce size
            logger.info("High volatility detected - widening scalping TP/SL")
        elif volatility < 1.5:
            scalping_adj['tp_pct'] = 0.5  # Tighten TP
            scalping_adj['sl_pct'] = 0.3  # Tighten SL
            logger.info("Low volatility - tightening scalping targets")
        else:
            scalping_adj['tp_pct'] = 0.8
            scalping_adj['sl_pct'] = 0.5
        
        # Strong trend = adjust RSI thresholds
        if trend > 2:  # Uptrend
            scalping_adj['rsi_entry_long'] = 35  # Less strict for longs
            scalping_adj['rsi_entry_short'] = 75  # More strict for shorts
        elif trend < -2:  # Downtrend
            scalping_adj['rsi_entry_long'] = 25  # More strict for longs
            scalping_adj['rsi_entry_short'] = 65  # Less strict for shorts
        else:
            scalping_adj['rsi_entry_long'] = 30
            scalping_adj['rsi_entry_short'] = 70
        
        adjustments['scalping'] = scalping_adj
        
        # === GRID ADJUSTMENTS ===
        grid_adj = {}
        
        # High volatility = wider grid spacing, fewer levels
        if volatility > 3.0:
            grid_adj['grid_spacing'] = 2.0
            grid_adj['grid_levels'] = 8
            grid_adj['grid_position_size'] = 300  # Smaller per level
            logger.info("High volatility - widening grid, reducing levels")
        elif volatility < 1.5:
            grid_adj['grid_spacing'] = 0.5
            grid_adj['grid_levels'] = 15
            grid_adj['grid_position_size'] = 600
            logger.info("Low volatility - tightening grid, more levels")
        else:
            grid_adj['grid_spacing'] = 1.0
            grid_adj['grid_levels'] = 10
            grid_adj['grid_position_size'] = 500
        
        adjustments['grid'] = grid_adj
        
        # === BREAKOUT ADJUSTMENTS ===
        breakout_adj = {}
        
        # High volume = lower threshold for breakout confirmation
        if volume > 2.0:
            breakout_adj['volume_threshold'] = 1.2
            logger.info("High volume - lowering breakout threshold")
        else:
            breakout_adj['volume_threshold'] = 1.5
        
        # High volatility = wider TP/SL using ATR
        if volatility > 3.0:
            breakout_adj['atr_multiplier_tp'] = 3.0
            breakout_adj['atr_multiplier_sl'] = 1.5
        else:
            breakout_adj['atr_multiplier_tp'] = 2.0
            breakout_adj['atr_multiplier_sl'] = 1.0
        
        adjustments['breakout'] = breakout_adj
        
        return adjustments
    
    def apply_adjustments(self, adjustments: Dict):
        """Apply calculated adjustments to bot configs"""
        env_file = '/root/.openclaw/workspace/skills/bybit-trading/scripts/.env'
        
        # Read current .env
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Track changes
        changes_made = []
        
        for strategy, params in adjustments.items():
            for param, value in params.items():
                # Update current config
                if strategy in self.current_configs:
                    self.current_configs[strategy][param] = value
                
                # Update .env file
                env_var = f"{param.upper()}="
                found = False
                for i, line in enumerate(lines):
                    if line.startswith(env_var):
                        lines[i] = f"{env_var}{value}\n"
                        found = True
                        changes_made.append(f"{param}: {value}")
                        break
                
                if not found:
                    lines.append(f"{env_var}{value}\n")
                    changes_made.append(f"{param}: {value}")
        
        # Write updated .env
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        # Save configs
        self.save_configs()
        
        # Log changes
        if changes_made:
            logger.info(f"Applied adjustments: {', '.join(changes_made)}")
            self.adjustment_history.append({
                'timestamp': datetime.now().isoformat(),
                'changes': changes_made
            })
    
    def get_performance_feedback(self) -> Dict:
        """Get recent performance metrics"""
        try:
            resp = self.session.get_closed_pnl(category='linear', limit=50)
            trades = resp['result']['list']
            
            if not trades:
                return {'win_rate': 0.5, 'avg_pnl': 0}
            
            pnls = [float(t['closedPnl']) for t in trades]
            wins = sum(1 for p in pnls if p > 0)
            win_rate = wins / len(pnls)
            avg_pnl = sum(pnls) / len(pnls)
            
            return {
                'win_rate': win_rate,
                'avg_pnl': avg_pnl,
                'total_trades': len(pnls)
            }
        except Exception as e:
            logger.error(f"Error getting performance: {e}")
            return {'win_rate': 0.5, 'avg_pnl': 0}
    
    def adaptive_adjustment(self):
        """Adjust based on recent performance"""
        performance = self.get_performance_feedback()
        
        logger.info(f"Recent performance: {performance['win_rate']:.1%} win rate, "
                   f"avg PnL: ${performance['avg_pnl']:.2f}")
        
        # If win rate is low, tighten risk
        if performance['win_rate'] < 0.4 and performance['total_trades'] > 10:
            logger.warning("Low win rate detected - tightening risk parameters")
            adjustments = {
                'scalping': {
                    'position_size_pct': 2.0,  # Reduce size
                    'sl_pct': 0.4  # Tighter stops
                }
            }
            self.apply_adjustments(adjustments)
        
        # If win rate is high, can increase size slightly
        elif performance['win_rate'] > 0.6 and performance['avg_pnl'] > 0:
            logger.info("Good performance - maintaining or slightly increasing size")
            adjustments = {
                'scalping': {
                    'position_size_pct': 6.0  # Slightly larger
                }
            }
            self.apply_adjustments(adjustments)
    
    def run(self):
        """Main adjustment loop"""
        logger.info("⚙️ AUTO-PARAMETER ADJUSTER STARTED")
        
        while True:
            try:
                # 1. Get market conditions
                conditions = self.get_market_conditions()
                logger.info(f"Market: vol={conditions['volatility']:.2f}%, "
                           f"trend={conditions['trend']:.2f}%, "
                           f"volume={conditions['volume_ratio']:.2f}x")
                
                # 2. Calculate adjustments
                adjustments = self.calculate_adjustments(conditions)
                
                # 3. Apply adjustments
                self.apply_adjustments(adjustments)
                
                # 4. Check performance feedback (every 4th cycle)
                if len(self.adjustment_history) % 4 == 0:
                    self.adaptive_adjustment()
                
                # 5. Sleep
                logger.info("Sleeping 30 minutes until next adjustment...")
                time.sleep(1800)  # 30 minutes
                
            except Exception as e:
                logger.error(f"Error in adjuster: {e}")
                time.sleep(600)

if __name__ == '__main__':
    adjuster = AutoParameterAdjuster()
    adjuster.run()
