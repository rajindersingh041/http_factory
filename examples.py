"""
Advanced Usage Examples for Trading Services

This file demonstrates various ways to use the service classes
with different configurations and patterns.
"""

import asyncio
import logging

from network_test.config import INTERVALS, POPULAR_INSTRUMENTS, UPSTOX_CONFIG
from network_test.services import GrowwService, UpstoxService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


async def demo_basic_usage():
    """Basic usage with default configuration"""
    print("🚀 DEMO 1: Basic Service Usage\n")

    async with UpstoxService() as upstox:
        # Simple method calls
        try:
            data = await upstox.get_candles("NSE_EQ|INE002A01018", interval="I1", limit=5)
            print(f"✅ Got {len(str(data))} characters of candle data")
        except Exception as e:
            print(f"❌ Error: {e}")


async def demo_bulk_operations():
    """Fetch data for multiple stocks concurrently"""
    print("\n📊 DEMO 2: Bulk Operations (Multiple Stocks)\n")

    stocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

    async with UpstoxService(rate_limit=30) as upstox:
        print(f"Fetching data for {len(stocks)} stocks concurrently...")

        # Create tasks for concurrent execution
        tasks = []
        for stock in stocks:
            instrument_key = POPULAR_INSTRUMENTS.get(stock)
            if instrument_key:
                task = upstox.get_candles(
                    instrument_key=instrument_key,
                    interval=INTERVALS["5MIN"],
                    limit=10
                )
                tasks.append((stock, task))

        # Execute all tasks concurrently
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

        # Process results
        for (stock, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                print(f"❌ {stock}: {result}")
            else:
                print(f"✅ {stock}: {len(str(result))} characters")


async def demo_custom_endpoints():
    """Using custom endpoint configurations"""
    print("\n🔧 DEMO 3: Custom Endpoint Configuration\n")

    # Create service with custom configuration
    custom_config = UPSTOX_CONFIG.copy()
    custom_config["rate_limit"] = 15  # Slower rate limit
    custom_config["cache_ttl"] = 5    # Shorter cache

    async with UpstoxService(**{k: v for k, v in custom_config.items()
                               if k not in ["endpoints"]}) as upstox:

        # Add custom endpoints dynamically
        from network_test.services import EndpointConfig

        # Add a custom endpoint for real-time quotes
        upstox.ENDPOINTS["realtime_quotes"] = EndpointConfig(
            path="market-quote/quotes",
            method="GET",
            cache_ttl=1,  # 1 second cache for real-time data
            description="Real-time quotes with minimal caching"
        )

        try:
            # Use the custom endpoint
            response = await upstox.call_endpoint(
                "realtime_quotes",
                query_params={"instrument_key": POPULAR_INSTRUMENTS["RELIANCE"]}
            )
            print(f"✅ Real-time quote: {type(response)}")
        except Exception as e:
            print(f"❌ Real-time quote error: {e}")


async def demo_error_handling():
    """Demonstrate proper error handling"""
    print("\n⚠️ DEMO 4: Error Handling & Circuit Breaker\n")

    async with UpstoxService(rate_limit=100, enable_circuit_breaker=True) as upstox:

        # Test with invalid endpoint
        try:
            await upstox.call_endpoint("invalid_endpoint")
        except ValueError as e:
            print(f"✅ Caught expected error: {e}")

        # Test with invalid instrument
        try:
            await upstox.get_candles("INVALID_INSTRUMENT", limit=1)
        except Exception as e:
            print(f"✅ Handled API error: {type(e).__name__}")

        # Test circuit breaker stats
        stats = await upstox.client.get_cache_stats()
        print(f"📊 Request stats: {stats}")


async def demo_caching_behavior():
    """Demonstrate caching behavior"""
    print("\n💾 DEMO 5: Caching Behavior\n")

    async with UpstoxService() as upstox:
        instrument = POPULAR_INSTRUMENTS["TCS"]

        print("Making first request (cache miss)...")
        start_time = asyncio.get_event_loop().time()
        try:
            _ = await upstox.get_candles(instrument, limit=5)
            time1 = asyncio.get_event_loop().time() - start_time
            print(f"✅ First request: {time1:.3f}s")
        except Exception as e:
            print(f"❌ First request failed: {e}")
            return

        print("Making second request (cache hit)...")
        start_time = asyncio.get_event_loop().time()
        try:
            _ = await upstox.get_candles(instrument, limit=5)
            time2 = asyncio.get_event_loop().time() - start_time
            print(f"✅ Second request: {time2:.3f}s")
            print(f"🚀 Speed improvement: {time1/time2:.1f}x faster!")
        except Exception as e:
            print(f"❌ Second request failed: {e}")


async def demo_mixed_services():
    """Using multiple services together"""
    print("\n🔄 DEMO 6: Multiple Services Integration\n")

    async with UpstoxService() as upstox, GrowwService() as groww:
        print("Using both Upstox and Groww services...")

        # Get data from both services concurrently
        upstox_task = upstox.get_candles(POPULAR_INSTRUMENTS["RELIANCE"], limit=3)
        groww_task = groww.get_nifty_data("BANKNIFTY")

        try:
            upstox_data, groww_data = await asyncio.gather(
                upstox_task, groww_task, return_exceptions=True
            )

            if not isinstance(upstox_data, Exception):
                print(f"✅ Upstox data: {len(str(upstox_data))} characters")
            else:
                print(f"❌ Upstox error: {upstox_data}")

            if not isinstance(groww_data, Exception):
                print(f"✅ Groww data: {type(groww_data)}")
            else:
                print(f"❌ Groww error: {groww_data}")

        except Exception as e:
            print(f"❌ Mixed services error: {e}")


async def main():
    """Run all demonstrations"""
    print("🎯 Trading Services Advanced Examples\n")
    print("=" * 50)

    demos = [
        demo_basic_usage,
        demo_bulk_operations,
        demo_custom_endpoints,
        demo_error_handling,
        demo_caching_behavior,
        demo_mixed_services
    ]

    for demo in demos:
        try:
            await demo()
            print("\n" + "=" * 50)
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            print("\n" + "=" * 50)

    print("🎉 All demonstrations completed!")


if __name__ == "__main__":
    asyncio.run(main())
