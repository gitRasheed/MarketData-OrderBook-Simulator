import pytest
from decimal import Decimal
from src.ticker import Ticker

def test_ticker_creation():
    ticker = Ticker("SPY", "0.01")
    assert ticker.symbol == "SPY"
    assert ticker.tick_size == Decimal("0.01")

def test_valid_price():
    ticker = Ticker("SPY", "0.01")
    assert ticker.is_valid_price("100.00") == True
    assert ticker.is_valid_price("100.01") == True
    assert ticker.is_valid_price("100.001") == False

def test_invalid_price():
    ticker = Ticker("SPY", "0.05")
    assert ticker.is_valid_price("100.00") == True
    assert ticker.is_valid_price("100.05") == True
    assert ticker.is_valid_price("100.02") == False