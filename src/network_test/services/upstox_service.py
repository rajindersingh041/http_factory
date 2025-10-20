"""
Upstox Service Implementation

This service provides access to Upstox API endpoints with proper authentication,
rate limiting, caching, and error handling.
"""

from typing import Any, Dict

from ..config import UPSTOX_API_CONFIG
from .base_service import BaseTradingService
from .models import EndpointConfig


class UpstoxService(BaseTradingService):
    """
    Upstox Trading Service implementation.

    Provides access to Upstox API endpoints with proper authentication,
    rate limiting, caching, and error handling.
    """

    # Predefined endpoints with their configurations
    _ENDPOINTS = {
        # Market Data Endpoints
        "candles": EndpointConfig(
            path="chart/open/v3/candles/",
            method="GET",
            cache_ttl=5,  # Stock prices change frequently
            description="Get candlestick data for instruments"
        ),
        "quote": EndpointConfig(
            path="market-quote/quotes",
            method="GET",
            cache_ttl=1,  # Live quotes need minimal caching
            description="Get live quotes for instruments"
        ),
        "market_status": EndpointConfig(
            path="market-quote/market-status/{segment}",
            method="GET",
            cache_ttl=60,  # Market status doesn't change often
            description="Get market status for segment"
        ),

        # Portfolio & Holdings
        "holdings": EndpointConfig(
            path="portfolio/long-term-holdings",
            method="GET",
            cache_ttl=30,
            description="Get long term holdings"
        ),
        "positions": EndpointConfig(
            path="portfolio/short-term-positions",
            method="GET",
            cache_ttl=5,  # Positions can change during trading
            description="Get short term positions"
        ),
        "funds": EndpointConfig(
            path="user/get-funds-and-margin",
            method="GET",
            cache_ttl=10,
            description="Get available funds and margin"
        ),

        # Orders
        "orders": EndpointConfig(
            path="order/retrieve-all",
            method="GET",
            cache_ttl=5,
            description="Get all orders"
        ),
        "place_order": EndpointConfig(
            path="order/place",
            method="POST",
            use_cache=False,  # Never cache order placement
            description="Place a new order"
        ),
        "modify_order": EndpointConfig(
            path="order/modify",
            method="PUT",
            use_cache=False,
            description="Modify existing order"
        ),
        "cancel_order": EndpointConfig(
            path="order/cancel",
            method="DELETE",
            use_cache=False,
            description="Cancel an order"
        ),

        # Historical Data
        "historical_candles": EndpointConfig(
            path="historical-candle/{instrument_key}/{interval}/{to_date}",
            method="GET",
            cache_ttl=300,  # Historical data doesn't change
            description="Get historical candlestick data"
        ),

        # User Profile
        "profile": EndpointConfig(
            path="user/profile",
            method="GET",
            cache_ttl=3600,  # Profile changes rarely
            description="Get user profile information"
        ),
    }

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Upstox service."""
        try:
            return UPSTOX_API_CONFIG
        except (ImportError, NameError):
            # Fallback to minimal config if config.py doesn't exist
            return {
                'base_url': 'https://api.upstox.com/v2/',
                'rate_limit': 100,
                'timeout': 30
            }

    def get_default_base_url(self) -> str:
        """Get default base URL for Upstox API."""
        return 'https://api.upstox.com/v2/'

    def get_service_endpoints(self) -> Dict[str, EndpointConfig]:
        """Get service-specific endpoint configurations."""
        return self._ENDPOINTS

    def get_service_name(self) -> str:
        """Return the service name identifier"""
        return "upstox"

    def _apply_authentication(self, headers: Dict[str, str]) -> None:
        """Apply Upstox-specific authentication."""
        # Get auth config from service config
        access_token = self.config.get("access_token")
        api_key = self.config.get("api_key")

        # Upstox uses Bearer token authentication
        if access_token:
            self._add_bearer_token(headers, access_token)

        # Some Upstox endpoints might need API key in headers
        if api_key:
            self._add_api_key_header(headers, api_key, "X-API-Key")

    # Convenient methods for common operations (specific to Upstox)
    async def get_candles(self,
                         instrument_key: str,
                         interval: str = "I1",
                         from_time: str = "1760977799999",
                         limit: int = 375) -> Dict[str, Any]:
        """Get candlestick data for an instrument"""
        return await self.call_endpoint(
            "candles",
            query_params={
                "instrumentKey": instrument_key,
                "interval": interval,
                "from": from_time,
                "limit": limit
            }
        )

    async def get_quote(self, instrument_key: str) -> Dict[str, Any]:
        """Get live quote for an instrument"""
        return await self.call_endpoint(
            "quote",
            query_params={"instrument_key": instrument_key}
        )

    async def place_order(self,
                         quantity: int,
                         product: str,
                         validity: str,
                         price: float,
                         tag: str,
                         instrument_token: str,
                         order_type: str,
                         transaction_type: str,
                         disclosed_quantity: int = 0,
                         trigger_price: float = 0,
                         is_amo: bool = False) -> Dict[str, Any]:
        """Place a new order"""
        order_data = {
            "quantity": quantity,
            "product": product,
            "validity": validity,
            "price": price,
            "tag": tag,
            "instrument_token": instrument_token,
            "order_type": order_type,
            "transaction_type": transaction_type,
            "disclosed_quantity": disclosed_quantity,
            "trigger_price": trigger_price,
            "is_amo": is_amo
        }

        return await self.call_endpoint("place_order", json_data=order_data)
