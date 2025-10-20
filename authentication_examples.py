"""
Authentication Examples for Trading Services

This demonstrates how to implement and use different authentication
methods with your services.
"""

import asyncio
import base64

from network_test.services import CustomAPIService, GrowwService, UpstoxService


async def demo_upstox_auth():
    """Demo: Upstox authentication with Bearer token and API key"""
    print("🔐 DEMO: Upstox Authentication\n")

    # Method 1: Using config dict
    upstox_config = {
        "base_url": "https://api.upstox.com/v2/",
        "access_token": "your_bearer_token_here",
        "api_key": "your_api_key_here",
        "rate_limit": 100
    }

    async with UpstoxService(config=upstox_config) as upstox:
        print("✅ Upstox service with Bearer token authentication")
        print(f"   Auth header: {upstox.client.default_headers.get('Authorization', 'Not set')}")
        print(f"   API key header: {upstox.client.default_headers.get('X-API-Key', 'Not set')}")

    # Method 2: Direct kwargs
    async with UpstoxService(
        access_token="another_token",
        api_key="another_key",
        rate_limit=50
    ) as upstox2:
        print("✅ Upstox service with direct auth kwargs")
        print(f"   Auth header: {upstox2.client.default_headers.get('Authorization', 'Not set')}")


async def demo_groww_auth():
    """Demo: Groww authentication with session tokens and custom headers"""
    print("\n🌱 DEMO: Groww Authentication\n")

    groww_config = {
        "base_url": "https://groww.in/",
        "session_token": "your_session_token_here",
        "user_agent": "Mozilla/5.0 Custom Groww Client",
        "auth_headers": {
            "X-Custom-Auth": "custom_value",
            "X-Client-ID": "client_123"
        }
    }

    async with GrowwService(config=groww_config) as groww:
        print("✅ Groww service with session token and custom headers")
        print(f"   Session token: {groww.client.default_headers.get('X-Session-Token', 'Not set')}")
        print(f"   Custom auth: {groww.client.default_headers.get('X-Custom-Auth', 'Not set')}")
        print(f"   Client ID: {groww.client.default_headers.get('X-Client-ID', 'Not set')}")


async def demo_custom_service_auth_types():
    """Demo: Different authentication types with CustomAPIService"""
    print("\n🔧 DEMO: Custom Service Authentication Types\n")

    # Bearer Token Authentication
    bearer_endpoints = {
        "profile": {"path": "/user/profile", "method": "GET"}
    }

    bearer_config = {
        "auth": {
            "type": "bearer",
            "token": "your_bearer_token_here"
        }
    }

    async with CustomAPIService(
        base_url="https://api.example.com",
        endpoints=bearer_endpoints,
        **bearer_config
    ) as bearer_service:
        print("✅ Bearer token authentication")
        print(f"   Authorization: {bearer_service.client.default_headers.get('Authorization', 'Not set')}")

    # API Key Authentication
    api_key_endpoints = {
        "data": {"path": "/data", "method": "GET"}
    }

    api_key_config = {
        "auth": {
            "type": "api_key",
            "key": "your_api_key_here",
            "header_name": "X-RapidAPI-Key"  # Custom header name
        }
    }

    async with CustomAPIService(
        base_url="https://rapidapi.com",
        endpoints=api_key_endpoints,
        **api_key_config
    ) as api_service:
        print("✅ API key authentication")
        print(f"   API Key: {api_service.client.default_headers.get('X-RapidAPI-Key', 'Not set')}")

    # Basic Authentication
    basic_endpoints = {
        "protected": {"path": "/protected", "method": "GET"}
    }

    basic_config = {
        "auth": {
            "type": "basic",
            "username": "your_username",
            "password": "your_password"
        }
    }

    async with CustomAPIService(
        base_url="https://httpbin.org",
        endpoints=basic_endpoints,
        **basic_config
    ) as basic_service:
        print("✅ Basic authentication")
        auth_header = basic_service.client.default_headers.get('Authorization', 'Not set')
        print(f"   Authorization: {auth_header}")
        if auth_header.startswith('Basic '):
            # Decode to show what was encoded
            encoded = auth_header.split(' ')[1]
            decoded = base64.b64decode(encoded).decode()
            print(f"   Decoded credentials: {decoded}")

    # Custom Headers Authentication
    custom_endpoints = {
        "webhook": {"path": "/webhook", "method": "POST"}
    }

    custom_config = {
        "auth": {
            "type": "custom",
            "headers": {
                "X-Webhook-Secret": "webhook_secret_123",
                "X-Client-Version": "1.0.0",
                "X-Service-Key": "service_key_456"
            }
        }
    }

    async with CustomAPIService(
        base_url="https://webhook.site",
        endpoints=custom_endpoints,
        **custom_config
    ) as custom_service:
        print("✅ Custom headers authentication")
        for header in ["X-Webhook-Secret", "X-Client-Version", "X-Service-Key"]:
            value = custom_service.client.default_headers.get(header, 'Not set')
            print(f"   {header}: {value}")


async def demo_backwards_compatibility():
    """Demo: Backwards compatibility with direct auth config"""
    print("\n🔄 DEMO: Backwards Compatibility\n")

    endpoints = {
        "test": {"path": "/test", "method": "GET"}
    }

    # Old way - direct in config
    async with CustomAPIService(
        base_url="https://api.example.com",
        endpoints=endpoints,
        access_token="legacy_bearer_token",
        api_key="legacy_api_key"
    ) as legacy_service:
        print("✅ Legacy authentication (backwards compatible)")
        print(f"   Bearer token: {legacy_service.client.default_headers.get('Authorization', 'Not set')}")
        print(f"   API key: {legacy_service.client.default_headers.get('X-API-Key', 'Not set')}")


async def demo_auth_configuration_patterns():
    """Demo: Common authentication configuration patterns"""
    print("\n📋 DEMO: Authentication Configuration Patterns\n")

    # Pattern 1: Environment-based configuration
    import os

    # Simulating environment variables
    os.environ.setdefault("UPSTOX_TOKEN", "env_bearer_token")
    os.environ.setdefault("API_SECRET", "env_api_secret")

    env_config = {
        "auth": {
            "type": "bearer",
            "token": os.getenv("UPSTOX_TOKEN")
        },
        "api_secret": os.getenv("API_SECRET")
    }

    endpoints = {"quotes": {"path": "/quotes", "method": "GET"}}

    async with CustomAPIService(
        base_url="https://api.trading.com",
        endpoints=endpoints,
        **env_config
    ) as env_service:
        print("✅ Environment-based auth configuration")
        print(f"   Token from env: {env_service.client.default_headers.get('Authorization', 'Not set')}")

    # Pattern 2: Multi-service factory with different auth
    def create_authenticated_service(service_name: str, credentials: dict):
        """Factory function for creating services with different auth"""

        service_configs = {
            "trading_api": {
                "base_url": "https://api.trading.com",
                "endpoints": {
                    "orders": {"path": "/orders", "method": "GET"},
                    "positions": {"path": "/positions", "method": "GET"}
                },
                "auth": {
                    "type": "bearer",
                    "token": credentials.get("bearer_token")
                }
            },
            "market_data": {
                "base_url": "https://data.market.com",
                "endpoints": {
                    "live_prices": {"path": "/live/{symbol}", "method": "GET"}
                },
                "auth": {
                    "type": "api_key",
                    "key": credentials.get("api_key"),
                    "header_name": "X-Market-Key"
                }
            },
            "news_api": {
                "base_url": "https://news.financial.com",
                "endpoints": {
                    "headlines": {"path": "/headlines", "method": "GET"}
                },
                "auth": {
                    "type": "custom",
                    "headers": {
                        "X-News-Token": credentials.get("news_token"),
                        "X-Subscription": credentials.get("subscription_tier", "basic")
                    }
                }
            }
        }

        config = service_configs.get(service_name)
        if not config:
            raise ValueError(f"Unknown service: {service_name}")

        return CustomAPIService(
            base_url=config["base_url"],
            endpoints=config["endpoints"],
            **{k: v for k, v in config.items() if k not in ["base_url", "endpoints"]}
        )

    # Example credentials (in real app, these would come from secure storage)
    credentials = {
        "bearer_token": "trading_bearer_123",
        "api_key": "market_key_456",
        "news_token": "news_token_789",
        "subscription_tier": "premium"
    }

    # Create different services with different auth
    service_names = ["trading_api", "market_data", "news_api"]

    for name in service_names:
        service = create_authenticated_service(name, credentials)
        async with service:
            print(f"✅ Created '{name}' service with appropriate auth")
            headers = service.client.default_headers
            auth_headers = {k: v for k, v in headers.items()
                          if any(auth_word in k.lower() for auth_word in ['auth', 'key', 'token', 'subscription'])}
            if auth_headers:
                for header, value in auth_headers.items():
                    print(f"    {header}: {value}")
            else:
                print("    No auth headers found")


async def main():
    """Run all authentication demos"""
    await demo_upstox_auth()
    await demo_groww_auth()
    await demo_custom_service_auth_types()
    await demo_backwards_compatibility()
    await demo_auth_configuration_patterns()

    print("\n🎉 All authentication demos completed!")
    print("\n📚 Summary of supported authentication methods:")
    print("   1. Bearer tokens (Authorization: Bearer <token>)")
    print("   2. API keys (X-API-Key or custom header)")
    print("   3. Basic authentication (Authorization: Basic <encoded>)")
    print("   4. Custom headers (any combination)")
    print("   5. Service-specific authentication (overridden per service)")
    print("   6. Environment-based configuration")
    print("   7. Backwards compatibility with direct config")


if __name__ == "__main__":
    asyncio.run(main())
