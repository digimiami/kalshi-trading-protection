# HEARTBEAT.md

## Kalshi Alerts Check
- Check `/root/.openclaw/workspace/skills/kalshi-live-trading/logs/alerts.log`
- If there are new lines since last check, send them to the user via Telegram
- Use `/root/.openclaw/workspace/skills/kalshi-live-trading/logs/heartbeat_alerts.pos` to track last-read position

## Self-Improving Check
- Read `./skills/self-improving/heartbeat-rules.md`
- Use `~/self-improving/heartbeat-state.md` for last-run markers and action notes
- If no file inside `~/self-improving/` changed since the last reviewed change, return `HEARTBEAT_OK`
