import pytest
from datetime import datetime
from server.src.order import Order, OrderType, OrderSide, OrderStatus

def test_order_creation():
    order = Order(
        order_id="123",
        instrument_id="AAPL",
        price=150.0,
        quantity=100,
        side=OrderSide.BUY,
        type=OrderType.LIMIT,
        timestamp=datetime.now()
    )
    
    assert order.order_id == "123"
    assert order.instrument_id == "AAPL"
    assert order.price == 150.0
    assert order.quantity == 100
    assert order.side == OrderSide.BUY
    assert order.type == OrderType.LIMIT
    assert order.status == OrderStatus.NEW
    assert isinstance(order.timestamp, datetime)

def test_market_order_creation():
    order = Order(
        order_id="456",
        instrument_id="GOOGL",
        quantity=50,
        side=OrderSide.SELL,
        type=OrderType.MARKET,
        timestamp=datetime.now()
    )
    
    assert order.order_id == "456"
    assert order.instrument_id == "GOOGL"
    assert order.price is None
    assert order.quantity == 50
    assert order.side == OrderSide.SELL
    assert order.type == OrderType.MARKET
    assert order.status == OrderStatus.NEW
    assert isinstance(order.timestamp, datetime)

def test_invalid_order_type():
    with pytest.raises(ValueError):
        Order(
            order_id="789",
            instrument_id="MSFT",
            price=200.0,
            quantity=75,
            side=OrderSide.BUY,
            type="INVALID_TYPE",
            timestamp=datetime.now()
        )

def test_invalid_order_side():
    with pytest.raises(ValueError):
        Order(
            order_id="101",
            instrument_id="AMZN",
            price=3000.0,
            quantity=10,
            side="INVALID_SIDE",
            type=OrderType.LIMIT,
            timestamp=datetime.now()
        )

def test_negative_price():
    with pytest.raises(ValueError):
        Order(
            order_id="202",
            instrument_id="TSLA",
            price=-500.0,
            quantity=20,
            side=OrderSide.SELL,
            type=OrderType.LIMIT,
            timestamp=datetime.now()
        )

def test_negative_quantity():
    with pytest.raises(ValueError):
        Order(
            order_id="303",
            instrument_id="FB",
            price=300.0,
            quantity=-30,
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            timestamp=datetime.now()
        )