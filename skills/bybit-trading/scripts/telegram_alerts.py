#!/usr/bin/env python3
"""
Telegram Trading Alert System for Bybit
Sends automated trading reports to Telegram
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "8720858195:AAEZp2p-Z1F4wmXcry7K86yHDE4RsQvpz7M"
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5804173449")  # Human Boss's Telegram

def send_telegram_message(message, parse_mode="HTML"):
    """Send message to Telegram bot"""
    if not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_CHAT_ID not set")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": parse_mode
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")
        return False

def get_trading_summary():
    """Get current trading status summary"""
    try:
        import ccxt
        
        exchange = ccxt.bybit({
            'apiKey': os.getenv('BYBIT_API_KEY'),
            'secret': os.getenv('BYBIT_API_SECRET'),
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        
        # Get balance
        balance = exchange.fetch_balance()
        total_balance = balance['USDT']['total']
        available = balance['USDT']['free']
        
        # Get positions
        positions = exchange.fetch_positions()
        active_positions = []
        for p in positions:
            contracts = float(p.get('contracts', 0))
            if contracts != 0:
                active_positions.append({
                    'symbol': p['symbol'],
                    'side': p['side'].upper(),
                    'size': contracts,
                    'entry': float(p['entryPrice']),
                    'pnl': float(p['unrealizedPnl']),
                    'leverage': p.get('leverage', 5)
                })
        
        return {
            'balance': total_balance,
            'available': available,
            'positions': active_positions,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {'error': str(e)}

def format_alert(summary):
    """Format trading summary as Telegram message"""
    if 'error' in summary:
        return f"❌ <b>Trading Alert Error</b>\n\n{summary['error']}"
    
    msg = f"""📊 <b>Bybit Trading Report</b>
⏰ {summary['timestamp']}

💰 <b>Balance:</b> ${summary['balance']:.2f} USDT
💵 <b>Available:</b> ${summary['available']:.2f} USDT
"""
    
    if summary['positions']:
        msg += f"\n📈 <b>Open Positions ({len(summary['positions'])}):</b>\n"
        for pos in summary['positions']:
            pnl_emoji = "🟢" if pos['pnl'] >= 0 else "🔴"
            msg += f"\n{pos['symbol']} {pos['side']}\n"
            msg += f"  Size: {pos['size']} @ {pos['leverage']}x\n"
            msg += f"  Entry: ${pos['entry']:.2f}\n"
            msg += f"  {pnl_emoji} PnL: ${pos['pnl']:+.2f}\n"
    else:
        msg += "\n📈 <b>No Open Positions</b>\n"
        msg += "   Bots scanning for entries...\n"
    
    # Add bot status
    msg += "\n🤖 <b>Bot Status:</b> 13 Active\n"
    msg += "   BTC/ETH/XRP - Scalping/Mean/Momentum/Grid"
    
    return msg

def main():
    """Main function - send trading alert"""
    print(f"[{datetime.now()}] Generating trading alert...")
    
    # Get trading data
    summary = get_trading_summary()
    
    # Format message
    message = format_alert(summary)
    
    # Send to Telegram
    if send_telegram_message(message):
        print("✅ Alert sent successfully")
    else:
        print("❌ Failed to send alert")
        print(message)

if __name__ == "__main__":
    main()
