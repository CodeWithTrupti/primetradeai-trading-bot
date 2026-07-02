"""Command-line entry point for the Binance Futures Testnet trading bot.

Examples
--------
    python cli.py BTCUSDT BUY MARKET 0.001
    python cli.py BTCUSDT SELL LIMIT 0.001 --price 65000
    python cli.py BTCUSDT BUY STOP 0.001 --price 66000 --stop-price 65500
    python cli.py BTCUSDT BUY MARKET 0.001 --dry-run    # validate only, no API call
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client import (
    BinanceAPIError,
    BinanceClientError,
    BinanceFuturesClient,
)
from bot.logging_config import get_logger
from bot.orders import build_order_params, place_order
from bot.validators import ValidationError, validate_order

logger = get_logger()

BASE_URL = "https://testnet.binancefuture.com"


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Place Market / Limit / Stop-Limit orders on the "
        "Binance USDT-M Futures Testnet.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("symbol", help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("side", help="BUY or SELL")
    parser.add_argument("type", help="MARKET, LIMIT, or STOP (stop-limit)")
    parser.add_argument("quantity", type=float, help="Order quantity (> 0)")
    parser.add_argument(
        "--price",
        type=float,
        default=None,
        help="Limit price (required for LIMIT and STOP orders)",
    )
    parser.add_argument(
        "--stop-price",
        type=float,
        default=None,
        help="Trigger price (required for STOP / stop-limit orders)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the order payload without calling the API",
    )
    return parser.parse_args(argv)


def print_summary(order: dict) -> None:
    print("\n=== Order Request Summary ===")
    print(f"  Symbol     : {order['symbol']}")
    print(f"  Side       : {order['side']}")
    print(f"  Type       : {order['order_type']}")
    print(f"  Quantity   : {order['quantity']}")
    if order.get("price") is not None:
        print(f"  Price      : {order['price']}")
    if order.get("stop_price") is not None:
        print(f"  Stop Price : {order['stop_price']}")
    print("=============================\n")


def print_response(resp: dict) -> None:
    print("=== Order Response ===")
    print(f"  Order ID    : {resp.get('orderId')}")
    print(f"  Status      : {resp.get('status')}")
    print(f"  Executed Qty: {resp.get('executedQty')}")
    # Binance returns avgPrice='0' until (partially) filled.
    avg_price = resp.get("avgPrice")
    if avg_price and avg_price not in ("0", "0.00000"):
        print(f"  Avg Price   : {avg_price}")
    print("======================\n")


def run(args: argparse.Namespace) -> int:
    # 1. Validate & normalise input (raises ValidationError).
    order = validate_order(
        symbol=args.symbol,
        side=args.side,
        order_type=args.type,
        quantity=args.quantity,
        price=args.price,
        stop_price=args.stop_price,
    )
    print_summary(order)

    # 2. Build the exact Binance parameter dict.
    params = build_order_params(
        symbol=order["symbol"],
        side=order["side"],
        order_type=order["order_type"],
        quantity=order["quantity"],
        price=order["price"],
        stop_price=order["stop_price"],
    )

    if args.dry_run:
        logger.info("Dry run - order payload: %s", params)
        print("[DRY RUN] Order payload built and validated; API not called.")
        print(f"          Payload: {params}\n")
        return 0

    # 3. Build the client from environment credentials.
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    base_url = os.getenv("BINANCE_BASE_URL", BASE_URL)
    client = BinanceFuturesClient(api_key, api_secret, base_url=base_url)

    # 4. Place the order.
    resp = place_order(client, params)
    print_response(resp)
    logger.info(
        "Order placed successfully: orderId=%s status=%s",
        resp.get("orderId"),
        resp.get("status"),
    )
    print("SUCCESS: order submitted to Binance Futures Testnet.")
    return 0


def main(argv=None) -> int:
    load_dotenv()
    args = parse_args(argv)
    try:
        return run(args)
    except ValidationError as exc:
        logger.error("Validation error: %s", exc)
        print(f"\nFAILED (invalid input): {exc}", file=sys.stderr)
        return 2
    except BinanceAPIError as exc:
        logger.error("Binance API error: %s", exc)
        print(f"\nFAILED (Binance API): {exc}", file=sys.stderr)
        return 3
    except BinanceClientError as exc:
        logger.error("Client/network error: %s", exc)
        print(f"\nFAILED (network/client): {exc}", file=sys.stderr)
        return 4
    except Exception as exc:  # noqa: BLE001 — last-resort guard for the CLI
        logger.exception("Unexpected error")
        print(f"\nFAILED (unexpected): {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
