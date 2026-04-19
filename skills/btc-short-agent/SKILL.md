---
name: btc-short-agent
description: >
  A disciplined BTC short-only futures trading agent for Bybit. 
  Executes short positions with exactly 5x leverage, automatic 4% TP / 2% SL placement,
  and strict risk management. Never goes long. Trades BTCUSDT perpetual with signal
  scoring based on EMA200, RSI, MACD, funding rates, and resistance levels.
  Use when deploying an automated short-only BTC futures strategy, running a 
  systematic short bot on Bybit, or executing leveraged BTC shorts with predefined
  risk parameters.
---

# BTC Short-Only Bybit Agent

A complete automated trading system that **only shorts BTC** on Bybit Futures with **5x leverage**, strict risk management, and automatic TP/SL.

## Philosophy

- **Short-only**: Never goes long. Ever.
- **Disciplined**: Rules-based entries, no FOMO
- **Protected**: Every trade has TP/SL set immediately
- **Risk-managed**: Position sizing, daily limits, consecutive loss protection

## Trading Parameters

| Setting | Value |
|---------|-------|
| Symbol | BTCUSDT Perpetual |
| Side | SELL only |
| Leverage | 5x (fixed) |
| Take Profit | 4% below entry |
| Stop Loss | 2% above entry |
| Risk per Trade | 1.5% of balance |
| Timeframe | 15-minute candles |
| Check Interval | Every 15 minutes |

## Entry Signal (Score out of 5)

The agent evaluates these conditions:

1. **Price below EMA200** → Bearish macro trend
2. **RSI < 55 and declining** → No bullish momentum  
3. **Price near resistance** → Optimal entry zone
4. **Funding rate > 0.01%** → Longs over-leveraged, paying shorts
5. **MACD bearish crossover** → Momentum confirmation

| Score | Action |
|-------|--------|
| 5/5 | Full position (100%) |
| 4/5 | Full position (100%) |
| 3/5 | Half position (50%) |
| 0-2 | No trade |

## Risk Management

**Hard stops that halt trading:**
- ❌ Account balance drops below $100
- ❌ Daily drawdown exceeds 10%
- ❌ 3 consecutive losses in a row
- ❌ Funding rate negative (shorts would pay)
- ❌ Position already open (no pyramiding)

**Position protection:**
- ✅ TP and SL set immediately after entry
- ✅ Reduce-only orders for exits
- ✅ Emergency close on >3% pump against position

## Installation

```bash
# Install dependencies
pip install ccxt pandas pandas-ta

# Configure API keys
cd skills/btc-short-agent/scripts
cp .env.example .env
# Edit .env with your Bybit API credentials
```

## Usage

```bash
# Run the agent
python btc_short_agent.py

# The agent will:
# 1. Check for open positions every 15 minutes
# 2. Evaluate signals if no position
# 3. Enter short if score >= 3/5
# 4. Set TP/SL immediately
# 5. Monitor until closed
```

## Configuration

Edit `.env`:

```env
BYBIT_API_KEY=your_api_key
BYBIT_API_SECRET=your_api_secret
BYBIT_TESTNET=false  # Set true for testnet
```

## Output

**Console:** Real-time trade logs with signal scores

**Log file:** `/tmp/bybit_bots/btc_short_agent.log`

**Trade history:** `/tmp/bybit_bots/btc_trades.json`

Example trade record:
```json
{
  "timestamp": "2026-03-07T04:00:00Z",
  "action": "SHORT",
  "entry": 85000.00,
  "tp": 81600.00,
  "sl": 86700.00,
  "size": 0.012,
  "leverage": 5,
  "score": 4,
  "conditions": {
    "below_ema200": true,
    "rsi_bearish": true,
    "near_resistance": true,
    "funding_positive": true,
    "macd_bearish": false
  },
  "result": "OPEN"
}
```

## Safety Warnings

⚠️ **This is leverage trading. You can lose money.**

- 5x leverage means 20% price move = 100% loss
- The 2% SL means a 0.4% BTC pump hits your stop
- Funding rates can turn negative — agent will stop
- Test thoroughly on Bybit testnet first
- Never risk more than you can afford to lose

## Emergency Stop

To kill the agent immediately:
```bash
pkill -f btc_short_agent.py
```

To close position manually:
```python
# In Python shell
from btc_short_agent import BybitShortClient
client = BybitShortClient()
pos = client.get_open_position()
if pos:
    client.close_position(float(pos['contracts']))
```

## Monitoring

Watch the logs:
```bash
tail -f /tmp/bybit_bots/btc_short_agent.log
```

Check trade history:
```bash
cat /tmp/bybit_bots/btc_trades.json | jq '.[-5:]'
```

## License

Use at your own risk. Trading carries significant risk of loss.
