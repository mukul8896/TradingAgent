# utils/portfolio_fetcher.py
from smartapi.SmartApiActions import SmartApiActions
from utils.commonutils import getSecretKeys
from utils.indicator import get_portfolio_data_with_indicators
import json
import pandas as pd

# Initialize SmartAPI session
smartApiActions = SmartApiActions(getSecretKeys())
# NSE master equity list (contains all ticker → company name mappings)
NSE_EQUITY_LIST_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
# Load once globally to avoid repeated downloads
equity_df = pd.read_csv(NSE_EQUITY_LIST_URL)

def simplify_holdings_json(data):
    """Reduce holding JSON to only essential fields for LLM input"""
    required_keys = ["tradingsymbol", "quantity", "averageprice", "ltp", "profitandloss", "pnlpercentage"]

    simplified = {
        "holdings": [
            {k: h[k] for k in required_keys if k in h}
            for h in data.get("holdings", [])
        ],
        "totalholding": {
            "totalholdingvalue": data.get("totalholding", {}).get("totalholdingvalue", 0),
            "totalinvvalue": data.get("totalholding", {}).get("totalinvvalue", 0),
            "totalprofitandloss": data.get("totalholding", {}).get("totalprofitandloss", 0),
            "totalpnlpercentage": data.get("totalholding", {}).get("totalpnlpercentage", 0),
        }
    }
    return simplified

def get_portfolio_stocks():
    """Fetch company names of holdings from Angel One SmartAPI."""
    response = smartApiActions.getAllHoldings()  # JSON response
    simplify_holdings_data = simplify_holdings_json(response)
    portfolio_data_with_indicators = get_portfolio_data_with_indicators(simplify_holdings_data['holdings'],smartApiActions)
    return portfolio_data_with_indicators
    # company_names = []

    # if response.get("status") and "data" in response and "holdings" in response["data"]:
    #     holdings = response["data"]["holdings"]
    #     for item in holdings:
    #         ticker = item.get("tradingsymbol")
    #         quantity = item.get("quantity", 0)

    #         if ticker and quantity > 0:
    #             ticker_clean = ticker.replace("-EQ", "")

    #             # Lookup company name in NSE equity list
    #             match = equity_df[equity_df["SYMBOL"] == ticker_clean]
    #             if not match.empty:
    #                 company_name = match["NAME OF COMPANY"].values[0]
    #                 company_names.append(company_name)
    #             else:
    #                 print(f"⚠️ Warning: Could not find company name for {ticker_clean}")

    # Remove duplicates and return as list
    # return list(set(company_names))
