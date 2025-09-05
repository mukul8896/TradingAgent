# intraday_trading_main.py

import datetime as dt
import telegram
import asyncio
import os
import sys
import json
from chartink.chartink_scanner import stocks_scanner
from chartink.chartink_queries import MONTHLY_SWING_QUERY,GOLDEN_CROSS_OVER_DAILY,OPEN_LOW_SAME_QUERY,BUY_INTRADAY_QUERY,BUY_GOLDEN_RATIO,SELL_GOLDEN_RATIO
from notification.telegram_msg import send_to_telegram
from prompts.intraday_prompt import INTRADAY_STOCK_PROMPT
from inidcators.indicator_utils import get_rsi_cross_over
from smartapi.SmartApiActions import SmartApiActions
from utils.news_fetcher import fetch_positive_stock_news
from prompts.intraday_prompt import INTRADAY_STOCK_PROMPT
import openai
from config import MODEL_ID

# ---- Windows event loop policy to avoid "Event loop is closed" (Proactor) ----
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    bot = telegram.Bot(token=os.getenv("TELEGRAM_MARKETBOT_TOKEN"))
    # Initialize SmartAPI session
    smartApiActions = SmartApiActions()
    try:
        scan_data = stocks_scanner(MONTHLY_SWING_QUERY)
        print(f"INFO : MONTHLY_SWING_QUERY {dt.datetime.now().hour}:{dt.datetime.now().minute}:\n{[item['tradingsymbol'] for item in scan_data]}\n")
        scan_data = get_rsi_cross_over("ONE_DAY",scan_data,smartApiActions)
        print(f"INFO : MONTHLY_SWING_QUERY RSI CROSSED {dt.datetime.now().hour}:{dt.datetime.now().minute}:\n{[item['tradingsymbol'] for item in scan_data]}\n")
        await bot.send_message(chat_id=os.getenv("TELEGRAM_BOT_CHAT_ID"),text=f"MONTHLY_SWING_QUERY RSI CROSSED {[item['tradingsymbol'] for item in scan_data]}\n")


        # scan_data = stocks_scanner(GOLDEN_CROSS_OVER_DAILY)
        # print(f"INFO : GOLDEN_CROSS_OVER_DAILY {dt.datetime.now().hour}:{dt.datetime.now().minute}:\n{[item['tradingsymbol'] for item in scan_data]}\n")
        # await bot.send_message(chat_id=os.getenv("TELEGRAM_BOT_CHAT_ID"),text=f"GOLDEN_CROSS_OVER_DAILY {[item['tradingsymbol'] for item in scan_data]}\n")

        # scan_data = stocks_scanner(OPEN_LOW_SAME_QUERY)
        # print(f"INFO : OPEN_LOW_SAME_QUERY {dt.datetime.now().hour}:{dt.datetime.now().minute}:\n{[item['tradingsymbol'] for item in scan_data]}\n")
        # await bot.send_message(chat_id=os.getenv("TELEGRAM_BOT_CHAT_ID"),text=f"OPEN_LOW_SAME_QUERY {[item['tradingsymbol'] for item in scan_data]}\n")

        # scan_data = stocks_scanner(BUY_INTRADAY_QUERY)
        # print(f"INFO : BUY_INTRADAY_QUERY {dt.datetime.now().hour}:{dt.datetime.now().minute}:\n{[item['tradingsymbol'] for item in scan_data]}\n")
        # await bot.send_message(chat_id=os.getenv("TELEGRAM_BOT_CHAT_ID"),text=f"BUY_INTRADAY_QUERY {[item['tradingsymbol'] for item in scan_data]}\n")

        # scan_data = stocks_scanner(BUY_GOLDEN_RATIO)
        # print(f"INFO : BUY_GOLDEN_RATIO {dt.datetime.now().hour}:{dt.datetime.now().minute}:\n{[item['tradingsymbol'] for item in scan_data]}\n")
        # await bot.send_message(chat_id=os.getenv("TELEGRAM_BOT_CHAT_ID"),text=f"BUY_GOLDEN_RATIO {[item['tradingsymbol'] for item in scan_data]}\n")

        # scan_data = stocks_scanner(SELL_GOLDEN_RATIO)
        # print(f"INFO : SELL_GOLDEN_RATIO {dt.datetime.now().hour}:{dt.datetime.now().minute}:\n{[item['tradingsymbol'] for item in scan_data]}\n")
        # await bot.send_message(chat_id=os.getenv("TELEGRAM_BOT_CHAT_ID"),text=f"SELL_GOLDEN_RATIO {[item['tradingsymbol'] for item in scan_data]}\n")

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