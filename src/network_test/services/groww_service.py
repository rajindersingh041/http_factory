"""
Groww Service Implementation

This service provides access to Groww API endpoints for market data with proper
authentication, rate limiting, caching, and error handling.
"""

from typing import Any, Dict

from ..config import GROWW_CONFIG
from .base_service import BaseTradingService
from .models import EndpointConfig


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
        except (ImportError, NameError):
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

    def get_service_name(self) -> str:
        """Return the service name identifier"""
        return "groww"

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
