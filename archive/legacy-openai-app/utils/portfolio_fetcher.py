# utils/portfolio_fetcher.py
from smartapi.SmartApiActions import SmartApiActions
from inidcators.indicator_utils import enriched_json_with_indicators
import json
from utils.news_fetcher import fetch_market_news
import pandas as pd
from chartink.chartink_scanner import stocks_scanner
from chartink.chartink_queries import MONTHLY_SWING_RSI_50_QUERY

def simplify_holdings_json(data,news_data):
    """Reduce holding JSON to only essential fields and enrich with news data if available.
    Also return cleaned news_data (excluding stocks already in holdings or merged).
    """
    required_keys = [
        "tradingsymbol", "quantity", "averageprice",
        "ltp", "profitandloss", "pnlpercentage"
    ]

    # Convert news_data into a lookup dictionary {tradingsymbol: {...news...}}
    news_lookup = {n["tradingsymbol"]: n for n in news_data}

    simplified_holding_json = {
        "current_holdings": [],
        "totalholding": {
            "totalholdingvalue": data.get("totalholding", {}).get("totalholdingvalue", 0),
            "totalinvvalue": data.get("totalholding", {}).get("totalinvvalue", 0),
            "totalprofitandloss": data.get("totalholding", {}).get("totalprofitandloss", 0),
            "totalpnlpercentage": data.get("totalholding", {}).get("totalpnlpercentage", 0),
        }
    }

    for h in data.get("holdings", []):
        holding_entry = {k: h.get(k, 0 if k != "tradingsymbol" else "") for k in required_keys}

        # If this stock is in news_data, merge news_headline + sentiment
        ticker = h.get("tradingsymbol")
        # if ticker in news_lookup:
        #     news_item = news_lookup[ticker]
        #     holding_entry["news"] = news_item.get("text", "")
        #     holding_entry["sentiment"] = news_item.get("sentiment", "")

        simplified_holding_json["current_holdings"].append(holding_entry)

    return simplified_holding_json


def get_portfolio_stocks(news_data,smartApiActions):
    """Fetch company names of holdings from Angel One SmartAPI."""
    response = smartApiActions.getAllHoldings()  # JSON response
    simplify_holdings_data = simplify_holdings_json(response,news_data)
    simplify_holdings_data['current_holdings'] = enriched_json_with_indicators(simplify_holdings_data['current_holdings'],"ONE_DAY",smartApiActions)
    return simplify_holdings_data

def get_watchlist_stocks(news_data,smartApiActions):
    """Create a watchlist JSON structure enriched with news if available."""
    watchlist = stocks_scanner(MONTHLY_SWING_RSI_50_QUERY)
    news_lookup = {n["tradingsymbol"]: n for n in news_data}
    watchlist_json = []

    for item in watchlist:
        ticker = item.get("tradingsymbol", "")
        entry = {"tradingsymbol": ticker}

        if ticker in news_lookup:
            news_item = news_lookup[ticker]
            entry["news"] = news_item.get("text", "")
            entry["sentiment"] = news_item.get("sentiment", "")

        watchlist_json.append(entry) 
    watchlist_json = enriched_json_with_indicators(watchlist_json, "ONE_DAY", smartApiActions)
    return watchlist_json
