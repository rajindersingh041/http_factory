import asyncio
import logging

from network_test.services import CustomAPIService

# Configure logging to see what's happening with network requests
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO to reduce noise
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def main():
    # Define your API endpoints
    my_endpoints = {
        "market_hours": {
            "path": "/v2/market/timings/{date}",
            "method": "GET",
            "cache_ttl": 300,
            "description": "Get market hours"
        },
        "holidays": {
            "path": "/v2/market/holidays/{date}",
            "method": "GET",
            "cache_ttl": 600,
            "description": "Get market holidays"
        }
    }

    # Create custom service instance
    async with CustomAPIService(
        base_url="https://api.upstox.com",
        endpoints=my_endpoints,
        rate_limit=5,
        timeout=10
    ) as market_service:

        print(f"✅ Created custom service with base URL: {market_service.client.base_url}")
        print(f"✅ Available endpoints: {list(market_service.list_endpoints().keys())}")

        # Use the custom service (this would work with a real API key)
        try:
            market_hours_data = await market_service.call_endpoint(
                "market_hours",
                path_params={"date": "2025-10-20"}
            )
            print(market_hours_data)


            holiday_data = await market_service.call_endpoint(
                "holidays",
                path_params={"date": "2025-10-21"}
            )
            print(holiday_data)


            print("✅ Custom service is ready to use!")
        except Exception as e:
            print(f"❌ Error (expected without API key): {e}")



if __name__ == "__main__":
    asyncio.run(main())
