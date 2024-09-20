from decimal import Decimal
from src.level_data import LevelData
from src.order import Order

def test_level_data_creation():
    level_data = LevelData()
    assert level_data.quantity == Decimal('0')
    assert level_data.count == 0

def test_add_order():
    level_data = LevelData()
    order = Order(1, "limit", "buy", "100.50", "10")
    level_data.add_order(order)
    assert level_data.quantity == Decimal('10')
    assert level_data.count == 1

def test_remove_order():
    level_data = LevelData()
    order = Order(1, "limit", "buy", "100.50", "10")
    level_data.add_order(order)
    level_data.remove_order(order)
    assert level_data.quantity == Decimal('0')
    assert level_data.count == 0

def test_update_quantity():
    level_data = LevelData()
    order = Order(1, "limit", "buy", "100.50", "10")
    level_data.add_order(order)
    level_data.update_quantity(Decimal('10'), Decimal('15'))
    assert level_data.quantity == Decimal('15')
    assert level_data.count == 1

def test_multiple_orders():
    level_data = LevelData()
    order1 = Order(1, "limit", "buy", "100.50", "10")
    order2 = Order(2, "limit", "buy", "100.50", "5")
    level_data.add_order(order1)
    level_data.add_order(order2)
    assert level_data.quantity == Decimal('15')
    assert level_data.count == 2