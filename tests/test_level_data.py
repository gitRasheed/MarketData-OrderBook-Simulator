from decimal import Decimal
from src.level_data import LevelData
from src.order import Order

def test_level_data_creation():
    level_data = LevelData(Decimal('100.50'))
    assert level_data.price == Decimal('100.50')
    assert level_data.quantity == Decimal('0')
    assert level_data.count == 0
    assert level_data.head_order is None
    assert level_data.tail_order is None

def test_add_order():
    level_data = LevelData(Decimal('100.50'))
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    level_data.add_order(order)
    assert level_data.quantity == Decimal('10')
    assert level_data.count == 1
    assert level_data.head_order == order
    assert level_data.tail_order == order

def test_remove_order():
    level_data = LevelData(Decimal('100.50'))
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    level_data.add_order(order)
    level_data.remove_order(order)
    assert level_data.quantity == Decimal('0')
    assert level_data.count == 0
    assert level_data.head_order is None
    assert level_data.tail_order is None

def test_update_quantity():
    level_data = LevelData(Decimal('100.50'))
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    level_data.add_order(order)
    level_data.update_quantity(Decimal('10'), Decimal('15'))
    assert level_data.quantity == Decimal('15')
    assert level_data.count == 1

def test_multiple_orders():
    level_data = LevelData(Decimal('100.50'))
    order1 = Order(1, "limit", "buy", "100.50", "10", "SPY")
    order2 = Order(2, "limit", "buy", "100.50", "5", "SPY")
    level_data.add_order(order1)
    level_data.add_order(order2)
    assert level_data.quantity == Decimal('15')
    assert level_data.count == 2
    assert level_data.head_order == order1
    assert level_data.tail_order == order2
    assert order1.next_order == order2
    assert order2.prev_order == order1