import pytest
from decimal import Decimal
from src.price_level import PriceLevel
from src.order import Order

def test_price_level_creation():
    level = PriceLevel(Decimal('100.50'))
    assert level.price == Decimal('100.50')
    assert level.total_volume == Decimal('0')
    assert level.order_count == 0
    assert level.head_order is None
    assert level.tail_order is None
    assert level.parent is None
    assert level.left_child is None
    assert level.right_child is None

def test_add_order():
    level = PriceLevel(Decimal('100.50'))
    order = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    level.add_order(order)
    assert level.total_volume == Decimal('10')
    assert level.order_count == 1
    assert level.head_order == order
    assert level.tail_order == order
    assert order.parent_level == level

def test_remove_order():
    level = PriceLevel(Decimal('100.50'))
    order = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    level.add_order(order)
    level.remove_order(order)
    assert level.total_volume == Decimal('0')
    assert level.order_count == 0
    assert level.head_order is None
    assert level.tail_order is None
    assert order.parent_level is None

def test_update_volume():
    level = PriceLevel(Decimal('100.50'))
    order = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    level.add_order(order)
    level.update_volume(Decimal('10'), Decimal('15'))
    assert level.total_volume == Decimal('15')
    assert level.order_count == 1

def test_multiple_orders():
    level = PriceLevel(Decimal('100.50'))
    order1 = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    order2 = Order(2, "limit", "buy", Decimal('100.50'), Decimal('5'), "SPY")
    level.add_order(order1)
    level.add_order(order2)
    assert level.total_volume == Decimal('15')
    assert level.order_count == 2
    assert level.head_order == order1
    assert level.tail_order == order2
    assert order1.next_order == order2
    assert order2.prev_order == order1

def test_remove_head_order():
    level = PriceLevel(Decimal('100.50'))
    order1 = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    order2 = Order(2, "limit", "buy", Decimal('100.50'), Decimal('5'), "SPY")
    level.add_order(order1)
    level.add_order(order2)
    level.remove_order(order1)
    assert level.total_volume == Decimal('5')
    assert level.order_count == 1
    assert level.head_order == order2
    assert level.tail_order == order2

def test_remove_tail_order():
    level = PriceLevel(Decimal('100.50'))
    order1 = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    order2 = Order(2, "limit", "buy", Decimal('100.50'), Decimal('5'), "SPY")
    level.add_order(order1)
    level.add_order(order2)
    level.remove_order(order2)
    assert level.total_volume == Decimal('10')
    assert level.order_count == 1
    assert level.head_order == order1
    assert level.tail_order == order1

def test_remove_middle_order():
    level = PriceLevel(Decimal('100.50'))
    order1 = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    order2 = Order(2, "limit", "buy", Decimal('100.50'), Decimal('5'), "SPY")
    order3 = Order(3, "limit", "buy", Decimal('100.50'), Decimal('7'), "SPY")
    level.add_order(order1)
    level.add_order(order2)
    level.add_order(order3)
    level.remove_order(order2)
    assert level.total_volume == Decimal('17')
    assert level.order_count == 2
    assert level.head_order == order1
    assert level.tail_order == order3
    assert order1.next_order == order3
    assert order3.prev_order == order1

def test_update_order_quantity():
    level = PriceLevel(Decimal('100.50'))
    order = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    level.add_order(order)
    level.update_volume(order.quantity, Decimal('15'))
    order.quantity = Decimal('15')
    assert level.total_volume == Decimal('15')
    assert level.order_count == 1
    assert level.head_order == order
    assert level.tail_order == order