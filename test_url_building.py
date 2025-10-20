#!/usr/bin/env python3
"""
Test URL building logic without making HTTP requests
"""


from src.network_test.network import AsyncNetworkClient


def test_url_building():
    """Test URL building with different base URLs and endpoints"""

    test_cases = [
        # (base_url, endpoint, expected_result)
        ("https://api.example.com", "/path", "https://api.example.com/path"),
        ("https://api.example.com/", "/path", "https://api.example.com/path"),
        ("https://api.example.com", "path", "https://api.example.com/path"),
        ("https://api.example.com/", "path", "https://api.example.com/path"),
        ("https://api.example.com/v1", "/users", "https://api.example.com/v1/users"),
        ("https://api.example.com/v1/", "/users", "https://api.example.com/v1/users"),
        ("https://api.example.com/v1", "users", "https://api.example.com/v1/users"),
        ("https://api.example.com/v1/", "users", "https://api.example.com/v1/users"),
        ("", "/absolute/path", "/absolute/path"),  # Empty base URL
        (
            "https://api.example.com/",
            "https://other.com/data",
            "https://other.com/data",
        ),  # Absolute endpoint
    ]

    print("=== URL Building Test Results ===")
    all_passed = True

    for i, (base_url, endpoint, expected) in enumerate(test_cases, 1):
        client = AsyncNetworkClient(base_url=base_url)
        result = client._build_url(endpoint)

        status = "✅ PASS" if result == expected else "❌ FAIL"
        if result != expected:
            all_passed = False

        print(f"Test {i:2d}: {status}")
        print(f"  Base URL: '{base_url}'")
        print(f"  Endpoint: '{endpoint}'")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
        print()

    print(
        f"Overall result: {'🎉 ALL TESTS PASSED' if all_passed else '💥 SOME TESTS FAILED'}"
    )
    return all_passed


if __name__ == "__main__":
    test_url_building()
