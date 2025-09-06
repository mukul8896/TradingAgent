# intraday_trading_main.py

import datetime as dt
import telegram
import asyncio
import os
import sys
import json
from chartink.chartink_scanner import stocks_scanner
from chartink.chartink_queries import MONTHLY_SWING_RSI_60_QUERY
from notification.telegram_msg import send_to_telegram
from prompts.intraday_prompt import INTRADAY_STOCK_PROMPT
from inidcators.indicator_utils import enriched_json_with_indicators
from smartapi.SmartApiActions import SmartApiActions
from prompts.intraday_prompt import INTRADAY_STOCK_PROMPT
from llm_api.openaiAPI import call_llm

# ---- Windows event loop policy to avoid "Event loop is closed" (Proactor) ----
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    bot = telegram.Bot(token=os.getenv("TELEGRAM_MARKETBOT_TOKEN"))
    # Initialize SmartAPI session
    smartApiActions = SmartApiActions()
    
    try:
        scan_data = stocks_scanner(MONTHLY_SWING_RSI_60_QUERY)
        print(f"INFO : Intraday Tickers at {dt.datetime.now().hour}:{dt.datetime.now().minute}:\n{[item['tradingsymbol'] for item in scan_data]}")
        scan_data = enriched_json_with_indicators(scan_data,"ONE_DAY",smartApiActions)
        scan_data = enriched_json_with_indicators(scan_data,"ONE_HOUR",smartApiActions)
        scan_data = enriched_json_with_indicators(scan_data,"FIFTEEN_MINUTE",smartApiActions)
        scan_data = enriched_json_with_indicators(scan_data,"FIVE_MINUTE",smartApiActions)
        print(f"INFO : {json.dumps(scan_data,indent=1)}")
        
        # LLM analysis
        print("INFO : Running intraday analysis...")
        analysis = call_llm(INTRADAY_STOCK_PROMPT, scan_data)
        print(f"INFO : {analysis}")
        await send_to_telegram(bot=bot,message=json.dumps(analysis))

        if analysis.get("ticker") and analysis.get("direction") and analysis.get("ticker") != "N/A":
            response = None
            await send_to_telegram(bot=bot,message=json.dumps(analysis, indent=1))
            print(f"INFO : Placing robo order for {analysis.get('ticker')} @ {analysis.get('entry_price')}")
            response = smartApiActions.place_robo_order(ticker = analysis.get("ticker"), 
                            buy_sell = analysis.get("direction"), 
                            price = analysis.get("entry_price"), 
                            quantity = analysis.get("qty", "1"), 
                            squareoff = analysis.get("squareoff"), 
                            stoploss = analysis.get("stop_loss"), 
                            trailing_sl = analysis.get("trailing_stop_loss"),
                            productType="INTRADAY", 
                            exchange="NSE"
                        )
            # Handle SmartAPI response
            if response is not None:
                if response.get("status") is False:
                    print(f"ERROR : Order Failed: {response['message']}")
                    await send_to_telegram(bot=bot,message=f"INFO : Order Failed: {response['message']}")
                else:
                    print(f"INFO : Order Success: {json.dumps(response, indent=2)}")
            else:
                print(f"ERROR : Request error while placing order")  
                await send_to_telegram(bot=bot,message=f"ERROR : Request error while placing order")  
        else:
            print("INFO : No valid trade recommendation from LLM (N/A).")
            await send_to_telegram(bot=bot,message=f"No valid trade recommendation from LLM (N/A).") 
            

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