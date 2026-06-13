# CLAUDE.md — TradingAgent (main trading repo)

## Project context

This repo is the **trading application workspace**: configuration, agent
definitions, and runtime state for an NSE trading agent. All trading
capability comes from the `trading-agent` MCP server, the published PyPI
package `trading-mcp-server` (installed via `pip install`). You — Claude Code —
are the trading agent; the MCP tools are your hands.

- `.env` is the **enforced** trading config read by the MCP server (mode,
  permissions, risk limits, credentials). `.env.example` documents it.
- `config/settings.yaml` holds app-level choices (agent modes, MCP package
  name).
- `storage/` is runtime state written by the server (paper trades, pending
  orders, audit log). Treat it as data, not code.
- `archive/` is the dead legacy OpenAI-era app. Never import from it or
  resurrect it without being asked.

## How this repo uses the MCP server

`.mcp.json` launches `python -m trading_mcp_server.server` with
`TRADING_MCP_HOME` pointing at this repo, so the server reads `./.env` and
writes `./storage/`. The server is the `trading-mcp-server` PyPI package,
installed from `requirements.txt`. This repo only consumes it — the server's
source lives in its own package and is not part of this workspace.

## Hard rules

1. **Do not put MCP server implementation code in this repo.** Tools,
   services, indicators, broker code, backtests — all of that belongs to the
   `trading-mcp-server` package, not here. This repo only consumes the server.
2. **Never make real trading the default.** Paper trading is the safe default
   everywhere: code, config templates, docs, examples.
3. **Never set `TRADING_MODE=live`, `ALLOW_LIVE_TRADING=true`, or
   `ALLOW_DELIVERY_SELL=true` yourself** — not in `.env`, not in examples that
   the user might copy blindly. Only the human enables live trading.
4. **Do not modify `.env`, broker credentials, secrets, or trading risk
   configuration without an explicit instruction** naming the exact change.
5. Never claim an order was executed unless an MCP tool returned
   `status='executed'` (live) or `status='filled'` (paper).
6. Delivery sells are recommendation-only. Do not look for workarounds.
7. Do not provide financial advice; always include a disclaimer in trade
   analyses, and state the trading mode (paper/live) in every trade plan.

## Working agreements

- The intraday and swing trading agents are defined in `.claude/agents/`
  (`intraday-trader.md`, `swing-trader.md`) — keep them separate; don't blend
  their rules.
- Keep this repo thin. If a change feels like "server logic", it belongs to
  the `trading-mcp-server` package, not here.
- Coding style: Python 3.10+, type hints, small focused modules.

## Important commands

```powershell
pip install -r requirements.txt          # install MCP server (trading-mcp-server) + deps
python -m trading_mcp_server.server      # run server manually
claude mcp list                          # verify registration
```

## Testing rules

- Server behavior is tested in the `trading-mcp-server` package itself, not in
  this repo. This workspace holds only config, agent definitions, and state.
- Safety behaviors (paper default, delivery-sell block, approval flow,
  risk limits) are enforced by the server — never try to work around them
  from this repo.
