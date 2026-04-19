#!/usr/bin/env python3
"""
Bybit Trading Report - Sends comprehensive report to Telegram every 30min
"""
import os
import json
import sys
from datetime import datetime
from pathlib import Path

# Load .env
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from pybit.unified_trading import HTTP
import ccxt

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram(message):
    """Send message to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured")
        return
    
    import urllib.request
    import urllib.parse
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }).encode()
    
    try:
        urllib.request.urlopen(url, data, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram: {e}")

def get_trades_today(session):
    """Get today's trade count."""
    try:
        resp = session.get_executions(category='linear', limit=100)
        executions = resp['result']['list']
        today = datetime.now().strftime('%Y-%m-%d')
        today_trades = []
        for e in executions:
            exec_time = e.get('execTime', '')
            if exec_time.isdigit():
                # Convert milliseconds to datetime
                from datetime import datetime as dt
                exec_dt = dt.fromtimestamp(int(exec_time) / 1000)
                if exec_dt.strftime('%Y-%m-%d') == today:
                    today_trades.append(e)
            elif exec_time.startswith(today):
                today_trades.append(e)
        return len(today_trades), today_trades[:3]
    except Exception as ex:
        print(f"Error getting trades: {ex}")
        return 0, []

def get_circuit_status():
    """Get circuit breaker status."""
    try:
        state_file = Path('/tmp/bybit_bots/circuit_breaker_state.json')
        if state_file.exists():
            state = json.loads(state_file.read_text())
            return state.get('tripped', False), state.get('drawdown_pct', 0)
    except:
        pass
    return False, 0

def get_bot_status():
    """Count running bots."""
    pid_dir = Path('/tmp/bybit_bots')
    if not pid_dir.exists():
        return 0, 0
    
    pid_files = list(pid_dir.glob('*.pid'))
    running = 0
    for pid_file in pid_files:
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)  # Check if process exists
            running += 1
        except:
            pass
    return running, len(pid_files)

def main():
    # Initialize APIs
    session = HTTP(
        testnet=False,
        api_key=os.getenv('BYBIT_API_KEY'),
        api_secret=os.getenv('BYBIT_API_SECRET')
    )
    
    exchange = ccxt.bybit({
        'apiKey': os.getenv('BYBIT_API_KEY'),
        'secret': os.getenv('BYBIT_API_SECRET'),
        'options': {'defaultType': 'swap'}
    })
    
    # Get data
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    total = usdt.get('total', 0)
    free = usdt.get('free', 0)
    used = usdt.get('used', 0)
    
    positions = exchange.fetch_positions()
    open_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
    
    trade_count, recent_trades = get_trades_today(session)
    tripped, drawdown = get_circuit_status()
    running_bots, total_bots = get_bot_status()
    
    # Build report
    now = datetime.now().strftime('%H:%M')
    
    report = f"""📊 <b>Bybit Report - {now}</b>

💰 <b>Balance:</b> {total:.2f} USDT
   Free: {free:.2f} | Used: {used:.2f}

📈 <b>Positions:</b> {len(open_positions)}
"""
    
    if open_positions:
        for pos in open_positions[:3]:
            symbol = pos.get('symbol', 'Unknown')
            side = pos.get('side', 'Unknown')
            pnl = float(pos.get('unrealizedPnl', 0))
            size = pos.get('contracts', '0')
            report += f"   {symbol} {side} {size} ({pnl:+.2f} USDT)\n"
    else:
        report += "   No open positions\n"
    
    report += f"""
🤖 <b>Bots:</b> {running_bots}/{total_bots} running
⚡ <b>Trades Today:</b> {trade_count}
"""
    
    if trade_count == 0:
        report += "   ⚠️ No trading activity today\n"
    
    report += f"""
🛡️ <b>Circuit:</b> {'🔴 TRIPPED' if tripped else '🟢 OK'}
   Drawdown: {drawdown:.2f}%
"""
    
    print(report)
    send_telegram(report)

if __name__ == '__main__':
    main()
