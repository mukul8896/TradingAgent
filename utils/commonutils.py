# -*- coding: utf-8 -*-
"""
Created on Mon Dec 18 14:15:59 2023

@author: mksha
"""
from datetime import datetime, timedelta, time
import os
import pandas as pd
import json
import urllib
import csv

smartAPIDateFormate = "%Y-%m-%d %H:%M"


###################################################################################################
###################################### CSV File Related Methods ###################################
###################################################################################################
def saveInstrumentList():
    instrument_list = json.loads(urllib.request.urlopen(
        "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    ).read())

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
    ticker = ticker.replace("-EQ","").replace("SM","")
    for instrument in instrument_list:
        if instrument["name"] == ticker and instrument["exch_seg"] == exchange:
            return instrument["token"], exchange
    # If not found in NSE, try BSE
    if exchange == "NSE":
        for instrument in instrument_list:
            if instrument["name"] == ticker and instrument["exch_seg"] == "BSE":
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