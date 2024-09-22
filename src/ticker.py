from decimal import Decimal

class Ticker:
    def __init__(self, symbol, tick_size):
        self.symbol = symbol
        self._tick_size = Decimal(str(tick_size))

    @property
    def tick_size(self):
        return self._tick_size

    def is_valid_price(self, price):
        price_decimal = Decimal(str(price))
        return price_decimal % self._tick_size == 0