# Placeholder LangGraph flow
class TradingGraph:
    def __init__(self, strategy, risk, execution):
        self.strategy = strategy
        self.risk = risk
        self.execution = execution

    def run(self, market_data, portfolio):
        trades = self.strategy.run(market_data, portfolio)
        trades = self.risk.apply(trades)
        self.execution.execute(trades)
