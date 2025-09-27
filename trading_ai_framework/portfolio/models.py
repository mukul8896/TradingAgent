from dataclasses import dataclass

@dataclass
class Position:
    ticker: str
    qty: float
    avg_price: float
    strategy: str
