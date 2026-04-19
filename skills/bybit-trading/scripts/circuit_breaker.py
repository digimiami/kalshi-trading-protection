#!/usr/bin/env python3
"""
Circuit Breaker Check for Bybit Trading
Monitors risk levels and trading conditions to prevent catastrophic losses
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, will rely on environment variables

# Configuration
CIRCUIT_BREAKER_FILE = Path("/root/.openclaw/workspace/skills/bybit-trading/data/circuit_breaker.json")
LOG_FILE = Path("/root/.openclaw/workspace/skills/bybit-trading/logs/circuit_breaker.log")
MAX_DAILY_DRAWDOWN = 0.10  # 10% max daily drawdown
MAX_CONSECUTIVE_LOSSES = 3
MIN_BALANCE = 100  # USD

# Ensure directories exist
CIRCUIT_BREAKER_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def log_message(message: str):
    """Write log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)
    print(log_entry.strip())


def load_circuit_state():
    """Load circuit breaker state from file"""
    if CIRCUIT_BREAKER_FILE.exists():
        with open(CIRCUIT_BREAKER_FILE, "r") as f:
            return json.load(f)
    return {
        "tripped": False,
        "reason": None,
        "tripped_at": None,
        "daily_pnl": 0,
        "consecutive_losses": 0,
        "last_reset": datetime.now().isoformat(),
        "checks": []
    }


def save_circuit_state(state: dict):
    """Save circuit breaker state to file"""
    with open(CIRCUIT_BREAKER_FILE, "w") as f:
        json.dump(state, f, indent=2)


def check_daily_reset(state: dict) -> dict:
    """Reset daily counters if it's a new day"""
    last_reset = datetime.fromisoformat(state["last_reset"])
    now = datetime.now()
    
    if last_reset.date() != now.date():
        log_message("🌅 New day - resetting daily counters")
        state["daily_pnl"] = 0
        state["consecutive_losses"] = 0
        state["last_reset"] = now.isoformat()
        state["tripped"] = False
        state["reason"] = None
        state["tripped_at"] = None
    
    return state


def check_drawdown(state: dict) -> tuple:
    """Check if daily drawdown exceeds limit"""
    daily_pnl_pct = state.get("daily_pnl", 0)
    if daily_pnl_pct <= -MAX_DAILY_DRAWDOWN:
        return False, f"Daily drawdown {daily_pnl_pct:.2%} exceeds limit {MAX_DAILY_DRAWDOWN:.2%}"
    return True, f"Daily drawdown {daily_pnl_pct:.2%} within limits"


def check_consecutive_losses(state: dict) -> tuple:
    """Check if consecutive losses exceed limit"""
    losses = state.get("consecutive_losses", 0)
    if losses >= MAX_CONSECUTIVE_LOSSES:
        return False, f"Consecutive losses ({losses}) at limit ({MAX_CONSECUTIVE_LOSSES})"
    return True, f"Consecutive losses ({losses}) within limits"


def check_balance() -> tuple:
    """Check if balance is above minimum"""
    # This would normally fetch from Bybit API
    # For now, we'll check environment or a balance file
    balance_file = Path("/root/.openclaw/workspace/skills/bybit-trading/data/balance.json")
    if balance_file.exists():
        with open(balance_file, "r") as f:
            data = json.load(f)
            balance = data.get("balance", 0)
            if balance < MIN_BALANCE:
                return False, f"Balance ${balance:.2f} below minimum ${MIN_BALANCE}"
            return True, f"Balance ${balance:.2f} above minimum ${MIN_BALANCE}"
    return True, "Balance check skipped (no data)"


def check_api_connectivity() -> tuple:
    """Check Bybit API connectivity"""
    # Check if API keys are configured
    api_key = os.environ.get("BYBIT_API_KEY")
    api_secret = os.environ.get("BYBIT_API_SECRET")
    
    if not api_key or not api_secret:
        return False, "Bybit API credentials not configured"
    
    # In a real implementation, we'd test the connection
    # For now, we assume OK if keys exist
    return True, "API credentials configured"


def run_circuit_check():
    """Run all circuit breaker checks"""
    log_message("=" * 50)
    log_message("🔍 Running Circuit Breaker Check")
    
    state = load_circuit_state()
    state = check_daily_reset(state)
    
    checks = []
    all_passed = True
    
    # Run all checks
    check_functions = [
        ("Daily Drawdown", check_drawdown, state),
        ("Consecutive Losses", check_consecutive_losses, state),
        ("Balance", check_balance, None),
        ("API Connectivity", check_api_connectivity, None),
    ]
    
    for name, check_fn, arg in check_functions:
        if arg is not None:
            passed, message = check_fn(arg)
        else:
            passed, message = check_fn()
        
        status = "✅" if passed else "❌"
        log_message(f"{status} {name}: {message}")
        
        checks.append({
            "name": name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        if not passed:
            all_passed = False
    
    # Update state
    state["checks"] = checks[-10:]  # Keep last 10 checks
    
    # Trip circuit if any check failed
    if not all_passed and not state["tripped"]:
        failed_checks = [c for c in checks if not c["passed"]]
        reasons = [c["message"] for c in failed_checks]
        state["tripped"] = True
        state["reason"] = " | ".join(reasons)
        state["tripped_at"] = datetime.now().isoformat()
        log_message(f"🚨 CIRCUIT BREAKER TRIPPED: {state['reason']}")
    
    save_circuit_state(state)
    
    # Print summary
    log_message("-" * 50)
    if state["tripped"]:
        log_message(f"🛑 CIRCUIT BREAKER: TRIPPED")
        log_message(f"   Reason: {state['reason']}")
        log_message(f"   Tripped at: {state['tripped_at']}")
        return 1
    else:
        log_message("✅ CIRCUIT BREAKER: NORMAL")
        log_message(f"   Daily P&L: {state['daily_pnl']:.2%}")
        log_message(f"   Consecutive Losses: {state['consecutive_losses']}")
        return 0


if __name__ == "__main__":
    exit_code = run_circuit_check()
    sys.exit(exit_code)