"""
Common models and configurations for trading services.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


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
