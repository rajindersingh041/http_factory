import asyncio
import logging

from network_test.network import AsyncNetworkClient

# Configure logging to see what's happening with network requests
logging.basicConfig(
    level=logging.DEBUG,  # Show all log levels (DEBUG, INFO, WARNING, ERROR)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

UPSTOX_URL = "https://service.upstox.com"

# ?instrumentKey=NSE_EQ|INE238A01034&interval=I1&from=1760977799999&limit=375


async def main():
    # Use async context manager to ensure proper cleanup
    async with AsyncNetworkClient(
        base_url=UPSTOX_URL,
        rate_limit=50,  # 🚀 Increased from 10 to 50 RPS (20ms between requests)
        timeout=3,  # 🚀 Reduced timeout for faster failure detection
        max_connections=50,  # 🚀 More concurrent connections
        max_retries=2,  # 🚀 Fewer retries for speed
        cache_ttl=5,
        enable_circuit_breaker=True,
        default_headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
        },
    ) as client:
        # Test different endpoint formats to verify URL building
        print("Testing URL building with different endpoint formats:")
        lst = [
            "NSE_EQ|INE155A01022",
            "NSE_EQ|INE040A01034",

        ]
        results = await asyncio.gather(
            *[
                client.request(
                    method="GET",
                    endpoint=f"chart/open/v3/candles/?instrumentKey={item}&interval=I1&from=1760977799999&limit=375",
                    params=None,
                    data=None,
                    json_data=None,
                    use_cache=True,
                    cache_ttl=10,
                )
                for item in lst
            ]
        )
        response = await client.request(
            method="GET",
            endpoint="chart/open/v3/candles/",  # Leading slash
            params={
                "instrumentKey": "NSE_EQ|INE238A01034",
                "interval": "I1",
                "from": 1760977799999,
                "limit": 375,
            },
            data=None,
            json_data=None,
            use_cache=True,
            cache_ttl=10,
        )
        for response in results:
            print("Response received:", len(str(response)), "characters")



    async with AsyncNetworkClient(
        base_url="https://groww.in/",
        rate_limit=50,
        timeout=3,
        max_connections=5,
        max_retries=2,
        cache_ttl=300,
        enable_circuit_breaker=True,
        default_headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
        },
    ) as client:
        response = await client.request(
            method="GET",
            endpoint="v1/api/stocks_data/v1/accord_points/exchange/NSE/segment/CASH/latest_indices_ohlc/BANKNIFTY",
            cache_ttl=300,
        )
        print(f"Groww stocks response type: {type(response)}")
        print(f"Groww stocks response content: {str(response)[:200]}...")
        if isinstance(response, dict):
            print("Response received:", len(str(response)), "characters")
        else:
            print("Non-JSON response length:", len(str(response)) if response else 0, "characters")




    async with AsyncNetworkClient(
        rate_limit=50,
        timeout=3,
        max_connections=5,
        max_retries=2,
        cache_ttl=300,
        enable_circuit_breaker=True,
        default_headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
        },
    ) as client:
        response = await client.request(
            method="POST",
            endpoint= "https://groww.in/v1/api/stocks_data/v1/tr_live_delayed/segment/CASH/latest_aggregated",
            json_data={"exchangeAggReqMap":{"NSE":{"priceSymbolList":["HDFCBANK","ICICIBANK","SBIN","KOTAKBANK","AXISBANK","BANKBARODA","PNB","CANBK"],"indexSymbolList":[]},"BSE":{"priceSymbolList":[],"indexSymbolList":[]}}},  # Empty payload for POST request
            cache_ttl=300,
        )
        print(f"Groww POST response type: {type(response)}")
        print(f"Groww POST response content: {str(response)[:200]}...")
        if isinstance(response, dict):
            print("Response received:", len(str(response)), "characters")
        else:
            print("Non-JSON response length:", len(str(response)) if response else 0, "characters")



    async with AsyncNetworkClient(
        rate_limit=50,
        timeout=3,
        max_connections=5,
        max_retries=2,
        cache_ttl=300,
        enable_circuit_breaker=True,
        default_headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
        },
    ) as client:
        response = await client.request(
            method="POST",
            endpoint= "https://groww.in/v1/api/stocks_data/v1/tr_live_delayed/segment/CASH/latest_aggregated",
            json_data={"exchangeAggReqMap":{"NSE":{"priceSymbolList":["HDFCBANK","ICICIBANK","SBIN","KOTAKBANK","AXISBANK","BANKBARODA","PNB","CANBK"],"indexSymbolList":[]},"BSE":{"priceSymbolList":[],"indexSymbolList":[]}}},  # Empty payload for POST request
            cache_ttl=300,
        )
        print(f"Groww POST response type: {type(response)}")
        print(f"Groww POST response content: {str(response)[:200]}...")
        if isinstance(response, dict):
            print("Response received:", len(str(response)), "characters")
        else:
            print("Non-JSON response length:", len(str(response)) if response else 0, "characters")

if __name__ == "__main__":
    asyncio.run(main())
