---
name: bybit-trading
description: Automated cryptocurrency trading system for Bybit Futures with multiple strategies (scalping, mean reversion, momentum, grid), risk management via circuit breakers, and P&L monitoring. Use when setting up or managing automated trading bots on Bybit, configuring trading strategies, monitoring risk limits, checking trading performance, or managing bot lifecycle (start/stop/restart/health checks).
---

# Bybit Trading Skill

Comprehensive automated trading system for Bybit Futures with multiple strategies, risk management, and monitoring.

## Features

- **Multiple Trading Strategies:**
  - Scalping (RSI + Bollinger Bands) - 1m timeframe
  - Mean Reversion - 5m/15m timeframe
  - Momentum Trading - 15m/1h timeframe
  - Grid Trading - automated grid bot

- **Risk Management:**
  - Circuit breaker with daily loss and drawdown limits
  - Automatic TP/SL enforcement
  - Position sizing controls

- **Monitoring:**
  - P&L tracking and reporting
  - Bot health checks
  - Centralized bot management

## Quick Start

### 1. Configure API Keys

```bash
cd skills/bybit-trading/scripts
cp .env.example .env
# Edit .env with your Bybit API credentials
```

### 2. Install Dependencies

```bash
pip install ccxt pandas numpy python-dotenv
```

### 3. Start Trading

```bash
# Start individual bots
python bot_manager.py start scalping
python bot_manager.py start mean_reversion
python bot_manager.py start momentum
python bot_manager.py start grid

# Or check status first
python bot_manager.py status
```

## Commands

### Bot Management

```bash
# Start a bot
python bot_manager.py start scalping

# Stop a bot
python bot_manager.py stop scalping

# Restart a bot
python bot_manager.py restart scalping

# Check all bot status
python bot_manager.py status

# Health check (JSON output)
python bot_manager.py health

# Stop all bots
python bot_manager.py stop-all
```

### Risk Management

```bash
# Check circuit breaker status
python circuit_breaker.py

# Ensure all positions have TP/SL (one-time check)
python ensure_tp_sl.py --once

# Run TP/SL guardian (continuous monitoring)
python ensure_tp_sl.py
```

### P&L Reporting

```bash
# Generate P&L report
python pnl_check.py
```

## Configuration

Edit `.env` file:

```env
BYBIT_API_KEY=your_key
BYBIT_API_SECRET=your_secret
TRADING_SYMBOL=BTC/USDT:USDT
LEVERAGE=5
POSITION_SIZE_PCT=5

# Risk Limits
MAX_DAILY_LOSS_PCT=5
MAX_DRAWDOWN_PCT=10
CIRCUIT_COOLDOWN_HOURS=4
```

See `.env.example` for all options.

## Strategy Details

See [references/strategies.md](references/strategies.md) for detailed strategy documentation including:
- Entry/exit conditions
- Risk parameters
- Timeframe specifications

## File Structure

```
bybit-trading/
├── SKILL.md                    # This file
├── scripts/
│   ├── bot_manager.py          # Central bot control
│   ├── scalping_bot.py         # RSI+BB scalping strategy
│   ├── mean_reversion_bot.py   # Mean reversion strategy
│   ├── momentum_bot.py         # Momentum breakout strategy
│   ├── grid_bot.py             # Grid trading bot
│   ├── circuit_breaker.py      # Risk management
│   ├── ensure_tp_sl.py         # TP/SL guardian
│   ├── pnl_check.py            # P&L reporting
│   ├── config.py               # Configuration module
│   └── .env.example            # Example configuration
└── references/
    └── strategies.md           # Strategy documentation
```

## Important Notes

**⚠️ Risk Warning:**
- Trading involves significant risk of loss
- Start with small position sizes
- Test strategies on Bybit testnet first
- Never trade with money you cannot afford to lose
- The circuit breaker provides limited protection - manual oversight required

**API Requirements:**
- Bybit Unified Trading Account
- API key with "Contract" permissions
- IP whitelist recommended

**Monitoring:**
- Check bot health regularly via `bot_manager.py health`
- Monitor circuit breaker status
- Review P&L reports daily

## Cron Jobs (Optional)

Set up automated monitoring:

```bash
# Edit crontab
crontab -e

# P&L report every 30 minutes
*/30 * * * * cd /path/to/scripts && python pnl_check.py >> /var/log/bybit/pnl.log 2>&1

# Circuit breaker check every 5 minutes
*/5 * * * * cd /path/to/scripts && python circuit_breaker.py >> /var/log/bybit/risk.log 2>&1

# TP/SL guardian every minute
* * * * * cd /path/to/scripts && python ensure_tp_sl.py --once >> /var/log/bybit/tpsl.log 2>&1
```

## Troubleshooting

**Bot won't start:**
- Check API credentials in `.env`
- Verify balance is sufficient
- Check `python bot_manager.py health` for errors

**No trades executed:**
- Verify signal conditions are met
- Check circuit breaker is not tripped
- Review bot logs in `/tmp/bybit_bots/*.log`

**Circuit breaker tripped:**
- Review loss limits in circuit breaker output
- Wait for cooldown period (4 hours default)
- Or manually reset state file at `/tmp/bybit_bots/circuit_breaker_state.json`

## License

MIT License - Use at your own risk.
