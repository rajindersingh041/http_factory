"""
Example: Creating Custom Services On-the-Go

This demonstrates different ways to create and customize services
dynamically in your application.
"""

import asyncio
from typing import Any, Dict

from network_test.services import BaseTradingService, EndpointConfig


class CustomAPIService(BaseTradingService):
    """
    Example custom service for any API endpoint
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


async def demo_custom_service_class():
    """Demo: Creating a custom service class"""
    print("🎯 DEMO: Custom Service Class\n")

    # Define your API endpoints
    my_endpoints = {
        "weather": {
            "path": "weather",
            "method": "GET",
            "cache_ttl": 300,
            "description": "Get weather data"
        },
        "forecast": {
            "path": "forecast/{city}",
            "method": "GET",
            "cache_ttl": 600,
            "description": "Get weather forecast for city"
        }
    }

    # Create custom service instance
    async with CustomAPIService(
        base_url="https://api.openweathermap.org/data/2.5/",
        endpoints=my_endpoints,
        rate_limit=5,
        timeout=10
    ) as weather_service:

        print(f"✅ Created custom service with base URL: {weather_service.client.base_url}")
        print(f"✅ Available endpoints: {list(weather_service.list_endpoints().keys())}")

        # Use the custom service (this would work with a real API key)
        try:
            # weather_data = await weather_service.call_endpoint(
            #     "weather",
            #     query_params={"q": "London", "appid": "your_api_key"}
            # )
            print("✅ Custom service is ready to use!")
        except Exception as e:
            print(f"❌ Error (expected without API key): {e}")


async def demo_dynamic_service_modification():
    """Demo: Modifying existing services on the fly"""
    print("\n🔧 DEMO: Dynamic Service Modification\n")

    from network_test.services import UpstoxService

    # Start with existing service
    async with UpstoxService() as upstox:

        # Add new endpoints dynamically
        upstox._ENDPOINTS["custom_market_data"] = EndpointConfig(
            path="custom/market-data/{symbol}",
            method="GET",
            cache_ttl=10,
            description="Custom market data endpoint"
        )

        upstox._ENDPOINTS["batch_quotes"] = EndpointConfig(
            path="market-quote/batch",
            method="POST",
            cache_ttl=5,
            use_cache=True,
            description="Get multiple quotes in one call"
        )

        print(f"✅ Added custom endpoints to existing service")
        print(f"✅ Total endpoints: {len(upstox.list_endpoints())}")
        print(f"✅ New endpoints: {[k for k in upstox.list_endpoints().keys() if 'custom' in k or 'batch' in k]}")


async def demo_configuration_based_service():
    """Demo: Creating services from configuration"""
    print("\n⚙️ DEMO: Configuration-Based Service Creation\n")

    from network_test.services import UpstoxService

    # Define multiple service configurations
    service_configs = {
        "fast_trading": {
            "base_url": "https://api.upstox.com/v2/",
            "rate_limit": 100,
            "timeout": 5,
            "cache_ttl": 1,  # Very short cache for fast trading
            "endpoints": {
                "quick_quote": {
                    "path": "market-quote/quotes",
                    "method": "GET",
                    "cache_ttl": 1,
                    "description": "Ultra-fast quotes"
                }
            }
        },
        "research_mode": {
            "base_url": "https://api.upstox.com/v2/",
            "rate_limit": 10,
            "timeout": 30,
            "cache_ttl": 300,  # Long cache for research
            "endpoints": {
                "detailed_analysis": {
                    "path": "portfolio/long-term-holdings",
                    "method": "GET",
                    "cache_ttl": 600,
                    "description": "Detailed portfolio analysis"
                }
            }
        }
    }

    # Create services from configurations
    for mode, config in service_configs.items():
        async with UpstoxService(config=config) as service:
            print(f"✅ Created '{mode}' service:")
            print(f"   Rate limit: {service.client.rate_limiter.requests_per_second} RPS")
            print(f"   Cache TTL: {service.config.get('cache_ttl')} seconds")
            print(f"   Custom endpoints: {[k for k in service.list_endpoints().keys() if k in config.get('endpoints', {})]}")


async def demo_service_factory():
    """Demo: Service factory pattern"""
    print("\n🏭 DEMO: Service Factory Pattern\n")

    def create_service_for_purpose(purpose: str, **overrides):
        """Factory function to create services for specific purposes"""

        base_configs = {
            "live_trading": {
                "rate_limit": 50,
                "timeout": 5,
                "cache_ttl": 1,
                "enable_circuit_breaker": True,
                "endpoints": {
                    "place_order_fast": {
                        "path": "order/place",
                        "method": "POST",
                        "use_cache": False,
                        "description": "Fast order placement"
                    }
                }
            },
            "data_analysis": {
                "rate_limit": 10,
                "timeout": 30,
                "cache_ttl": 300,
                "max_connections": 5,
                "endpoints": {
                    "bulk_historical": {
                        "path": "historical-candle/{instrument_key}/{interval}/{to_date}",
                        "method": "GET",
                        "cache_ttl": 3600,
                        "description": "Bulk historical data"
                    }
                }
            },
            "monitoring": {
                "rate_limit": 1,
                "timeout": 60,
                "cache_ttl": 60,
                "endpoints": {
                    "health_check": {
                        "path": "user/profile",
                        "method": "GET",
                        "cache_ttl": 60,
                        "description": "Service health monitoring"
                    }
                }
            }
        }

        if purpose not in base_configs:
            raise ValueError(f"Unknown purpose: {purpose}")

        # Merge base config with overrides
        config = base_configs[purpose].copy()
        config.update(overrides)

        from network_test.services import UpstoxService
        return UpstoxService(config=config)

    # Use the factory
    purposes = ["live_trading", "data_analysis", "monitoring"]

    for purpose in purposes:
        service = create_service_for_purpose(purpose)
        async with service:
            print(f"✅ Created '{purpose}' service:")
            print(f"   Rate limit: {service.client.rate_limiter.requests_per_second} RPS")
            print(f"   Cache TTL: {service.config.get('cache_ttl')} seconds")


async def main():
    """Run all demos"""
    await demo_custom_service_class()
    await demo_dynamic_service_modification()
    await demo_configuration_based_service()
    await demo_service_factory()

    print("\n🎉 All custom service demos completed!")


if __name__ == "__main__":
    asyncio.run(main())
