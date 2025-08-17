import pandas as pd
import numpy as np
import json
import time
from datetime import datetime
# Assume smartApiActions is already initialized

# --- Helper functions (RSI, EMA, MACD, Bollinger) ---
def ema(ser, n=9):
    multiplier = 2 / (n + 1)
    sma = ser.rolling(n).mean()
    ema_arr = np.full(len(ser), np.nan)
    ema_arr[len(sma) - len(sma.dropna())] = sma.dropna().iloc[0]
    for i in range(len(ser)):
        if i > 0 and not np.isnan(ema_arr[i-1]):
            ema_arr[i] = ((ser.iloc[i] - ema_arr[i-1]) * multiplier) + ema_arr[i-1]
    return ema_arr

def RSI(df, period=14):
    df = df.copy()
    df["change"] = df["close"] - df["close"].shift(1)
    df["gain"] = np.where(df["change"] >= 0, df["change"], 0)
    df["loss"] = np.where(df["change"] < 0, -df["change"], 0)
    df["avgGain"] = df["gain"].rolling(period).mean()
    df["avgLoss"] = df["loss"].rolling(period).mean()
    df["rs"] = df["avgGain"] / df["avgLoss"]
    df["RSI"] = 100 - (100 / (1 + df["rs"]))
    df = df.drop(["change","gain","loss","avgGain","avgLoss","rs"], axis=1)
    return df

def calculate_indicators(df):
    df = df.copy()
    df["RSI"] = RSI(df)["RSI"]
    df["EMA50"] = ema(df["close"], 50)
    df["EMA100"] = ema(df["close"], 100)
    df["EMA200"] = ema(df["close"], 200)
    
    # MACD
    fast = ema(df["close"], 12)
    slow = ema(df["close"], 26)
    df["MACD"] = fast - slow
    df["MACD_signal"] = ema(pd.Series(df["MACD"]), 9)
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]
    
    # Bollinger Bands
    df["MB"] = df["close"].rolling(20).mean()
    df["bollinger_upper"] = df["MB"] + 2 * df["close"].rolling(20).std()
    df["bollinger_lower"] = df["MB"] - 2 * df["close"].rolling(20).std()
    df.drop("MB", axis=1, inplace=True)
    
    return df

# --- Fetch historical data ---
def hist_data_by_ticker(ticker, startDate, endDate, interval, smartApiActions):
    df_data = pd.DataFrame(columns=["date","open","high","low","close","volume"])
    st_date = startDate
    while st_date < endDate:
        print(f"INFO : Fetching historical data for {ticker}")
        time.sleep(2)  # avoid throttling
        hist = smartApiActions.get_candel_data(ticker, st_date, endDate, interval)
        temp = pd.DataFrame(hist["data"], columns=["date","open","high","low","close","volume"])
        if df_data.empty:
            df_data = temp.copy()
        else:
            df_data = pd.concat([df_data,temp])
        if len(temp) == 0: break
        endDate = datetime.strptime(temp['date'].iloc[0][:16], "%Y-%m-%dT%H:%M")
        if len(temp) <= 1: break
    df_data.set_index("date", inplace=True)
    df_data.index = pd.to_datetime(df_data.index).tz_localize(None)
    df_data.drop_duplicates(inplace=True)
    return df_data

# --- Merge indicators with portfolio ---
def get_portfolio_data_with_indicators(portfolio_json, smartApiActions):
    enriched_portfolio = []
    for stock in portfolio_json:
        ticker = stock["tradingsymbol"].replace("-EQ", "")
        if ticker != "GROWWDEFNC" and ticker!="GROWWNET":
            df = hist_data_by_ticker(
                ticker,
                startDate=datetime(2024,1,1),
                endDate=datetime.now(),
                interval="ONE_DAY",
                smartApiActions=smartApiActions
            )
            df = calculate_indicators(df)
            latest = df.iloc[-1]
            stock["RSI"] = round(latest["RSI"],2)
            stock["EMA50"] = round(latest["EMA50"],2)
            stock["EMA100"] = round(latest["EMA100"],2)
            stock["EMA200"] = round(latest["EMA200"],2)
            stock["MACD"] = round(latest["MACD"],2)
            stock["bollinger_upper"] = round(latest["bollinger_upper"],2)
            stock["bollinger_lower"] = round(latest["bollinger_lower"],2)
            
        enriched_portfolio.append(stock)
    
    return enriched_portfolio
