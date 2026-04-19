"""
P&L Check - Calculate and report trading performance
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import ccxt
import config  # Loads .env file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('pnl_check')

class PnLTracker:
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        
        self.exchange = ccxt.bybit({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'options': {'defaultType': 'swap'}
        })
    
    def get_balance(self) -> Dict:
        """Get current balance info."""
        balance = self.exchange.fetch_balance()
        usdt = balance.get('USDT', {})
        return {
            'free': usdt.get('free', 0),
            'used': usdt.get('used', 0),
            'total': usdt.get('total', 0)
        }
    
    def get_positions_pnl(self) -> List[Dict]:
        """Get unrealized P&L from open positions."""
        positions = self.exchange.fetch_positions()
        results = []
        
        for pos in positions:
            contracts = float(pos.get('contracts', 0))
            if contracts == 0:
                continue
            
            unrealized_pnl = float(pos.get('unrealizedPnl', 0))
            initial_margin = float(pos.get('initialMargin', 0))
            
            roi_pct = (unrealized_pnl / initial_margin * 100) if initial_margin > 0 else 0
            
            results.append({
                'symbol': pos['symbol'],
                'side': pos['side'],
                'size': contracts,
                'entry_price': float(pos.get('entryPrice', 0)),
                'mark_price': float(pos.get('markPrice', 0)),
                'unrealized_pnl': unrealized_pnl,
                'roi_pct': roi_pct,
                'leverage': float(pos.get('leverage', 1))
            })
        
        return results
    
    def get_closed_pnl(self, days: int = 1) -> float:
        """Get realized P&L from closed trades."""
        try:
            since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            trades = self.exchange.fetch_my_trades(since=since)
            
            realized_pnl = sum(float(trade.get('realizedPnl', 0)) for trade in trades)
            return realized_pnl
        except Exception as e:
            logger.error(f"Failed to fetch closed PnL: {e}")
            return 0
    
    def generate_report(self) -> Dict:
        """Generate comprehensive P&L report."""
        balance = self.get_balance()
        positions = self.get_positions_pnl()
        
        total_unrealized = sum(p['unrealized_pnl'] for p in positions)
        daily_realized = self.get_closed_pnl(days=1)
        weekly_realized = self.get_closed_pnl(days=7)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'balance': balance,
            'open_positions': {
                'count': len(positions),
                'positions': positions,
                'total_unrealized_pnl': total_unrealized
            },
            'realized_pnl': {
                'daily': daily_realized,
                'weekly': weekly_realized
            },
            'total_pnl': total_unrealized + daily_realized
        }
        
        return report
    
    def format_report(self, report: Dict) -> str:
        """Format report for display."""
        lines = [
            "="*50,
            "📊 Bybit Trading P&L Report",
            f"Generated: {report['timestamp']}",
            "="*50,
            "",
            f"💰 Balance: {report['balance']['total']:.2f} USDT",
            f"   (Free: {report['balance']['free']:.2f} | Used: {report['balance']['used']:.2f})",
            "",
            f"📈 Open Positions: {report['open_positions']['count']}",
        ]
        
        for pos in report['open_positions']['positions']:
            emoji = "🟢" if pos['unrealized_pnl'] >= 0 else "🔴"
            lines.append(f"   {emoji} {pos['symbol']} {pos['side'].upper()}")
            lines.append(f"      PnL: {pos['unrealized_pnl']:.2f} USDT ({pos['roi_pct']:+.2f}%)")
        
        if report['open_positions']['positions']:
            lines.append(f"\n   Total Unrealized: {report['open_positions']['total_unrealized_pnl']:.2f} USDT")
        
        lines.extend([
            "",
            "💵 Realized PnL:",
            f"   Daily:  {report['realized_pnl']['daily']:+.2f} USDT",
            f"   Weekly: {report['realized_pnl']['weekly']:+.2f} USDT",
            "",
            f"📊 Total PnL (inc. unrealized): {report['total_pnl']:+.2f} USDT",
            "="*50
        ])
        
        return "\n".join(lines)

def main():
    tracker = PnLTracker()
    report = tracker.generate_report()
    
    print(tracker.format_report(report))
    
    # Also output JSON for automation
    output_json = os.getenv('OUTPUT_JSON')
    if output_json:
        with open(output_json, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to {output_json}")

if __name__ == '__main__':
    main()
