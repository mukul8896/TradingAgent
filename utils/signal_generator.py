def generate_signal_from_news(news_text: str) -> str:
    # Placeholder: Replace with LLM prompt logic
    # Example decision based on simple keywords
    if "rallies" in news_text.lower() or "strong" in news_text.lower():
        return "BUY"
    elif "falls" in news_text.lower() or "uncertainty" in news_text.lower():
        return "SELL"
    return "HOLD"
