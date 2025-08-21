# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 13:56:06 2023

@author: mksha
"""

from SmartApi import SmartConnect
from pyotp import TOTP
import pandas as pd
import time
import re
from utils.commonutils import token_lookup,saveInstrumentList
import os
class SmartApiActions:
    
    def __init__(self):
        self.sessionObj = SmartConnect(api_key = os.getenv("SMART_API_KEY"))
        self.session = self.sessionObj.generateSession(os.getenv("SMART_API_CLIENT_CODE"), os.getenv("SMART_API_PASSWORD"),TOTP(os.getenv("SMART_API_TOTP")).now())
        saveInstrumentList()
        
        
    def getSmartAPISessionObject(self):
        return self.sessionObj
    
    def getGainers(self):
        params_gainers = {
                    "datatype":"PercPriceGainers", # Type of Data you want(PercOILosers/PercOIGainers/PercPriceGainers/PercPriceLosers)
                    "expirytype":"NEAR" # Expiry Type (NEAR/NEXT/FAR)
                    }
        time.sleep(1)
        response_gainers = self.sessionObj.gainersLosers(params_gainers)
        gainers_list = [re.match(r"(.*?)(\d{2}[A-Z]{3}\d{2})", item['tradingSymbol']).group(1) for item in response_gainers['data'][:5]]
        return gainers_list
    
    def getLosers(self):
        params_losers = {
                    "datatype":"PercPriceLosers", # Type of Data you want(PercOILosers/PercOIGainers/PercPriceGainers/PercPriceLosers)
                    "expirytype":"NEAR" # Expiry Type (NEAR/NEXT/FAR)
                    }
        time.sleep(1)
        response_losers = self.sessionObj.gainersLosers(params_losers)
        losers_list = [re.match(r"(.*?)(\d{2}[A-Z]{3}\d{2})", item['tradingSymbol']).group(1) for item in response_losers['data'][:1]]
        return losers_list
    
    def get_ltp(self,ticker,exchange="NSE"):
        token,exchange = token_lookup(ticker)
        time.sleep(1)
        response = self.sessionObj.ltpData(exchange,"{}-EQ".format(ticker),token)
        ltp = response['data']["ltp"]
        return ltp
    
    def place_limit_order(self,ticker,buy_sell,price,quantity,productType="DELIVERY",exchange="NSE"):
        token,exchange = token_lookup(ticker)
        params = {
                    "variety":"NORMAL",
                    "tradingsymbol":"{}-EQ".format(ticker),
                    "symboltoken": token,
                    "transactiontype":buy_sell,
                    "exchange":exchange,
                    "ordertype":"LIMIT",
                    "producttype":productType,
                    "duration":"DAY",
                    "price":price,
                    "quantity":quantity
                    }
        response = self.sessionObj.placeOrder(params)
        return response
    
    
    def getMargineRequire(self,ticker,buy_sell,quantity,productType="INTRADAY",exchange="NSE"):
        token,exchange = token_lookup(ticker)
        params = {
                    "positions": [
                                      {
                                           "exchange": exchange,
                                           "qty": quantity,
                                           "price": 0,
                                           "productType": productType,
                                           "token": token,
                                           "tradeType": buy_sell
                                      }
                                 ]
                    }
        response = self.sessionObj.getMarginApi(params)
        return response["data"]["totalMarginRequired"]
    
    def getBrokerage(self,ticker,buy_sell,quantity,price,productType="INTRADAY",exchange="NSE"):
        token,exchange = token_lookup(ticker)
        params = {
                    "orders": [
                                {
                                    "product_type": productType,
                                    "transaction_type": buy_sell,
                                    "quantity": quantity,
                                    "price": price,
                                    "exchange": exchange,
                                    "symbol_name": ticker,
                                    "token": token
                                }
                            ]
                        }
        time.sleep(1)
        response = self.sessionObj.estimateCharges(params)
        return response["data"]["summary"]["total_charges"]
    
    def place_market_order(self,ticker,buy_sell,quantity,productType="INTRADAY",exchange="NSE"):
        token,exchange = token_lookup(ticker)
        params = {
                    "variety":"NORMAL",
                    "tradingsymbol":"{}-EQ".format(ticker),
                    "symboltoken":token,
                    "transactiontype":buy_sell,
                    "exchange":exchange,
                    "ordertype":"MARKET",
                    "producttype":productType,
                    "duration":"DAY",
                    "price":0,
                    "quantity":quantity
                    }
        time.sleep(1)
        response = self.sessionObj.placeOrder(params)
        return response
    
    def place_stoploss_market_order(self,ticker,buy_sell,price,quantity,productType="INTRADAY",exchange="NSE"):
        token,exchange = token_lookup(ticker)
        params = {
                    "variety":"STOPLOSS",
                    "tradingsymbol":"{}-EQ".format(ticker),
                    "symboltoken":token,
                    "transactiontype":buy_sell,
                    "exchange":exchange,
                    "ordertype":"STOPLOSS_MARKET",
                    "producttype":productType,
                    "duration":"DAY",
                    "price":0,
                    "quantity":quantity,
                    "triggerprice":price*0.99
                    }
        response = self.sessionObj.placeOrder(params)
        return response
    
    def get_open_orders(self):
        response = self.sessionObj.orderBook()
        df = pd.DataFrame(response['data'])
        if len(df) > 0:
            return df[df["orderstatus"]=="open"]
        else:
            return None
    
    def cancel_order(self, order_id):
        params = {
                    "variety":"NORMAL",
                    "orderid":order_id
                    }
        response = self.sessionObj.cancelOrder(params["orderid"], params["variety"])
        return response
    
    def modify_limit_order(self,ticker,order_id,price,quantity):
        token,exchange = token_lookup(ticker)
        params = {
                    "variety":"NORMAL",
                    "orderid":order_id,
                    "ordertype":"LIMIT",
                    "producttype":"INTRADAY",
                    "duration":"DAY",
                    "price":price,
                    "quantity":quantity,
                    "tradingsymbol":"{}-EQ".format(ticker),
                    "symboltoken":token,
                    "exchange":"NSE"
                    }
        response = self.sessionObj.modifyOrder(params)
        return response
    
    def modify_order_type(self,ticker,order_id,order_type,quantity):
        token,exchange = token_lookup(ticker)
        params = {
                    "variety":"NORMAL",
                    "orderid":order_id,
                    "ordertype":order_type,
                    "producttype":"INTRADAY",
                    "duration":"DAY",
                    "tradingsymbol":"{}-EQ".format(ticker),
                    "quantity":quantity,
                    "symboltoken":token,
                    "exchange":exchange
                    }
        response = self.sessionObj.modifyOrder(params)
        return response
    
    def get_candel_data(self,ticker, st_date, end_date, interval, exchange="NSE"):
        token,exchange = token_lookup(ticker)
        params = {
                 "exchange": exchange,
                 "symboltoken": token,
                 "interval": interval,
                 "fromdate": (st_date).strftime('%Y-%m-%d %H:%M'),
                 "todate": (end_date).strftime('%Y-%m-%d %H:%M') 
                 }
        response = self.sessionObj.getCandleData(params)
        return response
    
    def getPosition(self):
        time.sleep(1)
        response = self.sessionObj.position()
        df = pd.DataFrame(response['data'])
        return df
    
    def getTradeBook(self):
        response = self.sessionObj.tradeBook()
        return response
    
    def hasExistingPosition(self,ticker):
        positionData = self.getPosition()
        open_position = False
        if len(positionData) > 0:
            if len(positionData[positionData["tradingsymbol"]==ticker+"-EQ"]) > 0:
                ticker_pos = positionData[positionData["tradingsymbol"]==ticker+"-EQ"].iloc[-1]
                if int(ticker_pos["netqty"]) == 0:
                    open_position = False
                else:
                    open_position = True
        return open_position
    
    def isTradeDoneForDay(self,ticker):
        positionData = self.getPosition()
        if len(positionData) == 0:
            return False
        if len(positionData[positionData["tradingsymbol"]==ticker+"-EQ"]) == 0:
            return False
        ticker_pos = positionData[positionData["tradingsymbol"]==ticker+"-EQ"].iloc[-1]
        if int(ticker_pos["netqty"]) == 0:
            return True
        else:
            return False

    
    def getHoldings(self,ticker):
        response = self.sessionObj.holding()
        df = pd.DataFrame(response['data'])
        df = df[df["tradingsymbol"]==ticker+"-EQ"]
        df = df[df["quantity"]>0]
        return df
    
    def getAllHoldings(self):
        response = self.sessionObj.allholding()
        return response['data']
