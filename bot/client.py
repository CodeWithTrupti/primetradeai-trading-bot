"""Binance Futures (USDT-M) Testnet REST client.

A thin, signed wrapper around the parts of the ``/fapi`` API this bot needs.
All requests are signed with HMAC-SHA256 and every call is logged (with the
API secret and signature redacted) to make behaviour auditable.
"""

import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .logging_config import get_logger

logger = get_logger()

DEFAULT_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_TIMEOUT = 10  # seconds
RECV_WINDOW = 5000  # ms Binance tolerance window for the request timestamp


class BinanceAPIError(Exception):
    """Raised when Binance returns an error payload (a ``code``/``msg``)."""

    def __init__(self, code: int, msg: str, status_code: Optional[int] = None):
        self.code = code
        self.msg = msg
        self.status_code = status_code
        super().__init__(f"Binance API error {code}: {msg}")


class BinanceClientError(Exception):
    """Raised for network/transport failures (timeouts, connection errors)."""


class BinanceFuturesClient:
    """Minimal signed client for the Binance USDT-M Futures Testnet."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        if not api_key or not api_secret:
            raise BinanceClientError(
                "API key and secret are required. Set them in your .env file."
            )
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": api_key})

    # -- internal helpers -------------------------------------------------

    def _sign(self, query_string: str) -> str:
        """Return the HMAC-SHA256 signature for a query string."""
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _redact(params: Dict[str, Any]) -> Dict[str, Any]:
        """Copy of params safe for logging (signature hidden)."""
        safe = dict(params)
        if "signature" in safe:
            safe["signature"] = "***redacted***"
        return safe

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Any:
        params = dict(params or {})
        url = f"{self.base_url}{path}"

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = RECV_WINDOW
            query = urlencode(params)
            params["signature"] = self._sign(query)

        logger.debug(
            "Request %s %s params=%s", method, path, self._redact(params)
        )

        try:
            response = self.session.request(
                method, url, params=params, timeout=self.timeout
            )
        except requests.exceptions.Timeout as exc:
            logger.error("Request to %s timed out after %ss", url, self.timeout)
            raise BinanceClientError(f"Request timed out: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            logger.error("Network error calling %s: %s", url, exc)
            raise BinanceClientError(f"Network error: {exc}") from exc

        return self._handle_response(response)

    @staticmethod
    def _handle_response(response: requests.Response) -> Any:
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if response.status_code != 200:
            if isinstance(payload, dict) and "code" in payload:
                logger.error(
                    "API error %s: %s (HTTP %s)",
                    payload.get("code"),
                    payload.get("msg"),
                    response.status_code,
                )
                raise BinanceAPIError(
                    code=payload["code"],
                    msg=payload.get("msg", "Unknown error"),
                    status_code=response.status_code,
                )
            logger.error("HTTP %s: %s", response.status_code, response.text)
            raise BinanceClientError(
                f"HTTP {response.status_code}: {response.text}"
            )

        logger.debug("Response: %s", payload)
        return payload

    # -- public API -------------------------------------------------------

    def ping(self) -> Dict[str, Any]:
        """Connectivity check (unsigned)."""
        return self._request("GET", "/fapi/v1/ping")

    def get_exchange_info(self) -> Dict[str, Any]:
        """Full exchange metadata (unsigned) — used to validate symbols."""
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def place_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a new order. ``params`` should come from ``bot.orders``."""
        logger.info(
            "Placing order: %s %s %s qty=%s",
            params.get("side"),
            params.get("type"),
            params.get("symbol"),
            params.get("quantity"),
        )
        return self._request("POST", "/fapi/v1/order", params, signed=True)
