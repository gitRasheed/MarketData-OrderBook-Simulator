import pytest
from decimal import Decimal
from src.limit import Limit
from src.order import Order

def test_limit_creation():
    limit = Limit(Decimal('100.50'))
    assert limit.price == Decimal('100.50')
    assert limit.total_volume == Decimal('0')
    assert limit.order_count == 0
    assert limit.head_order is None
    assert limit.tail_order is None
    assert limit.parent is None
    assert limit.left_child is None
    assert limit.right_child is None

def test_add_order():
    limit = Limit(Decimal('100.50'))
    order = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    limit.add_order(order)
    assert limit.total_volume == Decimal('10')
    assert limit.order_count == 1
    assert limit.head_order == order
    assert limit.tail_order == order
    assert order.parent_limit == limit

def test_remove_order():
    limit = Limit(Decimal('100.50'))
    order = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    limit.add_order(order)
    limit.remove_order(order)
    assert limit.total_volume == Decimal('0')
    assert limit.order_count == 0
    assert limit.head_order is None
    assert limit.tail_order is None
    assert order.parent_limit is None

def test_update_volume():
    limit = Limit(Decimal('100.50'))
    order = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    limit.add_order(order)
    limit.update_volume(Decimal('10'), Decimal('15'))
    assert limit.total_volume == Decimal('15')
    assert limit.order_count == 1

def test_multiple_orders():
    limit = Limit(Decimal('100.50'))
    order1 = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    order2 = Order(2, "limit", "buy", Decimal('100.50'), Decimal('5'), "SPY")
    limit.add_order(order1)
    limit.add_order(order2)
    assert limit.total_volume == Decimal('15')
    assert limit.order_count == 2
    assert limit.head_order == order1
    assert limit.tail_order == order2
    assert order1.next_order == order2
    assert order2.prev_order == order1

def test_remove_head_order():
    limit = Limit(Decimal('100.50'))
    order1 = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    order2 = Order(2, "limit", "buy", Decimal('100.50'), Decimal('5'), "SPY")
    limit.add_order(order1)
    limit.add_order(order2)
    limit.remove_order(order1)
    assert limit.total_volume == Decimal('5')
    assert limit.order_count == 1
    assert limit.head_order == order2
    assert limit.tail_order == order2

def test_remove_tail_order():
    limit = Limit(Decimal('100.50'))
    order1 = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    order2 = Order(2, "limit", "buy", Decimal('100.50'), Decimal('5'), "SPY")
    limit.add_order(order1)
    limit.add_order(order2)
    limit.remove_order(order2)
    assert limit.total_volume == Decimal('10')
    assert limit.order_count == 1
    assert limit.head_order == order1
    assert limit.tail_order == order1

def test_remove_middle_order():
    limit = Limit(Decimal('100.50'))
    order1 = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    order2 = Order(2, "limit", "buy", Decimal('100.50'), Decimal('5'), "SPY")
    order3 = Order(3, "limit", "buy", Decimal('100.50'), Decimal('7'), "SPY")
    limit.add_order(order1)
    limit.add_order(order2)
    limit.add_order(order3)
    limit.remove_order(order2)
    assert limit.total_volume == Decimal('17')
    assert limit.order_count == 2
    assert limit.head_order == order1
    assert limit.tail_order == order3
    assert order1.next_order == order3
    assert order3.prev_order == order1

def test_update_order_quantity():
    limit = Limit(Decimal('100.50'))
    order = Order(1, "limit", "buy", Decimal('100.50'), Decimal('10'), "SPY")
    limit.add_order(order)
    limit.update_volume(order.quantity, Decimal('15'))
    order.quantity = Decimal('15')
    assert limit.total_volume == Decimal('15')
    assert limit.order_count == 1
    assert limit.head_order == order
    assert limit.tail_order == order