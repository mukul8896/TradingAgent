from agents.strategy_agent import StrategyAgent
from agents.risk_agent import RiskAgent
from agents.execution_agent import ExecutionAgent
from graphs.trading_graph import TradingGraph
from portfolio.portfolio_store import PortfolioStore

if __name__ == '__main__':
    strategy = StrategyAgent()
    risk = RiskAgent()
    execution = ExecutionAgent()
    graph = TradingGraph(strategy, risk, execution)

    portfolio = PortfolioStore()
    market_data = {'NIFTY': [100, 101, 102]}

    graph.run(market_data, portfolio)
