# utils/portfolio_fetcher.py
from smartapi.SmartApiActions import SmartApiActions
from inidcators.indicator_utils import enriched_json_with_indicators
import json
from utils.news_fetcher import fetch_all_stock_news
import pandas as pd

def simplify_holdings_json(data):
    """Reduce holding JSON to only essential fields and enrich with news data if available.
    Also return cleaned news_data (excluding stocks already in holdings or merged).
    """
    news_data = fetch_all_stock_news()
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
        if ticker in news_lookup:
            news_item = news_lookup[ticker]
            holding_entry["news_headline"] = news_item.get("new_headline", "")
            holding_entry["sentiment"] = news_item.get("sentiment", "")

        simplified_holding_json["current_holdings"].append(holding_entry)

    return simplified_holding_json


def get_portfolio_stocks(smartApiActions):
    """Fetch company names of holdings from Angel One SmartAPI."""
    response = smartApiActions.getAllHoldings()  # JSON response
    simplify_holdings_data = simplify_holdings_json(response)
    simplify_holdings_data['current_holdings'] = enriched_json_with_indicators(simplify_holdings_data['current_holdings'],"ONE_DAY",smartApiActions)
    return simplify_holdings_data
