def rsi(data): return 50

def ema(data, period=20): return sum(data[-period:]) / period
