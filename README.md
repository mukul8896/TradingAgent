# TradingAgent

AI-driven trading workspace for NSE (India) where **Claude Code / Copilot CLI is the trading agent** and all market access goes through the **MCP server** `trading-mcp-server` (a PyPI package). There is no OpenAI dependency — the agent you chat with *is* the brain; the MCP server provides data, risk checks, paper trading, and a guarded broker layer.

## How it works

```
You ──chat──> Claude Code (agent)
                 │  MCP (stdio)
                 ▼
        trading-mcp-server          ← PyPI package (pip install)
        ├── market data, indicators, news
        ├── risk + order validation
        ├── paper trading engine    ← DEFAULT
        └── broker layer (Angel One) — guarded, approval-gated
                 │
                 ▼
        TRADING_MCP_HOME = this repo
        ├── .env       (trading config — single source of truth)
        └── storage/   (paper state, pending orders, audit log)
```

This repo holds **configuration, agent definitions, and runtime state** — no MCP server code (it lives in the `trading-mcp-server` package; see `CLAUDE.md` rules).

## ⚠️ Paper vs real trading

| | Paper (default) | Real/live |
|---|---|---|
| Orders | Simulated locally in `storage/` | Sent to Angel One SmartAPI |
| Enable | Nothing to do — default | `TRADING_MODE=live` **and** `ALLOW_LIVE_TRADING=true` in `.env`, edited by you manually |
| Approval | — | Every order: prepare → you approve a token → execute |
| Delivery sell | Blocked (recommendation only) | Still blocked unless `ALLOW_DELIVERY_SELL=true` (don't) |

**Real trading must only ever be enabled intentionally, by hand, after paper trading has proven the approach profitable.** No tool can flip the live switches; the agent cannot enable real trading on its own. Nothing here is financial advice.

## Setup

```powershell
# 1. install the MCP server (trading-mcp-server) plus this repo's deps
pip install -r requirements.txt

# 2. create your config
copy .env.example .env
#    leave TRADING_MODE=paper; add broker credentials only when you
#    want live market data (LTP/candles need an Angel One account)

# 3. open this folder in Claude Code — .mcp.json registers the server automatically
claude
```

`requirements.txt` pulls `trading-mcp-server[broker,scanners]` from PyPI. `.mcp.json` launches the installed package as `python -m trading_mcp_server.server` — no local checkout of the server is needed.

## Running the trading application

The "application" is a conversation. Examples:

```text
> Scan the watchlist for swing opportunities and paper-trade the best setup
> Analyze RELIANCE for an intraday trade
> Backtest ma_crossover on TCS over the last 500 days
> Generate my paper trading report — are we profitable?
> Review my portfolio exposure and concentration
```

Useful checks:

```powershell
python -m trading_mcp_server.server      # run the MCP server manually (stdio)
claude mcp list                          # verify Claude Code sees the server
```

## Trading rules enforced by the server

- **Intraday**: buy and sell allowed (paper always; live only with `ALLOW_INTRADAY_BUY/SELL=true`). No new entries after 15:15 IST. Market must be open. Stop-loss and target mandatory.
- **Swing/delivery**: buy allowed (paper always; live only with `ALLOW_DELIVERY_BUY=true`). **Delivery sell is never executed** — the agent records a recommendation and tells you to verify holdings and sell manually.
- **Every order**: risk per trade ≤ `MAX_RISK_PER_TRADE_PERCENT`, daily loss ≤ `MAX_DAILY_LOSS_PERCENT`, ≤ `MAX_OPEN_POSITIONS`, position ≤ `MAX_POSITION_SIZE_PERCENT` of capital, risk:reward ≥ `MIN_RISK_REWARD_RATIO`.

## Folder structure

```
TradingAgent/
├── README.md            # this file
├── CLAUDE.md            # rules for Claude Code in this repo
├── .claude/agents/      # intraday + swing agent definitions (Claude Code subagents)
├── .mcp.json            # registers trading-mcp-server with Claude Code
├── .env.example         # template for .env (the enforced trading config)
├── config/settings.yaml # app-level settings (agent modes, MCP source)
├── storage/             # runtime state written by the server (gitignored)
└── archive/             # legacy OpenAI-era app, kept for reference
```

## Important commands

| Command | Purpose |
|---|---|
| `pip install -r requirements.txt` | install MCP server (`trading-mcp-server`) + deps |
| `python -m trading_mcp_server.server` | run server manually |
| `claude mcp list` | confirm MCP registration |
| edit `.env` → `TRADING_MODE` | switch paper/live (live also needs `ALLOW_LIVE_TRADING=true`) |
