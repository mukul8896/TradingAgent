# Archived: legacy OpenAI-era trading app

This folder preserves the pre-MCP implementation that used the OpenAI API as
the decision-maker (scan → dump data into a GPT prompt → parse JSON → place
order). It is kept for reference only and is **not used** by the current
system. Notable contents:

- `intraday_trading_main.py`, `portfolio_analysis_main.py`,
  `watchlist_analysis_main.py`, `daily_scan.py` — old entry scripts
- `llm_api/` — OpenAI API wrapper (replaced by Claude Code acting as the agent)
- `smartapi/`, `inidcators/`, `chartink/`, `utils/`, `notification/` — broker,
  indicator, scanner, news and Telegram code, since ported/cleaned into the
  `trading-mcp-server` package
- `prompts/` — old LLM prompts, since adapted into MCP prompts
- `strategies/`, `trading_ai_framework/` — unfinished experiments (broken imports)
- `github-workflows/` — old GitHub Actions that ran the OpenAI scripts on a
  schedule. Do not re-enable: they place unvalidated real orders.

Safe to delete once you are confident nothing else is needed from here.
