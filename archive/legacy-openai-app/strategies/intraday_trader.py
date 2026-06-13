# strategies/intraday_trader.py
"""
Intraday trading strategy for quick 1-2% daily gains
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta, time
from technical_indicators import RSI, VWAP, ATR, volume_spike
from SmartApiActions import SmartApiActions

class IntradayTrader:
    def __init__(self, smart_api: SmartApiActions):
        self.smart_api = smart_api
        self.target_return = 0.015  # 1.5% target
        self.stop_loss = 0.02  # 2% stop loss
        self.square_off_time = time(15, 15)  # 3:15 PM
        
    def identify_gap_opportunities(self, watchlist: List[str]) -> List[Dict]:
        """Identify gap up/down opportunities at market open"""
        gap_stocks = []
        
        for stock in watchlist:
            try:
                # Get yesterday's close and today's open
                end_date = datetime.now()
                start_date = end_date - timedelta(days=2)
                
                candle_data = self.smart_api.get_candel_data(
                    stock, start_date, end_date, "ONE_DAY"
                )
                
                if candle_data and candle_data.get('data') and len(candle_data['data']) >= 2:
                    yesterday_close = candle_data['data'][-2][4]  # Previous day close
                    today_open = candle_data['data'][-1][1]  # Today open
                    
                    gap_pct = (today_open - yesterday_close) / yesterday_close * 100
                    
                    if abs(gap_pct) > 1:  # Significant gap
                        gap_stocks.append({
                            'symbol': stock,
                            'gap_type': 'up' if gap_pct > 0 else 'down',
                            'gap_percentage': gap_pct,
                            'yesterday_close': yesterday_close,
                            'today_open': today_open,
                            'trade_direction': 'BUY' if gap_pct > 0 else 'SELL'
                        })
                        
            except Exception as e:
                print(f"Error checking gap for {stock}: {str(e)}")
                continue
                
        return sorted(gap_stocks, key=lambda x: abs(x['gap_percentage']), reverse=True)
    
    def calculate_intraday_levels(self, stock: str) -> Dict:
        """Calculate important intraday levels"""
        try:
            # Get 5-minute data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            
            candle_data = self.smart_api.get_candel_data(
                stock, start_date, end_date, "FIVE_MINUTE"
            )
            
            if candle_data and candle_data.get('data'):
                df = pd.DataFrame(candle_data['data'])
                df['datetime'] = pd.to_datetime(df[0])
                df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
                df.set_index('datetime', inplace=True)
                
                # Today's data only
                today_df = df[df.index.date == datetime.now().date()]
                
                if not today_df.empty:
                    # Calculate levels
                    day_high = today_df['high'].max()
                    day_low = today_df['low'].min()
                    vwap = VWAP(today_df)['VWAP'].iloc[-1] if len(today_df) > 0 else 0
                    
                    # Pivot points
                    pivot = (day_high + day_low + today_df['close'].iloc[-1]) / 3
                    r1 = 2 * pivot - day_low
                    s1 = 2 * pivot - day_high
                    
                    return {
                        'symbol': stock,
                        'day_high': day_high,
                        'day_low': day_low,
                        'vwap': vwap,
                        'pivot': pivot,
                        'resistance_1': r1,
                        'support_1': s1,
                        'current_price': today_df['close'].iloc[-1],
                        'range_position': (today_df['close'].iloc[-1] - day_low) / (day_high - day_low) if day_high > day_low else 0.5
                    }
                    
        except Exception as e:
            print(f"Error calculating levels for {stock}: {str(e)}")
            
        return {}
    
    def generate_bracket_order_params(self, stock: str, signal: str, entry_price: float) -> Dict:
        """Generate parameters for bracket order"""
        quantity = self._calculate_position_size(entry_price)
        
        if signal == "BUY":
            target = entry_price * (1 + self.target_return)
            stop_loss = entry_price * (1 - self.stop_loss)
        else:
            target = entry_price * (1 - self.target_return)
            stop_loss = entry_price * (1 + self.stop_loss)
            
        trailing_stop = abs(entry_price - stop_loss) * 0.5  # 50% of stop loss distance
        
        return {
            'symbol': stock,
            'signal': signal,
            'entry_price': entry_price,
            'target_price': target,
            'stop_loss': stop_loss,
            'trailing_stop': trailing_stop,
            'quantity': quantity,
            'squareoff': abs(target - entry_price),
            'stoploss': abs(entry_price - stop_loss)
        }
    
    def _calculate_position_size(self, price: float, capital: float = 100000) -> int:
        """Calculate position size based on capital and risk"""
        position_value = capital * 0.3  # 30% per trade
        quantity = int(position_value / price)
        return max(1, quantity)
    
    def monitor_open_positions(self) -> List[Dict]:
        """Monitor and manage open intraday positions"""
        positions = self.smart_api.getPosition()
        current_time = datetime.now().time()
        
        alerts = []
        
        for _, pos in positions.iterrows():
            if pos['producttype'] == 'INTRADAY' and int(pos['netqty']) != 0:
                symbol = pos['tradingsymbol'].replace('-EQ', '')
                pnl = float(pos['pnl'])
                pnl_pct = float(pos['pnl']) / float(pos['netvalue']) * 100 if float(pos['netvalue']) > 0 else 0
                
                # Check for square-off time
                if current_time >= self.square_off_time:
                    alerts.append({
                        'symbol': symbol,
                        'action': 'SQUARE_OFF',
                        'reason': 'End of day square-off',
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
                    
                # Check for target/stop loss
                elif pnl_pct >= self.target_return * 100:
                    alerts.append({
                        'symbol': symbol,
                        'action': 'BOOK_PROFIT',
                        'reason': 'Target achieved',
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
                    
                elif pnl_pct <= -self.stop_loss * 100:
                    alerts.append({
                        'symbol': symbol,
                        'action': 'STOP_LOSS',
                        'reason': 'Stop loss triggered',
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
                    
        return alerts