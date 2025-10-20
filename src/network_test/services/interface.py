"""
Trading Service Interface

This module defines the contract that all trading services must implement.
The interface ensures consistent behavior across different service providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional



class ITradingService(ABC):
    """
    Interface for all trading service implementations.

    This interface defines the contract that all trading services must implement,
    ensuring consistent behavior and method signatures across different providers.

    **Key Methods:**
    - call_endpoint(): Execute API calls to service endpoints
    - list_endpoints(): Get available endpoints for the service
    - get_service_name(): Get the name identifier of the service
    - close(): Clean up resources and connections

    **Context Manager Support:**
    - All services support async context manager for proper resource cleanup

    **Usage Example:**
        async with service_instance as service:
            result = await service.call_endpoint("endpoint_name",
                                                path_params={"id": "123"})
    """

    @abstractmethod
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
            query_params: Query parameters for the request
            json_data: JSON payload for POST/PUT requests
            **kwargs: Additional parameters to override endpoint config

        Returns:
            API response data

        Raises:
            ValueError: If endpoint_name is not found
            HTTPError: If the API request fails
        """


    @abstractmethod
    def list_endpoints(self) -> Dict[str, Any]:
        """
        Get a dictionary of all available endpoints for this service.

        Returns:
            Dictionary mapping endpoint names to their configurations
        """


    @abstractmethod
    def get_service_name(self) -> str:
        """
        Get the name identifier of the service.

        Returns:
            String identifier for the service (e.g., "upstox", "groww", "custom")
        """


    @abstractmethod
    async def close(self) -> None:
        """
        Close the service and clean up any resources.

        This method should be called when the service is no longer needed
        to properly close network connections and free resources.
        """


    # Standardized trading operations (handled by StandardizedOperationsMixin)
    async def place_order_standard(self, **kwargs) -> Any:
        """
        Place an order using standardized parameters.

        Args:
            **kwargs: Standardized order parameters that will be mapped
                     to broker-specific format automatically

        Returns:
            Order response from the broker
        """
        pass  # Implementation provided by StandardizedOperationsMixin

    async def get_quotes_standard(self, **kwargs) -> Any:
        """
        Get quotes using standardized parameters.

        Args:
            **kwargs: Standardized quote parameters

        Returns:
            Quote data from the broker
        """
        pass  # Implementation provided by StandardizedOperationsMixin

    async def get_historical_data_standard(self, **kwargs) -> Any:
        """
        Get historical data using standardized parameters.

        Args:
            **kwargs: Standardized historical data parameters

        Returns:
            Historical data from the broker
        """
        pass  # Implementation provided by StandardizedOperationsMixin    # Context manager support
    @abstractmethod
    async def __aenter__(self) -> ITradingService:
        """Async context manager entry"""


    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
