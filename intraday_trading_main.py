# intraday_trading_main.py

import datetime as dt
import telegram
import asyncio
import os
import sys
import json
from chartink.chartink_scanner import stocks_scanner
from chartink.chartink_queries import MONTHLY_SWING_QUERY
from notification.telegram_msg import send_to_telegram
from prompts.intraday_prompt import INTRADAY_STOCK_PROMPT
from inidcators.indicator_utils import enriched_json_with_indicators
from smartapi.SmartApiActions import SmartApiActions
from utils.news_fetcher import fetch_positive_stock_news
from prompts.intraday_prompt import INTRADAY_STOCK_PROMPT
import openai
from config import MODEL_ID

# ---- Windows event loop policy to avoid "Event loop is closed" (Proactor) ----
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL_ID", MODEL_ID)
def call_llm(prompt, data):
    """Call the LLM with a structured prompt and return parsed JSON dict."""
    full_prompt = f"{prompt}\n\nData:\n{json.dumps(data, indent=1)}"
    resp = openai.chat.completions.create(
        model=os.getenv("MODEL_ID", MODEL_ID),
        messages=[{"role": "user", "content": full_prompt}],
    )
    content = resp.choices[0].message.content or ""

    # Strip accidental code fences if any
    cleaned = content.replace("```json", "").replace("```", "").strip()

    # Parse JSON safely
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Fall back: try to extract JSON substring if model added extra text
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start:end+1])
            except Exception:
                pass
        raise RuntimeError(f"LLM did not return valid JSON: {e}\nRaw:\n{content}")

async def main():
    bot = telegram.Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    # Initialize SmartAPI session
    smartApiActions = SmartApiActions()
    try:
        scan_data = stocks_scanner(MONTHLY_SWING_QUERY)
        print(f"INFO : Intraday Tickers at {dt.datetime.now().hour}:{dt.datetime.now().minute}:\n{scan_data}")
        scan_data = enriched_json_with_indicators(scan_data,"ONE_DAY",smartApiActions)
        scan_data = enriched_json_with_indicators(scan_data,"FIFTEEN_MINUTE",smartApiActions)
        scan_data = enriched_json_with_indicators(scan_data,"FIVE_MINUTE",smartApiActions)
        # LLM analysis
        print("INFO : Running intraday analysis...")
        analysis = call_llm(INTRADAY_STOCK_PROMPT, scan_data)
        print(json.dumps(analysis,indent=1))
        await bot.send_message(chat_id=os.getenv("TELEGRAM_BOT_CHAT_ID"),text=json.dumps(analysis,indent=1))

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