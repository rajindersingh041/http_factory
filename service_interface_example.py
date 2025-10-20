"""
Service Interface Example

This example demonstrates how to use the new service interface and factory pattern.
The application uses ITradingService interface without knowing the specific implementation.
"""

import asyncio
import logging
from typing import Optional

from network_test.services import ITradingService, ServiceFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class TradingApplication:
    """
    Example application that uses trading services through the interface.

    This demonstrates how your application can be service-agnostic by using
    the ITradingService interface. The application doesn't need to know
    whether it's using Upstox, Groww, Custom API, or XTS service.
    """

    def __init__(self, service: ITradingService):
        """Initialize with any service that implements ITradingService"""
        self.service = service

    async def get_service_info(self) -> dict:
        """Get information about the service"""
        return {
            "service_name": self.service.get_service_name(),
            "available_endpoints": list(self.service.list_endpoints().keys()),
            "endpoint_descriptions": self.service.list_endpoints()
        }

    async def call_endpoint_safely(self, endpoint_name: str, **kwargs):
        """Call an endpoint with error handling"""
        try:
            return await self.service.call_endpoint(endpoint_name, **kwargs)
        except ValueError as e:
            print(f"❌ Endpoint error: {e}")
            return None
        except Exception as e:
            print(f"❌ API error: {e}")
            return None


async def demonstrate_service_factory():
    """Demonstrate creating different services using the factory"""

    print("🏭 Service Factory Demo")
    print("=" * 50)

    # Show available services
    available_services = ServiceFactory.get_available_services()
    print("Available services:")
    for service_type, description in available_services.items():
        print(f"  - {service_type}: {description}")
    print()

    # Create different types of services
    services_to_demo = []

    # 1. Custom API Service (this will work)
    try:
        forecast_endpoints = {
            "latest_forecast": {
                "path": "v1/parcel-forecast/revisions/{revision_id}/PER_COUNTRY/DAYS/PROD/latest-run",
                "method": "GET",
                "cache_ttl": 300,
                "description": "Get latest forecast data"
            },
            "models": {
                "path": "/v1/parcel-forecast/models/all",
                "method": "GET",
                "cache_ttl": 600,
                "description": "Get all models"
            }
        }

        custom_service = ServiceFactory.create_service(
            "custom",
            base_url="https://parcel-forecast-manager.dlvryk8sp.int.aws.zooplus.io",
            endpoints=forecast_endpoints,
            rate_limit=5,
            timeout=10
        )
        services_to_demo.append(("Custom API", custom_service))

    except Exception as e:
        print(f"❌ Could not create custom service: {e}")

    # 2. Upstox Service (demo only - won't work without credentials)
    try:
        upstox_service = ServiceFactory.create_service(
            "upstox",
            access_token="demo_token_123",  # This won't work but demonstrates the pattern
            rate_limit=10
        )
        services_to_demo.append(("Upstox", upstox_service))

    except Exception as e:
        print(f"❌ Could not create Upstox service: {e}")

    # 3. Groww Service (demo only - won't work without credentials)
    try:
        groww_service = ServiceFactory.create_service(
            "groww",
            session_token="demo_session_123",  # This won't work but demonstrates the pattern
            rate_limit=15
        )
        services_to_demo.append(("Groww", groww_service))

    except Exception as e:
        print(f"❌ Could not create Groww service: {e}")

    # Demonstrate using services through the interface
    for service_name, service in services_to_demo:
        print(f"\n📊 Demonstrating {service_name} Service")
        print("-" * 40)

        # Create application instance (service-agnostic)
        app = TradingApplication(service)

        async with service:
            # Get service information
            info = await app.get_service_info()
            print(f"Service Name: {info['service_name']}")
            print(f"Available Endpoints: {len(info['available_endpoints'])}")

            # Show some endpoints
            for endpoint, description in list(info['endpoint_descriptions'].items())[:3]:
                print(f"  - {endpoint}: {description}")

            if info['available_endpoints']:
                print(f"\n🔍 Testing first endpoint: {info['available_endpoints'][0]}")
                result = await app.call_endpoint_safely(info['available_endpoints'][0])
                if result:
                    print("✅ Endpoint call successful!")
                else:
                    print("❌ Endpoint call failed (expected for demo)")


async def demonstrate_service_switching():
    """Demonstrate how easy it is to switch between services"""

    print("\n🔄 Service Switching Demo")
    print("=" * 50)

    # Same endpoint configuration for different custom APIs
    weather_endpoints = {
        "current_weather": {
            "path": "/current.json",
            "method": "GET",
            "description": "Get current weather"
        }
    }

    # Different API configurations - same interface!
    api_configs = [
        {
            "name": "Weather API 1",
            "base_url": "https://api.weatherapi.com/v1",
            "endpoints": weather_endpoints
        },
        {
            "name": "Weather API 2",
            "base_url": "https://api.openweathermap.org/data/2.5",
            "endpoints": {
                "current_weather": {
                    "path": "/weather",
                    "method": "GET",
                    "description": "Current weather data"
                }
            }
        }
    ]

    # Application can easily switch between different APIs
    for config in api_configs:
        print(f"\n🌤️  Using {config['name']}")
        print("-" * 30)

        # Create service using factory
        service = ServiceFactory.create_service(
            "custom",
            base_url=config["base_url"],
            endpoints=config["endpoints"],
            timeout=5
        )

        # Use same application code with different service
        app = TradingApplication(service)

        async with service:
            info = await app.get_service_info()
            print(f"Service: {info['service_name']}")
            print(f"Endpoints: {list(info['available_endpoints'])}")


async def main():
    """Main demonstration function"""

    print("🚀 Trading Service Interface & Factory Demo")
    print("=" * 60)
    print()

    await demonstrate_service_factory()
    await demonstrate_service_switching()

    print("\n✅ Demo completed!")
    print("\n💡 Key Benefits:")
    print("  - Service-agnostic application code")
    print("  - Easy service switching via factory")
    print("  - Consistent interface across all services")
    print("  - Clean separation of concerns")
    print("  - Easy to add new service implementations")


if __name__ == "__main__":
    asyncio.run(main())
