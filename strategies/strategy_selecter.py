# strategies/strategy_selector.py
"""
Strategy selector and coordinator
"""

from typing import Dict, Any, List
from datetime import datetime
from strategies.long_term_investor import LongTermInvestor
from strategies.swing_trader import SwingTrader
from strategies.intraday_trader import IntradayTrader
from SmartApiActions import SmartApiActions

class StrategySelector:
    def __init__(self, smart_api: SmartApiActions):
        self.smart_api = smart_api
        self.long_term = LongTermInvestor(smart_api)
        self.swing = SwingTrader(smart_api)
        self.intraday = IntradayTrader(smart_api)
        
    def select_best_strategy(self, market_conditions: Dict) -> str:
        """Select the best strategy based on current market conditions"""
        
        # Market volatility check
        volatility = market_conditions.get('volatility', 0.15)
        trend = market_conditions.get('trend', 'neutral')
        time_of_day = datetime.now().hour
        
        # Intraday during market hours with good volatility
        if 9 <= time_of_day < 15 and volatility > 0.01:
            return 'intraday'
            
        # Swing for medium volatility and clear trend
        elif 0.15 < volatility < 0.30 and trend in ['bullish', 'bearish']:
            return 'swing'
            
        # Long-term for stable conditions
        else:
            return 'long_term'
    
    def execute_strategy(self, strategy_name: str, watchlist: List[str]) -> Dict:
        """Execute the selected strategy"""
        
        if strategy_name == 'long_term':
            fundamentals = self.long_term.analyze_fundamentals(watchlist[:10])
            etfs = self.long_term.identify_etf_opportunities()
            return {
                'strategy': 'long_term',
                'stock_analysis': fundamentals,
                'etf_recommendations': etfs
            }
            
        elif strategy_name == 'swing':
            momentum = self.swing.scan_momentum_stocks(watchlist)
            return {
                'strategy': 'swing',
                'momentum_stocks': momentum[:5]
            }
            
        elif strategy_name == 'intraday':
            gaps = self.intraday.identify_gap_opportunities(watchlist[:20])
            alerts = self.intraday.monitor_open_positions()
            return {
                'strategy': 'intraday',
                'gap_opportunities': gaps[:3],
                'position_alerts': alerts
            }
            
        return {}