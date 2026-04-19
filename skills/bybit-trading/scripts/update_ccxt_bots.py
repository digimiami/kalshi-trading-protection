#!/usr/bin/env python3
"""Update all ccxt-based bot files to use fixed $50 position size"""
import os
import re

SCRIPTS_DIR = '/root/.openclaw/workspace/skills/bybit-trading/scripts'

# Files to update (ccxt-based versions for ETH, XRP, SOL)
ccxt_files = [
    'mean_reversion_bot_eth.py', 'mean_reversion_bot_xrp.py', 'mean_reversion_bot_sol.py',
    'momentum_bot_eth.py', 'momentum_bot_xrp.py', 'momentum_bot_sol.py',
]

# Old pattern for ccxt-based bots
ccxt_old = '''    def calculate_position_size(self) -> float:
        balance = self.get_balance()
        position_value = balance * (self.position_size_pct / 100)
        ticker = self.exchange.fetch_ticker(self.symbol)
        price = ticker['last']
        amount = position_value / price
        return max(0.001, round(amount, 3))  # Minimum 0.001 BTC for Bybit'''

ccxt_new = '''    def calculate_position_size(self) -> float:
        """Calculate position size - fixed $50 USD per position."""
        position_value = float(os.getenv('POSITION_SIZE_USDT', '50'))  # Fixed $50
        ticker = self.exchange.fetch_ticker(self.symbol)
        price = ticker['last']
        amount = position_value / price
        return max(0.001, round(amount, 3))  # Minimum 0.001 for Bybit'''

# Update leverage in __init__ from default 3 to use env
leverage_old = "self.leverage = int(os.getenv('LEVERAGE', '3'))"

for filename in ccxt_files:
    filepath = os.path.join(SCRIPTS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"Skipping {filename} (not found)")
        continue
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Update calculate_position_size
    if 'def calculate_position_size(self) -> float:' in content and 'position_size_pct' in content:
        content = content.replace(ccxt_old, ccxt_new)
        print(f"Updated {filename} (position size)")
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
    else:
        print(f"No changes for {filename}")

print("\nAll ccxt-based bot files updated!")
