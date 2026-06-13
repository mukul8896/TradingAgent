# config.py
"""
Configuration file for the trading system
"""

import os

# NSE master equity list (contains all ticker → company name mappings)
NSE_EQUITY_LIST_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
NEWS_API_URL = "https://newsapi.org/v2/everything"
TRADIENT_NEWS_URL = "https://api.tradient.org/v1/api/market/news"
CHARTINK_SCAN_URL = "https://chartink.com/screener/process"
INSTRUMENT_LIST_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"


# Trading Configuration
TRADING_CONFIG = {
    "long_term": {
        "max_positions": 10,
        "position_size_pct": 0.15,  # 15% per position
        "stop_loss_pct": 0.10,  # 10% stop loss
        "target_return_pct": 0.25,  # 25% target
        "holding_period_days": 180,
        "rebalance_frequency": "monthly"
    },
    "swing": {
        "max_positions": 5,
        "position_size_pct": 0.20,  # 20% per position
        "stop_loss_pct": 0.05,  # 5% stop loss
        "target_return_pct": 0.08,  # 8% target
        "holding_period_days": 20,
        "min_volume": 1000000,  # Minimum daily volume
        "min_confidence": 70
    },
    "intraday": {
        "max_positions": 3,
        "position_size_pct": 0.30,  # 30% per position
        "stop_loss_pct": 0.02,  # 2% stop loss
        "target_return_pct": 0.015,  # 1.5% target
        "square_off_time": "15:15",  # Auto square-off time
        "min_volume": 5000000,
        "min_confidence": 80
    }
}

# Technical Indicators Settings
INDICATOR_SETTINGS = {
    "ema_periods": [9, 20, 50, 100, 200],
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "atr_period": 14,
    "volume_spike_multiplier": 2
}

# Risk Management Rules
RISK_RULES = {
    "max_daily_loss_pct": 0.03,  # 3% max daily loss
    "max_open_positions": 10,
    "correlation_threshold": 0.7,  # Avoid highly correlated positions
    "margin_buffer": 0.2,  # Keep 20% margin buffer
    "max_sector_exposure": 0.4  # Max 40% in single sector
}

# Market Hours
MARKET_HOURS = {
    "pre_open": {"start": "09:00", "end": "09:15"},
    "normal": {"start": "09:15", "end": "15:30"},
    "post_close": {"start": "15:30", "end": "16:00"}
}

# Watchlist Categories
WATCHLIST = {
    "nifty50": [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK"
    ],
    "high_momentum": [],  # Will be populated dynamically
    "value_picks": [],  # Will be populated dynamically
    "breakout_candidates": []  # Will be populated dynamically
}

# .env.example
# Angel One SmartAPI Credentials
ANGEL_ACCOUNT = "_NEW"
SMART_API_KEY=os.getenv(f"SMART_API_KEY{ANGEL_ACCOUNT}")
SMART_API_CLIENT_CODE=os.getenv(f"SMART_API_CLIENT_CODE{ANGEL_ACCOUNT}")
SMART_API_PASSWORD=os.getenv(f"SMART_API_PASSWORD{ANGEL_ACCOUNT}")
SMART_API_TOTP=os.getenv(f"SMART_API_TOTP{ANGEL_ACCOUNT}")

# OpenAI API
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
MODEL_ID = "gpt-5"

# News API
NEWS_API_KEY=os.getenv("NEWS_API_KEY")

# Database (optional)
# DATABASE_URL=postgresql://user:password@localhost:5432/trading_db

# Notification Settings (optional)
TELEGRAM_MARKETBOT_TOKEN=os.getenv("TELEGRAM_MARKETBOT_TOKEN")
TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_BOT_CHAT_ID")
# EMAIL_SMTP_SERVER=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USERNAME=your_email@gmail.com
# EMAIL_PASSWORD=your_app_password