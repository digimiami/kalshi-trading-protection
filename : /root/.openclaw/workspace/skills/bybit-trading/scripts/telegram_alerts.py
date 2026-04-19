: import os
import sys
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pybit.unified_trading import HTTP

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Bybit API Configuration
API_KEY = os.getenv('BYBIT_API_KEY', '')
API_SECRET = os.getenv('BYBIT_API_SECRET', '')

async def send_telegram_message(message: str, parse_mode: str = 'HTML'):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram credentials not configured")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                print("✅ Telegram message sent successfully")
                return True
            else:
                print(f"❌ Failed to send Telegram message: {response.status}")
                return False

def get_bybit_client():
    """Create Bybit API client"""
    return HTTP(
        testnet=False,
        api_key=API_KEY,
        api_secret=API_SECRET,
    )

def get_account_balance(session):
    """Get account balance"""
    try:
        response = session.get_wallet_balance(accountType="UNIFIED")
        if response['retCode'] == 0:
            total_balance = 0
            available_balance = 0
            for coin_data in response['result']['list'][0]['coin']:
                if coin_data['coin'] == 'USDT':
                    total_balance = float(coin_data['walletBalance'])
                    available_balance = float(coin_data['availableToWithdraw'])
                    break
            return total_balance, available_balance
        return 0, 0
    except Exception as e:
        print(f"Error fetching balance: {e}")
        return 0, 0

def get_positions(session):
    """Get current positions"""
    try:
        response = session.get_positions(category="linear", settleCoin="USDT")
        if response['retCode'] == 0:
            positions = []
            for pos in response['result']['list']:
                if float(pos['size']) > 0:
                    positions.append({
                        'symbol': pos['symbol'],
                        'side': pos['side'],
                        'size': float(pos['size']),
                        'entry_price': float(pos['avgPrice']),
                        'mark_price': float(pos['markPrice']),
                        'pnl': float(pos['unrealisedPnl']),
                        'pnl_percent': float(pos['unrealisedPnl']) / (float(pos['avgPrice']) * float(pos['size'])) * 100 if float(pos['avgPrice']) > 0 else 0,
                        'leverage': pos['leverage'],
                        'tp': pos.get('takeProfit', '0'),
                        'sl': pos.get('stopLoss', '0')
                    })
            return positions
        return []
    except Exception as e:
        print(f"Error fetching positions: {e}")
        return []

def get_24h_pnl(session):
    """Get 24h P&L"""
    try:
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)
        
        response = session.get_closed_pnl(
            category="linear",
            startTime=start_time,
            endTime=end_time,
            limit=100
        )
        
        if response['retCode'] == 0:
            total_pnl = sum(float(trade['closedPnl']) for trade in response['result']['list'])
            return total_pnl
        return 0
    except Exception as e:
        print(f"Error fetching 24h PnL: {e}")
        return 0

def get_market_prices(session):
    """Get current market prices for major pairs"""
    try:
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        prices = {}
        for symbol in symbols:
            response = session.get_tickers(category="linear", symbol=symbol)
            if response['retCode'] == 0 and response['result']['list']:
                ticker = response['result']['list'][0]
                prices[symbol] = {
                    'last_price': float(ticker['lastPrice']),
                    'change_24h': float(ticker['price24hPcnt']) * 100,
                    'volume': float(ticker['turnover24h'])
                }
        return prices
    except Exception as e:
        print(f"Error fetching market prices: {e}")
        return {}

def format_alert_report(balance, available, positions, pnl_24h, prices):
    """Format trading alert report"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S CST')
    
    # Header
    report = f"📊 <b>Bybit Trading Alert</b>\n"
    report += f"🕐 <code>{now}</code>\n"
    report += "─" * 25 + "\n\n"
    
    # Account Balance
    report += f"💰 <b>Account Balance</b>\n"
    report += f"   Total: <code>${balance:,.2f}</code> USDT\n"
    report += f"   Available: <code>${available:,.2f}</code> USDT\n"
    report += f"   In Positions: <code>${balance - available:,.2f}</code> USDT\n\n"
    
    # 24h P&L
    pnl_emoji = "🟢" if pnl_24h >= 0 else "🔴"
    report += f"{pnl_emoji} <b>24h Realized P&L</b>: <code>${pnl_24h:+.2f}</code>\n\n"
    
    # Active Positions
    if positions:
        report += f"📈 <b>Active Positions ({len(positions)})</b>\n\n"
        for pos in positions:
            side_emoji = "🟢 LONG" if pos['side'] == 'Buy' else "🔴 SHORT"
            pnl_status = "🟢" if pos['pnl'] >= 0 else "🔴"
            
            report += f"<b>{pos['symbol']}</b> {side_emoji}\n"
            report += f"   Size: <code>{pos['size']}</code> @ <code>${pos['entry_price']:,.2f}</code>\n"
            report += f"   Mark: <code>${pos['mark_price']:,.2f}</code>\n"
            report += f"   P&L: {pnl_status} <code>${pos['pnl']:+.2f}</code> ({pos['pnl_percent']:+.2f}%)\n"
            if pos['tp'] != '0':
                report += f"   TP: <code>${float(pos['tp']):,.2f}</code>\n"
            if pos['sl'] != '0':
                report += f"   SL: <code>${float(pos['sl']):,.2f}</code>\n"
            report += "\n"
    else:
        report += "📭 <b>No Active Positions</b>\n\n"
    
    # Market Prices
    if prices:
        report += f"🌍 <b>Market Prices (24h)</b>\n"
        for symbol, data in prices.items():
            change_emoji = "🟢" if data['change_24h'] >= 0 else "🔴"
            coin = symbol.replace('USDT', '')
            report += f"   {coin}: <code>${data['last_price']:,.2f}</code> {change_emoji} {data['change_24h']:+.2f}%\n"
    
    return report

async def main():
    """Main function"""
    print("🚀 Starting Telegram Trading Alert...")
    
    try:
        # Initialize Bybit client
        session = get_bybit_client()
        
        # Fetch data
        print("📊 Fetching account data...")
        balance, available = get_account_balance(session)
        
        print("📈 Fetching positions...")
        positions = get_positions(session)
        
        print("💹 Fetching 24h P&L...")
        pnl_24h = get_24h_pnl(session)
        
        print("🌍 Fetching market prices...")
        prices = get_market_prices(session)
        
        # Format report
        print("📝 Formatting alert report...")
        report = format_alert_report(balance, available, positions, pnl_24h, prices)
        
        # Send to Telegram
        print("📤 Sending to Telegram...")
        await send_telegram_message(report)
        
        print("✅ Trading alert completed successfully!")
        
    except Exception as e:
        error_msg = f"❌ <b>Trading Alert Error</b>\n\n<code>{str(e)}</code>"
        print(f"Error: {e}")
        await send_telegram_message(error_msg)

if __name__ == "__main__":
    asyncio.run(main())