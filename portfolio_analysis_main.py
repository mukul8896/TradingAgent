# main.py
import json
import asyncio
import sys
from utils.portfolio_fetcher import get_portfolio_stocks
from prompts.portfolio_prompt import PORTFOLIO_ANALYSIS_PROMPT
from notification.telegram_msg import send_portfolio_analysis
import os
import telegram
from inidcators.indicator_utils import enriched_json_with_indicators
from utils.news_fetcher import fetch_positive_stock_news, fetch_all_stock_news
from smartapi.SmartApiActions import SmartApiActions
from llm_api.openaiAPI import call_llm

# ---- Windows event loop policy to avoid "Event loop is closed" (Proactor) ----
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    # Create bot inside the running loop and ensure graceful cleanup
    bot = telegram.Bot(token=os.getenv("TELEGRAM_MARKETBOT_TOKEN"))
    # Initialize SmartAPI session
    smartApiActions = SmartApiActions()
    try:
        # Fetch holdings
        print("INFO: Fetching portfolio stocks...")
        holding_data = get_portfolio_stocks(smartApiActions)
        print("INFO: Stocks Data:\n", json.dumps(holding_data, indent=1))

        # LLM analysis
        print("INFO: Running portfolio analysis...")
        analysis = call_llm(PORTFOLIO_ANALYSIS_PROMPT, holding_data)
        print(json.dumps(analysis, indent=4))

        # Send to Telegram
        await send_portfolio_analysis(bot, analysis)

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
