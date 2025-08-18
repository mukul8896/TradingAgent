# utils/portfolio_fetcher.py
from smartapi.SmartApiActions import SmartApiActions
from utils.commonutils import getSecretKeys
from utils.indicator import get_portfolio_data_with_indicators
import json
import pandas as pd

def simplify_holdings_json(data, news_data):
    """Reduce holding JSON to only essential fields and enrich with news data if available.
    Also return cleaned news_data (excluding stocks already in holdings or merged).
    """
    required_keys = [
        "tradingsymbol", "quantity", "averageprice",
        "ltp", "profitandloss", "pnlpercentage"
    ]

    # Convert news_data into a lookup dictionary {tradingsymbol: {...news...}}
    news_lookup = {n["tradingsymbol"]: n for n in news_data}

    simplified = {
        "current_holdings": [],
        "totalholding": {
            "totalholdingvalue": data.get("totalholding", {}).get("totalholdingvalue", 0),
            "totalinvvalue": data.get("totalholding", {}).get("totalinvvalue", 0),
            "totalprofitandloss": data.get("totalholding", {}).get("totalprofitandloss", 0),
            "totalpnlpercentage": data.get("totalholding", {}).get("totalpnlpercentage", 0),
        }
    }

    used_tickers = set()

    for h in data.get("holdings", []):
        holding_entry = {k: h.get(k, 0 if k != "tradingsymbol" else "") for k in required_keys}

        # If this stock is in news_data, merge news_headline + sentiment
        ticker = h.get("tradingsymbol")
        if ticker in news_lookup:
            news_item = news_lookup[ticker]
            holding_entry["news_headline"] = news_item.get("new_headline", "")
            holding_entry["sentiment"] = news_item.get("sentiment", "")
            used_tickers.add(ticker)

        simplified["current_holdings"].append(holding_entry)
        used_tickers.add(ticker)

    # Remove news items for tickers already in holdings or merged
    cleaned_news = [n for n in news_data if n["tradingsymbol"] not in used_tickers]

    return simplified, cleaned_news


def get_portfolio_stocks(smartApiActions,news_data):
    """Fetch company names of holdings from Angel One SmartAPI."""
    response = smartApiActions.getAllHoldings()  # JSON response
    simplify_holdings_data,other_hot_news = simplify_holdings_json(response,news_data)
    simplify_holdings_data['current_holdings'] = get_portfolio_data_with_indicators(simplify_holdings_data['current_holdings'],smartApiActions)
    return simplify_holdings_data,other_hot_news
