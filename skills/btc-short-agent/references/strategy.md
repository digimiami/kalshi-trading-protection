# Trading Strategy Reference

## Signal Conditions Explained

### 1. Price Below EMA200
- **What it means**: BTC trading below its 200-period moving average
- **Why it matters**: Indicates bearish macro trend
- **Threshold**: Price < EMA200

### 2. RSI Below 55 and Declining
- **What it means**: Momentum indicator showing weakening buying pressure
- **Why it matters**: Early signal of potential reversal
- **Threshold**: RSI(14) < 55 AND current RSI < previous RSI

### 3. Near Resistance
- **What it means**: Price within 0.5% of recent swing high
- **Why it matters**: Resistance often causes reversals
- **Calculation**: `abs(price - recent_high) / recent_high < 0.005`

### 4. Positive Funding Rate
- **What it means**: Longs pay shorts to hold positions
- **Why it matters**: Indicates over-leveraged longs, ripe for squeeze
- **Threshold**: Funding rate > 0.01%

### 5. MACD Bearish
- **What it means**: MACD line crosses below signal line
- **Why it matters**: Confirms bearish momentum shift
- **Calculation**: MACD < Signal

## Position Sizing

```python
position_size = (balance * risk_pct * confidence) / price_risk * leverage

# Example:
# Balance: $1000
# Risk: 1.5%
# Entry: $80,000
# SL: $81,600 (2% above)
# Price risk: $1,600
# Leverage: 5x
# Confidence: 1.0 (full) or 0.5 (half)

qty = (1000 * 0.015 * 1.0) / 1600 * 5 = 0.046 BTC
```

## Risk/Reward Math

| Metric | Value |
|--------|-------|
| Entry | $80,000 |
| TP (4% below) | $76,800 |
| SL (2% above) | $81,600 |
| Potential Profit | $3,200 per BTC |
| Potential Loss | $1,600 per BTC |
| Risk/Reward | 1:2 |

With 5x leverage:
- 4% move = 20% account gain
- 2% move = 10% account loss

## When NOT to Trade

Skip the signal if:
- ❌ Any single condition scores 0/5 with no compensating factors
- ❌ Major news event (FOMC, CPI, ETF approval)
- ❌ BTC pumped >5% in last hour (chasing)
- ❌ Weekend low volume (wider spreads)
- ❌ You already have an open position

## Win Rate Expectations

With 2:1 R/R and 35% win rate:
- 35 wins × 2R = +70R
- 65 losses × 1R = -65R
- Net: +5R (profitable)

Target: 40-50% win rate with strict discipline.
