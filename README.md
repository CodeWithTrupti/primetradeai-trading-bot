# Simplified Trading Bot — Binance Futures Testnet (USDT-M)

A small, well-structured Python CLI that places **Market**, **Limit**, and
**Stop-Limit** orders on the [Binance Futures Testnet](https://testnet.binancefuture.com)
using direct, HMAC-signed REST calls. It validates input, prints clear order
summaries and responses, and logs every request/response/error to a file.

## Features

- Order types: **MARKET**, **LIMIT**, and **STOP** (stop-limit) — bonus third type.
- **Interactive mode** — a guided, menu-driven prompt flow with per-field
  validation and re-prompts (bonus: enhanced CLI UX).
- Both sides: **BUY** and **SELL**.
- CLI input validation (symbol, side, type, quantity, price rules).
- Clear output: request summary → order response (`orderId`, `status`,
  `executedQty`, `avgPrice`) → success/failure message.
- Structured code: separate **client/API layer** and **CLI layer**.
- Logging of API requests, responses, and errors to `logs/trading_bot.log`
  (secret and signature are redacted).
- Robust exception handling: invalid input, Binance API errors, and network
  failures each produce a distinct message and exit code.
- `--dry-run` mode to validate and preview the payload without any API call.

## Project structure

```
primetradeai_application/
├── bot/
│   ├── __init__.py
│   ├── client.py          # BinanceFuturesClient — signed REST wrapper
│   ├── orders.py          # order-param builders + place_order dispatcher
│   ├── validators.py      # CLI input validation
│   └── logging_config.py  # file (DEBUG) + console (INFO) logging
├── tests/
│   ├── test_orders.py     # pure-function tests (no network)
│   └── test_validators.py
├── cli.py                 # argparse entry point
├── logs/                  # trading_bot.log is written here
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. **Register & activate** a Binance Futures Testnet account at
   <https://testnet.binancefuture.com>, then generate an **API Key / Secret**
   (top-right → *API Key* panel on the testnet site).

2. **Install dependencies** (Python 3.9+):

   ```bash
   python -m venv .venv
   # Windows PowerShell:  .venv\Scripts\Activate.ps1
   # macOS/Linux:         source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure credentials** — copy the template and fill in your keys:

   ```bash
   cp .env.example .env      # Windows: copy .env.example .env
   ```

   ```dotenv
   BINANCE_API_KEY=your_testnet_api_key
   BINANCE_API_SECRET=your_testnet_api_secret
   ```

   `.env` is gitignored so your keys are never committed.

## Usage

```
python cli.py <symbol> <side> <type> <quantity> [--price P] [--stop-price S] [--dry-run]
```

| Argument       | Description                                    | Required for      |
|----------------|------------------------------------------------|-------------------|
| `symbol`       | Trading pair, e.g. `BTCUSDT`                    | all               |
| `side`         | `BUY` or `SELL`                                | all               |
| `type`         | `MARKET`, `LIMIT`, or `STOP` (stop-limit)      | all               |
| `quantity`     | Order quantity (> 0)                           | all               |
| `--price`      | Limit price                                    | `LIMIT`, `STOP`   |
| `--stop-price` | Trigger price                                  | `STOP`            |
| `--dry-run`    | Validate & print payload, skip the API call    | optional          |

### Examples

```bash
# Market buy
python cli.py BTCUSDT BUY MARKET 0.001

# Limit sell
python cli.py BTCUSDT SELL LIMIT 0.001 --price 65000

# Stop-limit buy (triggers at 65500, places a limit at 66000)
python cli.py BTCUSDT BUY STOP 0.001 --price 66000 --stop-price 65500

# Validate without hitting the API (no keys needed)
python cli.py BTCUSDT BUY MARKET 0.001 --dry-run
```

### Interactive mode

Run with no arguments (or `-i` / `--interactive`) for a guided flow that prompts
for each field, validates immediately, and re-prompts on bad input:

```bash
python cli.py            # or:  python cli.py --interactive
```

```
=== Binance Futures Testnet - Interactive Order Entry ===
Symbol (e.g. BTCUSDT): BTCUSDT
Side:
  1) BUY
  2) SELL
  Select (number or name): 1
Order type:
  1) MARKET
  2) LIMIT
  3) STOP
  Select (number or name): 1
Quantity: 0.001
Dry run? (validate only, no API call) [y/N]: n
```

### Example output

```
=== Order Request Summary ===
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
=============================

=== Order Response ===
  Order ID    : 4021948373
  Status      : NEW
  Executed Qty: 0.001
  Avg Price   : 65012.30
======================

SUCCESS: order submitted to Binance Futures Testnet.
```

## Generating the deliverable log files

Run one MARKET and one LIMIT order against the testnet — both append to
`logs/trading_bot.log`:

```bash
python cli.py BTCUSDT BUY  MARKET 0.001
python cli.py BTCUSDT SELL LIMIT  0.001 --price 50000
```

The log records each request (params, with secret/signature redacted), the raw
Binance response, and any errors.

## Running the tests

```bash
pip install pytest
pytest -q
```

The tests cover the order-parameter builders and input validators and require
no network access.

## Exit codes

| Code | Meaning                          |
|------|----------------------------------|
| 0    | Success (or successful dry-run)  |
| 1    | Unexpected error                 |
| 2    | Invalid input (validation)       |
| 3    | Binance API error                |
| 4    | Network / client error           |

## Assumptions & notes

- **Testnet only.** The base URL defaults to `https://testnet.binancefuture.com`
  and can be overridden with `BINANCE_BASE_URL`.
- The account must hold testnet USDT margin; testnet balances reset periodically.
- `quantity` and `price` must satisfy each symbol's lot-size / tick-size and
  minimum-notional filters, or Binance rejects the order (surfaced as a clear
  API error). Values in the examples may need adjusting to current testnet
  prices.
- **Stop-limit** is implemented as Binance order `type=STOP`: a limit order
  (`price`) that activates once the market reaches `stopPrice`.
- The request timestamp uses local system time; keep your clock in sync or
  Binance may reject requests with a timestamp error.
```
