#!/usr/bin/env python3
"""Update all bot files to use fixed $50 position size"""
import os
import re

SCRIPTS_DIR = '/root/.openclaw/workspace/skills/bybit-trading/scripts'

# Files to update
bot_files = [
    'scalping_bot.py', 'scalping_bot_eth.py', 'scalping_bot_xrp.py', 'scalping_bot_sol.py',
    'mean_reversion_bot.py', 'mean_reversion_bot_eth.py', 'mean_reversion_bot_xrp.py', 'mean_reversion_bot_sol.py',
    'momentum_bot.py', 'momentum_bot_eth.py', 'momentum_bot_xrp.py', 'momentum_bot_sol.py',
    'grid_bot.py', 'grid_bot_eth.py', 'grid_bot_xrp.py', 'grid_bot_sol.py',
]

# Pattern to find and replace in scalping bots (ccxt-based)
scalping_old = '''    def calculate_position_size(self) -> float:
        """Calculate position size based on balance percentage."""
        balance = self.get_balance()
        position_value = balance * (self.position_size_pct / 100)'''

scalping_new = '''    def calculate_position_size(self) -> float:
        """Calculate position size - fixed $50 USD per position."""
        position_value = float(os.getenv('POSITION_SIZE_USDT', '50'))  # Fixed $50'''

# Pattern for pybit-based bots (mean reversion, momentum)
pybit_old = '''    def calculate_position_size(self):
        """Calculate position size based on percentage of balance."""
        balance = self.get_balance()
        ticker = self.session.get_tickers(category='linear', symbol=SYMBOL)
        price = float(ticker['result']['list'][0].get('lastPrice', 70000))
        position_value = balance * (POSITION_SIZE_PCT / 100)
        amount = position_value / price
        return max(0.001, round(amount, 3))'''

pybit_new = '''    def calculate_position_size(self):
        """Calculate position size - fixed $50 USD per position."""
        ticker = self.session.get_tickers(category='linear', symbol=SYMBOL)
        price = float(ticker['result']['list'][0].get('lastPrice', 70000))
        amount = POSITION_SIZE_USDT / price  # Fixed $50 position
        return max(0.001, round(amount, 3))'''

# Pattern for config in pybit bots
config_old = '''LEVERAGE = 3
POSITION_SIZE_PCT = 10'''

config_new = '''LEVERAGE = int(os.getenv('LEVERAGE', '3'))
POSITION_SIZE_USDT = float(os.getenv('POSITION_SIZE_USDT', '50'))  # Fixed $50 per position'''

config_old_momentum = '''LEVERAGE = 4
POSITION_SIZE_PCT = 8'''

# Grid bot pattern
grid_old = '''self.position_size = float(os.getenv('GRID_POSITION_SIZE', '100'))  # USDT per grid'''

grid_new = '''self.position_size = float(os.getenv('POSITION_SIZE_USDT', '50'))  # Fixed $50 per grid level'''

for filename in bot_files:
    filepath = os.path.join(SCRIPTS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"Skipping {filename} (not found)")
        continue
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Update based on file type
    if 'scalping' in filename:
        if scalping_old in content:
            content = content.replace(scalping_old, scalping_new)
            print(f"Updated {filename} (scalping position size)")
    
    elif 'mean_reversion' in filename or 'momentum' in filename:
        # Update config
        if config_old in content:
            content = content.replace(config_old, config_new)
            print(f"Updated {filename} (mean rev config)")
        elif config_old_momentum in content:
            content = content.replace(config_old_momentum, config_new)
            print(f"Updated {filename} (momentum config)")
        
        # Update calculate_position_size
        if pybit_old in content:
            content = content.replace(pybit_old, pybit_new)
            print(f"Updated {filename} (pybit position size)")
    
    elif 'grid' in filename:
        if grid_old in content:
            content = content.replace(grid_old, grid_new)
            print(f"Updated {filename} (grid position size)")
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
    else:
        print(f"No changes needed for {filename}")

print("\nAll bot files updated!")
