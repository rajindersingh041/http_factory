#!/usr/bin/env python3
"""
Network Test - Standardized Trading Service Interface

This script demonstrates the new standardized parameter system that allows
the same code to work with different broker APIs (Upstox, XTS, Groww, etc.).

Usage:
    uv run demo_standardized.py
"""

import asyncio
from decimal import Decimal

from src.network_test.services.parameters import (OrderSide, OrderType,
                                                  ParameterMapperFactory,
                                                  ProductType,
                                                  StandardHistoricalParams,
                                                  StandardOrderParams,
                                                  StandardQuoteParams,
                                                  Validity)


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")


def print_section(title: str):
    """Print a formatted section"""
    print(f"\n📋 {title}")
    print("-" * 40)


async def demo_order_standardization():
    """Demonstrate order parameter standardization across brokers"""
    print_header("ORDER PARAMETER STANDARDIZATION")

    # Create a standard order that works with ANY broker
    order = StandardOrderParams(
        symbol="RELIANCE",
        exchange="NSE",
        quantity=10,
        order_side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        product_type=ProductType.INTRADAY,
        price=Decimal("2500.75"),
        validity=Validity.DAY,
        tag="standardized_demo",
        disclosed_quantity=5,
        trigger_price=Decimal("2400.00")
    )

    print_section("Standard Order Parameters")
    print(f"Symbol: {order.symbol}")
    print(f"Exchange: {order.exchange}")
    print(f"Quantity: {order.quantity}")
    print(f"Side: {order.order_side.value}")
    print(f"Type: {order.order_type.value}")
    print(f"Product: {order.product_type.value}")
    print(f"Price: ₹{order.price}")
    print(f"Validity: {order.validity.value}")
    print(f"Tag: {order.tag}")

    # Show how it maps to different brokers
    brokers = ["upstox", "xts", "groww"]

    for broker_name in brokers:
        print_section(f"{broker_name.title()} Mapped Parameters")

        # Add broker-specific extras if needed
        if broker_name == "xts":
            order.extras["exchangeInstrumentID"] = 26000  # XTS needs instrument ID

        mapper = ParameterMapperFactory.get_mapper(broker_name)
        mapped_params = mapper.map_order_params(order)

        for key, value in mapped_params.items():
            print(f"{key}: {value}")

        print(f"\n✅ Ready for {broker_name.title()} API!")


async def demo_quote_standardization():
    """Demonstrate quote parameter standardization"""
    print_header("QUOTE PARAMETER STANDARDIZATION")

    # Standard quote request
    quote_request = StandardQuoteParams(
        symbols=["RELIANCE", "TCS", "INFY", "WIPRO"],
        exchange="NSE"
    )

    print_section("Standard Quote Parameters")
    print(f"Symbols: {', '.join(quote_request.symbols)}")
    print(f"Exchange: {quote_request.exchange}")

    # Show mapping for each broker
    brokers = ["upstox", "xts", "groww"]

    for broker_name in brokers:
        print_section(f"{broker_name.title()} Quote Format")

        # Add broker-specific extras for XTS
        if broker_name == "xts":
            quote_request.extras["instruments"] = "26000,26009,26051,26017"
            quote_request.extras["xtsMessageCode"] = 1512

        mapper = ParameterMapperFactory.get_mapper(broker_name)
        mapped_params = mapper.map_quote_params(quote_request)

        for key, value in mapped_params.items():
            print(f"{key}: {value}")


async def demo_historical_data_standardization():
    """Demonstrate historical data parameter standardization"""
    print_header("HISTORICAL DATA STANDARDIZATION")

    # Standard historical data request
    historical_request = StandardHistoricalParams(
        symbol="RELIANCE",
        exchange="NSE",
        interval="1d",
        from_date="2024-01-01",
        to_date="2024-01-31",
        limit=100
    )

    print_section("Standard Historical Parameters")
    print(f"Symbol: {historical_request.symbol}")
    print(f"Exchange: {historical_request.exchange}")
    print(f"Interval: {historical_request.interval}")
    print(f"From: {historical_request.from_date}")
    print(f"To: {historical_request.to_date}")
    print(f"Limit: {historical_request.limit}")

    # Show mapping for each broker
    brokers = ["upstox", "xts", "groww"]

    for broker_name in brokers:
        print_section(f"{broker_name.title()} Historical Format")

        # Add broker-specific extras for XTS
        if broker_name == "xts":
            historical_request.extras["exchangeInstrumentID"] = 26000

        mapper = ParameterMapperFactory.get_mapper(broker_name)
        mapped_params = mapper.map_historical_params(historical_request)

        for key, value in mapped_params.items():
            print(f"{key}: {value}")


def demo_benefits():
    """Show the benefits of the standardized approach"""
    print_header("KEY BENEFITS")

    benefits = [
        "🎯 One interface works with ALL brokers",
        "🛡️ Type-safe with enums (no string errors)",
        "🔄 Easy to switch between brokers",
        "📝 Clear, readable parameter names",
        "⚡ Automatic parameter mapping",
        "🔧 Support for broker-specific features",
        "✅ Consistent validation across brokers",
        "🧪 Easy to test and mock",
        "📚 Self-documenting code",
        "🚀 Faster development cycle"
    ]

    for benefit in benefits:
        print(f"   {benefit}")

    print_header("COMPARISON")

    print("❌ OLD WAY (broker-specific):")
    print("   # Different code for each broker")
    print("   await upstox.place_order(quantity=1, product='I', transaction_type='BUY')")
    print("   await xts.place_order(orderQuantity=1, productType='MIS', orderSide='BUY')")
    print("   await groww.place_order(qty=1, side='buy')")

    print("\n✅ NEW WAY (standardized):")
    print("   # Same code for ALL brokers")
    print("   order = StandardOrderParams(quantity=1, product_type=ProductType.INTRADAY, order_side=OrderSide.BUY)")
    print("   await any_broker.place_order_standard(order)")


async def demo_real_world_usage():
    """Show a real-world usage scenario"""
    print_header("REAL-WORLD USAGE SCENARIO")

    print_section("Multi-Broker Trading Strategy")
    print("Scenario: Place the same order across multiple brokers for best execution")

    # Define a standard order
    strategy_order = StandardOrderParams(
        symbol="NIFTY50",
        exchange="NSE",
        quantity=50,
        order_side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        product_type=ProductType.INTRADAY,
        tag="momentum_strategy"
    )

    print(f"\nStrategy Order: {strategy_order.symbol} {strategy_order.order_side.value} {strategy_order.quantity}")

    # Show how it would work with multiple brokers
    broker_configs = [
        {"name": "upstox", "allocation": 60, "extras": {}},
        {"name": "xts", "allocation": 40, "extras": {"exchangeInstrumentID": 26000}},
    ]

    print_section("Broker Allocation")

    for config in broker_configs:
        allocation_qty = int(strategy_order.quantity * config["allocation"] / 100)
        broker_order = StandardOrderParams(
            symbol=strategy_order.symbol,
            exchange=strategy_order.exchange,
            quantity=allocation_qty,
            order_side=strategy_order.order_side,
            order_type=strategy_order.order_type,
            product_type=strategy_order.product_type,
            tag=f"{strategy_order.tag}_{config['name']}",
            extras=config["extras"]
        )

        print(f"\n{config['name'].title()} ({config['allocation']}% allocation):")
        print(f"   Quantity: {allocation_qty}")
        print(f"   Tag: {broker_order.tag}")

        # Show mapped parameters
        mapper = ParameterMapperFactory.get_mapper(config["name"])
        mapped = mapper.map_order_params(broker_order)
        print(f"   Mapped to: {len(mapped)} parameters")

        # In real code, you would do:
        print(f"   💡 Execute: await {config['name']}_service.place_order_standard(broker_order)")


async def main():
    """Main demonstration function"""
    print("🌟 NETWORK TEST - STANDARDIZED TRADING INTERFACE")
    print("=" * 60)
    print("This demo shows how the same code can work with different")
    print("broker APIs using standardized parameters.")

    # Run all demonstrations
    await demo_order_standardization()
    await demo_quote_standardization()
    await demo_historical_data_standardization()
    demo_benefits()
    await demo_real_world_usage()

    print_header("CONCLUSION")
    print("🎉 The standardized parameter system solves the core issue of")
    print("   different brokers requiring different parameter formats!")
    print()
    print("🚀 Next steps:")
    print("   1. Run: uv run python test_parameters_simple.py")
    print("   2. Check: STANDARDIZED_PARAMETERS.md for full documentation")
    print("   3. Try: Creating your own StandardOrderParams")
    print()
    print("✅ Ready for production use!")


if __name__ == "__main__":
    asyncio.run(main())
