"""
Trading Services Package

This package provides a unified interface for different trading service providers.
All services implement the ITradingService interface for consistent behavior.

Available Services:
- UpstoxService: Upstox trading platform integration
- GrowwService: Groww trading platform integration
- CustomAPIService: Generic API service for custom endpoints
- XTSService: XTS trading platform integration

Usage:
    from network_test.services import ITradingService, ServiceFactory

    # Using the factory
    service = ServiceFactory.create_service("upstox", api_key="your_key")

    # Or directly
    from network_test.services.upstox_service import UpstoxService
    service = UpstoxService(api_key="your_key")
"""

from .base_service import BaseTradingService
from .custom_service import CustomAPIService
from .factory import ServiceFactory
from .groww_service import GrowwService
from .interface import ITradingService
from .upstox_service import UpstoxService
from .xts_service import XTSService

__all__ = [
    "ITradingService",
    "BaseTradingService",
    "UpstoxService",
    "GrowwService",
    "CustomAPIService",
    "XTSService",
    "ServiceFactory"
]
