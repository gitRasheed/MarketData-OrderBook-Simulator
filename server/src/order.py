from enum import Enum
from datetime import datetime
from typing import Optional

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"

class Order:
    def __init__(
        self,
        order_id: str,
        instrument_id: str,
        quantity: int,
        side: OrderSide,
        type: OrderType,
        timestamp: datetime,
        price: Optional[float] = None
    ):
        self.order_id = order_id
        self.instrument_id = instrument_id
        self.quantity = quantity
        self.side = side
        self.type = type
        self.timestamp = timestamp
        self.price = price
        self.status = OrderStatus.NEW

        self._validate()

    def _validate(self):
        if not isinstance(self.type, OrderType):
            raise ValueError(f"Invalid order type: {self.type}")
        
        if not isinstance(self.side, OrderSide):
            raise ValueError(f"Invalid order side: {self.side}")
        
        if self.type == OrderType.LIMIT and self.price is None:
            raise ValueError("Limit orders must have a price")
        
        if self.price is not None and self.price <= 0:
            raise ValueError(f"Invalid price: {self.price}")
        
        if self.quantity <= 0:
            raise ValueError(f"Invalid quantity: {self.quantity}")

    def __repr__(self):
        return f"Order(id={self.order_id}, instrument={self.instrument_id}, " \
               f"price={self.price}, quantity={self.quantity}, " \
               f"side={self.side.value}, type={self.type.value}, status={self.status.value})"