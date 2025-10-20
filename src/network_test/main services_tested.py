"""Demonstration script for testing Groww and Upstox services with various configurations."""
import asyncio
import logging

from network_test.services import GrowwService, UpstoxService

# Configure logging to see what's happening with network requests
logging.basicConfig(
    level=logging.DEBUG,  # Changed to INFO to reduce noise
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def main():
    # === DEMO: UPSTOX SERVICE WITH PREDEFINED ENDPOINTS ===
    print("🚀 Testing Upstox Service with predefined endpoints\n")

    # Example 1: Using default configuration
    print("Using default Upstox configuration from config.py")
    async with UpstoxService() as upstox:

        # List all available endpoints
        print("📋 Available Upstox endpoints:")
        for name, description in upstox.list_endpoints().items():
            print(f"  • {name}: {description}")
        print()

        # Test candles endpoint using the convenient method
        print("📈 Getting candlestick data using convenient method:")
        try:
            candles = await upstox.get_candles(
                instrument_key="NSE_EQ|INE002A01018",  # Reliance Industries
                interval="I1",
                limit=5
            )
            print(f"✅ Candles data: {len(str(candles))} characters")
        except Exception as e:
            print(f"❌ Error getting candles: {e}")

        # Test calling endpoint directly with custom parameters
        print("\n🔧 Using call_endpoint method directly:")
        try:
            response = await upstox.call_endpoint(
                "candles",
                query_params={
                    "instrumentKey": "NSE_EQ|INE155A01022",  # TCS
                    "interval": "I1",
                    "from": "1760977799999",
                    "limit": "10"
                },
                cache_ttl=60  # Override default cache TTL
            )
            print(f"✅ Direct endpoint call: {len(str(response))} characters")
        except Exception as e:
            print(f"❌ Error in direct call: {e}")

    # === DEMO: GROWW SERVICE ===
    print("\n🌱 Testing Groww Service with custom parameters\n")

    # Example 2: Override specific parameters while keeping defaults for others
    async with GrowwService(
        rate_limit=30,  # Override rate limit
        timeout=5,      # Override timeout
        cache_ttl=60    # Override cache TTL
    ) as groww:        # Get Nifty data using convenient method
        print("📊 Getting BANKNIFTY data:")
        try:
            nifty_data = await groww.get_nifty_data("BANKNIFTY")
            if isinstance(nifty_data, dict):
                print(f"✅ BANKNIFTY: {nifty_data.get('close', 'N/A')}")
            else:
                print(f"✅ Response: {type(nifty_data)}")
        except Exception as e:
            print(f"❌ Error getting BANKNIFTY: {e}")

        # Test live aggregated data
        print("\n📡 Getting live aggregated data:")
        try:
            live_data = await groww.get_live_aggregated()
            print(f"✅ Live data type: {type(live_data)}")
        except Exception as e:
            print(f"❌ Error getting live data: {e}")

    # === DEMO: CUSTOM CONFIGURATION ===
    print("\n⚙️ Testing Custom Configuration\n")

    # Example 3: Using completely custom configuration
    custom_upstox_config = {
        "base_url": "https://service.upstox.com/",  # Different base URL
        "rate_limit": 15,
        "timeout": 8,
        "max_connections": 15,
        "cache_ttl": 45,
        "enable_circuit_breaker": True,
        "default_headers": {
            "User-Agent": "CustomBot/1.0",
            "X-Client": "network-test"
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
                "candles",
                query_params={
                    "instrumentKey": "NSE_EQ|INE002A01018",
                    "interval": "I1",
                    "from": "1760977799999",
                    "limit": "3"
                }
            )
            print(f"✅ Custom service response: {len(str(response))} characters")
        except Exception as e:
            print(f"❌ Custom service error: {e}")

    print("\n🎉 All service demos completed!")
if __name__ == "__main__":
    asyncio.run(main())
