"""
Test script to verify the refactored services work correctly with the abstract base class.
"""

import asyncio
# import os
# import sys
import traceback

from network_test.services import GrowwService, UpstoxService, BaseTradingService

# Add the src directory to the path
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))



async def test_upstox_service():
    """Test the refactored UpstoxService"""
    print("Testing UpstoxService...")

    # Create service instance
    service = UpstoxService()

    # Test that endpoints are available
    endpoints = service.list_endpoints()
    print(f"UpstoxService has {len(endpoints)} endpoints:")
    for name, description in endpoints.items():
        print(f"  - {name}: {description}")

    # Test configuration
    config = service.get_default_config()
    print(f"UpstoxService default config: {config.get('base_url', 'N/A')}")

    await service.client.close()
    print("UpstoxService test completed\n")




async def test_upstox_service_v2():
    """Test the refactored UpstoxService"""
    print("Testing UpstoxService...")

    # Create service instance
    service = BaseTradingService()


    # Test that endpoints are available
    endpoints = service.list_endpoints()
    print(f"UpstoxService has {len(endpoints)} endpoints:")
    for name, description in endpoints.items():
        print(f"  - {name}: {description}")

    # Test configuration
    config = service.get_default_config()
    print(f"UpstoxService default config: {config.get('base_url', 'N/A')}")

    await service.client.close()
    print("UpstoxService test completed\n")


async def test_groww_service():
    """Test the refactored GrowwService"""
    print("Testing GrowwService...")

    # Create service instance
    service = GrowwService()

    # Test that endpoints are available
    endpoints = service.list_endpoints()
    print(f"GrowwService has {len(endpoints)} endpoints:")
    for name, description in endpoints.items():
        print(f"  - {name}: {description}")

    # Test configuration
    config = service.get_default_config()
    print(f"GrowwService default config: {config.get('base_url', 'N/A')}")

    await service.client.close()
    print("GrowwService test completed\n")


async def test_polymorphism():
    """Test that both services work with the abstract base class interface"""
    print("Testing polymorphism...")

    services = [UpstoxService(), GrowwService()]

    for service in services:
        service_name = service.__class__.__name__
        print(f"{service_name}:")
        print(f"  Base URL: {service.get_default_base_url()}")
        print(f"  Endpoints: {len(service.get_service_endpoints())}")
        await service.client.close()

    print("Polymorphism test completed\n")


async def main():
    """Main test function"""
    print("=" * 50)
    print("TESTING REFACTORED SERVICES")
    print("=" * 50)

    try:
        await test_upstox_service()
        await test_groww_service()
        await test_polymorphism()

        print("✅ All tests passed! Services are working correctly with abstract base class.")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
