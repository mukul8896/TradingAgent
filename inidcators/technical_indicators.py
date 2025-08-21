# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 20:47:02 2023

@author: mksha
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, time
import ta
from sklearn.linear_model import LinearRegression

def ema(ser, n=9):
    if len(ser) < n:   # Not enough data for EMA
        return np.full(len(ser), np.nan)

    multiplier = 2 / (n + 1)
    sma = ser.rolling(n).mean()
    ema_arr = np.full(len(ser), np.nan)

    # Only set seed value if we actually have enough data
    dropna = sma.dropna()
    if not dropna.empty:
        ema_arr[len(sma) - len(dropna)] = dropna.iloc[0]

    for i in range(1, len(ser)):
        if not np.isnan(ema_arr[i-1]):
            ema_arr[i] = ((ser.iloc[i] - ema_arr[i-1]) * multiplier) + ema_arr[i-1]
    return ema_arr

def RMA(ser, n=9):
    multiplier = 1/n    
    sma = ser.rolling(n).mean()
    ema = np.full(len(ser), np.nan)
    ema[len(sma) - len(sma.dropna())] = sma.dropna().iloc[0]
    for i in range(len(ser)):
        if not np.isnan(ema[i-1]):
            ema[i] = ((ser.iloc[i] - ema[i-1])*multiplier) + ema[i-1]
    ema[len(sma) - len(sma.dropna())] = np.nan
    return ema

def EMA(data,n,column_name="ema"):
    for df in data:
        # Assuming the ema() function is defined elsewhere or replace it with appropriate implementation
        data[df][column_name] = ema(data[df]["close"], n)  
        
        # Calculating divergence percentage
        data[df]["diverg_%"] = round((abs(data[df][column_name] - data[df]["close"]) / data[df]["close"]) * 100,2)
        
    return data

def VEMA(data,n,column_name="vema"):
    for df in data:
        data[df][column_name] = ema(data[df]["volume"],n)
    return data

def changeInPercent(data,column,column_name="PercentChange"):
    for df in data:
        data[df][column_name] = round(data[df][column].pct_change() * 100,3)
    return data     

def classify_gap(gap_pct, gap, threshold):
    if gap_pct > threshold:
        return 'Gap Up'
    elif gap_pct < -threshold:
        return 'Gap Down'
    else:
        return 'No Gap'

def goldenNumber(one_min_hist_data,one_day_hist_data,golden_ratio):
    for ticker in one_min_hist_data:
        min_df = one_min_hist_data[ticker]
        golden_numbers = []
        buy_price = []
        sell_price = []
        signal_list = []
        daily_high = one_min_hist_data[ticker]['high'].iloc[0]
        daily_low = one_min_hist_data[ticker]['low'].iloc[0]
        daily_close = one_min_hist_data[ticker]['close'].iloc[0]
        for candel_date, row in min_df.iterrows():
            #prv_day_candel = one_day_hist_data[ticker].shift(1).loc[candel_date.normalize()]
            if candel_date.time() <= time(10,0):
                if row['high'] > daily_high:
                    daily_high = row['high']
                if row['low'] < daily_low:
                    daily_low = row['low']
                daily_close = row["close"]
            
            golden_number = ((daily_high-daily_low) + (row["high"]-row["low"]))*(golden_ratio)
            buy_above = daily_close + golden_number
            sell_below = daily_close  - golden_number
            signal = "hold" 
            if row["close"] > buy_above: 
                signal = "buy"
            elif row["close"] < sell_below: 
                signal = "sell" 
            
            golden_numbers.append(golden_number)    
            buy_price.append(buy_above)
            sell_price.append(sell_below)
            signal_list.append(signal)
            
        one_min_hist_data[ticker]['gold_num'] = golden_numbers
        one_min_hist_data[ticker]['buy_price'] = buy_price
        one_min_hist_data[ticker]['sell_price'] = sell_price
        one_min_hist_data[ticker]['signal'] = signal_list
    return one_min_hist_data
    

def gapUpDown(data,threshold):
    for df in data:
        data[df]["gap"] = data[df]['open'] - data[df]['close'].shift(1)
        data[df]['gap_pct'] = data[df]['gap'] / data[df]['close'].shift(1)
        data[df]['gap_type'] = data[df].apply(lambda row: classify_gap(row['gap_pct'], row['gap'], threshold), axis=1)
        data[df].drop(["gap","gap_pct"], axis=1, inplace=True)
    return data

def swing_indicator(data):
    for ticker in data:
        data[ticker]['swing'] = (data[ticker]['close'] > data[ticker]['ema30']) & \
                                (data[ticker]['ema30'] > data[ticker]['ema50']) & \
                                (data[ticker]['ema50'] > data[ticker]['ema100']) & \
                                (data[ticker]['ema100'] > data[ticker]['ema200'])
    return data

def gapUpDown_SingleTicker(data,threshold):
    data["gap"] = data['open'] - data['close'].shift(1)
    data['gap_pct'] = data['gap'] / data['close'].shift(1)
    data['gap_type'] = data.apply(lambda row: classify_gap(row['gap_pct'], row['gap'], threshold), axis=1)
    data.drop(["gap","gap_pct"], axis=1, inplace=True)
    return data             

# def ATR(candle_data, period=14):
#     # candle_data is a dictionary where key is stock name and value is the DataFrame
#     normalized_atr_dict = {}
    
#     for stock, df in candle_data.items():
#         # Ensure the DataFrame is sorted by date
#         df = df.sort_index()
        
#         # Calculate True Range (TR)
#         df['previous_close'] = df['close'].shift(1)
#         df['tr'] = np.maximum(df['high'] - df['low'], 
#                               np.maximum(abs(df['high'] - df['previous_close']), 
#                                          abs(df['low'] - df['previous_close'])))
        
#         # Calculate the ATR using a rolling window
#         df['price_atr'] = df['tr'].rolling(window=period).mean()
        
#         # Normalize the ATR by dividing by the close price
#         df['atr'] = (df['price_atr'] / df['close']) * 100
#         df.drop(["previous_close","tr","price_atr"], axis=1, inplace=True)
#         # Store the DataFrame with the normalized ATR in the result dictionary
#         normalized_atr_dict[stock] = df
    
#     return normalized_atr_dict


# def VWAP(candle_data):
#     # candle_data is a dictionary where the key is the stock name and value is the DataFrame
#     vwap_dict = {}
    
#     for stock, df in candle_data.items():
#         # Ensure the DataFrame is sorted by date
#         df = df.sort_index()
        
#         # Calculate the typical price
#         df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        
#         # Calculate the VWAP: (Typical Price * Volume) / Cumulative Volume
#         df['cum_volume_price'] = (df['typical_price'] * df['volume']).cumsum()
#         df['cum_volume'] = df['volume'].cumsum()
#         df['vwap'] = df['cum_volume_price'] / df['cum_volume']
        
#         # Drop intermediate columns used for calculation
#         df.drop(['typical_price', 'cum_volume_price', 'cum_volume'], axis=1, inplace=True)
        
#         # Store the DataFrame with the VWAP in the result dictionary
#         vwap_dict[stock] = df
#     return vwap_dict

def VWAP(df):
    df = df.sort_index()
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3

    # Group by date to reset VWAP each day
    df['cum_volume_price'] = df['typical_price'] * df['volume']
    df['VWAP'] = df.groupby(df.index.date).apply(
        lambda g: g['cum_volume_price'].cumsum() / g['volume'].cumsum()
    ).reset_index(level=0, drop=True)

    # Clean up temporary columns
    df.drop(['typical_price', 'cum_volume_price'], axis=1, inplace=True)
    
    return df


def ATR(candle_data, period=14):
    df = candle_data.sort_index().copy()
    df['previous_close'] = df['close'].shift(1)
    
    # True Range
    df['tr'] = np.maximum(df['high'] - df['low'], 
                          np.maximum(abs(df['high'] - df['previous_close']), 
                                     abs(df['low'] - df['previous_close'])))
    
    # Wilder’s ATR (RMA)
    df['ATR'] = df['tr'].ewm(alpha=1/period, adjust=False).mean()
    
    df.drop(["previous_close","tr"], axis=1, inplace=True)
    return df

def volume_spike(df, span=20, multiplier=2):
    """
    Adds volume EMA and spike detection to intraday dataframe.
    
    Parameters:
        df (pd.DataFrame): intraday OHLCV data with 'volume' column
        span (int): EMA period for volume (default 20 candles)
        multiplier (float): how many times volume must exceed EMA to count as spike
    
    Returns:
        df (pd.DataFrame): with 'volume_ema' and 'volume_spike' columns
    """
    # Calculate EMA of volume
    df['volume_ema'] = df['volume'].ewm(span=span, adjust=False).mean()

    # Mark volume spike if current volume exceeds X * EMA
    df['volume_spike'] = df['volume'] > (df['volume_ema'] * multiplier)

    return df


def MACD(candle_data, fast_period=12, slow_period=26, signal_period=9):
    for df in candle_data:
        candle_data[df] = candle_data[df].copy()
        candle_data[df]["ma_fast"] = ema(candle_data[df]["close"],fast_period)
        candle_data[df]["ma_slow"] = ema(candle_data[df]["close"],slow_period)
        candle_data[df]["macd"] = round(candle_data[df]["ma_fast"] - candle_data[df]["ma_slow"],3)
        candle_data[df]["signal"] = ema(candle_data[df]["macd"],signal_period)
        candle_data[df]["macd_bar"] = round(candle_data[df]["macd"] - candle_data[df]["signal"],3)
        candle_data[df]["macd_bar_avg_fast"] = ema(abs(candle_data[df]["macd_bar"]), 100)
        candle_data[df]["macd_bar_avg_slow"] = ema(abs(candle_data[df]["macd_bar"]), 300)
        candle_data[df]["macd_avg_signal"] = candle_data[df]["macd_bar_avg_fast"] > candle_data[df]["macd_bar_avg_slow"]
        candle_data[df].drop(["ma_fast","ma_slow","macd_bar_avg_fast","macd_bar_avg_slow"], axis=1, inplace=True)
    return candle_data

def bollBand(candle_data, n=20):
    "function to calculate Bollinger Band"
    for df in candle_data:
        candle_data[df]["MB"] = candle_data[df]["close"].rolling(n).mean()
        candle_data[df]["UB"] = candle_data[df]["MB"] + 2*candle_data[df]["close"].rolling(n).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
        candle_data[df]["LB"] = candle_data[df]["MB"] - 2*candle_data[df]["close"].rolling(n).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
        candle_data[df]["BB_Width"] = candle_data[df]["UB"] -  candle_data[df]["LB"]
    return candle_data

def RSI(candel_data, n=14, column_name="rsi"):
    "function to calculate RSI"
    for df in candel_data:
        candel_data[df] = candel_data[df].copy()
        candel_data[df]["change"] = candel_data[df]["close"] - candel_data[df]["close"].shift(1)
        candel_data[df]["gain"] = np.where(candel_data[df]["change"]>=0, candel_data[df]["change"], 0)
        candel_data[df]["loss"] = np.where(candel_data[df]["change"]<0, -1*candel_data[df]["change"], 0)
        candel_data[df]["avgGain"] = RMA(candel_data[df]["gain"],n)
        candel_data[df]["avgLoss"] = RMA(candel_data[df]["loss"],n)
        candel_data[df]["rs"] = candel_data[df]["avgGain"]/candel_data[df]["avgLoss"]
        candel_data[df][column_name] = round(100 - (100/ (1 + candel_data[df]["rs"])),3)
        candel_data[df].drop(["change","gain","loss","avgGain","avgLoss","rs"], axis=1, inplace=True)
    return candel_data
        
        
def STOCHASTIC(candel_data, lookback=14, k=1, d=3):
    """function to calculate Stochastic Oscillator
       lookback = lookback period
       k and d = moving average window for %K and %D"""
    for df in candel_data:
        candel_data[df]["HH"] = candel_data[df]["high"].rolling(lookback).max()
        candel_data[df]["LL"] = candel_data[df]["low"].rolling(lookback).min()
        candel_data[df]["%K"] = (100 * (candel_data[df]["close"] - candel_data[df]["LL"])/(candel_data[df]["HH"]-candel_data[df]["LL"])).rolling(k).mean()
        candel_data[df]["%D"] = candel_data[df]["%K"].rolling(d).mean()
        candel_data[df].drop(["HH","LL"], axis=1, inplace=True)
    return candel_data


def LRSLOP(candle_data, lookback, slope_col="slope"):
    def linear_regression_slope(x, y):
        var_x = np.var(x, ddof=0)
        if var_x == 0:
            return 0  # avoid division by zero
        return np.cov(x, y, ddof=0)[0, 1] / var_x

    for ticker, df in candle_data.items():
        candle_data[ticker][slope_col] = (
            df['close']
            .rolling(window=lookback, min_periods=1)
            .apply(
                lambda prices: linear_regression_slope(np.arange(len(prices)), prices),
                raw=False
            )
        )
    return candle_data

def TEMA(candel_data, lookback, column_name="tema"):
    for df in candel_data:
        ema1 = candel_data[df]["close"].ewm(span=lookback, adjust=False).mean()
        ema2 = ema1.ewm(span=lookback, adjust=False).mean()
        ema3 = ema2.ewm(span=lookback, adjust=False).mean()
        tema = 3 * ema1 - 3 * ema2 + ema3
        candel_data[df][column_name] = tema
        #candel_data[df]["tslope"] = candel_data[df]['tema'].rolling(window=int(lookback/2), min_periods=1).apply(lambda close_prices: linear_regression_slope(np.arange(len(close_prices)), close_prices), raw=False)
    return candel_data
    
def getDayPercentChange(min_data,current_time):
    min_data_until_now = min_data.loc[:current_time]

    # Aggregate the minute data to form a daily candlestick for the current day
    daily_data = {
        'open': min_data_until_now['open'].iloc[0],  # Open price of the first candle at 9:15 AM
        'high': min_data_until_now['high'].max(),    # Highest price up to the current time
        'low': min_data_until_now['low'].min(),      # Lowest price up to the current time
        'close': min_data_until_now['close'].iloc[-1], # Close price of the last available candle
        'volume': min_data_until_now['volume'].sum()  # Sum of the volume up to the current time
    }
    
    # Calculate the percent change from the open to the current close
    open_price = daily_data['open']
    close_price = daily_data['close']
    
    # Percent change calculation
    return ((close_price - open_price) / open_price) * 100


def RSI(df, period=14):
    df = df.copy()
    df["change"] = df["close"].diff()

    df["gain"] = np.where(df["change"] > 0, df["change"], 0.0)
    df["loss"] = np.where(df["change"] < 0, -df["change"], 0.0)

    # Wilder’s smoothing (exponential moving average with alpha=1/period)
    df["avgGain"] = df["gain"].ewm(alpha=1/period, adjust=False).mean()
    df["avgLoss"] = df["loss"].ewm(alpha=1/period, adjust=False).mean()

    df["rs"] = df["avgGain"] / df["avgLoss"]
    df["RSI"] = 100 - (100 / (1 + df["rs"]))

    return df.drop(["change","gain","loss","avgGain","avgLoss","rs"], axis=1)

def candelColor(data_dict):
    for ticker in data_dict:
        # Vectorized operation to determine candle color for each row
        data_dict[ticker]['candle_color'] = np.where(data_dict[ticker]['close'] - data_dict[ticker]['open'] > 0, 
                                                     "Green Candle", 
                                                     "Red Candle")
    return data_dict

def calculate_rsi(df, window=14):
    df['RSI'] = ta.momentum.rsi(df['close'], window=window)
    return df
def calculate_adx(df, window=14):
    df['ADX'] = ta.trend.adx(df['high'], df['low'], df['close'], window=window)
    return df
def calculate_bollinger_bands(df, window=20, num_of_std=2):
    df['SMA'] = df['close'].rolling(window).mean()
    df['Upper Band'] = df['SMA'] + (df['close'].rolling(window).std() * num_of_std)
    df['Lower Band'] = df['SMA'] - (df['close'].rolling(window).std() * num_of_std)
    return df
def calculate_moving_average(df, window=50):
    df['SMA'] = df['close'].rolling(window=window).mean()
    return df
def calculate_trend_slope(df, column='close'):
    X = np.arange(len(df)).reshape(-1, 1)  # Time as the independent variable
    y = df[column].values  # Closing prices as the dependent variable
    model = LinearRegression().fit(X, y)
    return model.coef_[0]  # Slope of the trend line
def identify_trend_direction(df):
    df = calculate_moving_average(df)
    df = calculate_bollinger_bands(df)
    df = calculate_adx(df)
    df = calculate_rsi(df)
    
    trend_slope = calculate_trend_slope(df)
    
    if df['ADX'].iloc[-1] > 25:  # Strong trend
        if trend_slope > 0 and df['RSI'].iloc[-1] > 60:
            return "Up"
        elif trend_slope < 0 and df['RSI'].iloc[-1] < 40:
            return "Down"
    else:
        if df['RSI'].iloc[-1] > 40 and df['RSI'].iloc[-1] < 60:
            return "Sideways"
    
    return "Unclear Trend"

# Apply to a dictionary of stocks
def trend(stock_data_dict):
    for stock, df in stock_data_dict.items():
        trend = identify_trend_direction(df)
        print(f"Stock: {stock}, Trend: {trend}")
        

    
    
