import logging
from typing import List, Dict
from decimal import Decimal

class OrderBookLogger:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.logger = logging.getLogger(f"orderbook.{symbol}")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_change(self, action: str, side: str, price: Decimal, quantity: int):
        self.logger.info(f"{self.symbol} - {action.upper()}: {side} {quantity} @ {price}")
