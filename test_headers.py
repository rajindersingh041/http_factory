#!/usr/bin/env python3
"""
Test script to verify default headers functionality
"""

import asyncio

from src.network_test.network import AsyncNetworkClient


async def test_default_headers():
    """Test that default headers work correctly"""

    # Create client with default headers
    client = AsyncNetworkClient(
        base_url="https://httpbin.org",  # Use httpbin for testing
        default_headers={
            "User-Agent": "MyBot/1.0",
            "Authorization": "Bearer default-token",
            "Content-Type": "application/json",
        },
    )

    print("=== Test 1: Request with no additional headers ===")
    print("Should use only default headers")

    try:
        response = await client.request(
            method="GET",
            endpoint="/headers",  # httpbin.org/headers returns the headers it received
        )
        print("Response headers received by server:")
        print(response.get("headers", {}))
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Test 2: Request with additional headers ===")
    print("Should merge default headers with request-specific headers")

    try:
        response = await client.request(
            method="GET",
            endpoint="/headers",
            headers={
                "X-Custom-Header": "custom-value",
                "Authorization": "Bearer override-token",  # This should override the default
            },
        )
        print("Response headers received by server:")
        print(response.get("headers", {}))
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Test 3: Request with empty headers dict ===")
    print("Should use only default headers")

    try:
        response = await client.request(method="GET", endpoint="/headers", headers={})
        print("Response headers received by server:")
        print(response.get("headers", {}))
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_default_headers())
