# main.py
import json
import asyncio
import sys
from utils.portfolio_fetcher import get_portfolio_stocks,get_watchlist_stocks
from prompts.watchlist_prompt import SWING_TRADING_ANALYSIS_PROMPT
from notification.telegram_msg import send_watchlist_analysis
import os
import telegram
from smartapi.SmartApiActions import SmartApiActions
from llm_api.openaiAPI import call_llm
from config import *
from utils.news_fetcher import fetch_market_news
# ---- Windows event loop policy to avoid "Event loop is closed" (Proactor) ----
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def analyze_single_stock(stock):
    # Call LLM with single stock data
    response = call_llm(SWING_TRADING_ANALYSIS_PROMPT, stock)
    
    # LLM should already return JSON with "top_swing_trades"
    if "top_swing_trades" in response and len(response["top_swing_trades"]) > 0:
        trade = response["top_swing_trades"][0]
        return trade
    return None

def analyze_watchlist(watchlist_stocks):
    results = []

    for stock in watchlist_stocks:
        print(f"{stock['tradingsymbol']} Data: {json.dumps(stock)}")
        trade_plan = analyze_single_stock(stock)
        print(f"{stock['tradingsymbol']} Analysis: {json.dumps(trade_plan,indent=1)}")
        if trade_plan and float(trade_plan["confidence"].replace("%","")) >= 70:
            results.append(trade_plan)

    # Sort by confidence
    top_trades = sorted(results, key=lambda x: float(x["confidence"].replace("%","")), reverse=True)[:3]

    summary = {
        "top_opportunities": [t["tradingsymbol"] for t in top_trades],
        "allocation_advice": "Distribute capital equally across top trades or size more into the highest-confidence trade."
    }

    return {
        "top_swing_trades": top_trades,
        "summary": summary
    }

async def main():
    # Create bot inside the running loop and ensure graceful cleanup
    bot = telegram.Bot(token=TELEGRAM_MARKETBOT_TOKEN)
    # Initialize SmartAPI session
    smartApiActions = SmartApiActions()
    try:
        news_data = fetch_market_news("all","all")

        # Fetch watchlist
        print("INFO: Fetching watchlist stocks...")
        watchlist_stocks = get_watchlist_stocks(news_data,smartApiActions)
        print("INFO: Stocks Data:\n", json.dumps(watchlist_stocks, indent=1))

        # LLM analysis
        print("INFO: Running portfolio analysis...")
        analysis = call_llm(SWING_TRADING_ANALYSIS_PROMPT, watchlist_stocks)
        print(json.dumps(analysis, indent=2,ensure_ascii=False))

        # Send to Telegram
        await send_watchlist_analysis(bot, analysis)

    finally:
        # Try to explicitly close underlying HTTP client to avoid noisy shutdown on Windows
        try:
            # PTB v20+ uses httpx under the hood; close if available
            if hasattr(bot, "close") and callable(getattr(bot, "close")):
                await bot.close()
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())
