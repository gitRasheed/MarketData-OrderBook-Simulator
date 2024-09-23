from decimal import Decimal
from src.limit_tree import LimitTree
from src.limit import Limit

def test_limit_tree_creation():
    tree = LimitTree()
    assert tree.root is None
    assert tree.lowest_limit is None
    assert tree.highest_limit is None

def test_insert():
    tree = LimitTree()
    limit1 = Limit(Decimal('100.50'))
    limit2 = Limit(Decimal('100.60'))
    limit3 = Limit(Decimal('100.40'))

    tree.insert(limit1)
    assert tree.root == limit1
    assert tree.lowest_limit == limit1
    assert tree.highest_limit == limit1

    tree.insert(limit2)
    assert tree.root.right_child == limit2
    assert tree.highest_limit == limit2

    tree.insert(limit3)
    assert tree.root.left_child == limit3
    assert tree.lowest_limit == limit3

def test_find():
    tree = LimitTree()
    limit1 = Limit(Decimal('100.50'))
    limit2 = Limit(Decimal('100.60'))
    tree.insert(limit1)
    tree.insert(limit2)

    assert tree.find(Decimal('100.50')) == limit1
    assert tree.find(Decimal('100.60')) == limit2
    assert tree.find(Decimal('100.70')) is None

def test_delete():
    tree = LimitTree()
    limit1 = Limit(Decimal('100.50'))
    limit2 = Limit(Decimal('100.60'))
    limit3 = Limit(Decimal('100.40'))
    tree.insert(limit1)
    tree.insert(limit2)
    tree.insert(limit3)

    tree.delete(Decimal('100.50'))
    assert tree.root.price == Decimal('100.60')
    assert tree.lowest_limit.price == Decimal('100.40')
    assert tree.highest_limit.price == Decimal('100.60')

def test_min_max():
    tree = LimitTree()
    limit1 = Limit(Decimal('100.50'))
    limit2 = Limit(Decimal('100.60'))
    limit3 = Limit(Decimal('100.40'))
    tree.insert(limit1)
    tree.insert(limit2)
    tree.insert(limit3)

    assert tree.min().price == Decimal('100.40')
    assert tree.max().price == Decimal('100.60')