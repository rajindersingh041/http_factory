import asyncio
import logging

from network_test.services import UpstoxService

# Configure logging to see what's happening with network requests
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO to reduce noise
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def main():

    # Example 3: Using completely custom configuration
    custom_upstox_config = {
        "base_url": "https://api.upstox.com/",
        "rate_limit": 15,
        "timeout": 8,
        "max_connections": 15,
        "cache_ttl": 45,
        "enable_circuit_breaker": True,
        "default_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
        },
        "endpoints": {
        "market_timing": {
            "path": "v2/market/timings/",
            "method": "POST",
            "cache_ttl": 86400,  # Cache for 1 day
            "description": "Market timings information"
        },
        "holiday_timing": {
            "path": "v2/market/holidays/",
            "method": "GET",
            "cache_ttl": 86400,  # Cache for 1 day
            "description": "Market holidays information"
        }
    }
    }

    async with UpstoxService(config=custom_upstox_config) as custom_upstox:
        print("🔧 Custom Upstox config:")
        print(f"   Base URL: {custom_upstox.client.base_url}")
        print(f"   Rate limit: {custom_upstox.client.rate_limiter.requests_per_second} RPS")
        print(f"   Custom header: {custom_upstox.client.default_headers.get('X-Client')}")

        # Test the custom configured service
        try:
            response = await custom_upstox.call_endpoint(
                "market_timing",
            )
            print(f"✅ Custom service response: {len(str(response))} characters")
        except Exception as e:
            print(f"❌ Custom service error: {e}")

    print("\n🎉 All service demos completed!")
if __name__ == "__main__":
    asyncio.run(main())
