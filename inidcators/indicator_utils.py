import pandas as pd
import numpy as np
import json
import time
from datetime import datetime
from .technical_indicators import ema,RSI,VWAP,ATR,volume_spike
from utils.commonutils import get_start_date
import pandas as pd
import time
from datetime import datetime

def calculate_indicators(df,interval):
    df = df.copy()
    if len(df) < 30:   # not enough data for indicators
        for col in ["RSI","EMA20","EMA50","EMA200","MACD","MACD_signal","MACD_histogram","bollinger_upper","bollinger_lower","VWAP","volume_spike","ATR"]:
            df[col] = np.nan
        return df
    df["RSI"] = RSI(df)["RSI"]
    if interval != "ONE_DAY":
        df["VWAP"] = VWAP(df)["VWAP"]
        df["volume_spike"] = volume_spike(df)["volume_spike"]
    df["ATR"] = ATR(df)["ATR"]
    df["EMA20"] = ema(df["close"], 20)
    df["EMA50"] = ema(df["close"], 50)
    df["EMA200"] = ema(df["close"], 200)
    
    # MACD
    fast = ema(df["close"], 12)
    slow = ema(df["close"], 26)
    df["MACD"] = fast - slow
    df["MACD_signal"] = ema(pd.Series(df["MACD"]), 9)
    df["MACD_histogram"] = df["MACD"] - df["MACD_signal"]
    
    # Bollinger Bands
    df["MB"] = df["close"].rolling(20).mean()
    df["bollinger_upper"] = df["MB"] + 2 * df["close"].rolling(20).std(ddof=0)
    df["bollinger_lower"] = df["MB"] - 2 * df["close"].rolling(20).std(ddof=0)
    df.drop("MB", axis=1, inplace=True)
    
    return df

def hist_data_by_ticker(ticker, startDate, endDate, interval, smartApiActions):
    try:
        df_data = pd.DataFrame(columns=["date","open","high","low","close","volume"])
        st_date = startDate
        print(f"INFO : Fetching historical data for {ticker} interval {interval}")
        while st_date < endDate:
            time.sleep(1)  # avoid throttling

            hist = smartApiActions.get_candel_data(ticker, st_date, endDate, interval)
            temp = pd.DataFrame(hist["data"], columns=["date","open","high","low","close","volume"])

            if df_data.empty:
                df_data = temp.copy()
            else:
                df_data = pd.concat([df_data, temp])

            if len(temp) == 0:
                break

            endDate = datetime.strptime(temp['date'].iloc[0][:16], "%Y-%m-%dT%H:%M")

            if len(temp) <= 1:
                break

        df_data.set_index("date", inplace=True)
        df_data.index = pd.to_datetime(df_data.index).tz_localize(None)
        df_data.drop_duplicates(inplace=True)
        return df_data

    except Exception as e:
        print(f"ERROR in hist_data_by_ticker for {ticker}: {e}")
        return None

def get_rsi_cross_over(interval,scan_data,smartApiActions):
    start_date = get_start_date(interval)
    crossed_rsi_ticker = []
    for stock in scan_data:
        ticker = stock["tradingsymbol"].replace("-EQ", "")
        df = hist_data_by_ticker(
            ticker,
            startDate=start_date,
            endDate=datetime.now(),
            interval=interval,
            smartApiActions=smartApiActions
        )
        if df is not None and not df.empty and len(df) >= 100:
            df = calculate_indicators(df,interval)
            latest = df.iloc[-1]
            previous_day = df.iloc[-2]
            if round(latest["RSI"],2) > 50 and round(previous_day["RSI"],2) < 50:
                crossed_rsi_ticker.append(ticker)
    return [{"tradingsymbol": x} for x in crossed_rsi_ticker]


# --- Merge indicators with portfolio ---
# input json formate should be [{"tradingsymbol": "RELIANCE"}, {"tradingsymbol": "TCS"}]
def enriched_json_with_indicators(json_data,interval,smartApiActions):
    enriched_data = []
    start_date = get_start_date(interval)
    for stock in json_data:
        ticker = stock["tradingsymbol"].replace("-EQ", "")
        df = hist_data_by_ticker(
            ticker,
            startDate=start_date,
            endDate=datetime.now(),
            interval=interval,
            smartApiActions=smartApiActions
        )
        if df is not None and not df.empty and len(df) >= 100:
            df = calculate_indicators(df,interval)
            latest = df.iloc[-1]
            indicators_data = {}
            if indicators_data.get("ltp") is None:
                stock["ltp"] = smartApiActions.get_ltp(ticker)
            indicators_data["RSI"] = round(latest["RSI"],2)

            if interval!="ONE_DAY":
                indicators_data["VWAP"] = round(latest["VWAP"],2)
                indicators_data["volume_spike"] = str(latest["volume_spike"])

            indicators_data["ATR"] = round(latest["ATR"],2)
            indicators_data["EMA20"] = round(latest["EMA20"],2)
            indicators_data["EMA50"] = round(latest["EMA50"],2)
            indicators_data["EMA200"] = round(latest["EMA200"],2)
            indicators_data["MACD"] = round(latest["MACD"],2)
            indicators_data["MACD_signal"] = round(latest["MACD_signal"],2)
            indicators_data["bollinger_upper"] = round(latest["bollinger_upper"],2)
            indicators_data["bollinger_lower"] = round(latest["bollinger_lower"],2)
            stock[interval+"_INTERVAL"] = indicators_data   
            enriched_data.append(stock)
    
    return enriched_data
