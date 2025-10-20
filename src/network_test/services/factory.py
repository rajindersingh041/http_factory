"""
Service Factory

This module provides a factory for creating trading service instances.
The factory supports different service types and configurations.
"""

from typing import Any, Dict, Optional, Type, cast

from .base_service import BaseTradingService
from .custom_service import CustomAPIService
from .groww_service import GrowwService
from .interface import ITradingService
from .upstox_service import UpstoxService
from .xts_service import XTSService


class ServiceFactory:
    """
    Factory class for creating trading service instances.

    This factory provides a unified way to create different types of trading services
    without the application needing to know the specific implementation details.

    **Supported Services:**
    - upstox: Upstox trading platform
    - groww: Groww trading platform
    - custom: Custom API service for any REST API
    - xts: XTS (Symphony Fintech) trading platform

    **Usage Examples:**
        # Create an Upstox service
        service = ServiceFactory.create_service("upstox", access_token="your_token")

        # Create a custom service
        custom_endpoints = {
            "endpoint1": {"path": "/api/v1/data", "method": "GET"}
        }
        service = ServiceFactory.create_service(
            "custom",
            base_url="https://api.example.com",
            endpoints=custom_endpoints
        )

        # Get available service types
        available = ServiceFactory.get_available_services()
    """

    # Registry of available service classes
    _SERVICE_REGISTRY: Dict[str, Type[ITradingService]] = {
        "upstox": UpstoxService,
        "groww": GrowwService,
        "custom": CustomAPIService,
        "xts": XTSService,
    }

    @classmethod
    def create_service(cls,
                      service_type: str,
                      config: Optional[Dict[str, Any]] = None,
                      **kwargs) -> ITradingService:
        """
        Create a trading service instance.

        Args:
            service_type: Type of service to create ("upstox", "groww", "custom", "xts")
            config: Optional configuration dictionary
            **kwargs: Additional configuration parameters

        Returns:
            Trading service instance implementing ITradingService

        Raises:
            ValueError: If service_type is not supported
            TypeError: If required parameters are missing for the service type

        Examples:
            # Upstox service
            upstox = ServiceFactory.create_service("upstox", access_token="token123")

            # Custom service
            custom = ServiceFactory.create_service(
                "custom",
                base_url="https://api.example.com",
                endpoints={"test": {"path": "/test", "method": "GET"}}
            )
        """
        if service_type not in cls._SERVICE_REGISTRY:
            available = list(cls._SERVICE_REGISTRY.keys())
            raise ValueError(f"Unsupported service type: {service_type}. "
                           f"Available types: {available}")

        service_class = cls._SERVICE_REGISTRY[service_type]

        # Special handling for CustomAPIService which requires specific parameters
        if service_type == "custom":
            base_url = kwargs.get("base_url")
            endpoints = kwargs.get("endpoints")

            if not base_url:
                raise TypeError("CustomAPIService requires 'base_url' parameter")
            if not endpoints:
                raise TypeError("CustomAPIService requires 'endpoints' parameter")

            # Remove these from kwargs since they're handled specially
            custom_kwargs = kwargs.copy()
            custom_kwargs.pop("base_url", None)
            custom_kwargs.pop("endpoints", None)

            # Cast to CustomAPIService to satisfy type checker
            custom_service_class = cast(Type[CustomAPIService], service_class)
            return custom_service_class(
                base_url=base_url,
                endpoints=endpoints,
                **custom_kwargs
            )
        else:
            # For other services, pass config and kwargs to constructor
            # Cast to BaseTradingService to satisfy type checker
            base_service_class = cast(Type[BaseTradingService], service_class)
            return base_service_class(config=config, **kwargs)

    @classmethod
    def get_available_services(cls) -> Dict[str, str]:
        """
        Get a dictionary of available service types and their descriptions.

        Returns:
            Dictionary mapping service type to description
        """
        descriptions = {
            "upstox": "Upstox trading platform integration",
            "groww": "Groww trading platform integration",
            "custom": "Generic REST API service for custom endpoints",
            "xts": "XTS (Symphony Fintech) trading platform integration",
        }

        return {service_type: descriptions.get(service_type, "Trading service")
                for service_type in cls._SERVICE_REGISTRY.keys()}

    @classmethod
    def register_service(cls, service_type: str, service_class: Type[ITradingService]) -> None:
        """
        Register a new service type with the factory.

        This allows adding custom service implementations to the factory.

        Args:
            service_type: Unique identifier for the service type
            service_class: Class that implements ITradingService

        Raises:
            TypeError: If service_class doesn't implement ITradingService
        """
        if not issubclass(service_class, ITradingService):
            raise TypeError("Service class must implement ITradingService interface")

        cls._SERVICE_REGISTRY[service_type] = service_class

    @classmethod
    def is_service_available(cls, service_type: str) -> bool:
        """
        Check if a service type is available.

        Args:
            service_type: Service type to check

        Returns:
            True if service type is available, False otherwise
        """
        return service_type in cls._SERVICE_REGISTRY
