import telegram
import os
import requests
from config import *
TELEGRAM_MAX_LEN = 4096  # Telegram hard cap

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


def send_image_to_telegram(image_path, caption='Your image post is ready!',token=None):
    """
    Sends an image file to a specified Telegram chat.
    """
    url = f'https://api.telegram.org/bot{token}/sendPhoto'
    with open(image_path, 'rb') as image_file:
        files = {'photo': image_file}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
        
        try:
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()  # Raise an exception for bad status codes
            print("Image sent to Telegram successfully!")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send image: {e}")

async def send_portfolio_analysis(bot: telegram.Bot, analysis_json: dict):
    """Send formatted portfolio analysis according to the strict JSON schema."""
    # 1) Per-holding analysis
    portfolio_analysis = analysis_json.get("portfolio_analysis", [])
    for holding in portfolio_analysis:
        msg = (
            f"📌 *{holding.get('tradingsymbol','')}*\n"
            f"Decision: {holding.get('final_decision','')} "
            f"({holding.get('confidence','')} confident)\n"
            f"Reason: {holding.get('reason','')}\n"
        )
        relocate = holding.get("relocate_fund_to")
        if relocate:
            msg += (
                f"💡 Relocate to: {relocate.get('ticker','')} "
                f"at {fmt_price(relocate.get('BUY_PRICE'))}\n"
                f"Reason: {relocate.get('reason','')}\n"
            )
        await send_to_telegram(bot, msg)

async def send_watchlist_analysis(bot: telegram.Bot, analysis_json: dict):
    """Send formatted watchlist analysis according to the strict JSON schema."""
    # 1) Per-holding analysis
    portfolio_analysis = analysis_json.get("top_swing_trades", [])
    for holding in portfolio_analysis:
        msg = (
            f"📌 *{holding.get('tradingsymbol','')}*\n"
            f"Entry Range: {holding.get('entry_range','')}\n"
            f"Stop Loss: {holding.get('stop_loss','')}\n"
            f"Targets: {holding.get('targets','')}\n"
            f"Risk Rewards: {holding.get('risk_reward','')}\n"
            f"Holding Period: {holding.get('holding_period','')}\n"
            f"({holding.get('confidence','')} confident)\n"
            f"Reason: {holding.get('reason','')}\n"
        )
        await send_to_telegram(bot, msg)

def notify_order_status(bot,response):
    if response is not None and type(response) is dict:
        if response.get("status") is False:
            print(f"ERROR : Order Failed: {response['message']}")
            send_to_telegram(bot=bot,message=f"ERROR : Order Failed: {response['message']}")
        elif response.get("status") is True:
            print(f"INFO : Order Success: {response}")
            send_to_telegram(bot=bot,message=f"INFO : Order Success: {response}")
    elif response is not None and type(response) is str:
        print(f"INFO : Order placed {response}")
        send_to_telegram(bot=bot,message=f"INFO : Order placed {response}")
    else:
        print(f"ERROR : Order Failed: {response}")
        send_to_telegram(bot=bot,message=f"ERROR : Order Failed: {response}")
