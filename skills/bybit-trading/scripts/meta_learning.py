"""
Meta-Learning Trading System
Self-improving AI that optimizes parameters and evolves strategies
"""
import os
import json
import time
import logging
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('meta_learning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MetaLearning')

@dataclass
class TradeExperience:
    """Individual trade experience for learning"""
    timestamp: str
    strategy: str
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    qty: float
    pnl: float
    pnl_pct: float
    holding_time: float
    market_regime: str
    entry_score: float
    exit_reason: str
    parameters: Dict[str, Any]
    market_features: Dict[str, float]
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ParameterSet:
    """Parameter configuration for a strategy"""
    strategy_name: str
    parameters: Dict[str, Any]
    performance_score: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    trade_count: int = 0
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

class ExperienceReplayBuffer:
    """Store and sample trading experiences"""
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)
        self.priority_buffer = deque(maxlen=capacity)
        
    def add(self, experience: TradeExperience, priority: float = 1.0):
        """Add experience with priority (higher = more important)"""
        self.buffer.append(experience)
        self.priority_buffer.append(priority)
        
    def sample(self, batch_size: int = 32) -> List[TradeExperience]:
        """Sample batch of experiences, weighted by priority"""
        if len(self.buffer) < batch_size:
            return list(self.buffer)
        
        # Weighted sampling based on priority
        priorities = np.array(self.priority_buffer)
        probs = priorities / priorities.sum()
        indices = np.random.choice(len(self.buffer), batch_size, p=probs, replace=False)
        return [self.buffer[i] for i in indices]
    
    def get_best_experiences(self, n: int = 100) -> List[TradeExperience]:
        """Get top N profitable experiences"""
        sorted_exp = sorted(self.buffer, key=lambda x: x.pnl, reverse=True)
        return sorted_exp[:n]
    
    def get_worst_experiences(self, n: int = 100) -> List[TradeExperience]:
        """Get worst N losing experiences for learning"""
        sorted_exp = sorted(self.buffer, key=lambda x: x.pnl)
        return sorted_exp[:n]
    
    def save(self, filepath: str):
        """Save buffer to disk"""
        data = [e.to_dict() for e in self.buffer]
        with open(filepath, 'w') as f:
            json.dump(data, f)
    
    def load(self, filepath: str):
        """Load buffer from disk"""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                for d in data:
                    self.add(TradeExperience(**d))

class StrategyPerformanceTracker:
    """Track and analyze strategy performance over time"""
    def __init__(self, lookback_days: int = 30):
        self.lookback_days = lookback_days
        self.performance_history = {}
        self.trades_by_strategy = {}
        
    def record_trade(self, strategy: str, pnl: float, params: Dict):
        """Record a trade for performance tracking"""
        if strategy not in self.trades_by_strategy:
            self.trades_by_strategy[strategy] = []
        
        self.trades_by_strategy[strategy].append({
            'timestamp': datetime.utcnow().isoformat(),
            'pnl': pnl,
            'params': params
        })
        
        # Keep only lookback period
        cutoff = datetime.utcnow() - timedelta(days=self.lookback_days)
        self.trades_by_strategy[strategy] = [
            t for t in self.trades_by_strategy[strategy]
            if datetime.fromisoformat(t['timestamp']) > cutoff
        ]
    
    def calculate_performance(self, strategy: str) -> Dict:
        """Calculate comprehensive performance metrics"""
        trades = self.trades_by_strategy.get(strategy, [])
        if not trades:
            return {'score': 0, 'win_rate': 0, 'profit_factor': 0}
        
        pnls = [t['pnl'] for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        
        win_rate = len(wins) / len(pnls) if pnls else 0
        profit_factor = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else float('inf')
        
        # Calculate Sharpe-like ratio
        if len(pnls) > 1:
            returns = np.array(pnls)
            sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(365)
        else:
            sharpe = 0
        
        # Performance score (weighted composite)
        score = (
            win_rate * 0.3 +
            min(profit_factor / 3, 1.0) * 0.3 +
            min(sharpe / 2, 1.0) * 0.2 +
            min(len(trades) / 100, 1.0) * 0.2
        )
        
        return {
            'score': score,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe,
            'total_trades': len(trades),
            'total_pnl': sum(pnls),
            'avg_pnl': np.mean(pnls),
            'max_drawdown': self._calculate_drawdown(pnls)
        }
    
    def _calculate_drawdown(self, pnls: List[float]) -> float:
        """Calculate maximum drawdown"""
        cumulative = np.cumsum(pnls)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / (running_max + 1e-10)
        return abs(np.min(drawdown)) if len(drawdown) > 0 else 0
    
    def get_best_parameters(self, strategy: str) -> Optional[Dict]:
        """Get parameters that produced best results"""
        trades = self.trades_by_strategy.get(strategy, [])
        if not trades:
            return None
        
        # Group by parameter hash and find best
        param_performance = {}
        for trade in trades:
            param_key = json.dumps(trade['params'], sort_keys=True)
            if param_key not in param_performance:
                param_performance[param_key] = {'pnl': 0, 'count': 0, 'params': trade['params']}
            param_performance[param_key]['pnl'] += trade['pnl']
            param_performance[param_key]['count'] += 1
        
        if not param_performance:
            return None
        
        best = max(param_performance.values(), key=lambda x: x['pnl'])
        return best['params']

class GeneticParameterOptimizer:
    """Genetic algorithm for parameter optimization"""
    def __init__(self, population_size: int = 20, mutation_rate: float = 0.1):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.population = []
        self.generation = 0
        
    def initialize_population(self, param_ranges: Dict[str, Tuple]):
        """Create initial random population"""
        self.population = []
        for _ in range(self.population_size):
            individual = {}
            for param, (min_val, max_val) in param_ranges.items():
                if isinstance(min_val, int):
                    individual[param] = np.random.randint(min_val, max_val + 1)
                else:
                    individual[param] = np.random.uniform(min_val, max_val)
            self.population.append(individual)
    
    def evaluate_fitness(self, individual: Dict, backtest_func) -> float:
        """Evaluate parameter set using backtest"""
        try:
            result = backtest_func(individual)
            return result.get('score', 0)
        except Exception as e:
            logger.error(f"Fitness evaluation error: {e}")
            return 0
    
    def select_parents(self, fitness_scores: List[float]) -> Tuple[Dict, Dict]:
        """Select two parents using tournament selection"""
        # Normalize fitness
        total = sum(fitness_scores) + 1e-10
        probs = [f / total for f in fitness_scores]
        
        parent1_idx = np.random.choice(len(self.population), p=probs)
        parent2_idx = np.random.choice(len(self.population), p=probs)
        
        return self.population[parent1_idx], self.population[parent2_idx]
    
    def crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """Create child by combining parents"""
        child = {}
        for key in parent1:
            if np.random.random() < 0.5:
                child[key] = parent1[key]
            else:
                child[key] = parent2[key]
        return child
    
    def mutate(self, individual: Dict, param_ranges: Dict):
        """Randomly mutate parameters"""
        for param, (min_val, max_val) in param_ranges.items():
            if np.random.random() < self.mutation_rate:
                if isinstance(min_val, int):
                    individual[param] = np.random.randint(min_val, max_val + 1)
                else:
                    individual[param] = np.random.uniform(min_val, max_val)
    
    def evolve(self, fitness_scores: List[float], param_ranges: Dict) -> List[Dict]:
        """Evolve population one generation"""
        new_population = []
        
        # Elitism: keep best individual
        best_idx = np.argmax(fitness_scores)
        new_population.append(self.population[best_idx].copy())
        
        # Create rest of new population
        while len(new_population) < self.population_size:
            parent1, parent2 = self.select_parents(fitness_scores)
            child = self.crossover(parent1, parent2)
            self.mutate(child, param_ranges)
            new_population.append(child)
        
        self.population = new_population
        self.generation += 1
        
        return self.population

class BayesianOptimizer:
    """Bayesian optimization for parameter tuning"""
    def __init__(self, param_ranges: Dict[str, Tuple]):
        self.param_ranges = param_ranges
        self.observations = []
        self.best_params = None
        self.best_score = -float('inf')
        
    def suggest_parameters(self) -> Dict:
        """Suggest next parameters to try"""
        if len(self.observations) < 5:
            # Random exploration phase
            params = {}
            for param, (min_val, max_val) in self.param_ranges.items():
                if isinstance(min_val, int):
                    params[param] = np.random.randint(min_val, max_val + 1)
                else:
                    params[param] = np.random.uniform(min_val, max_val)
            return params
        
        # Exploitation: try parameters near best observed
        if self.best_params:
            params = self.best_params.copy()
            for param in params:
                min_val, max_val = self.param_ranges[param]
                noise = np.random.normal(0, (max_val - min_val) * 0.1)
                params[param] = max(min_val, min(max_val, params[param] + noise))
                if isinstance(min_val, int):
                    params[param] = int(round(params[param]))
            return params
        
        return self._random_params()
    
    def _random_params(self) -> Dict:
        params = {}
        for param, (min_val, max_val) in self.param_ranges.items():
            if isinstance(min_val, int):
                params[param] = np.random.randint(min_val, max_val + 1)
            else:
                params[param] = np.random.uniform(min_val, max_val)
        return params
    
    def update(self, params: Dict, score: float):
        """Update with observation"""
        self.observations.append({'params': params, 'score': score})
        if score > self.best_score:
            self.best_score = score
            self.best_params = params.copy()

class MetaLearningEngine:
    """Main meta-learning engine that coordinates all components"""
    def __init__(self):
        self.experience_buffer = ExperienceReplayBuffer(capacity=50000)
        self.performance_tracker = StrategyPerformanceTracker(lookback_days=30)
        self.genetic_optimizer = GeneticParameterOptimizer()
        self.bayesian_optimizers = {}
        
        self.current_parameters = {}
        self.learning_rate = 0.1
        self.optimization_interval = 24  # hours
        self.last_optimization = None
        
        self.load_state()
    
    def load_state(self):
        """Load saved learning state"""
        if os.path.exists('meta_learning_state.pkl'):
            try:
                with open('meta_learning_state.pkl', 'rb') as f:
                    state = pickle.load(f)
                    self.current_parameters = state.get('parameters', {})
                    self.last_optimization = state.get('last_opt')
                logger.info("Loaded meta-learning state")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
    
    def save_state(self):
        """Save learning state"""
        state = {
            'parameters': self.current_parameters,
            'last_opt': self.last_optimization,
            'timestamp': datetime.utcnow().isoformat()
        }
        with open('meta_learning_state.pkl', 'wb') as f:
            pickle.dump(state, f)
    
    def record_trade(self, strategy: str, symbol: str, side: str,
                    entry_price: float, exit_price: float, qty: float,
                    pnl: float, holding_time: float, market_regime: str,
                    entry_score: float, exit_reason: str,
                    parameters: Dict, market_features: Dict):
        """Record a trade for learning"""
        
        experience = TradeExperience(
            timestamp=datetime.utcnow().isoformat(),
            strategy=strategy,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            qty=qty,
            pnl=pnl,
            pnl_pct=(exit_price - entry_price) / entry_price * (1 if side == 'buy' else -1),
            holding_time=holding_time,
            market_regime=market_regime,
            entry_score=entry_score,
            exit_reason=exit_reason,
            parameters=parameters.copy(),
            market_features=market_features.copy()
        )
        
        # Priority based on profit/loss magnitude
        priority = 1.0 + abs(pnl) / 100
        self.experience_buffer.add(experience, priority)
        
        # Track performance
        self.performance_tracker.record_trade(strategy, pnl, parameters)
        
        logger.info(f"Recorded trade: {strategy} {side} {symbol} PnL: ${pnl:.2f}")
    
    def should_optimize(self) -> bool:
        """Check if optimization should run"""
        if self.last_optimization is None:
            return True
        
        last = datetime.fromisoformat(self.last_optimization)
        hours_since = (datetime.utcnow() - last).total_seconds() / 3600
        
        return hours_since >= self.optimization_interval
    
    def optimize_strategy(self, strategy: str, backtest_func, param_ranges: Dict):
        """Run optimization for a specific strategy"""
        logger.info(f"Starting optimization for {strategy}")
        
        # Use genetic algorithm
        self.genetic_optimizer.initialize_population(param_ranges)
        
        best_fitness_history = []
        
        for generation in range(10):  # 10 generations
            # Evaluate fitness
            fitness_scores = []
            for individual in self.genetic_optimizer.population:
                score = self.genetic_optimizer.evaluate_fitness(individual, backtest_func)
                fitness_scores.append(score)
            
            best_idx = np.argmax(fitness_scores)
            best_fitness = fitness_scores[best_idx]
            best_params = self.genetic_optimizer.population[best_idx]
            
            best_fitness_history.append(best_fitness)
            logger.info(f"Gen {generation}: Best fitness = {best_fitness:.3f}")
            
            # Evolve
            self.genetic_optimizer.evolve(fitness_scores, param_ranges)
        
        # Save best parameters
        self.current_parameters[strategy] = best_params
        
        logger.info(f"Optimization complete for {strategy}")
        logger.info(f"Best parameters: {best_params}")
        logger.info(f"Best fitness: {max(best_fitness_history):.3f}")
        
        return best_params
    
    def adapt_to_market_regime(self, current_regime: str) -> Dict[str, Dict]:
        """Adapt parameters based on current market regime"""
        adapted = {}
        
        # Load experiences from similar regime
        for exp in self.experience_buffer.buffer:
            if exp.market_regime == current_regime:
                strategy = exp.strategy
                if strategy not in adapted:
                    adapted[strategy] = {'params': [], 'pnls': []}
                adapted[strategy]['params'].append(exp.parameters)
                adapted[strategy]['pnls'].append(exp.pnl)
        
        # Find best performing parameters for this regime
        regime_params = {}
        for strategy, data in adapted.items():
            if data['pnls']:
                best_idx = np.argmax(data['pnls'])
                regime_params[strategy] = data['params'][best_idx]
                logger.info(f"Adapted {strategy} for {current_regime} regime")
        
        return regime_params
    
    def generate_insights(self) -> Dict:
        """Generate trading insights from learning"""
        insights = {
            'best_strategies': [],
            'worst_strategies': [],
            'profitable_regimes': [],
            'recommended_adjustments': {}
        }
        
        # Strategy performance
        for strategy in self.performance_tracker.trades_by_strategy.keys():
            perf = self.performance_tracker.calculate_performance(strategy)
            if perf['score'] > 0.7:
                insights['best_strategies'].append({
                    'strategy': strategy,
                    'score': perf['score'],
                    'win_rate': perf['win_rate']
                })
            elif perf['score'] < 0.3:
                insights['worst_strategies'].append({
                    'strategy': strategy,
                    'score': perf['score']
                })
        
        # Market regime analysis
        regime_performance = {}
        for exp in self.experience_buffer.buffer:
            regime = exp.market_regime
            if regime not in regime_performance:
                regime_performance[regime] = []
            regime_performance[regime].append(exp.pnl)
        
        for regime, pnls in regime_performance.items():
            if np.mean(pnls) > 0:
                insights['profitable_regimes'].append({
                    'regime': regime,
                    'avg_pnl': np.mean(pnls),
                    'win_rate': len([p for p in pnls if p > 0]) / len(pnls)
                })
        
        return insights
    
    def run_continuous_learning(self):
        """Main learning loop"""
        logger.info("Meta-learning engine started")
        
        while True:
            try:
                # Check if optimization needed
                if self.should_optimize():
                    logger.info("Running scheduled optimization...")
                    
                    # Optimize each strategy
                    strategies = ['scalping', 'mean_reversion', 'momentum', 'breakout']
                    
                    for strategy in strategies:
                        if strategy in self.performance_tracker.trades_by_strategy:
                            # Get param ranges for strategy
                            param_ranges = self._get_param_ranges(strategy)
                            
                            # Define backtest function
                            def backtest_func(params):
                                return self._simulate_backtest(strategy, params)
                            
                            # Run optimization
                            self.optimize_strategy(strategy, backtest_func, param_ranges)
                    
                    self.last_optimization = datetime.utcnow().isoformat()
                    self.save_state()
                
                # Generate insights
                insights = self.generate_insights()
                if insights['best_strategies']:
                    logger.info(f"Best performing: {insights['best_strategies']}")
                
                # Sleep before next check
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Learning loop error: {e}")
                time.sleep(300)
    
    def _get_param_ranges(self, strategy: str) -> Dict:
        """Get parameter ranges for a strategy"""
        ranges = {
            'scalping': {
                'rsi_period': (10, 20),
                'rsi_overbought': (65, 80),
                'rsi_oversold': (20, 35),
                'bb_period': (15, 25),
                'bb_std': (1.5, 2.5),
                'tp_pct': (0.005, 0.015),
                'sl_pct': (0.003, 0.008)
            },
            'mean_reversion': {
                'zscore_threshold': (1.5, 3.0),
                'lookback': (30, 100),
                'tp_pct': (0.015, 0.04),
                'sl_pct': (0.01, 0.025)
            },
            'momentum': {
                'ema_fast': (8, 15),
                'ema_slow': (20, 35),
                'adx_threshold': (20, 35),
                'volume_mult': (1.2, 2.0),
                'tp_pct': (0.03, 0.08),
                'sl_pct': (0.015, 0.04)
            },
            'breakout': {
                'lookback': (15, 50),
                'volume_mult': (1.5, 3.0),
                'atr_mult_tp': (1.5, 3.0),
                'atr_mult_sl': (0.8, 1.5)
            }
        }
        return ranges.get(strategy, {})
    
    def _simulate_backtest(self, strategy: str, params: Dict) -> Dict:
        """Simulate backtest with given parameters"""
        # Get relevant experiences
        relevant = [e for e in self.experience_buffer.buffer if e.strategy == strategy]
        
        if not relevant:
            return {'score': 0}
        
        # Simulate with new parameters
        # (Simplified - in production would use actual backtest)
        simulated_pnls = []
        for exp in relevant[-50:]:  # Last 50 trades
            # Adjust based on parameter changes
            adjustment = 1.0
            for key, value in params.items():
                if key in exp.parameters:
                    diff = abs(value - exp.parameters[key]) / (exp.parameters[key] + 1e-10)
                    adjustment *= (1 - diff * 0.1)  # Small penalty for large changes
            
            simulated_pnls.append(exp.pnl * adjustment)
        
        wins = [p for p in simulated_pnls if p > 0]
        win_rate = len(wins) / len(simulated_pnls) if simulated_pnls else 0
        
        return {
            'score': win_rate * min(sum(simulated_pnls) / 100, 1.0),
            'win_rate': win_rate,
            'total_pnl': sum(simulated_pnls)
        }

if __name__ == "__main__":
    engine = MetaLearningEngine()
    engine.run_continuous_learning()
