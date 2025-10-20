"""
Base Trading Service Implementation

This module provides the abstract base class for all trading service implementations.
It implements the ITradingService interface and provides common functionality.
"""

import base64
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..network import AsyncNetworkClient
from .interface import ITradingService
from .models import EndpointConfig, NetworkClientConfig
from .scalable_architecture import (StandardizedOperationsMixin)


class BaseTradingService(ITradingService, StandardizedOperationsMixin, ABC):
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
    - Use `call_endpoint(endpoint_name, path_params=, query_params=, json_data=, **kwargs)` to invoke endpoints.
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

        # Initialize standardized operations support
        self.__init_standardized_operations__(self.get_service_name())

    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """Return the default configuration for this service."""


    @abstractmethod
    def get_default_base_url(self) -> str:
        """Return the default base URL for this service."""


    @abstractmethod
    def get_service_endpoints(self) -> Dict[str, EndpointConfig]:
        """Return the predefined endpoints for this service."""


    @abstractmethod
    def get_service_name(self) -> str:
        """Return the service name identifier."""


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

    def list_endpoints(self) -> Dict[str, Any]:
        """List all available endpoints with descriptions"""
        endpoints = self.get_service_endpoints()
        return {name: config.description for name, config in endpoints.items()}

    # Note: Standardized operations are now handled by StandardizedOperationsMixin

    async def close(self) -> None:
        """Close the service and clean up resources."""
        if hasattr(self, 'client'):
            await self.client.__aexit__(None, None, None)
