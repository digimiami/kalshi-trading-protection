"""
Diagnostic script for Bybit trading system
Checks all components and reports issues
"""
import os
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/bybit-trading/scripts')

import config
import ccxt

def check_api_connection():
    """Test Bybit API connection."""
    print("🔌 Testing Bybit API connection...")
    try:
        exchange = ccxt.bybit({
            'apiKey': os.getenv('BYBIT_API_KEY'),
            'secret': os.getenv('BYBIT_API_SECRET'),
            'options': {'defaultType': 'swap'}
        })
        balance = exchange.fetch_balance()
        usdt = balance.get('USDT', {})
        print(f"   ✅ API Connected")
        print(f"   💰 Balance: ${usdt.get('total', 0):.2f} USDT")
        return True
    except Exception as e:
        print(f"   ❌ API Error: {e}")
        return False

def check_indicators():
    """Test indicator calculations."""
    print("📊 Testing technical indicators...")
    try:
        import pandas as pd
        import pandas_ta as ta
        
        # Sample data
        data = {'close': [100, 101, 102, 101, 100, 99, 98, 97, 96, 95]}
        df = pd.DataFrame(data)
        
        rsi = ta.rsi(df['close'], length=14)
        ema = ta.ema(df['close'], length=200)
        
        print(f"   ✅ Indicators working (RSI, EMA)")
        return True
    except Exception as e:
        print(f"   ❌ Indicator Error: {e}")
        return False

def check_file_permissions():
    """Check if log directories are writable."""
    print("📁 Checking file permissions...")
    import os
    paths = [
        '/tmp/bybit_bots',
        '/root/.openclaw/workspace/skills/bybit-trading/scripts'
    ]
    all_ok = True
    for path in paths:
        if os.path.exists(path):
            if os.access(path, os.W_OK):
                print(f"   ✅ {path} - writable")
            else:
                print(f"   ❌ {path} - NOT writable")
                all_ok = False
        else:
            try:
                os.makedirs(path, exist_ok=True)
                print(f"   ✅ {path} - created")
            except Exception as e:
                print(f"   ❌ {path} - cannot create: {e}")
                all_ok = False
    return all_ok

def main():
    print("=" * 50)
    print("BYBIT TRADING SYSTEM DIAGNOSTIC")
    print("=" * 50)
    
    results = {
        'API': check_api_connection(),
        'Indicators': check_indicators(),
        'Permissions': check_file_permissions()
    }
    
    print("=" * 50)
    if all(results.values()):
        print("✅ ALL SYSTEMS OPERATIONAL")
        return 0
    else:
        print("⚠️  ISSUES DETECTED - See above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
