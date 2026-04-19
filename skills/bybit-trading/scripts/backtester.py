"""
Backtesting Framework for Strategy Optimization
Tests strategies on historical data to find optimal parameters
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
import pandas_ta as ta
import numpy as np
from pybit.unified_trading import HTTP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('backtester')

class Backtester:
    def __init__(self, symbol: str = 'BTCUSDT', timeframe: str = '15m'):
        self.symbol = symbol
        self.timeframe = timeframe
        self.initial_balance = 1000  # USDT
        
        session = HTTP(
            testnet=False,
            api_key=os.getenv('BYBIT_API_KEY'),
            api_secret=os.getenv('BYBIT_API_SECRET'),
        )
        self.session = session
        
    def fetch_historical_data(self, days: int = 30) -> pd.DataFrame:
        """Fetch historical kline data."""
        logger.info(f"Fetching {days} days of historical data for {self.symbol}")
        
        # Calculate timestamps
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        all_data = []
        current_time = end_time
        
        while current_time > start_time:
            resp = self.session.get_kline(
                category='linear',
                symbol=self.symbol,
                interval=self.timeframe,
                end=current_time,
                limit=200
            )
            
            data = resp['result']['list']
            if not data:
                break
                
            all_data.extend(data)
            current_time = int(data[-1][0]) - 1  # Start from last candle
            
        # Convert to DataFrame
        df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        df = df.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': float})
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        df = df.sort_values('timestamp').drop_duplicates()
        
        logger.info(f"Fetched {len(df)} candles")
        return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators."""
        # RSI
        df['rsi'] = ta.rsi(df['close'], length=14)
        
        # Bollinger Bands
        bb = ta.bbands(df['close'], length=20, std=2.0)
        if bb is not None:
            df['bb_upper'] = bb['BBU_20_2.0']
            df['bb_lower'] = bb['BBL_20_2.0']
            df['bb_middle'] = bb['BBM_20_2.0']
        
        # Moving Averages
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        macd = ta.macd(df['close'])
        if macd is not None:
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
        
        # ATR
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        return df
    
    def backtest_scalping(self, df: pd.DataFrame, 
                         rsi_entry: int = 30,
                         rsi_exit: int = 55,
                         tp_pct: float = 0.8,
                         sl_pct: float = 0.5) -> Dict:
        """Backtest scalping strategy."""
        df = self.calculate_indicators(df)
        
        trades = []
        balance = self.initial_balance
        position = None
        entry_price = 0
        
        for i in range(20, len(df)):
            row = df.iloc[i]
            
            if np.isnan(row['rsi']):
                continue
            
            # Check for entry
            if position is None:
                # Long entry: RSI oversold
                if row['rsi'] < rsi_entry and row['close'] <= row['bb_lower']:
                    position = 'long'
                    entry_price = row['close']
                    entry_time = row['timestamp']
                
                # Short entry: RSI overbought
                elif row['rsi'] > (100 - rsi_entry) and row['close'] >= row['bb_upper']:
                    position = 'short'
                    entry_price = row['close']
                    entry_time = row['timestamp']
            
            # Check for exit
            else:
                exit_reason = None
                
                if position == 'long':
                    # TP hit
                    if row['high'] >= entry_price * (1 + tp_pct/100):
                        exit_price = entry_price * (1 + tp_pct/100)
                        exit_reason = 'TP'
                    # SL hit
                    elif row['low'] <= entry_price * (1 - sl_pct/100):
                        exit_price = entry_price * (1 - sl_pct/100)
                        exit_reason = 'SL'
                    # RSI exit
                    elif row['rsi'] > rsi_exit:
                        exit_price = row['close']
                        exit_reason = 'RSI'
                
                else:  # short
                    # TP hit
                    if row['low'] <= entry_price * (1 - tp_pct/100):
                        exit_price = entry_price * (1 - tp_pct/100)
                        exit_reason = 'TP'
                    # SL hit
                    elif row['high'] >= entry_price * (1 + sl_pct/100):
                        exit_price = entry_price * (1 + sl_pct/100)
                        exit_reason = 'SL'
                    # RSI exit
                    elif row['rsi'] < (100 - rsi_exit):
                        exit_price = row['close']
                        exit_reason = 'RSI'
                
                if exit_reason:
                    pnl = (exit_price - entry_price) / entry_price * 100
                    if position == 'short':
                        pnl = -pnl
                    
                    trades.append({
                        'side': position,
                        'entry': entry_price,
                        'exit': exit_price,
                        'pnl_pct': pnl,
                        'exit_reason': exit_reason,
                        'duration': str(row['timestamp'] - entry_time)
                    })
                    
                    balance *= (1 + pnl/100)
                    position = None
        
        # Calculate metrics
        if trades:
            wins = [t for t in trades if t['pnl_pct'] > 0]
            losses = [t for t in trades if t['pnl_pct'] <= 0]
            
            win_rate = len(wins) / len(trades) * 100
            avg_win = np.mean([t['pnl_pct'] for t in wins]) if wins else 0
            avg_loss = np.mean([t['pnl_pct'] for t in losses]) if losses else 0
            total_return = (balance - self.initial_balance) / self.initial_balance * 100
            
            return {
                'trades': len(trades),
                'win_rate': round(win_rate, 2),
                'profit_factor': abs(sum(t['pnl_pct'] for t in wins) / sum(t['pnl_pct'] for t in losses)) if losses and sum(t['pnl_pct'] for t in losses) != 0 else 999,
                'total_return': round(total_return, 2),
                'final_balance': round(balance, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'parameters': {'rsi_entry': rsi_entry, 'rsi_exit': rsi_exit, 'tp_pct': tp_pct, 'sl_pct': sl_pct}
            }
        
        return {'trades': 0, 'total_return': 0}
    
    def optimize_parameters(self) -> Dict:
        """Find optimal parameters through grid search."""
        logger.info("Starting parameter optimization...")
        
        df = self.fetch_historical_data(days=30)
        
        # Parameter grid for scalping
        rsi_entries = [25, 30, 35]
        rsi_exits = [50, 55, 60]
        tp_pcts = [0.5, 0.8, 1.0]
        sl_pcts = [0.3, 0.5, 0.8]
        
        results = []
        
        for rsi_entry in rsi_entries:
            for rsi_exit in rsi_exits:
                for tp_pct in tp_pcts:
                    for sl_pct in sl_pcts:
                        result = self.backtest_scalping(df, rsi_entry, rsi_exit, tp_pct, sl_pct)
                        if result['trades'] > 10:  # Minimum trades
                            results.append(result)
        
        # Sort by total return
        results.sort(key=lambda x: x['total_return'], reverse=True)
        
        # Save results
        os.makedirs('/tmp/bybit_bots', exist_ok=True)
        with open('/tmp/bybit_bots/backtest_results.json', 'w') as f:
            json.dump(results[:10], f, indent=2)
        
        logger.info(f"Optimization complete. Best result: {results[0] if results else 'No valid results'}")
        return results[0] if results else {}
    
    def run(self):
        """Run backtest and optimization."""
        best_params = self.optimize_parameters()
        
        if best_params:
            print("\n" + "="*70)
            print("📊 BACKTEST RESULTS - OPTIMAL PARAMETERS")
            print("="*70)
            print(f"Trades: {best_params['trades']}")
            print(f"Win Rate: {best_params['win_rate']}%")
            print(f"Total Return: {best_params['total_return']}%")
            print(f"Profit Factor: {best_params['profit_factor']}")
            print(f"Final Balance: ${best_params['final_balance']}")
            print(f"\nOptimal Parameters:")
            for k, v in best_params['parameters'].items():
                print(f"  {k}: {v}")
            print("="*70)
        
        return best_params

if __name__ == '__main__':
    bt = Backtester()
    bt.run()
