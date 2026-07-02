"""Input validation for CLI order parameters.

Kept free of any network/API dependency so it can be unit-tested in isolation
and reused by any front-end (CLI today, a UI tomorrow).
"""

from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_TYPES = {"MARKET", "LIMIT", "STOP"}


class ValidationError(Exception):
    """Raised when user-supplied order parameters are invalid."""


def validate_symbol(symbol: str) -> str:
    if not symbol or not symbol.strip():
        raise ValidationError("Symbol is required (e.g. BTCUSDT).")
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValidationError(f"Symbol '{symbol}' contains invalid characters.")
    return symbol


def validate_side(side: str) -> str:
    side = (side or "").strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Side must be one of {sorted(VALID_SIDES)}, got '{side}'."
        )
    return side


def validate_order_type(order_type: str) -> str:
    order_type = (order_type or "").strip().upper()
    if order_type not in VALID_TYPES:
        raise ValidationError(
            f"Order type must be one of {sorted(VALID_TYPES)}, got '{order_type}'."
        )
    return order_type


def validate_quantity(quantity: float) -> float:
    if quantity is None or quantity <= 0:
        raise ValidationError(f"Quantity must be greater than 0, got {quantity}.")
    return quantity


def validate_price(price: Optional[float], *, field: str = "price") -> float:
    if price is None or price <= 0:
        raise ValidationError(f"{field} must be greater than 0, got {price}.")
    return price


def validate_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> dict:
    """Validate a full order request and return normalised values.

    ``price`` is required for LIMIT and STOP orders; ``stop_price`` is required
    for STOP (stop-limit) orders.
    """
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    quantity = validate_quantity(quantity)

    if order_type in ("LIMIT", "STOP"):
        price = validate_price(price, field="price")
    if order_type == "STOP":
        stop_price = validate_price(stop_price, field="stop-price")

    return {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "price": price,
        "stop_price": stop_price,
    }
