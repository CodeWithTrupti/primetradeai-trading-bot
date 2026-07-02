"""Unit tests for the pure order-parameter builders (no network)."""

import pytest

from bot.orders import build_order_params


def test_market_order_params():
    params = build_order_params("BTCUSDT", "BUY", "MARKET", 0.001)
    assert params == {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "quantity": 0.001,
    }


def test_limit_order_params():
    params = build_order_params("BTCUSDT", "SELL", "LIMIT", 0.001, price=65000)
    assert params["type"] == "LIMIT"
    assert params["timeInForce"] == "GTC"
    assert params["price"] == 65000


def test_stop_limit_order_params():
    params = build_order_params(
        "BTCUSDT", "BUY", "STOP", 0.001, price=66000, stop_price=65500
    )
    assert params["type"] == "STOP"
    assert params["price"] == 66000
    assert params["stopPrice"] == 65500


def test_unsupported_type_raises():
    with pytest.raises(ValueError):
        build_order_params("BTCUSDT", "BUY", "OCO", 0.001)
