"""
Bot Manager - Central control for ALL trading bots (Complete System)
Usage: python bot_manager.py [start|stop|restart|status|health|stop-all] [bot_name]
"""
import os
import sys
import json
import time
import signal
import subprocess
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('bot_manager')

PID_DIR = Path('/tmp/bybit_bots')
PID_DIR.mkdir(exist_ok=True)

# ALL BOTS - Complete trading system
BOTS = {
    # ===== SCALPING STRATEGIES =====
    'scalping_btc': {'script': 'scalping_bot.py', 'pair': 'BTC/USDT', 'desc': 'RSI+BB scalping', 'category': 'scalping'},
    'scalping_eth': {'script': 'scalping_bot_eth.py', 'pair': 'ETH/USDT', 'desc': 'RSI+BB scalping', 'category': 'scalping'},
    'scalping_xrp': {'script': 'scalping_bot_xrp.py', 'pair': 'XRP/USDT', 'desc': 'RSI+BB scalping', 'category': 'scalping'},
    'scalping_sol': {'script': 'scalping_bot_sol.py', 'pair': 'SOL/USDT', 'desc': 'RSI+BB scalping', 'category': 'scalping'},
    
    # ===== MEAN REVERSION =====
    'mean_reversion_btc': {'script': 'mean_reversion_bot.py', 'pair': 'BTC/USDT', 'desc': 'Z-score mean reversion', 'category': 'mean_reversion'},
    'mean_reversion_eth': {'script': 'mean_reversion_bot_eth.py', 'pair': 'ETH/USDT', 'desc': 'Z-score mean reversion', 'category': 'mean_reversion'},
    'mean_reversion_xrp': {'script': 'mean_reversion_bot_xrp.py', 'pair': 'XRP/USDT', 'desc': 'Z-score mean reversion', 'category': 'mean_reversion'},
    'mean_reversion_sol': {'script': 'mean_reversion_bot_sol.py', 'pair': 'SOL/USDT', 'desc': 'Z-score mean reversion', 'category': 'mean_reversion'},
    
    # ===== MOMENTUM/TREND =====
    'momentum_btc': {'script': 'momentum_bot.py', 'pair': 'BTC/USDT', 'desc': 'Breakout + volume momentum', 'category': 'momentum'},
    'momentum_eth': {'script': 'momentum_bot_eth.py', 'pair': 'ETH/USDT', 'desc': 'Breakout + volume momentum', 'category': 'momentum'},
    'momentum_xrp': {'script': 'momentum_bot_xrp.py', 'pair': 'XRP/USDT', 'desc': 'Breakout + volume momentum', 'category': 'momentum'},
    'momentum_sol': {'script': 'momentum_bot_sol.py', 'pair': 'SOL/USDT', 'desc': 'Breakout + volume momentum', 'category': 'momentum'},
    
    # ===== GRID TRADING =====
    'grid_btc': {'script': 'grid_bot.py', 'pair': 'BTC/USDT', 'desc': 'Grid trading', 'category': 'grid'},
    'grid_eth': {'script': 'grid_bot_eth.py', 'pair': 'ETH/USDT', 'desc': 'Grid trading', 'category': 'grid'},
    'grid_xrp': {'script': 'grid_bot_xrp.py', 'pair': 'XRP/USDT', 'desc': 'Grid trading', 'category': 'grid'},
    'grid_sol': {'script': 'grid_bot_sol.py', 'pair': 'SOL/USDT', 'desc': 'Grid trading', 'category': 'grid'},
    
    # ===== NEW STRATEGIES =====
    'breakout_btc': {'script': 'breakout_bot.py', 'pair': 'BTC/USDT', 'desc': 'Support/resistance breakout', 'category': 'breakout'},
    'arbitrage': {'script': 'arbitrage_bot.py', 'pair': 'BTC/ETH', 'desc': 'Statistical arbitrage', 'category': 'arbitrage'},
    'ml_btc': {'script': 'ml_bot.py', 'pair': 'BTC/USDT', 'desc': 'ML prediction enhanced', 'category': 'ml'},
    
    # ===== SYSTEM =====
    'strategy_selector': {'script': 'strategy_selector.py', 'pair': 'ALL', 'desc': 'Market regime detector', 'category': 'system'},
    'tpsl_guardian': {'script': 'ensure_tp_sl.py', 'pair': 'ALL', 'desc': 'TP/SL protection', 'category': 'system'},
}

def get_pid_file(bot_name: str) -> Path:
    return PID_DIR / f"{bot_name}.pid"

def read_pid(bot_name: str) -> int:
    pid_file = get_pid_file(bot_name)
    if pid_file.exists():
        return int(pid_file.read_text().strip())
    return None

def write_pid(bot_name: str, pid: int):
    get_pid_file(bot_name).write_text(str(pid))

def remove_pid(bot_name: str):
    pid_file = get_pid_file(bot_name)
    if pid_file.exists():
        pid_file.unlink()

def is_running(bot_name: str) -> bool:
    pid = read_pid(bot_name)
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        remove_pid(bot_name)
        return False

def start_bot(bot_name: str):
    """Start a bot."""
    if bot_name not in BOTS:
        logger.error(f"Unknown bot: {bot_name}")
        return False
    
    if is_running(bot_name):
        logger.info(f"{bot_name} already running")
        return True
    
    bot_config = BOTS[bot_name]
    script_path = Path(__file__).parent / bot_config['script']
    log_file = PID_DIR / f"{bot_name}.log"
    
    # Set environment variable for symbol if needed
    env = os.environ.copy()
    if bot_name.startswith('breakout'):
        env['TRADING_SYMBOL'] = bot_config['pair'] + ':USDT'
    
    try:
        with open(log_file, 'a') as f:
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env=env
            )
        
        write_pid(bot_name, process.pid)
        logger.info(f"Started {bot_name} (PID: {process.pid})")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start {bot_name}: {e}")
        return False

def stop_bot(bot_name: str) -> bool:
    """Stop a bot."""
    pid = read_pid(bot_name)
    if not pid:
        return True
    
    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except:
                break
        try:
            os.kill(pid, signal.SIGKILL)
        except:
            pass
        
        remove_pid(bot_name)
        logger.info(f"Stopped {bot_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to stop {bot_name}: {e}")
        return False

def restart_bot(bot_name: str):
    """Restart a bot."""
    stop_bot(bot_name)
    time.sleep(2)
    return start_bot(bot_name)

def get_status():
    """Get status of all bots."""
    return {name: is_running(name) for name in BOTS.keys()}

def print_status():
    """Print formatted status."""
    status = get_status()
    
    # Group by category
    categories = {
        'SCALPING': [],
        'MEAN REVERSION': [],
        'MOMENTUM': [],
        'GRID': [],
        'ADVANCED': [],
        'SYSTEM': []
    }
    
    for bot_name, running in status.items():
        cat = BOTS[bot_name]['category'].upper()
        if cat == 'breakout' or cat == 'arbitrage' or cat == 'ml':
            categories['ADVANCED'].append((bot_name, running, BOTS[bot_name]))
        elif cat in categories:
            categories[cat].append((bot_name, running, BOTS[bot_name]))
        else:
            categories['SYSTEM'].append((bot_name, running, BOTS[bot_name]))
    
    print("\n" + "="*80)
    print("🤖 BYBIT TRADING SYSTEM - COMPLETE STATUS")
    print("="*80)
    
    for cat_name, bots in categories.items():
        if bots:
            print(f"\n📂 {cat_name}:")
            for bot_name, running, config in bots:
                icon = "🟢" if running else "🔴"
                short_name = bot_name.split('_')[0]
                print(f"  {icon} {short_name:20} {config['pair']:12} {config['desc']}")
    
    running_count = sum(status.values())
    print(f"\n{'='*80}")
    print(f"Total: {running_count}/{len(BOTS)} bots running")
    print("="*80 + "\n")

def start_all():
    """Start all bots."""
    logger.info("Starting all bots...")
    for bot_name in BOTS.keys():
        start_bot(bot_name)
        time.sleep(0.5)

def stop_all():
    """Stop all bots."""
    logger.info("Stopping all bots...")
    for bot_name in BOTS.keys():
        stop_bot(bot_name)

def start_by_category(category: str):
    """Start bots by category."""
    cats = {
        'scalping': ['scalping_btc', 'scalping_eth', 'scalping_xrp'],
        'mean_reversion': ['mean_reversion_btc', 'mean_reversion_eth', 'mean_reversion_xrp'],
        'momentum': ['momentum_btc', 'momentum_eth', 'momentum_xrp'],
        'grid': ['grid_btc', 'grid_eth', 'grid_xrp'],
        'advanced': ['breakout_btc', 'arbitrage', 'ml_btc'],
        'system': ['strategy_selector', 'tpsl_guardian']
    }
    
    if category in cats:
        for bot in cats[category]:
            start_bot(bot)
            time.sleep(0.5)
    else:
        print(f"Unknown category: {category}")
        print(f"Available: {', '.join(cats.keys())}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python bot_manager.py [command] [bot_name|category]")
        print("\nCommands:")
        print("  start [bot_name|category]  - Start bot or category")
        print("  stop [bot_name|category]   - Stop bot or category")
        print("  restart [bot_name]         - Restart specific bot")
        print("  status                     - Show all bot status")
        print("  start-all                  - Start all bots")
        print("  stop-all                   - Stop all bots")
        print("\nCategories: scalping, mean_reversion, momentum, grid, advanced, system")
        print(f"\nAll bots: {', '.join(BOTS.keys())}")
        return
    
    command = sys.argv[1].lower()
    target = sys.argv[2] if len(sys.argv) > 2 else None
    
    if command == 'start':
        if target == 'all':
            start_all()
        elif target in ['scalping', 'mean_reversion', 'momentum', 'grid', 'advanced', 'system']:
            start_by_category(target)
        elif target:
            start_bot(target)
        else:
            print("Error: Specify bot name, category, or 'all'")
    
    elif command == 'stop':
        if target == 'all':
            stop_all()
        elif target:
            stop_bot(target)
        else:
            print("Error: Specify bot name or 'all'")
    
    elif command == 'restart':
        if not target:
            print("Error: Specify bot name")
            return
        restart_bot(target)
    
    elif command == 'status':
        print_status()
    
    elif command == 'start-all':
        start_all()
    
    elif command == 'stop-all':
        stop_all()
    
    else:
        print(f"Unknown command: {command}")

if __name__ == '__main__':
    main()
