# -*- coding: utf-8 -*-
"""
Created on Mon Dec 18 14:15:59 2023

@author: mksha
"""
from datetime import datetime, timedelta, time
import os
import pandas as pd
import json
import urllib.request
import csv
from config import INSTRUMENT_LIST_URL

smartAPIDateFormate = "%Y-%m-%d %H:%M"


###################################################################################################
###################################### CSV File Related Methods ###################################
###################################################################################################
def saveInstrumentList():
    instrument_list = json.loads(urllib.request.urlopen(INSTRUMENT_LIST_URL).read())

    hist_data_dir = os.path.join(os.path.expanduser("~"), "hist_data")
    os.makedirs(hist_data_dir, exist_ok=True)  # <-- create folder if missing

    json_file_path = os.path.join(hist_data_dir, "instrumentList.json")
    with open(json_file_path, 'w') as json_file:
        json.dump(instrument_list, json_file, indent=4)

    
def getInstrumentList():
    json_file_path = os.path.join(os.path.expanduser("~"), "hist_data", "instrumentList.json")
    if not os.path.isfile(json_file_path):
        saveInstrumentList()
    
    with open(json_file_path, 'r') as json_file:
        instrumentList = json.load(json_file)
    return instrumentList

def token_lookup(ticker, exchange="NSE"):
    instrument_list = getInstrumentList()
    ticker = ticker.replace("-EQ","").replace("-SM","").upper().strip()  # normalize

    # First try the requested exchange
    for instrument in instrument_list:
        if instrument.get("name", "").upper().strip() == ticker and instrument.get("exch_seg", "").upper() == exchange.upper():
            return instrument["token"], exchange

    # If not found in NSE, try BSE
    if exchange.upper() == "NSE":
        for instrument in instrument_list:
            if instrument.get("name", "").upper().strip() == ticker and instrument.get("exch_seg", "").upper() == "BSE":
                return instrument["token"], "BSE"

    return None

def symbol_lookup(token, exchange="NSE"):
    instrument_list = getInstrumentList()
    for instrument in instrument_list:
        if instrument["token"] == token and instrument["exch_seg"] == exchange and instrument["symbol"].split('-')[-1] == "EQ":
            return instrument["name"]
        
def getSecretKeys():
    secret_file = os.path.join(os.path.expanduser("~"), "key.txt")
    key_secret = open(secret_file,"r").read().split()
    return key_secret

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)

def is_market_time(dt: datetime) -> bool:
    return dt.weekday() < 5 and MARKET_OPEN <= dt.time() <= MARKET_CLOSE

def get_start_date(interval: str, num_intervals: int = 250) -> datetime:
    """
    Returns the past date such that the number of trading intervals from that date to now is num_intervals.
    Market hours: Mon-Fri 9:15 AM - 3:30 PM
    """
    now = datetime.now()
    
    # Define interval in minutes
    interval_map = {
        "ONE_MINUTE": 1,
        "FIVE_MINUTE": 5,
        "FIFTEEN_MINUTE": 15,
        "THIRTY_MINUTES": 30,
        "ONE_HOUR": 60,
        "TEN_MINUTE": 10,
        "ONE_DAY": 1,  # special handling
    }

    if interval not in interval_map:
        raise ValueError(f"Unsupported interval: {interval}")
    
    if interval == "ONE_DAY":
        # Count only trading days (Mon-Fri)
        count = 0
        dt = now
        while count < num_intervals:
            dt -= timedelta(days=1)
            if dt.weekday() < 5:
                count += 1
        return datetime(dt.year, dt.month, dt.day, MARKET_OPEN.hour, MARKET_OPEN.minute)
    
    # For intraday intervals
    interval_minutes = interval_map[interval]
    count = 0
    dt = now
    while count < num_intervals:
        dt -= timedelta(minutes=interval_minutes)
        if is_market_time(dt):
            count += 1
    
    return dt