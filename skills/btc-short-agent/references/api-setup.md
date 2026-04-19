# Bybit API Key Setup

## Getting Your API Keys

1. Log in to [Bybit](https://www.bybit.com)
2. Go to **Account & Security** → **API Management**
3. Click **Create New Key**
4. Select **System-generated API Keys**
5. Enable permissions:
   - ✅ **Contract Trading** (Read & Write)
   - ✅ **Position** (Read)
   - ❌ **Withdrawal** (Never enable)
6. Add IP whitelist (your VPS IP for security)
7. Copy API Key and Secret

## Testnet vs Live

**Testnet (practice):**
- URL: https://testnet.bybit.com
- Free test funds
- Same API structure
- Set `BYBIT_TESTNET=true`

**Live trading:**
- Real money, real risk
- Set `BYBIT_TESTNET=false`

## Environment Variables

```bash
export BYBIT_API_KEY="your_api_key"
export BYBIT_API_SECRET="your_api_secret"
export BYBIT_TESTNET="false"
```

Or use the `.env` file in the scripts directory.

## Security Best Practices

1. **Never share API keys**
2. **Use IP whitelist** — restrict to your server IP
3. **No withdrawal permissions** — trading only
4. **Monitor API usage** — check for unauthorized access
5. **Rotate keys periodically** — generate new keys monthly
