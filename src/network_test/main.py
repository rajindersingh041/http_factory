import asyncio
import logging

from network_test.services import (CustomAPIService, ITradingService,
                                   ServiceFactory)

# Configure logging to see what's happening with network requests
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO to reduce noise
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def main():
    # Define your API endpoints
    my_endpoints = {
        "latest_forecast": {
            "path": "v1/parcel-forecast/revisions/{revision_id}/PER_COUNTRY/DAYS/PROD/latest-run",
            "method": "GET",
            "cache_ttl": 300,
            "description": "Get market hours"
        },
        "models": {
            "path": "/v1/parcel-forecast/models/all",
            "method": "GET",
            "cache_ttl": 600,
            "description": "Get market holidays"
        }
    }

    # Create custom service instance using factory
    forecast_service: ITradingService = ServiceFactory.create_service(
        "custom",
        base_url="https://parcel-forecast-manager.dlvryk8sp.int.aws.zooplus.io",
        endpoints=my_endpoints,
        rate_limit=5,
        timeout=10
    )

    async with forecast_service:

        print(f"✅ Created service: {forecast_service.get_service_name()}")
        print(f"✅ Available endpoints: {list(forecast_service.list_endpoints().keys())}")

        # Use the custom service (this would work with a real API key)
        try:
            latest_forecast_data = await forecast_service.call_endpoint(
                "latest_forecast",
                path_params={"revision_id": "5256"}
            )
            print(latest_forecast_data)


            models = await forecast_service.call_endpoint(
                "models")
            print(models)
            # holiday_data = await market_service.call_endpoint(
            #     "holidays",
            #     path_params={"date": "2025-10-21"}
            # )
            # print(holiday_data)


            print("✅ Custom service is ready to use!")
        except Exception as e:
            print(f"❌ Error (expected without API key): {e}")



if __name__ == "__main__":
    asyncio.run(main())
