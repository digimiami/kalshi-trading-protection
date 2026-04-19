#!/usr/bin/env python3
"""
Comprehensive trading system health check - Multi-pair
Reports all strategy status, positions, and balance
"""
import os
import sys
import json
from datetime import datetime
from pybit.unified_trading import HTTP

# Load env
env_path = '/root/.openclaw/workspace/skills/bybit-trading/scripts/.env'
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

session = HTTP(
    testnet=False,
    api_key=os.getenv('BYBIT_API_KEY'),
    api_secret=os.getenv('BYBIT_API_SECRET'),
)

PAIRS = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']

def get_balance():
    try:
        resp = session.get_wallet_balance(accountType='UNIFIED', coin='USDT')
        return float(resp['result']['list'][0]['totalEquity'])
    except:
        return 0

def get_positions(symbol):
    try:
        resp = session.get_positions(category='linear', symbol=symbol)
        positions = []
        for p in resp['result']['list']:
            if float(p.get('size', 0)) != 0:
                positions.append({
                    'symbol': p['symbol'],
                    'side': 'LONG' if p['side'] == 'Buy' else 'SHORT',
                    'size': p['size'],
                    'entry': p.get('avgPrice', p.get('entryPrice', '0')),
                    'leverage': p.get('leverage', '1'),
                    'pnl': p.get('unrealisedPnl', '0'),
                    'tp': p.get('takeProfit', '0'),
                    'sl': p.get('stopLoss', '0')
                })
        return positions
    except Exception as e:
        return []

def check_bots():
    """Check if bot processes are running"""
    import subprocess
    bots = {
        'scalping_btc': 'scalping_bot.py',
        'mean_reversion_btc': 'mean_reversion_bot.py',
        'momentum_btc': 'momentum_bot.py',
        'grid_btc': 'grid_bot.py',
        'scalping_eth': 'scalping_bot_eth.py',
        'mean_reversion_eth': 'mean_reversion_bot_eth.py',
        'momentum_eth': 'momentum_bot_eth.py',
        'grid_eth': 'grid_bot_eth.py',
        'scalping_xrp': 'scalping_bot_xrp.py',
        'mean_reversion_xrp': 'mean_reversion_bot_xrp.py',
        'momentum_xrp': 'momentum_bot_xrp.py',
        'grid_xrp': 'grid_bot_xrp.py',
        'tpsl': 'ensure_tp_sl.py'
    }
    status = {}
    for name, script in bots.items():
        result = subprocess.run(['pgrep', '-f', script], capture_output=True)
        status[name] = 'RUNNING' if result.returncode == 0 else 'DOWN'
    return status

def main():
    print(f"📊 BYBIT MULTI-PAIR REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Balance
    balance = get_balance()
    print(f"💰 Total Balance: ${balance:.2f} USDT")
    print()
    
    # Bot Status by Pair
    bot_status = check_bots()
    print("🤖 BOT STATUS:")
    print()
    
    pairs = {
        'BTC/USDT': [k for k in bot_status.keys() if '_btc' in k],
        'ETH/USDT': [k for k in bot_status.keys() if '_eth' in k],
        'XRP/USDT': [k for k in bot_status.keys() if '_xrp' in k],
        'OTHER': ['tpsl']
    }
    
    for pair, bot_list in pairs.items():
        if pair == 'OTHER':
            print(f"🛡️  PROTECTION:")
            for bot in bot_list:
                icon = "🟢" if bot_status.get(bot) == "RUNNING" else "🔴"
                print(f"   {icon} TP/SL Guardian    {bot_status.get(bot, 'UNKNOWN')}")
        else:
            print(f"📊 {pair}:")
            for bot in bot_list:
                icon = "🟢" if bot_status.get(bot) == "RUNNING" else "🔴"
                short_name = bot.split('_')[0]
                print(f"   {icon} {short_name:15} {bot_status.get(bot, 'UNKNOWN')}")
        print()
    
    # Positions
    all_positions = []
    for pair in PAIRS:
        positions = get_positions(pair)
        all_positions.extend(positions)
    
    if all_positions:
        print(f"📈 OPEN POSITIONS ({len(all_positions)}):")
        for pos in all_positions:
            pnl_float = float(pos['pnl'])
            pnl_icon = "🟢" if pnl_float >= 0 else "🔴"
            print(f"   {pnl_icon} {pos['symbol']} {pos['side']}")
            print(f"      Size: {pos['size']} @ ${float(pos['entry']):,.2f}")
            print(f"      PnL: ${pnl_float:+.2f} | Lev: {pos['leverage']}x")
            has_tp = float(pos['tp'] or 0) != 0
            has_sl = float(pos['sl'] or 0) != 0
            print(f"      TP: {'✅' if has_tp else '❌'} | SL: {'✅' if has_sl else '❌'}")
            print()
    else:
        print("📈 OPEN POSITIONS: None (scanning for entries)")
        print()
    
    # Overall status
    running = sum(1 for s in bot_status.values() if s == 'RUNNING')
    total = len(bot_status)
    print("=" * 70)
    if running == total:
        print(f"🟢 STATUS: HEALTHY - All {total} systems operational")
    elif running > 0:
        print(f"🟡 STATUS: DEGRADED - {running}/{total} systems running")
    else:
        print(f"🔴 STATUS: CRITICAL - All systems down")
    print("=" * 70)
    print()
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'balance': balance,
        'bots': bot_status,
        'positions': all_positions,
        'healthy': running == total
    }
    
    os.makedirs('/tmp/bybit_bots', exist_ok=True)
    with open('/tmp/bybit_bots/health_report.json', 'w') as f:
        json.dump(report, f, indent=2)

if __name__ == '__main__':
    main()
