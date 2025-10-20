#!/usr/bin/env python3
"""
Simple test to verify header merging logic without making actual HTTP requests
"""

from src.network_test.network import AsyncNetworkClient


def test_header_merging():
    """Test the header merging logic"""

    # Test case 1: Default headers only
    client = AsyncNetworkClient(
        default_headers={
            "User-Agent": "MyBot/1.0",
            "Authorization": "Bearer default-token",
            "Content-Type": "application/json",
        }
    )

    print("=== Test 1: Default headers only ===")
    print("Default headers:", client.default_headers)

    # Simulate the merging logic from the request method
    request_headers = None
    merged_headers = client.default_headers.copy()
    if request_headers:
        merged_headers.update(request_headers)

    print("Merged headers:", merged_headers)
    print()

    # Test case 2: Request headers override defaults
    print("=== Test 2: Request headers override defaults ===")
    print("Default headers:", client.default_headers)

    request_headers = {
        "X-Custom-Header": "custom-value",
        "Authorization": "Bearer override-token",  # This should override the default
    }

    merged_headers = client.default_headers.copy()
    if request_headers:
        merged_headers.update(request_headers)

    print("Request headers:", request_headers)
    print("Merged headers:", merged_headers)
    print()

    # Test case 3: Empty request headers
    print("=== Test 3: Empty request headers ===")
    print("Default headers:", client.default_headers)

    request_headers = {}
    merged_headers = client.default_headers.copy()
    if request_headers:
        merged_headers.update(request_headers)

    print("Request headers:", request_headers)
    print("Merged headers:", merged_headers)
    print()

    # Test case 4: No default headers
    client_no_defaults = AsyncNetworkClient()
    print("=== Test 4: No default headers ===")
    print("Default headers:", client_no_defaults.default_headers)

    request_headers = {"X-Custom-Header": "custom-value"}
    merged_headers = client_no_defaults.default_headers.copy()
    if request_headers:
        merged_headers.update(request_headers)

    print("Request headers:", request_headers)
    print("Merged headers:", merged_headers)


if __name__ == "__main__":
    test_header_merging()
