"""
Custom API Service Implementation

This service allows you to create a service for any API on the fly with custom endpoints.
"""

from typing import Any, Dict

from .base_service import BaseTradingService
from .models import EndpointConfig


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

    def get_service_name(self) -> str:
        """Return the service name identifier"""
        return "custom"

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
