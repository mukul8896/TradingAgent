# main_chain.py
import json
import asyncio
import sys
from utils.portfolio_fetcher import get_portfolio_stocks
from utils.news_fetcher import fetch_stock_news
from prompts.prompts import PORTFOLIO_ANALYSIS_PROMPT
import openai
import telegram
import os
from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

# ---- Windows event loop policy to avoid "Event loop is closed" (Proactor) ----
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_BOT_CHAT_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_MAX_LEN = 4096  # Telegram hard cap
MODEL = os.getenv("MODEL_ID", "gpt-5")


# --------------------------
# Telegram helpers
# --------------------------
def split_for_telegram(text: str, chunk_size: int = TELEGRAM_MAX_LEN):
    while text:
        yield text[:chunk_size]
        text = text[chunk_size:]

async def send_to_telegram(bot: telegram.Bot, message: str):
    for chunk in split_for_telegram(message):
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=chunk, parse_mode="Markdown")


def fmt_price(val):
    return "N/A" if val in (None, "", "null") else str(val)


async def send_portfolio_analysis(bot: telegram.Bot, analysis_json: dict):
    portfolio_analysis = analysis_json.get("portfolio_analysis", [])
    for holding in portfolio_analysis:
        msg = (
            f"📌 *{holding.get('ticker','')}*\n"
            f"Decision: {holding.get('final_decision','')} "
            f"({holding.get('confidence','')} confident)\n"
            f"Reason: {holding.get('reason','')}\n"
            f"Exit Price: {fmt_price(holding.get('EXIT_PRICE'))}\n"
            f"Buy Price: {fmt_price(holding.get('BUY_PRICE'))}\n"
        )
        relocate = holding.get("relocate_fund_to")
        if relocate:
            msg += (
                f"💡 Relocate to: {relocate.get('ticker','')} "
                f"at {fmt_price(relocate.get('BUY_PRICE'))}\n"
                f"Reason: {relocate.get('reason','')}\n"
            )
        await send_to_telegram(bot, msg)

    swings = analysis_json.get("top_5_swing_trade_stocks", []) or \
             analysis_json.get("swing_trade_stocks", [])
    if swings:
        msg_lines = ["⚡ *Safe Swing Trades:*"]
        for s in swings:
            msg_lines.append(
                f"\n*{s.get('ticker','')}* at {fmt_price(s.get('BUY_PRICE'))}\n"
                f"Reason: {s.get('reason','')}"
            )
        await send_to_telegram(bot, "\n".join(msg_lines))


# --------------------------
# LangChain workflow
# --------------------------
def run_portfolio_analysis_chain(news_data: list, portfolio_data: list) -> dict:
    llm = OpenAI(temperature=0, openai_api_key=openai.api_key, model_name=MODEL)

    # Step 1: News analysis
    news_prompt = PromptTemplate(
        input_variables=["news_data"],
        template="""
                You are a market analyst. Given the following news headlines and summaries:
                {news_data}

                For each stock, determine sentiment: positive, negative, or neutral. Provide a brief reason.
                Return a JSON array: [{"ticker": "TICKER", "sentiment": "positive/negative/neutral", "reason": "brief reason"}]
                """
        )
    news_chain = LLMChain(llm=llm, prompt=news_prompt, output_key="news_sentiment")

    # Step 2: Portfolio analysis
    portfolio_prompt = PromptTemplate(
        input_variables=["portfolio_data", "news_sentiment"],
        template=f"""
                {PORTFOLIO_ANALYSIS_PROMPT}

                Portfolio: {{portfolio_data}}
                Market news sentiment: {{news_sentiment}}

                Consider market news sentiment along with technical and fundamental data when making BUY/SELL/HOLD recommendations.
                Return in the strict JSON format defined earlier.
                """
        )
    portfolio_chain = LLMChain(llm=llm, prompt=portfolio_prompt, output_key="portfolio_analysis")

    # Sequential chain: news -> portfolio
    chain = SequentialChain(
        chains=[news_chain, portfolio_chain],
        input_variables=["news_data", "portfolio_data"],
        output_variables=["portfolio_analysis"],
        verbose=True
    )

    # Run chain
    result = chain({"news_data": news_data, "portfolio_data": portfolio_data})
    return result["portfolio_analysis"]


# --------------------------
# Main async workflow
# --------------------------
async def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    try:
        # Fetch holdings
        # holding_data = get_portfolio_stocks()

        # Fetch market news
        print("INFO: Fetching stock-specific news...")
        news_data = fetch_stock_news(max_articles=100)
        print(json.dumps(news_data,indent=2))
        print(f"INFO: {len(news_data)} stock news articles fetched.")

        # Run LangChain analysis
        analysis = run_portfolio_analysis_chain(news_data, holding_data)

        # # Send analysis to Telegram
        await send_portfolio_analysis(bot, analysis)

    finally:
        try:
            if hasattr(bot, "close") and callable(getattr(bot, "close")):
                await bot.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
