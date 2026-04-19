# RSI + Moving Average Trading Bot Configuration

## Trading Pairs
BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, NEARUSDT, LINKUSDT, DOGEUSDT

## Strategy: RSI + Moving Averages

### Buy Conditions
- RSI oversold (< 30)
- OR price above MA20 with upward trend

### Sell Conditions  
- RSI overbought (> 70)

## Risk Management Settings

| Setting | Value |
|---------|-------|
| Max Positions | 3 |
| Position Size | 10% of balance |
| Take Profit | 2.5% |
| Stop Loss | 2.5% |
| Trailing Stop | 1% (activates after 1% profit) |

## Technical Indicators
- RSI Period: 14
- MA Period: 20
- Timeframe: 5m (recommended) or 15m

## Other Bots in System
1. **Scalping Bot** (1-minute timeframe)
2. **Momentum Trader**
3. **Mean Reversion Trader**
4. **RSI + MA Bot** (this configuration)

## Notes
- This bot focuses on swing trading with trend confirmation
- Trailing stop protects profits once 1% gain is achieved
- Max 3 concurrent positions to avoid overexposure

---
Created: 2026-03-23
Status: Configuration ready for implementation
