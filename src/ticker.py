from decimal import Decimal

class Ticker:
    def __init__(self, symbol, tick_size):
        self.symbol = symbol
        self.tick_size = Decimal(str(tick_size))

    def is_valid_price(self, price):
        return Decimal(str(price)) % self.tick_size == 0