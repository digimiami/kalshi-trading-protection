# Trading Strategies Reference

## Scalping (RSI + Bollinger Bands)

**Timeframe:** 1 minute  
**Hold Time:** 15-20 minutes max

### Entry Conditions

**Long Entry:**
- RSI < 30 (oversold)
- Price touches or breaks below lower Bollinger Band
- Price bounces back above lower band (confirmation candle)

**Short Entry:**
- RSI > 70 (overbought)
- Price touches or breaks above upper Bollinger Band
- Price rejects back below upper band (confirmation candle)

### Exit Conditions
- Take Profit: 0.8%
- Stop Loss: 0.5%
- Time limit: 20 minutes (market exit)

### Risk Parameters
- Position size: 5% of balance
- Leverage: 5x
- Max concurrent positions: 5

---

## Mean Reversion

**Timeframe:** 5m / 15m

### Entry Conditions

**Long Entry:**
- Z-score < -2 (price 2+ standard deviations below mean)
- Price below lower Bollinger Band
- Price showing reversal candle

**Short Entry:**
- Z-score > 2 (price 2+ standard deviations above mean)
- Price above upper Bollinger Band
- Price showing rejection candle

### Exit Conditions
- Take Profit: 2-3%
- Stop Loss: 1.5%

### Risk Parameters
- Position size: 10% of balance
- Leverage: 3x
- Max concurrent positions: 3

---

## Momentum

**Timeframe:** 15m / 1h

### Entry Conditions

**Long Entry:**
- Price breaks above 20-period high
- Volume > 1.5x average
- ATR expanding (volatility confirmation)

**Short Entry:**
- Price breaks below 20-period low
- Volume > 1.5x average
- ATR expanding (volatility confirmation)

### Exit Conditions
- Take Profit: 5-8%
- Stop Loss: 2-3%
- Trailing stop after 3% profit

### Risk Parameters
- Position size: 8% of balance
- Leverage: 4x
- Max concurrent positions: 2

---

## Grid Trading

### Configuration
- Grid levels: 10
- Grid spacing: 1%
- Position per grid: $100 USDT

### Operation
1. Center grid around current price
2. Place buy orders below current price
3. Place sell orders above current price
4. When a buy fills, place a sell 1 level higher
5. When a sell fills, place a buy 1 level lower
6. Rebalance grid when price moves >5 levels away

### Risk Parameters
- Total allocated: $1000 USDT (10 grids × $100)
- Leverage: 3x
- Max loss per grid: limited by grid spacing

---

## Risk Management Summary

| Parameter | Value |
|-----------|-------|
| Max Daily Loss | 5% |
| Max Drawdown | 10% |
| Circuit Cooldown | 4 hours |
| Max Positions (per strategy) | 5 |
| Max Total Positions | 10 |

### Circuit Breaker Triggers
1. Daily loss exceeds 5%
2. Drawdown from peak exceeds 10%
3. Manual trigger via API

When tripped:
- All new position entries blocked
- Existing positions managed to TP/SL
- 4-hour cooldown before re-enabling
