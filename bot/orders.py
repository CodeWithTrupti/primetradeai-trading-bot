"""Order-parameter builders and the place-order dispatcher.

The ``build_*`` functions are pure (no I/O): given validated inputs they
return the exact parameter dict Binance's ``/fapi/v1/order`` endpoint expects.
That makes them trivial to unit-test without touching the network.
"""

from typing import Any, Dict, Optional

from .client import BinanceFuturesClient
from .logging_config import get_logger

logger = get_logger()


def build_market_order(symbol: str, side: str, quantity: float) -> Dict[str, Any]:
    return {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": quantity,
    }


def build_limit_order(
    symbol: str, side: str, quantity: float, price: float
) -> Dict[str, Any]:
    return {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": quantity,
        "price": price,
    }


def build_stop_limit_order(
    symbol: str, side: str, quantity: float, price: float, stop_price: float
) -> Dict[str, Any]:
    """Stop-limit: a LIMIT order (``price``) that triggers at ``stop_price``."""
    return {
        "symbol": symbol,
        "side": side,
        "type": "STOP",
        "timeInForce": "GTC",
        "quantity": quantity,
        "price": price,
        "stopPrice": stop_price,
    }


def build_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> Dict[str, Any]:
    """Dispatch to the right builder based on ``order_type``."""
    if order_type == "MARKET":
        return build_market_order(symbol, side, quantity)
    if order_type == "LIMIT":
        return build_limit_order(symbol, side, quantity, price)
    if order_type == "STOP":
        return build_stop_limit_order(symbol, side, quantity, price, stop_price)
    raise ValueError(f"Unsupported order type: {order_type}")


def place_order(
    client: BinanceFuturesClient, params: Dict[str, Any]
) -> Dict[str, Any]:
    """Send a prepared order-parameter dict to Binance and return the response."""
    return client.place_order(params)
