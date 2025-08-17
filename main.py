# main.py
import json
import asyncio
import sys
from utils.portfolio_fetcher import get_portfolio_stocks
from prompts.prompts import PORTFOLIO_ANALYSIS_PROMPT
import openai
import telegram
import os

# ---- Windows event loop policy to avoid "Event loop is closed" (Proactor) ----
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_BOT_CHAT_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_MAX_LEN = 4096  # Telegram hard cap
# Read model ID from environment or default to gpt-5
MODEL = os.getenv("MODEL_ID", "gpt-5")

def call_llm(prompt: str, data: dict) -> dict:
    """Call the LLM with a structured prompt and return parsed JSON dict."""
    full_prompt = f"{prompt}\n\nData:\n{json.dumps(data, indent=2)}"
    resp = openai.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0
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

def split_for_telegram(text: str, chunk_size: int = TELEGRAM_MAX_LEN):
    """Yield chunks to respect Telegram message size limits."""
    while text:
        yield text[:chunk_size]
        text = text[chunk_size:]

async def send_to_telegram(bot: telegram.Bot, message: str):
    """Send message with Markdown parse mode and chunking."""
    for chunk in split_for_telegram(message):
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=chunk,
            parse_mode="Markdown"  # for *bold* formatting
        )

def fmt_price(val):
    return "N/A" if val in (None, "", "null") else str(val)

async def send_portfolio_analysis(bot: telegram.Bot, analysis_json: dict):
    """Send formatted portfolio analysis according to the strict JSON schema."""
    # 1) Per-holding analysis
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

    # 2) Long-term ideas
    long_term = analysis_json.get("long_term_stocks", [])
    if long_term:
        msg_lines = ["🌟 *Long-Term Hot Stocks:*"]
        for s in long_term:
            msg_lines.append(
                f"\n*{s.get('ticker','')}* at {fmt_price(s.get('BUY_PRICE'))}\n"
                f"Reason: {s.get('reason','')}"
            )
        await send_to_telegram(bot, "\n".join(msg_lines))

    # 3) Swing trades
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

async def main():
    # Create bot inside the running loop and ensure graceful cleanup
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    try:
        # Fetch holdings
        print("INFO: Fetching portfolio stocks...")
        holding_data = get_portfolio_stocks()
        print("INFO: Current holdings:\n", json.dumps(holding_data, indent=4))
        print(f"{PORTFOLIO_ANALYSIS_PROMPT}\n\nData:\n{json.dumps(holding_data, indent=2)}")

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
