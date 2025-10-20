#!/usr/bin/env python3
"""
🚀 Simple Demo - Complete Modular Architecture

This script demonstrates the key benefits of the modular architecture:
1. Works with `uv run` out of the box
2. Shows SOLID principles in action
3. Demonstrates design patterns
4. Easy to extend and maintain

Usage: uv run python simple_demo.py
"""

import asyncio
import sys
from pathlib import Path

# Ensure proper imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def main():
    print("🎯 SIMPLE MODULAR ARCHITECTURE DEMO")
    print("=" * 50)

    try:
        # Import the components
        from network_test.services import ServiceFactory
        from network_test.services.broker_configurations import \
            TransformerFactory

        print("✅ All imports successful!")

        # 1. Factory Pattern - Create services easily
        print("\\n🏭 Factory Pattern:")
        service = ServiceFactory.create_service("upstox", access_token="demo")
        print(f"   Created service: {service.get_service_name()}")

        # 2. Interface Pattern - Same interface for all services
        print("\\n🔌 Unified Interface:")
        async with service:
            endpoints = service.list_endpoints()
            print(f"   Available endpoints: {len(endpoints)}")

        # 3. Strategy Pattern - Parameter transformation
        print("\\n🔄 Strategy Pattern:")
        params = {'symbol': 'RELIANCE', 'quantity': 100, 'product_type': 'INTRADAY'}

        transformer = TransformerFactory.create_transformer('upstox')
        result = transformer.transform(params)
        print(f"   Transformed {len(params)} → {len(result)} fields")

        # 4. Open/Closed Principle - Add new broker
        print("\\n📈 Open/Closed Principle:")
        class NewBrokerMappings:
            FIELD_MAP = {'symbol': 'instrument', 'quantity': 'qty'}

        TransformerFactory.register_broker('new_broker', NewBrokerMappings)
        brokers = TransformerFactory.list_supported_brokers()
        print(f"   Supported brokers: {brokers}")

        print("\\n🎉 SUCCESS! Architecture working perfectly with uv!")
        print("\\n💡 Key Benefits Shown:")
        print("  ✓ Easy service creation with Factory Pattern")
        print("  ✓ Consistent interface across all services")
        print("  ✓ Automatic parameter transformation")
        print("  ✓ Easy extension without code modification")
        print("  ✓ SOLID principles implementation")

        return 0

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the project directory")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
