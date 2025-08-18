# intraday_trading_main.py

import datetime as dt
import telegram
import asyncio
import os
import sys
from chartink.chartink_scanner import stocks_scanner
from chartink.chartink_queries import BUY_INTRADAY_QUERY
from notification.telegram_msg import send_to_telegram

# ---- Windows event loop policy to avoid "Event loop is closed" (Proactor) ----
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    bot = telegram.Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    try:
        tickers = stocks_scanner(BUY_INTRADAY_QUERY)
        print(f"*Intraday Tickers* at {dt.datetime.now().hour}:{dt.datetime.now().minute}\n are {tickers}")
        await send_to_telegram(bot, message=f"*Intraday Tickers* at {dt.datetime.now().hour}:{dt.datetime.now().minute}\n are {tickers}")
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