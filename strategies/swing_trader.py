# strategies/swing_trader.py
"""
Swing trading strategy for 5-10% monthly returns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta
from technical_indicators import RSI, MACD, volume_spike, VWAP
from SmartApiActions import SmartApiActions

class SwingTrader:
    def __init__(self, smart_api: SmartApiActions):
        self.smart_api = smart_api
        self.target_return = 0.08  # 8% target
        self.stop_loss = 0.05  # 5% stop loss
        self.holding_period = 20  # days
        
    def scan_momentum_stocks(self, watchlist: List[str]) -> List[Dict]:
        """Scan for stocks with momentum characteristics"""
        momentum_stocks = []
        
        for stock in watchlist:
            try:
                # Get 60-day data for swing analysis
                end_date = datetime.now()
                start_date = end_date - timedelta(days=60)
                
                candle_data = self.smart_api.get_candel_data(
                    stock, start_date, end_date, "ONE_DAY"
                )
                
                if candle_data and candle_data.get('data'):
                    df = pd.DataFrame(candle_data['data'])
                    df['datetime'] = pd.to_datetime(df[0])
                    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
                    df.set_index('datetime', inplace=True)
                    
                    # Apply indicators
                    df = RSI(df)
                    df = volume_spike(df)
                    df = VWAP(df)
                    
                    # Calculate momentum metrics
                    momentum_score = self._calculate_momentum_score(df)
                    
                    if momentum_score > 60:
                        momentum_stocks.append({
                            'symbol': stock,
                            'momentum_score': momentum_score,
                            'rsi': df['RSI'].iloc[-1],
                            'volume_spike': df['volume_spike'].iloc[-1],
                            'entry_price': df['close'].iloc[-1],
                            'target': df['close'].iloc[-1] * (1 + self.target_return),
                            'stop_loss': df['close'].iloc[-1] * (1 - self.stop_loss)
                        })
                        
            except Exception as e:
                print(f"Error scanning {stock}: {str(e)}")
                continue
                
        return sorted(momentum_stocks, key=lambda x: x['momentum_score'], reverse=True)
    
    def _calculate_momentum_score(self, df: pd.DataFrame) -> float:
        """Calculate momentum score based on multiple factors"""
        score = 0
        
        # Price above VWAP
        if 'VWAP' in df.columns and df['close'].iloc[-1] > df['VWAP'].iloc[-1]:
            score += 20
            
        # RSI in bullish zone (50-70)
        if 'RSI' in df.columns:
            rsi = df['RSI'].iloc[-1]
            if 50 < rsi < 70:
                score += 30
                
        # Volume spike
        if 'volume_spike' in df.columns and df['volume_spike'].iloc[-1]:
            score += 25
            
        # Price trend (5-day vs 20-day)
        sma5 = df['close'].rolling(5).mean().iloc[-1]
        sma20 = df['close'].rolling(20).mean().iloc[-1]
        if sma5 > sma20:
            score += 25
            
        return score
    
    def identify_reversal_patterns(self, df: pd.DataFrame) -> Dict:
        """Identify potential reversal patterns for swing trades"""
        patterns = {
            'double_bottom': False,
            'ascending_triangle': False,
            'bullish_flag': False,
            'reversal_probability': 0
        }
        
        # Simple double bottom detection
        lows = df['low'].rolling(20).min()
        if len(lows.value_counts()) > 1:
            bottom_price = lows.mode()[0]
            recent_lows = df['low'].iloc[-5:]
            if any(abs(low - bottom_price) / bottom_price < 0.02 for low in recent_lows):
                patterns['double_bottom'] = True
                patterns['reversal_probability'] += 30
                
        # Volume analysis for reversal
        recent_volume = df['volume'].iloc[-5:].mean()
        avg_volume = df['volume'].iloc[-30:].mean()
        if recent_volume > avg_volume * 1.5:
            patterns['reversal_probability'] += 20
            
        return patterns