"""
Machine Learning Signal Enhancement Bot
Uses technical indicators + price patterns to predict short-term moves
"""
import os
import time
import logging
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import ccxt
import config
import pandas as pd
import pandas_ta as ta
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ml_bot')

class MLTradingBot:
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        self.symbol = os.getenv('TRADING_SYMBOL', 'BTC/USDT:USDT')
        self.leverage = int(os.getenv('LEVERAGE', '3'))
        self.position_size_pct = float(os.getenv('POSITION_SIZE_PCT', '5'))
        self.lookback_period = int(os.getenv('ML_LOOKBACK', '100'))
        self.prediction_horizon = int(os.getenv('PREDICTION_HORIZON', '5'))  # candles ahead
        self.confidence_threshold = float(os.getenv('CONFIDENCE_THRESHOLD', '0.65'))
        self.retrain_interval = int(os.getenv('RETRAIN_INTERVAL', '100'))  # candles
        
        self.exchange = ccxt.bybit({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'options': {'defaultType': 'swap'}
        })
        
        self.model = None
        self.scaler = StandardScaler()
        self.candle_count = 0
        self.model_path = '/tmp/bybit_bots/ml_model.pkl'
        self.scaler_path = '/tmp/bybit_bots/ml_scaler.pkl'
        
        self.load_model()
        
    def load_model(self):
        """Load existing model if available."""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info("ML model loaded from disk")
            else:
                self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
                logger.info("New ML model initialized")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    
    def save_model(self):
        """Save model to disk."""
        try:
            os.makedirs('/tmp/bybit_bots', exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            logger.info("Model saved to disk")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def fetch_ohlcv(self, timeframe='15m', limit: int = 200) -> pd.DataFrame:
        """Fetch OHLCV data."""
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = df.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': float})
        return df
    
    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical features for ML."""
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['returns_3'] = df['close'].pct_change(3)
        df['returns_5'] = df['close'].pct_change(5)
        
        # Moving averages
        df['sma_10'] = df['close'].rolling(10).mean()
        df['sma_20'] = df['close'].rolling(20).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        macd = ta.macd(df['close'])
        if macd is not None:
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            df['macd_hist'] = macd['MACDh_12_26_9']
        
        # RSI
        df['rsi'] = ta.rsi(df['close'], length=14)
        df['rsi_5'] = ta.rsi(df['close'], length=5)
        
        # Bollinger Bands
        bb = ta.bbands(df['close'], length=20, std=2.0)
        if bb is not None:
            df['bb_upper'] = bb['BBU_20_2.0']
            df['bb_lower'] = bb['BBL_20_2.0']
            df['bb_pct'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # ATR (volatility)
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        df['atr_pct'] = df['atr'] / df['close']
        
        # Volume features
        df['volume_sma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Price position
        df['close_position'] = (df['close'] - df['low'].rolling(20).min()) / (df['high'].rolling(20).max() - df['low'].rolling(20).min())
        
        return df
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and labels for training."""
        df = self.calculate_features(df)
        
        # Create target: 1 if price goes up in next N candles, 0 if down
        future_returns = df['close'].shift(-self.prediction_horizon) / df['close'] - 1
        df['target'] = (future_returns > 0).astype(int)
        
        # Select features
        feature_cols = [
            'returns', 'returns_3', 'returns_5',
            'sma_10', 'sma_20', 'ema_12', 'ema_26',
            'macd', 'macd_signal', 'macd_hist',
            'rsi', 'rsi_5', 'bb_pct', 'atr_pct',
            'volume_ratio', 'close_position'
        ]
        
        # Drop NaN
        df = df[feature_cols + ['target']].dropna()
        
        if len(df) < 50:
            return None, None
        
        X = df[feature_cols].values
        y = df['target'].values
        
        return X, y
    
    def train_model(self):
        """Train the ML model."""
        try:
            logger.info("Training ML model...")
            df = self.fetch_ohlcv(limit=500)
            X, y = self.prepare_training_data(df)
            
            if X is None or len(X) < 50:
                logger.warning("Not enough data to train")
                return
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            accuracy = self.model.score(X_scaled, y)
            
            logger.info(f"Model trained | Accuracy: {accuracy:.2%} | Samples: {len(X)}")
            self.save_model()
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
    
    def predict(self, df: pd.DataFrame) -> Tuple[str, float]:
        """
        Predict direction and confidence.
        Returns: (direction, confidence)
        """
        try:
            df = self.calculate_features(df)
            
            feature_cols = [
                'returns', 'returns_3', 'returns_5',
                'sma_10', 'sma_20', 'ema_12', 'ema_26',
                'macd', 'macd_signal', 'macd_hist',
                'rsi', 'rsi_5', 'bb_pct', 'atr_pct',
                'volume_ratio', 'close_position'
            ]
            
            latest = df[feature_cols].iloc[-1:].values
            
            # Handle NaN
            if np.isnan(latest).any():
                logger.warning("NaN in features, cannot predict")
                return 'neutral', 0.5
            
            X_scaled = self.scaler.transform(latest)
            
            # Get prediction probability
            proba = self.model.predict_proba(X_scaled)[0]
            prediction = self.model.predict(X_scaled)[0]
            
            confidence = proba[prediction]
            direction = 'long' if prediction == 1 else 'short'
            
            return direction, confidence
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 'neutral', 0.5
    
    def get_balance(self) -> float:
        balance = self.exchange.fetch_balance()
        return balance['USDT']['free'] if 'USDT' in balance else 0
    
    def get_position(self) -> Optional[Dict]:
        positions = self.exchange.fetch_positions([self.symbol])
        for pos in positions:
            if float(pos.get('contracts', 0)) != 0:
                return pos
        return None
    
    def calculate_position_size(self) -> float:
        balance = self.get_balance()
        position_value = balance * (self.position_size_pct / 100)
        ticker = self.exchange.fetch_ticker(self.symbol)
        price = ticker['last']
        amount = position_value / price
        return max(0.001, round(amount, 3))
    
    def open_position(self, side: str, confidence: float):
        try:
            try:
                self.exchange.set_leverage(self.leverage, self.symbol)
            except:
                pass
            
            amount = self.calculate_position_size()
            
            ticker = self.exchange.fetch_ticker(self.symbol)
            entry_price = ticker['last']
            
            # TP/SL based on confidence
            tp_pct = 0.02 * confidence  # 2% scaled by confidence
            sl_pct = 0.01  # 1% fixed stop
            
            if side == 'long':
                tp_price = entry_price * (1 + tp_pct)
                sl_price = entry_price * (1 - sl_pct)
            else:
                tp_price = entry_price * (1 - tp_pct)
                sl_price = entry_price * (1 + sl_pct)
            
            ccxt_side = 'buy' if side == 'long' else 'sell'
            
            order = self.exchange.create_market_order(
                self.symbol,
                ccxt_side,
                amount,
                params={
                    'takeProfit': tp_price,
                    'stopLoss': sl_price
                }
            )
            
            logger.info(f"🤖 ML {side.upper()} | Confidence: {confidence:.1%} | Entry: ${entry_price:.2f}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to open: {e}")
            return None
    
    def close_position(self):
        try:
            pos = self.get_position()
            if not pos:
                return
            side = 'sell' if pos['side'] == 'long' else 'buy'
            amount = abs(float(pos['contracts']))
            self.exchange.create_market_order(self.symbol, side, amount, {'reduceOnly': True})
            logger.info("Position closed")
        except Exception as e:
            logger.error(f"Error closing: {e}")
    
    def run(self):
        logger.info(f"🤖 ML bot started | Symbol: {self.symbol} | Confidence threshold: {self.confidence_threshold:.0%}")
        
        # Initial training
        self.train_model()
        
        while True:
            try:
                self.candle_count += 1
                
                # Retrain periodically
                if self.candle_count % self.retrain_interval == 0:
                    self.train_model()
                
                current_pos = self.get_position()
                
                if current_pos:
                    logger.info("Position active - monitoring...")
                else:
                    df = self.fetch_ohlcv()
                    direction, confidence = self.predict(df)
                    
                    if confidence >= self.confidence_threshold and direction != 'neutral':
                        logger.info(f"🤖 ML SIGNAL: {direction.upper()} | Confidence: {confidence:.1%}")
                        self.open_position(direction, confidence)
                    else:
                        logger.debug(f"No trade | Direction: {direction} | Confidence: {confidence:.1%}")
                
                time.sleep(900)  # 15 minutes
                
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    bot = MLTradingBot()
    bot.run()
