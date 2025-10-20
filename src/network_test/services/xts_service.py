"""
XTS Service Implementation

XTS (Symphony Fintech) Trading Service implementation that provides separate
Interactive API (trading) and Market Data API endpoints.
"""

from typing import Any, Dict, Optional

from .base_service import BaseTradingService
from .models import EndpointConfig


class XTSService(BaseTradingService):
    """
    XTS (Symphony Fintech) Trading Service implementation.

    XTS provides separate Interactive API (trading) and Market Data API endpoints.
    This service supports both APIs with proper authentication and endpoint management.

    **Features:**
    - Interactive API: Trading, orders, portfolio, positions
    - Market Data API: Real-time quotes, OHLC data, instrument master
    - Separate authentication for Interactive and Market Data APIs
    - Comprehensive order management (regular, bracket, cover orders)
    - Portfolio and position management
    - Market data subscriptions and quotes

    **Authentication:**
    - Interactive API: Uses session-based authentication after login
    - Market Data API: Separate login with different credentials
    - Both APIs support token-based authentication after login
    """

    # Interactive API endpoints
    _INTERACTIVE_ENDPOINTS = {
        # User Management
        "user.login": EndpointConfig(
            path="/user/session",
            method="POST",
            use_cache=False,
            description="Login to Interactive API"
        ),
        "user.logout": EndpointConfig(
            path="/user/session",
            method="DELETE",
            use_cache=False,
            description="Logout from Interactive API"
        ),
        "user.profile": EndpointConfig(
            path="/user/profile",
            method="GET",
            cache_ttl=3600,
            description="Get user profile information"
        ),
        "user.balance": EndpointConfig(
            path="/user/balance",
            method="GET",
            cache_ttl=60,
            description="Get account balance"
        ),

        # Order Management
        "orders": EndpointConfig(
            path="/orders",
            method="GET",
            cache_ttl=5,
            description="Get all orders"
        ),
        "trades": EndpointConfig(
            path="/orders/trades",
            method="GET",
            cache_ttl=5,
            description="Get all trades"
        ),
        "order.place": EndpointConfig(
            path="/orders",
            method="POST",
            use_cache=False,
            description="Place a new order"
        ),
        "order.modify": EndpointConfig(
            path="/orders",
            method="PUT",
            use_cache=False,
            description="Modify existing order"
        ),
        "order.cancel": EndpointConfig(
            path="/orders",
            method="DELETE",
            use_cache=False,
            description="Cancel an order"
        ),

        # Portfolio & Positions
        "portfolio.positions": EndpointConfig(
            path="/portfolio/positions",
            method="GET",
            cache_ttl=10,
            description="Get portfolio positions"
        ),
        "portfolio.holdings": EndpointConfig(
            path="/portfolio/holdings",
            method="GET",
            cache_ttl=60,
            description="Get portfolio holdings"
        ),
    }

    # Market Data API endpoints
    _MARKET_ENDPOINTS = {
        # Authentication
        "market.login": EndpointConfig(
            path="/apimarketdata/auth/login",
            method="POST",
            use_cache=False,
            description="Login to Market Data API"
        ),
        "market.logout": EndpointConfig(
            path="/apimarketdata/auth/logout",
            method="DELETE",
            use_cache=False,
            description="Logout from Market Data API"
        ),

        # Instruments
        "market.instruments.master": EndpointConfig(
            path="/apimarketdata/instruments/master",
            method="GET",
            cache_ttl=86400,  # Master data changes rarely
            description="Get instruments master data"
        ),
        "market.instruments.quotes": EndpointConfig(
            path="/apimarketdata/instruments/quotes",
            method="GET",
            cache_ttl=1,
            description="Get real-time quotes"
        ),
        "market.instruments.ohlc": EndpointConfig(
            path="/apimarketdata/instruments/ohlc",
            method="GET",
            cache_ttl=60,
            description="Get OHLC data"
        ),

        # Search
        "market.search.instrumentsbystring": EndpointConfig(
            path="/apimarketdata/search/instruments",
            method="GET",
            cache_ttl=300,
            description="Search instruments by string"
        ),
    }

    def __init__(self, **kwargs):
        """Initialize XTS service with dual API support."""
        self.interactive_token = None
        self.market_token = None
        self.is_interactive_logged_in = False
        self.is_market_logged_in = False

        # Combine all endpoints
        self._all_endpoints = {**self._INTERACTIVE_ENDPOINTS, **self._MARKET_ENDPOINTS}

        super().__init__(**kwargs)

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for XTS service."""
        return {
            'interactive_base_url': 'https://developers.symphonyfintech.in/interactive/',
            'market_base_url': 'https://developers.symphonyfintech.in/marketdata/',
            'rate_limit': 10,  # Conservative rate limit
            'timeout': 30,
            'cache_ttl': 60,
            'source': 'WebAPI'
        }

    def get_default_base_url(self) -> str:
        """Get default base URL (Interactive API by default)."""
        return self.config.get('interactive_base_url', 'https://developers.symphonyfintech.in/interactive/')

    def get_service_endpoints(self) -> Dict[str, EndpointConfig]:
        """Get all XTS endpoints (Interactive + Market Data)."""
        return self._all_endpoints

    def get_service_name(self) -> str:
        """Return the service name identifier"""
        return "xts"

    def _apply_authentication(self, headers: Dict[str, str]) -> None:
        """Apply XTS authentication based on current tokens."""
        # Add interactive token if available
        if self.interactive_token:
            headers["authorization"] = self.interactive_token

        # Add market token if available (will be used for market API calls)
        if self.market_token:
            headers["x-market-token"] = self.market_token

        # Add source header (required by XTS)
        source = self.config.get("source", "WebAPI")
        headers["source"] = source

    async def call_endpoint(self,
                          endpoint_name: str,
                          path_params: Optional[Dict[str, str]] = None,
                          query_params: Optional[Dict[str, Any]] = None,
                          json_data: Optional[Dict[str, Any]] = None,
                          **kwargs) -> Any:
        """
        Override call_endpoint to handle dual base URLs.
        Market Data API calls use different base URL.
        """
        # Determine which API this endpoint belongs to
        if endpoint_name.startswith("market."):
            # Use market data base URL
            original_base_url = self.client.base_url
            self.client.base_url = self.config.get('market_base_url',
                                                 'https://developers.symphonyfintech.in/marketdata/')

            try:
                result = await super().call_endpoint(endpoint_name, path_params,
                                                   query_params, json_data, **kwargs)
                return result
            finally:
                # Restore original base URL
                self.client.base_url = original_base_url
        else:
            # Use interactive base URL (default)
            return await super().call_endpoint(endpoint_name, path_params,
                                             query_params, json_data, **kwargs)

    # Authentication convenience methods
    async def login_interactive(self, user_id: Optional[str] = None, password: Optional[str] = None,
                              public_key: Optional[str] = None, private_key: Optional[str] = None) -> Dict[str, Any]:
        """Login to Interactive API."""
        login_data = {
            "userId": user_id or self.config.get("user_id"),
            "password": password or self.config.get("password"),
            "publicKey": public_key or self.config.get("public_key"),
            "privateKey": private_key or self.config.get("private_key"),
            "source": self.config.get("source", "WebAPI")
        }

        response = await self.call_endpoint("user.login", json_data=login_data)

        # Store token for future requests
        if response and "token" in response:
            self.interactive_token = response["token"]
            self.is_interactive_logged_in = True

            # Update client headers
            self.client.default_headers["authorization"] = self.interactive_token

        return response

    async def login_market(self, user_id: Optional[str] = None, password: Optional[str] = None,
                         public_key: Optional[str] = None, private_key: Optional[str] = None) -> Dict[str, Any]:
        """Login to Market Data API."""
        login_data = {
            "userId": user_id or self.config.get("user_id"),
            "password": password or self.config.get("password"),
            "publicKey": public_key or self.config.get("public_key"),
            "privateKey": private_key or self.config.get("private_key"),
            "source": self.config.get("source", "WebAPI")
        }

        response = await self.call_endpoint("market.login", json_data=login_data)

        # Store token for future requests
        if response and "token" in response:
            self.market_token = response["token"]
            self.is_market_logged_in = True

            # Update client headers
            self.client.default_headers["x-market-token"] = self.market_token

        return response

    # Convenience methods for common operations
    async def place_order(self, exchangeSegment: str, exchangeInstrumentID: int,
                         productType: str, orderType: str, orderSide: str,
                         timeInForce: str, disclosedQuantity: int, orderQuantity: int,
                         limitPrice: float = 0, stopPrice: float = 0, **kwargs) -> Dict[str, Any]:
        """Place a regular order."""
        order_data = {
            "exchangeSegment": exchangeSegment,
            "exchangeInstrumentID": exchangeInstrumentID,
            "productType": productType,
            "orderType": orderType,
            "orderSide": orderSide,
            "timeInForce": timeInForce,
            "disclosedQuantity": disclosedQuantity,
            "orderQuantity": orderQuantity,
            "limitPrice": limitPrice,
            "stopPrice": stopPrice,
            **kwargs
        }

        return await self.call_endpoint("order.place", json_data=order_data)

    async def get_quotes(self, instruments: str, xtsMessageCode: int = 1512) -> Dict[str, Any]:
        """Get real-time quotes for instruments."""
        return await self.call_endpoint(
            "market.instruments.quotes",
            query_params={
                "instruments": instruments,
                "xtsMessageCode": xtsMessageCode
            }
        )

    async def search_instruments(self, searchString: str, source: Optional[str] = None) -> Dict[str, Any]:
        """Search instruments by string."""
        return await self.call_endpoint(
            "market.search.instrumentsbystring",
            query_params={
                "searchString": searchString,
                "source": source or self.config.get("source", "WebAPI")
            }
        )
