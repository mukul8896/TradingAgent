# Placeholder for broker API wrapper
class SmartApiAction:
    def place_order(self, side, ticker, qty, price=None):
        print(f'Order: {side} {qty} {ticker} at {price}')
