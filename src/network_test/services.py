"""
Trading Services Configuration

This module provides an abstract base class and concrete implementations
for different trading service providers with a common interface.
"""

import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .config import GROWW_CONFIG, UPSTOX_API_CONFIG
from .network import AsyncNetworkClient


@dataclass
class EndpointConfig:
    """Configuration for a specific API endpoint"""
    path: str
    method: str = "GET"
    cache_ttl: int = 30
    use_cache: bool = True
    description: str = ""


@dataclass
class NetworkClientConfig:
    """Configuration for AsyncNetworkClient parameters"""
    base_url: str
    rate_limit: int = 25
    timeout: int = 10
    max_connections: int = 20
    max_retries: int = 3
    cache_ttl: int = 30
    enable_circuit_breaker: bool = True
    default_headers: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for AsyncNetworkClient initialization"""
        return {
            "base_url": self.base_url,
            "rate_limit": self.rate_limit,
            "timeout": self.timeout,
            "max_connections": self.max_connections,
            "max_retries": self.max_retries,
            "cache_ttl": self.cache_ttl,
            "enable_circuit_breaker": self.enable_circuit_breaker,
            "default_headers": self.default_headers or {}
        }


class BaseTradingService(ABC):
    """
    Abstract base class for all trading service implementations.

    This defines the contract that all trading services must implement,
    ensuring consistent behavior and interface across different providers.

    **Key Features:**
    - Unified interface for all trading services
    - Supports dynamic endpoint configuration
    - Flexible authentication and headers
    - Async context manager support

    **Kwargs and Configuration:**
    - All services accept configuration via a `config` dict or as keyword arguments.
    - Common kwargs include:
        - base_url (str): Base URL for the API
        - rate_limit (int): Requests per second
        - timeout (int): Request timeout (seconds)
        - max_connections (int): Max concurrent connections
        - max_retries (int): Max retry attempts
        - cache_ttl (int): Default cache time-to-live (seconds)
        - enable_circuit_breaker (bool): Enable circuit breaker
        - default_headers (dict): Default HTTP headers
        - endpoints (dict): Custom endpoint definitions
    - Any unknown kwargs are passed to the underlying AsyncNetworkClient.

    **Endpoint Usage:**
    - Endpoints are defined as EndpointConfig objects, with support for path parameters (e.g., `/v2/market/timings/{date}`)
    - Use `call_endpoint(endpoint_name, path_params=..., query_params=..., json_data=..., **kwargs)` to invoke endpoints.
    - Path parameters are substituted using the `path_params` dict.
    - Query parameters and JSON payloads are passed as `query_params` and `json_data`.

    **Example:**
        service = UpstoxService()
        await service.call_endpoint(
            "market_timing",
            path_params={"date": "2025-10-20"},
            query_params={"foo": "bar"}
        )

    **Extending:**
    - Subclass BaseTradingService to implement new providers.
    - Override authentication, endpoint, and config methods as needed.
    """

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 **client_overrides):
        """
        Initialize the trading service with configurable parameters.

        Args:
            config: Configuration dictionary (uses service default if None)
            **client_overrides: Override any AsyncNetworkClient parameters
        """
        # Get default configuration for this service
        default_config = self.get_default_config()

        # Start with default configuration
        self.config = (config or default_config).copy()

        # Handle custom endpoints from config
        if "endpoints" in self.config:
            self._load_custom_endpoints(self.config["endpoints"])

        # Override with any provided parameters
        client_params = {k: v for k, v in client_overrides.items()
                        if k not in ["endpoints"]}
        self.config.update(client_params)

        # Build headers with service-specific authentication
        base_headers = self._build_default_headers()

        # Add custom headers from config
        if "default_headers" in self.config:
            base_headers.update(self.config["default_headers"])

        # Apply authentication headers
        self._apply_authentication(base_headers)

        # Prepare client configuration
        client_config = NetworkClientConfig(
            base_url=self.config.get("base_url", self.get_default_base_url()),
            rate_limit=self.config.get("rate_limit", 25),
            timeout=self.config.get("timeout", 10),
            max_connections=self.config.get("max_connections", 20),
            max_retries=self.config.get("max_retries", 3),
            cache_ttl=self.config.get("cache_ttl", 30),
            enable_circuit_breaker=self.config.get("enable_circuit_breaker", True),
            default_headers=base_headers
        )

        # Initialize the network client with configuration
        self.client = AsyncNetworkClient(**client_config.to_dict())

    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """Return the default configuration for this service."""

    @abstractmethod
    def get_default_base_url(self) -> str:
        """Return the default base URL for this service."""

    @abstractmethod
    def get_service_endpoints(self) -> Dict[str, EndpointConfig]:
        """Return the predefined endpoints for this service."""

    def _build_default_headers(self) -> Dict[str, str]:
        """Build default headers for this service. Override if needed."""
        return {
            "User-Agent": "NetworkTest/1.0",
            "Accept": "application/json",
        }

    def _apply_authentication(self, headers: Dict[str, str]) -> None:
        """
        Apply authentication to headers. Override in subclasses.

        This method is called during service initialization to add authentication
        headers based on the service's configuration.

        Common authentication patterns:
        - Bearer tokens: headers["Authorization"] = f"Bearer {token}"
        - API keys: headers["X-API-Key"] = api_key
        - Basic auth: headers["Authorization"] = f"Basic {encoded_credentials}"
        - Custom headers: headers["Custom-Auth"] = auth_value

        Args:
            headers: Dictionary of headers to modify with authentication
        """

    def _add_bearer_token(self, headers: Dict[str, str], token: str) -> None:
        """Helper method to add Bearer token authentication."""
        if token:
            headers["Authorization"] = f"Bearer {token}"

    def _add_api_key_header(self, headers: Dict[str, str], key: str, header_name: str = "X-API-Key") -> None:
        """Helper method to add API key to headers."""
        if key:
            headers[header_name] = key

    def _add_basic_auth(self, headers: Dict[str, str], username: str, password: str) -> None:
        """Helper method to add Basic authentication."""
        if username and password:
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"

    def _add_custom_auth(self, headers: Dict[str, str], auth_config: Dict[str, str]) -> None:
        """Helper method to add custom authentication headers from config."""
        for header_name, value in auth_config.items():
            if value:
                headers[header_name] = value

    def _load_custom_endpoints(self, endpoints_config: Dict[str, Any]) -> None:
        """Load custom endpoints from configuration."""
        for name, config in endpoints_config.items():
            endpoint_config = EndpointConfig(
                path=config.get("path", ""),
                method=config.get("method", "GET"),
                cache_ttl=config.get("cache_ttl", 30),
                use_cache=config.get("use_cache", True),
                description=config.get("description", f"Custom endpoint: {name}")
            )
            # Add to service endpoints dynamically
            service_endpoints = self.get_service_endpoints()
            service_endpoints[name] = endpoint_config

    async def __aenter__(self):
        """Async context manager entry"""
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def call_endpoint(self,
                          endpoint_name: str,
                          path_params: Optional[Dict[str, str]] = None,
                          query_params: Optional[Dict[str, Any]] = None,
                          json_data: Optional[Dict[str, Any]] = None,
                          **kwargs) -> Any:
        """
        Call a predefined endpoint with proper configuration.

        Args:
            endpoint_name: Name of the endpoint from service endpoints
            path_params: Parameters to substitute in the path
            query_params: Query parameters
            json_data: JSON payload for POST/PUT requests
            **kwargs: Override endpoint configuration

        Returns:
            API response data
        """
        endpoints = self.get_service_endpoints()

        if endpoint_name not in endpoints:
            raise ValueError(f"Unknown endpoint: {endpoint_name}. Available: {list(endpoints.keys())}")

        config = endpoints[endpoint_name]

        # Build the endpoint path with parameter substitution
        endpoint_path = config.path
        if path_params:
            endpoint_path = endpoint_path.format(**path_params)

        # Use endpoint config with optional overrides
        request_config = {
            "method": config.method,
            "endpoint": endpoint_path,
            "params": query_params,
            "json_data": json_data,
            "use_cache": config.use_cache,
            "cache_ttl": config.cache_ttl,
            **kwargs  # Allow overriding any config
        }

        return await self.client.request(**request_config)

    def list_endpoints(self) -> Dict[str, str]:
        """List all available endpoints with descriptions"""
        endpoints = self.get_service_endpoints()
        return {name: config.description for name, config in endpoints.items()}


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
        except ImportError:
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


class GrowwService(BaseTradingService):
    """
    Groww Service implementation for market data endpoints.

    Provides access to Groww API endpoints with proper authentication,
    rate limiting, caching, and error handling.
    """

    _ENDPOINTS = {
        "nifty_data": EndpointConfig(
            path="v1/api/stocks_data/v1/accord_points/exchange/NSE/segment/CASH/latest_indices_ohlc/{index_name}",
            method="GET",
            cache_ttl=60,
            description="Get Nifty index data"
        ),
        "live_aggregated": EndpointConfig(
            path="v1/api/stocks_data/v1/tr_live_delayed/segment/CASH/latest_aggregated",
            method="POST",
            cache_ttl=5,
            description="Get live aggregated market data"
        ),
    }

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Groww service."""
        try:
            return GROWW_CONFIG
        except ImportError:
            # Fallback to minimal config if config.py doesn't exist
            return {
                'base_url': 'https://groww.in/',
                'rate_limit': 50,
                'timeout': 5
            }

    def get_default_base_url(self) -> str:
        """Get default base URL for Groww API."""
        return 'https://groww.in/'

    def get_service_endpoints(self) -> Dict[str, EndpointConfig]:
        """Get service-specific endpoint configurations."""
        return self._ENDPOINTS

    def _apply_authentication(self, headers: Dict[str, str]) -> None:
        """Apply Groww-specific authentication."""
        # Groww typically uses session-based auth or custom headers
        session_token = self.config.get("session_token")
        user_agent = self.config.get("user_agent")

        if session_token:
            headers["X-Session-Token"] = session_token

        # Groww might require specific user agents or cookies
        if user_agent:
            headers["User-Agent"] = user_agent

        # Add any custom auth headers from config
        auth_headers = self.config.get("auth_headers", {})
        self._add_custom_auth(headers, auth_headers)

    # Convenient methods for common operations (specific to Groww)
    async def get_nifty_data(self, index_name: str = "BANKNIFTY"):
        """Get Nifty index data"""
        return await self.call_endpoint("nifty_data", path_params={"index_name": index_name})

    async def get_live_aggregated(self):
        """Get live aggregated market data"""
        return await self.call_endpoint("live_aggregated", json_data={})


class CustomAPIService(BaseTradingService):
    """
    CustomAPIService allows you to create a service for any API on the fly.

    **Features:**
    - Define your own base_url and endpoints at runtime
    - All BaseTradingService features (rate limiting, retries, caching, etc.)
    - Pass any supported kwargs to customize the network client

    **Kwargs and Configuration:**
    - base_url (str): The base URL for your API (required)
    - endpoints (dict): Dictionary of endpoint configs (required)
    - rate_limit (int): Requests per second (default: 10)
    - timeout (int): Request timeout (seconds, default: 30)
    - cache_ttl (int): Default cache time-to-live (seconds, default: 60)
    - Any other kwargs are passed to AsyncNetworkClient

    **Endpoint Usage:**
    - Endpoints are defined as a dict of name -> config dict
    - Each config dict can have: path, method, cache_ttl, use_cache, description
    - Path parameters are substituted using path_params in call_endpoint

    **Example:**
        my_endpoints = {
            "market_hours": {
                "path": "/v2/market/timings/{date}",
                "method": "POST",
                "cache_ttl": 300,
                "description": "Get market hours"
            }
        }
        async with CustomAPIService(
            base_url="https://api.upstox.com",
            endpoints=my_endpoints,
            rate_limit=5
        ) as service:
            data = await service.call_endpoint(
                "market_hours",
                path_params={"date": "2025-10-20"}
            )

    **Notes:**
    - All endpoint configs support path parameter substitution.
    - You can add or modify endpoints at runtime via `self.custom_endpoints`.
    - See BaseTradingService for more details on kwargs and usage.
    """

    def __init__(self, base_url: str, endpoints: Dict[str, Dict[str, Any]], **kwargs):
        """
        Create a custom service with your own base URL and endpoints

        Args:
            base_url: The base URL for your API
            endpoints: Dictionary of endpoint configurations
            **kwargs: Additional client parameters
        """
        self.custom_base_url = base_url
        self.custom_endpoints = {}

        # Convert endpoint configs to EndpointConfig objects
        for name, config in endpoints.items():
            self.custom_endpoints[name] = EndpointConfig(
                path=config.get("path", ""),
                method=config.get("method", "GET"),
                cache_ttl=config.get("cache_ttl", 30),
                use_cache=config.get("use_cache", True),
                description=config.get("description", f"Custom endpoint: {name}")
            )

        super().__init__(**kwargs)

    def get_default_config(self) -> Dict[str, Any]:
        """Default configuration for custom service"""
        return {
            'base_url': self.custom_base_url,
            'rate_limit': 10,
            'timeout': 30,
            'cache_ttl': 60
        }

    def get_default_base_url(self) -> str:
        """Return the custom base URL"""
        return self.custom_base_url

    def get_service_endpoints(self) -> Dict[str, EndpointConfig]:
        """Return custom endpoints"""
        return self.custom_endpoints

    def _apply_authentication(self, headers: Dict[str, str]) -> None:
        """Apply flexible authentication based on config."""
        auth_config = self.config.get("auth", {})

        # Support different auth types
        auth_type = auth_config.get("type", "none")

        if auth_type == "bearer":
            token = auth_config.get("token")
            self._add_bearer_token(headers, token)

        elif auth_type == "api_key":
            key = auth_config.get("key")
            header_name = auth_config.get("header_name", "X-API-Key")
            self._add_api_key_header(headers, key, header_name)

        elif auth_type == "basic":
            username = auth_config.get("username")
            password = auth_config.get("password")
            self._add_basic_auth(headers, username, password)

        elif auth_type == "custom":
            custom_headers = auth_config.get("headers", {})
            self._add_custom_auth(headers, custom_headers)

        # Also support direct auth config (backwards compatibility)
        if "access_token" in self.config:
            self._add_bearer_token(headers, self.config["access_token"])
        if "api_key" in self.config:
            self._add_api_key_header(headers, self.config["api_key"])


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

    **Example:**
        xts_config = {
            "interactive_base_url": "https://developers.symphonyfintech.in/interactive/",
            "market_base_url": "https://developers.symphonyfintech.in/marketdata/",
            "user_id": "your_user_id",
            "password": "your_password",
            "public_key": "your_public_key",
            "private_key": "your_private_key",
            "source": "WebAPI"
        }

        async with XTSService(config=xts_config) as xts:
            # Login to both APIs
            await xts.login_interactive()
            await xts.login_market()

            # Use Interactive API
            orders = await xts.call_endpoint("orders")

            # Use Market Data API
            quotes = await xts.call_endpoint("market.instruments.quotes",
                                           query_params={"instruments": "26000"})
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
        "order.status": EndpointConfig(
            path="/orders",
            method="GET",
            cache_ttl=1,
            description="Get order status"
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
        "order.cancelall": EndpointConfig(
            path="/orders/cancelall",
            method="DELETE",
            use_cache=False,
            description="Cancel all orders"
        ),
        "order.history": EndpointConfig(
            path="/orders",
            method="GET",
            cache_ttl=30,
            description="Get order history"
        ),

        # Bracket Orders
        "bracketorder.place": EndpointConfig(
            path="/orders/bracket",
            method="POST",
            use_cache=False,
            description="Place bracket order"
        ),
        "bracketorder.modify": EndpointConfig(
            path="/orders/bracket",
            method="PUT",
            use_cache=False,
            description="Modify bracket order"
        ),
        "bracketorder.cancel": EndpointConfig(
            path="/orders/bracket",
            method="DELETE",
            use_cache=False,
            description="Cancel bracket order"
        ),

        # Cover Orders
        "order.place.cover": EndpointConfig(
            path="/orders/cover",
            method="POST",
            use_cache=False,
            description="Place cover order"
        ),
        "order.exit.cover": EndpointConfig(
            path="/orders/cover",
            method="DELETE",
            use_cache=False,
            description="Exit cover order"
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
        "portfolio.positions.convert": EndpointConfig(
            path="/portfolio/positions/convert",
            method="PUT",
            use_cache=False,
            description="Convert position (MIS to CNC, etc.)"
        ),
        "portfolio.squareoff": EndpointConfig(
            path="/portfolio/squareoff",
            method="DELETE",
            use_cache=False,
            description="Square off positions"
        ),
        "portfolio.dealerpositions": EndpointConfig(
            path="/portfolio/dealerpositions",
            method="GET",
            cache_ttl=10,
            description="Get dealer positions"
        ),

        # Dealer Orders
        "order.dealer.status": EndpointConfig(
            path="/orders/dealerorderbook",
            method="GET",
            cache_ttl=5,
            description="Get dealer order book"
        ),
        "dealer.trades": EndpointConfig(
            path="/orders/dealertradebook",
            method="GET",
            cache_ttl=5,
            description="Get dealer trade book"
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

        # Configuration
        "market.config": EndpointConfig(
            path="/apimarketdata/config/clientConfig",
            method="GET",
            cache_ttl=3600,
            description="Get client configuration"
        ),

        # Instruments
        "market.instruments.master": EndpointConfig(
            path="/apimarketdata/instruments/master",
            method="GET",
            cache_ttl=86400,  # Master data changes rarely
            description="Get instruments master data"
        ),
        "market.instruments.subscription": EndpointConfig(
            path="/apimarketdata/instruments/subscription",
            method="POST",
            use_cache=False,
            description="Subscribe to instruments"
        ),
        "market.instruments.unsubscription": EndpointConfig(
            path="/apimarketdata/instruments/subscription",
            method="DELETE",
            use_cache=False,
            description="Unsubscribe from instruments"
        ),
        "market.instruments.ohlc": EndpointConfig(
            path="/apimarketdata/instruments/ohlc",
            method="GET",
            cache_ttl=60,
            description="Get OHLC data"
        ),
        "market.instruments.indexlist": EndpointConfig(
            path="/apimarketdata/instruments/indexlist",
            method="GET",
            cache_ttl=300,
            description="Get index list"
        ),
        "market.instruments.quotes": EndpointConfig(
            path="/apimarketdata/instruments/quotes",
            method="GET",
            cache_ttl=1,
            description="Get real-time quotes"
        ),

        # Search
        "market.search.instrumentsbyid": EndpointConfig(
            path="/apimarketdata/search/instrumentsbyid",
            method="GET",
            cache_ttl=300,
            description="Search instruments by ID"
        ),
        "market.search.instrumentsbystring": EndpointConfig(
            path="/apimarketdata/search/instruments",
            method="GET",
            cache_ttl=300,
            description="Search instruments by string"
        ),

        # Instrument Details
        "market.instruments.instrument.series": EndpointConfig(
            path="/apimarketdata/instruments/instrument/series",
            method="GET",
            cache_ttl=3600,
            description="Get instrument series"
        ),
        "market.instruments.instrument.equitysymbol": EndpointConfig(
            path="/apimarketdata/instruments/instrument/symbol",
            method="GET",
            cache_ttl=3600,
            description="Get equity symbol details"
        ),
        "market.instruments.instrument.futuresymbol": EndpointConfig(
            path="/apimarketdata/instruments/instrument/futureSymbol",
            method="GET",
            cache_ttl=3600,
            description="Get future symbol details"
        ),
        "market.instruments.instrument.optionsymbol": EndpointConfig(
            path="/apimarketdata/instruments/instrument/optionsymbol",
            method="GET",
            cache_ttl=3600,
            description="Get option symbol details"
        ),
        "market.instruments.instrument.optiontype": EndpointConfig(
            path="/apimarketdata/instruments/instrument/optionType",
            method="GET",
            cache_ttl=3600,
            description="Get option type details"
        ),
        "market.instruments.instrument.expirydate": EndpointConfig(
            path="/apimarketdata/instruments/instrument/expiryDate",
            method="GET",
            cache_ttl=3600,
            description="Get expiry date details"
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

    async def logout_interactive(self) -> Dict[str, Any]:
        """Logout from Interactive API."""
        response = await self.call_endpoint("user.logout")
        self.interactive_token = None
        self.is_interactive_logged_in = False

        # Remove token from headers
        self.client.default_headers.pop("authorization", None)

        return response

    async def logout_market(self) -> Dict[str, Any]:
        """Logout from Market Data API."""
        response = await self.call_endpoint("market.logout")
        self.market_token = None
        self.is_market_logged_in = False

        # Remove token from headers
        self.client.default_headers.pop("x-market-token", None)

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
