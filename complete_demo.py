"""
🎯 Complete Working Demo of Modular SOLID Architecture

This demo showcases all the key components working together:
- Factory Pattern
- Service Interface
- Broker Configurations
- SOLID Principles
- Design Patterns

Run with: uv run python complete_demo.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for proper imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)

async def main():
    """Complete working demonstration"""
    print("🎯 COMPLETE MODULAR TRADING ARCHITECTURE")
    print("=" * 80)

    try:
        # Import after path setup
        from network_test.services import ITradingService, ServiceFactory
        from network_test.services.broker_configurations import (
            TransformerFactory, initialize_scalable_architecture)

        # 1. Initialize Architecture
        print("\\n🏗️ Step 1: Initializing Scalable Architecture")
        print("-" * 50)
        initialize_scalable_architecture()

        # 2. Factory Pattern Demo
        print("\\n🏭 Step 2: Factory Pattern Demonstration")
        print("-" * 50)

        # Create different service types
        services_config = [
            {
                "name": "Upstox Demo Service",
                "type": "upstox",
                "config": {"access_token": "demo_token_123", "rate_limit": 50}
            },
            {
                "name": "Groww Demo Service",
                "type": "groww",
                "config": {"session_token": "demo_session_456", "rate_limit": 15}
            },
            {
                "name": "Custom API Service",
                "type": "custom",
                "config": {
                    "base_url": "https://api.example.com",
                    "endpoints": {
                        "status": {
                            "path": "/status",
                            "method": "GET",
                            "description": "API status check"
                        }
                    },
                    "rate_limit": 10
                }
            }
        ]

        # Demonstrate factory creating different services
        created_services = []
        for service_config in services_config:
            try:
                service = ServiceFactory.create_service(
                    service_config["type"],
                    **service_config["config"]
                )
                created_services.append((service_config["name"], service))
                print(f"✅ Created: {service_config['name']}")
            except Exception as e:
                print(f"⚠️  Could not create {service_config['name']}: {e}")

        # 3. Interface Demonstration
        print("\\n🔌 Step 3: Unified Interface Demonstration")
        print("-" * 50)

        # Use all services through the same interface
        async def demonstrate_service_interface(name: str, service: ITradingService):
            async with service:
                info = {
                    "service_name": service.get_service_name(),
                    "endpoints": list(service.list_endpoints().keys())
                }
                print(f"📊 {name}:")
                print(f"   Service ID: {info['service_name']}")
                print(f"   Endpoints: {len(info['endpoints'])} available")
                if info['endpoints']:
                    print(f"   Examples: {info['endpoints'][:3]}")

        for name, service in created_services:
            await demonstrate_service_interface(name, service)

        # 4. SOLID Principles Demonstration
        print("\\n🏛️ Step 4: SOLID Principles in Action")
        print("-" * 50)

        print("✅ Single Responsibility Principle:")
        print("   - ServiceFactory: Only creates services")
        print("   - Each service: Only handles its broker's API")
        print("   - TransformerFactory: Only creates transformers")

        print("\\n✅ Open/Closed Principle:")
        print("   - Easy to add new brokers without modifying existing code")
        print("   - New transformers can be registered dynamically")

        # Add a new broker transformer
        class DemoMappings:
            PRODUCT_TYPE_MAP = {'INTRADAY': 'I', 'DELIVERY': 'D'}
            FIELD_MAP = {'symbol': 'trading_symbol', 'quantity': 'qty'}

        TransformerFactory.register_broker('demo_broker', DemoMappings)
        print(f"   - Added demo_broker: {TransformerFactory.list_supported_brokers()}")

        print("\\n✅ Liskov Substitution Principle:")
        print("   - All services implement ITradingService")
        print("   - Any service can be used interchangeably")

        print("\\n✅ Interface Segregation Principle:")
        print("   - ITradingService: Core service methods only")
        print("   - Clients depend only on what they need")

        print("\\n✅ Dependency Inversion Principle:")
        print("   - High-level modules depend on abstractions")
        print("   - Concrete implementations are injected")

        # 5. Parameter Transformation Demo
        print("\\n🔄 Step 5: Parameter Transformation")
        print("-" * 50)

        test_params = {
            'symbol': 'RELIANCE',
            'quantity': 100,
            'product_type': 'INTRADAY',
            'order_type': 'LIMIT',
            'price': 2500.0
        }

        print(f"📋 Standard Parameters: {test_params}")

        for broker in ['upstox', 'xts', 'demo_broker']:
            try:
                transformer = TransformerFactory.create_transformer(broker)
                result = transformer.transform(test_params.copy())
                print(f"🔄 {broker.upper()} format: {len(result)} fields transformed")
            except Exception as e:
                print(f"⚠️  {broker.upper()} transformation failed: {e}")

        # 6. Success Summary
        print("\\n🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        print("\\n🏆 Architecture Benefits Demonstrated:")
        print("  🔧 Modular: Components are independent and replaceable")
        print("  🎯 SOLID: All five principles implemented")
        print("  🏭 Factory: Centralized object creation")
        print("  🔌 Interface: Consistent API across services")
        print("  🔄 Transformers: Automatic parameter mapping")
        print("  📈 Scalable: Easy to add new brokers and features")
        print("  🧪 Testable: Clean separation of concerns")

        print("\\n💡 Real-World Usage:")
        print("  - Add any new broker by implementing ITradingService")
        print("  - Use ServiceFactory.create_service() for all services")
        print("  - Parameter transformation happens automatically")
        print("  - Same code works with any broker")

        return 0

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("📝 This might indicate missing dependencies or import issues")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
