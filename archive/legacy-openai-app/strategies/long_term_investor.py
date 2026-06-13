# strategies/long_term_investor.py
"""
Long-term investment strategy focusing on fundamentals and value investing
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta
from SmartApiActions import SmartApiActions
from openaiAPI import call_llm

class LongTermInvestor:
    def __init__(self, smart_api: SmartApiActions):
        self.smart_api = smart_api
        self.holding_period = 180  # days
        self.target_return = 0.25  # 25%
        
    def analyze_fundamentals(self, stocks: List[str]) -> Dict[str, Any]:
        """Analyze fundamental metrics for long-term potential"""
        fundamental_scores = {}
        
        for stock in stocks:
            try:
                # Get historical data for trend analysis
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                
                candle_data = self.smart_api.get_candel_data(
                    stock, start_date, end_date, "ONE_DAY"
                )
                
                if candle_data and candle_data.get('data'):
                    df = pd.DataFrame(candle_data['data'])
                    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
                    
                    # Calculate metrics
                    returns_1y = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
                    volatility = df['close'].pct_change().std() * np.sqrt(252)
                    avg_volume = df['volume'].mean()
                    
                    # Price levels
                    support = df['low'].rolling(50).min().iloc[-1]
                    resistance = df['high'].rolling(50).max().iloc[-1]
                    current_price = df['close'].iloc[-1]
                    
                    # Score calculation
                    value_score = self._calculate_value_score(
                        current_price, support, resistance, returns_1y
                    )
                    
                    fundamental_scores[stock] = {
                        'returns_1y': returns_1y,
                        'volatility': volatility,
                        'avg_volume': avg_volume,
                        'support': support,
                        'resistance': resistance,
                        'current_price': current_price,
                        'value_score': value_score,
                        'recommendation': 'BUY' if value_score > 70 else 'HOLD'
                    }
                    
            except Exception as e:
                print(f"Error analyzing {stock}: {str(e)}")
                continue
                
        return fundamental_scores
    
    def _calculate_value_score(self, price, support, resistance, returns):
        """Calculate value score based on technical and fundamental factors"""
        # Distance from support (closer to support = higher score)
        support_score = max(0, min(100, (price - support) / support * 100))
        
        # Room to resistance (more room = higher score)
        resistance_score = max(0, min(100, (resistance - price) / price * 100))
        
        # Returns score (positive returns = higher score)
        returns_score = max(0, min(100, (returns + 0.2) * 200))
        
        # Weighted average
        value_score = (support_score * 0.3 + resistance_score * 0.4 + returns_score * 0.3)
        
        return value_score
    
    def identify_etf_opportunities(self) -> List[Dict]:
        """Identify suitable ETF investments"""
        etf_list = [
            {"symbol": "NIFTYBEES", "description": "Nifty 50 ETF"},
            {"symbol": "BANKBEES", "description": "Bank Nifty ETF"},
            {"symbol": "GOLDBEES", "description": "Gold ETF"},
            {"symbol": "ICICIMOM30", "description": "Momentum 30 ETF"},
            {"symbol": "ICICILOWVOL", "description": "Low Volatility ETF"}
        ]
        
        etf_recommendations = []
        for etf in etf_list:
            try:
                ltp = self.smart_api.get_ltp(etf['symbol'])
                etf_recommendations.append({
                    'symbol': etf['symbol'],
                    'description': etf['description'],
                    'current_price': ltp,
                    'allocation_pct': 0.2,  # 20% each
                    'strategy': 'diversification'
                })
            except:
                continue
                
        return etf_recommendations