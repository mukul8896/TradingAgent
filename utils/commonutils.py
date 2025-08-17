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
    instrument_list = json.loads(urllib.request.urlopen("https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json").read())
    json_file = open(os.path.join(os.path.expanduser("~")+"/hist_data", "instrumentList.json"), 'w')
    json.dump(instrument_list, json_file, indent=4)
    json_file.close()
    
def getInstrumentList():
    if(os.path.isfile(os.path.join(os.path.expanduser("~")+"/hist_data", "instrumentList.json")) == False):
        saveInstrumentList()
    json_file = open(os.path.join(os.path.expanduser("~")+"/hist_data", "instrumentList.json"), 'r')
    instrumentList = json.load(json_file)
    json_file.close()
    return instrumentList

def token_lookup(ticker, exchange="NSE"):
    instrument_list = getInstrumentList()

    # First try with the given exchange
    for instrument in instrument_list:
        if instrument["name"] == ticker and instrument["exch_seg"] == exchange:
            # Only NSE uses -EQ suffix check
            if exchange == "NSE":
                if instrument["symbol"].split('-')[-1] == "EQ":
                    return instrument["token"],exchange
            else:
                return instrument["token"],exchange

    # If not found in NSE, try BSE
    if exchange == "NSE":
        for instrument in instrument_list:
            if instrument["name"] == ticker and instrument["exch_seg"] == "BSE":
                return instrument["token"],"BSE"

    # Not found in either
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