# main.py
import json
import asyncio
import sys
from utils.portfolio_fetcher import get_portfolio_stocks
from prompts.portfolio_prompt import PORTFOLIO_ANALYSIS_PROMPT
import openai
from notification.telegram_msg import send_portfolio_analysis
import os
import telegram
from config import MODEL_ID
from inidcators.indicator_utils import enriched_json_with_indicators
from utils.news_fetcher import fetch_positive_stock_news, fetch_all_stock_news
from smartapi.SmartApiActions import SmartApiActions
from config import MODEL_ID
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL_ID", MODEL_ID)
# ---- Windows event loop policy to avoid "Event loop is closed" (Proactor) ----
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def call_llm(prompt: str, data: dict) -> dict:
    """Call the LLM with a structured prompt and return parsed JSON dict."""
    full_prompt = f"{prompt}\n\nData:\n{json.dumps(data, indent=1)}"
    resp = openai.chat.completions.create(
        model=MODEL,
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
    # Create bot inside the running loop and ensure graceful cleanup
    bot = telegram.Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    # Initialize SmartAPI session
    smartApiActions = SmartApiActions()
    try:
        # Fetch holdings
        print("INFO: Fetching portfolio stocks...")
        holding_data,other_hot_stocks = get_portfolio_stocks(smartApiActions,fetch_all_stock_news())
        print("INFO: Fetching positive sentiment stocks news...")
        positive_sentiment_stocks_from_news_analysis = fetch_positive_stock_news(other_hot_stocks)
        positive_sentiment_stocks_from_news_analysis = enriched_json_with_indicators(positive_sentiment_stocks_from_news_analysis,"ONE_DAY",smartApiActions)
        holding_data["positive_sentiment_stocks_from_news_analysis"] = positive_sentiment_stocks_from_news_analysis
        print("INFO: Stocks Data:\n", json.dumps(holding_data, indent=1))

        # LLM analysis
        print("INFO: Running portfolio analysis...")
        analysis = call_llm(PORTFOLIO_ANALYSIS_PROMPT, holding_data)
        print(json.dumps(analysis, indent=4))

        # # Send to Telegram
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
