"""Unit tests for input validation (no network)."""

import pytest

from bot.validators import ValidationError, validate_order


def test_valid_market_order_normalises():
    result = validate_order("btcusdt", "buy", "market", 0.001)
    assert result["symbol"] == "BTCUSDT"
    assert result["side"] == "BUY"
    assert result["order_type"] == "MARKET"


def test_limit_requires_price():
    with pytest.raises(ValidationError, match="price"):
        validate_order("BTCUSDT", "BUY", "LIMIT", 0.001)


def test_stop_requires_stop_price():
    with pytest.raises(ValidationError, match="stop-price"):
        validate_order("BTCUSDT", "BUY", "STOP", 0.001, price=66000)


def test_invalid_side_rejected():
    with pytest.raises(ValidationError, match="Side"):
        validate_order("BTCUSDT", "HOLD", "MARKET", 0.001)


def test_invalid_type_rejected():
    with pytest.raises(ValidationError, match="Order type"):
        validate_order("BTCUSDT", "BUY", "SWAP", 0.001)


def test_non_positive_quantity_rejected():
    with pytest.raises(ValidationError, match="Quantity"):
        validate_order("BTCUSDT", "BUY", "MARKET", 0)
