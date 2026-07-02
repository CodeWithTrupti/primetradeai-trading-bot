"""Interactive, menu-driven order entry (bonus: enhanced CLI UX).

Used when ``cli.py`` is run with no positional arguments (or ``--interactive``).
Each field is prompted, validated immediately via ``bot.validators``, and
re-prompted on error, so the user is guided to a valid order. The result is an
``argparse.Namespace`` identical in shape to the flag-based CLI, so it flows
through the exact same ``run()`` path — no duplicated order logic.
"""

import argparse

from .validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_symbol,
)


def _prompt(label: str, validate, *, allow_blank=False):
    """Prompt until ``validate`` accepts the input; return the clean value."""
    while True:
        raw = input(label).strip()
        if allow_blank and raw == "":
            return None
        try:
            return validate(raw)
        except ValidationError as exc:
            print(f"  ! {exc}  Please try again.")


def _prompt_choice(label: str, choices, validate):
    print(f"{label}")
    for i, choice in enumerate(choices, 1):
        print(f"  {i}) {choice}")
    while True:
        raw = input("  Select (number or name): ").strip()
        value = choices[int(raw) - 1] if raw.isdigit() and 1 <= int(raw) <= len(choices) else raw
        try:
            return validate(value)
        except ValidationError as exc:
            print(f"  ! {exc}  Please try again.")


def prompt_order() -> argparse.Namespace:
    """Run the guided flow and return CLI-shaped arguments."""
    print("\n=== Binance Futures Testnet - Interactive Order Entry ===")
    print("(Press Ctrl+C to cancel at any time)\n")

    symbol = _prompt("Symbol (e.g. BTCUSDT): ", validate_symbol)
    side = _prompt_choice("Side:", ["BUY", "SELL"], validate_side)
    order_type = _prompt_choice(
        "Order type:", ["MARKET", "LIMIT", "STOP"], validate_order_type
    )
    quantity = _prompt(
        "Quantity: ", lambda v: validate_quantity(float(v)) if _is_number(v)
        else _raise_number("Quantity")
    )

    price = None
    stop_price = None
    if order_type in ("LIMIT", "STOP"):
        price = _prompt(
            "Limit price: ",
            lambda v: validate_price(float(v), field="price") if _is_number(v)
            else _raise_number("price"),
        )
    if order_type == "STOP":
        stop_price = _prompt(
            "Stop (trigger) price: ",
            lambda v: validate_price(float(v), field="stop-price") if _is_number(v)
            else _raise_number("stop-price"),
        )

    dry = input("Dry run? (validate only, no API call) [y/N]: ").strip().lower()
    dry_run = dry in ("y", "yes")

    return argparse.Namespace(
        symbol=symbol,
        side=side,
        type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
        dry_run=dry_run,
    )


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _raise_number(field: str):
    raise ValidationError(f"{field} must be a number.")
