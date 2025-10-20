import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for proper imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from network_test.services import ITradingService, ServiceFactory
from network_test.services.broker_configurations import (
    TransformerFactory, initialize_scalable_architecture)

# Configure logging to see what's happening with network requests
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO to reduce noise
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def demonstrate_complete_architecture():
    """
    🏗️ Complete Modular Architecture Demo

    Demonstrates:
    1. Factory Pattern for service creation
    2. Standardized operations across brokers
    3. Design patterns implementation
    4. SOLID principles in action
    """
    print("🚀 COMPLETE MODULAR TRADING ARCHITECTURE DEMO")
    print("=" * 60)

    # Initialize the scalable architecture
    print("\n📋 Step 1: Initializing Architecture...")
    initialize_scalable_architecture()

    # Demo 1: Factory Pattern with Different Services
    print("\n🏭 Step 2: Factory Pattern Demo")
    print("-" * 40)

    # Custom API Service (works with any REST API)
    market_data_endpoints = {
        "market_status": {
            "path": "/v1/status",
            "method": "GET",
            "cache_ttl": 60,
            "description": "Market status information"
        },
        "instruments": {
            "path": "/v1/instruments/{exchange}",
            "method": "GET",
            "cache_ttl": 3600,
            "description": "List of instruments"
        },
        "quotes": {
            "path": "/v1/quotes",
            "method": "POST",
            "cache_ttl": 1,
            "description": "Real-time quotes"
        }
    }

    # Create different services using factory
    services = {
        "market_data": ServiceFactory.create_service(
            "custom",
            base_url="https://api.marketdata.example.com",
            endpoints=market_data_endpoints,
            rate_limit=10,
            timeout=5
        ),
        "upstox_demo": ServiceFactory.create_service(
            "upstox",
            access_token="demo_token_123",
            rate_limit=50
        ),
        "groww_demo": ServiceFactory.create_service(
            "groww",
            session_token="demo_session_456",
            rate_limit=15
        )
    }

    # Demo each service
    for service_name, service in services.items():
        print(f"\n📊 Testing {service_name} service:")
        async with service:
            info = {
                "name": service.get_service_name(),
                "endpoints": list(service.list_endpoints().keys())[:3]  # Show first 3
            }
            print(f"   Service: {info['name']}")
            print(f"   Endpoints: {info['endpoints']}")

    # Demo 2: Standardized Operations
    print("\n🎯 Step 3: Standardized Operations Demo")
    print("-" * 40)

    from network_test.services.parameters import (OrderSide, OrderType,
                                                  ProductType,
                                                  StandardOrderParams)

    # Create standardized order parameters
    standard_order = StandardOrderParams(
        symbol="RELIANCE",
        exchange="NSE",
        quantity=100,
        order_side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        product_type=ProductType.DELIVERY,
        price=2500.0
    )

    print(f"📋 Standard Order Created:")
    print(f"   Symbol: {standard_order.symbol}")
    print(f"   Quantity: {standard_order.quantity}")
    print(f"   Type: {standard_order.order_type.value}")

    # Demo 3: Design Patterns in Action
    print("\n🎨 Step 4: Design Patterns Demo")
    print("-" * 40)

    # Strategy Pattern: Different transformation strategies
    brokers = ['upstox', 'xts']
    test_params = {
        'symbol': 'RELIANCE',
        'quantity': 50,
        'product_type': 'INTRADAY',
        'order_type': 'LIMIT',
        'price': 2500.0
    }

    for broker in brokers:
        try:
            transformer = TransformerFactory.create_transformer(broker)
            result = transformer.transform(test_params)
            print(f"✅ {broker.upper()} transformation successful")
            print(f"   Fields transformed: {len(result)}")
        except Exception as e:
            print(f"❌ {broker.upper()} transformer error: {e}")

    print("\n✅ Complete Architecture Demo Finished!")
    print("\n💡 Key Features Demonstrated:")
    print("  ✓ Factory Pattern for service creation")
    print("  ✓ Strategy Pattern for parameter transformation")
    print("  ✓ Dependency Injection for mappings")
    print("  ✓ Interface Segregation (ITradingService)")
    print("  ✓ Single Responsibility per class")
    print("  ✓ Open/Closed principle for extensibility")


async def demonstrate_solid_principles():
    """
    🎯 SOLID Principles Demonstration

    Shows how each SOLID principle is implemented in the architecture
    """
    print("\n🏛️ SOLID PRINCIPLES DEMONSTRATION")
    print("=" * 50)

    # Single Responsibility Principle
    print("\n1️⃣ SINGLE RESPONSIBILITY PRINCIPLE")
    print("-" * 40)
    print("✅ Each class has ONE reason to change:")
    print("   - ServiceFactory: Only creates services")
    print("   - TransformerFactory: Only creates transformers")
    print("   - UpstoxMappings: Only contains Upstox mappings")
    print("   - NetworkClient: Only handles HTTP requests")

    # Open/Closed Principle
    print("\n2️⃣ OPEN/CLOSED PRINCIPLE")
    print("-" * 40)
    print("✅ Open for extension, closed for modification:")

    # Add a new broker without modifying existing code
    class ZerodhaMappings:
        PRODUCT_TYPE_MAP = {'INTRADAY': 'MIS', 'DELIVERY': 'CNC'}
        FIELD_MAP = {'symbol': 'tradingsymbol', 'quantity': 'quantity'}

    TransformerFactory.register_broker('zerodha', ZerodhaMappings)
    print("   ✅ Added Zerodha broker without modifying existing code!")
    print(f"   📊 Supported brokers: {TransformerFactory.list_supported_brokers()}")

    # Liskov Substitution Principle
    print("\n3️⃣ LISKOV SUBSTITUTION PRINCIPLE")
    print("-" * 40)
    print("✅ All services are interchangeable:")

    # Create different services but use them identically
    async def use_any_service(service: ITradingService):
        service_info = {
            "name": service.get_service_name(),
            "endpoint_count": len(service.list_endpoints())
        }
        return service_info

    # Test with different service implementations
    services = [
        ServiceFactory.create_service("upstox", access_token="demo"),
        ServiceFactory.create_service("groww", session_token="demo"),
        ServiceFactory.create_service("custom", base_url="https://api.example.com", endpoints={})
    ]

    for service in services:
        async with service:
            info = await use_any_service(service)
            print(f"   ✅ Service '{info['name']}' works identically")

    # Interface Segregation Principle
    print("\n4️⃣ INTERFACE SEGREGATION PRINCIPLE")
    print("-" * 40)
    print("✅ Clients depend only on methods they use:")
    print("   - ITradingService: Core service methods")
    print("   - IParameterTransformer: Only transformation")
    print("   - IParameterMapper: Only parameter mapping")

    # Dependency Inversion Principle
    print("\n5️⃣ DEPENDENCY INVERSION PRINCIPLE")
    print("-" * 40)
    print("✅ Depend on abstractions, not concretions:")
    print("   - ServiceFactory depends on ITradingService interface")
    print("   - TransformerFactory depends on IParameterTransformer")
    print("   - High-level modules don't depend on low-level modules")


async def main():
    """
    🚀 Main Entry Point

    Orchestrates the complete demonstration of the modular architecture
    """
    print("🎯 MODULAR TRADING SYSTEM POWERED BY SOLID PRINCIPLES")
    print("=" * 80)

    try:
        # Run complete architecture demo
        await demonstrate_complete_architecture()

        # Demonstrate SOLID principles
        await demonstrate_solid_principles()

        print("\n🎉 ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("\n🏆 Architecture Benefits:")
        print("  🔧 Modular: Easy to maintain and extend")
        print("  🎯 SOLID: Follows all SOLID principles")
        print("  🎨 Patterns: Uses proven design patterns")
        print("  🔄 Flexible: Works with any broker or API")
        print("  📈 Scalable: Easy to add new features")
        print("  🧪 Testable: Clean separation of concerns")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("💡 This might be expected for some demo components")
        return 1

    return 0



if __name__ == "__main__":
    asyncio.run(main())
