"""
Configuration Examples for Trading Services

This file demonstrates different ways to configure and use trading services
with custom parameters, base URLs, and settings.
"""

import asyncio
import logging

from network_test.config import GROWW_CONFIG, UPSTOX_CONFIG
from network_test.services import GrowwService, UpstoxService

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


async def demo_default_configuration():
    """Using default configuration from config.py"""
    print("🔧 DEMO 1: Default Configuration")
    print(f"Upstox default base_url: {UPSTOX_CONFIG['base_url']}")
    print(f"Upstox default rate_limit: {UPSTOX_CONFIG['rate_limit']}")
    print(f"Groww default base_url: {GROWW_CONFIG['base_url']}")
    print(f"Groww default rate_limit: {GROWW_CONFIG['rate_limit']}")

    async with UpstoxService() as upstox:
        print("✅ UpstoxService initialized with default config")
        print(f"   Base URL: {upstox.client.base_url}")

    async with GrowwService() as groww:
        print("✅ GrowwService initialized with default config")
        print(f"   Base URL: {groww.client.base_url}")


async def demo_parameter_overrides():
    """Override specific parameters without changing config files"""
    print("\n🛠️  DEMO 2: Parameter Overrides")

    # Override Upstox parameters
    async with UpstoxService(
        base_url="https://custom-upstox.example.com/",
        rate_limit=50,  # Increase rate limit
        timeout=15,     # Increase timeout
        max_connections=30,
        cache_ttl=60
    ) as upstox:
        print(f"✅ Custom Upstox - Base URL: {upstox.client.base_url}")
        print(f"   Rate limit: {upstox.client.rate_limiter.requests_per_second}")

    # Override Groww parameters
    async with GrowwService(
        base_url="https://api-test.groww.in/",
        rate_limit=25,  # Reduce rate limit
        timeout=10,
        enable_circuit_breaker=False
    ) as groww:
        print(f"✅ Custom Groww - Base URL: {groww.client.base_url}")
        print(f"   Circuit breaker: {groww.client.circuit_breaker is not None}")


async def demo_custom_configurations():
    """Using completely custom configuration dictionaries"""
    print("\n⚙️  DEMO 3: Custom Configuration Dictionaries")

    # Custom Upstox configuration for testing environment
    test_upstox_config = {
        "base_url": "https://test-api.upstox.com/",
        "rate_limit": 10,
        "timeout": 20,
        "max_connections": 5,
        "max_retries": 1,
        "cache_ttl": 120,
        "enable_circuit_breaker": False,
        "api_key": "test_api_key",
        "access_token": "test_access_token",
        "default_headers": {
            "User-Agent": "TestBot/1.0",
            "X-Environment": "testing"
        }
    }

    async with UpstoxService(config=test_upstox_config) as upstox:
        print(f"✅ Test Upstox - Base URL: {upstox.client.base_url}")
        print(f"   API Key: {upstox.api_key}")
        print(f"   Custom header: {upstox.client.default_headers.get('X-Environment')}")

    # Custom Groww configuration for high-frequency trading
    hft_groww_config = {
        "base_url": "https://hft.groww.in/",
        "rate_limit": 100,  # Very high rate limit
        "timeout": 2,       # Very fast timeout
        "max_connections": 50,
        "cache_ttl": 1,     # Minimal caching
        "default_headers": {
            "User-Agent": "HFT-Bot/2.0",
            "X-Trading-Mode": "high-frequency"
        }
    }

    async with GrowwService(config=hft_groww_config) as groww:
        print(f"✅ HFT Groww - Base URL: {groww.client.base_url}")
        print(f"   Rate limit: {groww.client.rate_limiter.requests_per_second}")


async def demo_environment_specific_configs():
    """Different configurations for different environments"""
    print("\n🌍 DEMO 4: Environment-Specific Configurations")

    environments = {
        "development": {
            "upstox": {
                "base_url": "https://dev-api.upstox.com/",
                "rate_limit": 5,
                "timeout": 30,
                "enable_circuit_breaker": False,
                "default_headers": {"X-Environment": "dev"}
            },
            "groww": {
                "base_url": "https://dev.groww.in/",
                "rate_limit": 10,
                "timeout": 15
            }
        },
        "staging": {
            "upstox": {
                "base_url": "https://staging-api.upstox.com/",
                "rate_limit": 15,
                "timeout": 15,
                "default_headers": {"X-Environment": "staging"}
            },
            "groww": {
                "base_url": "https://staging.groww.in/",
                "rate_limit": 25,
                "timeout": 10
            }
        },
        "production": {
            "upstox": UPSTOX_CONFIG,  # Use default production config
            "groww": GROWW_CONFIG
        }
    }

    for env_name, configs in environments.items():
        print(f"\n🏷️  Environment: {env_name.upper()}")

        async with UpstoxService(config=configs["upstox"]) as upstox:
            env_header = upstox.client.default_headers.get("X-Environment", "production")
            print(f"   Upstox: {upstox.client.base_url} (env: {env_header})")

        async with GrowwService(config=configs["groww"]) as groww:
            print(f"   Groww: {groww.client.base_url}")


async def demo_authentication_configuration():
    """Configure services with authentication"""
    print("\n🔐 DEMO 5: Authentication Configuration")

    # Method 1: Pass auth parameters directly
    async with UpstoxService(
        api_key="your_api_key_here",
        access_token="your_access_token_here",
        rate_limit=20
    ) as upstox:
        print(f"✅ Direct auth - API Key: {upstox.api_key[:10]}..." if upstox.api_key else "No API key")
        auth_header = upstox.client.default_headers.get("Authorization", "No auth header")
        print(f"   Auth header: {auth_header[:20]}..." if len(auth_header) > 20 else auth_header)

    # Method 2: Include in custom config
    auth_config = UPSTOX_CONFIG.copy()
    auth_config.update({
        "api_key": "config_api_key",
        "access_token": "config_access_token",
        "rate_limit": 30
    })

    async with UpstoxService(config=auth_config) as upstox:
        print(f"✅ Config auth - API Key: {upstox.api_key}")


async def demo_mixed_configurations():
    """Mix default config with parameter overrides"""
    print("\n🔀 DEMO 6: Mixed Configurations")

    # Start with default config, override specific parameters
    async with UpstoxService(
        # Use default UPSTOX_CONFIG as base
        rate_limit=35,  # Override just the rate limit
        timeout=8,      # Override just the timeout
        api_key="mixed_config_api_key"  # Add authentication
    ) as upstox:
        print(f"✅ Mixed config - Base URL: {upstox.client.base_url} (from default)")
        print(f"   Rate limit: {upstox.client.rate_limiter.requests_per_second} (overridden)")
        print(f"   Max connections: {upstox.client._connector.limit} (from default)")
        print(f"   API Key: {upstox.api_key} (overridden)")


async def main():
    """Run all configuration demonstrations"""
    print("🎛️  Trading Services Configuration Examples")
    print("=" * 60)

    demos = [
        demo_default_configuration,
        demo_parameter_overrides,
        demo_custom_configurations,
        demo_environment_specific_configs,
        demo_authentication_configuration,
        demo_mixed_configurations
    ]

    for demo in demos:
        try:
            await demo()
            print("\n" + "-" * 60)
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            print("\n" + "-" * 60)

    print("🎉 All configuration examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
