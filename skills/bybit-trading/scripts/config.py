"""
Bybit Trading Configuration
Central configuration module for all trading bots
"""
import os
from typing import Dict, Any
from pathlib import Path

# Load .env file if present
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# API Configuration
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')

# Trading Parameters
SYMBOL = os.getenv('TRADING_SYMBOL', 'BTC/USDT:USDT')
LEVERAGE = int(os.getenv('LEVERAGE', '5'))

# Strategy Configurations
STRATEGIES = {
    'scalping': {
        'timeframe': '1m',
        'tp_pct': float(os.getenv('SCALPING_TP_PCT', '0.8')),
        'sl_pct': float(os.getenv('SCALPING_SL_PCT', '0.5')),
        'position_size_pct': float(os.getenv('SCALPING_SIZE_PCT', '5')),
        'max_hold_minutes': int(os.getenv('MAX_HOLD_MINUTES', '20')),
        'rsi_period': 14,
        'bb_period': 20,
        'bb_std': 2.0
    },
    'mean_reversion': {
        'timeframe': os.getenv('MR_TIMEFRAME', '5m'),
        'tp_pct': float(os.getenv('MR_TP_PCT', '2.5')),
        'sl_pct': float(os.getenv('MR_SL_PCT', '1.5')),
        'position_size_pct': float(os.getenv('MR_SIZE_PCT', '10')),
        'lookback_period': 50,
        'deviation_threshold': 2.0
    },
    'momentum': {
        'timeframe': os.getenv('MOM_TIMEFRAME', '15m'),
        'tp_pct': float(os.getenv('MOM_TP_PCT', '6')),
        'sl_pct': float(os.getenv('MOM_SL_PCT', '2.5')),
        'position_size_pct': float(os.getenv('MOM_SIZE_PCT', '8')),
        'lookback': 20,
        'volume_multiplier': 1.5
    },
    'grid': {
        'levels': int(os.getenv('GRID_LEVELS', '10')),
        'spacing_pct': float(os.getenv('GRID_SPACING', '1.0')),
        'position_size_usdt': float(os.getenv('GRID_POSITION_SIZE', '100'))
    }
}

# Risk Management
RISK_LIMITS = {
    'max_daily_loss_pct': float(os.getenv('MAX_DAILY_LOSS_PCT', '5')),
    'max_drawdown_pct': float(os.getenv('MAX_DRAWDOWN_PCT', '10')),
    'circuit_cooldown_hours': int(os.getenv('CIRCUIT_COOLDOWN_HOURS', '4')),
    'max_positions_per_strategy': 5,
    'max_total_positions': 10
}

# Notifications
TELEGRAM_CONFIG = {
    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
    'chat_id': os.getenv('TELEGRAM_CHAT_ID')
}

def validate_config() -> list:
    """Validate configuration and return list of errors."""
    errors = []
    
    if not BYBIT_API_KEY or BYBIT_API_KEY == 'your_api_key_here':
        errors.append("BYBIT_API_KEY is not configured")
    
    if not BYBIT_API_SECRET or BYBIT_API_SECRET == 'your_api_secret_here':
        errors.append("BYBIT_API_SECRET is not configured")
    
    if LEVERAGE < 1 or LEVERAGE > 100:
        errors.append(f"LEVERAGE {LEVERAGE} is out of valid range (1-100)")
    
    return errors

def load_env_file(filepath: str = '.env'):
    """Load environment variables from .env file."""
    if os.path.exists(filepath):
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key, value)
