"""
Standardized Parameter Usage Examples

This demonstrates how to use the new standardized parameter system
that works consistently across all broker services.
"""

import asyncio
from decimal import Decimal

from src.network_test.services import GrowwService, UpstoxService, XTSService
from src.network_test.services.parameters import (OrderSide, OrderType,
                                                  ProductType,
                                                  StandardHistoricalParams,
                                                  StandardOrderParams,
                                                  StandardQuoteParams,
                                                  Validity)


async def demo_standardized_order_placement():
    """Demo: Placing orders with standardized parameters across different brokers"""
    print("🚀 DEMO: Standardized Order Placement\n")

    # Create standardized order parameters
    order_params = StandardOrderParams(
        symbol="RELIANCE",
        exchange="NSE",
        quantity=1,
        order_side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        product_type=ProductType.INTRADAY,
        price=Decimal("2500.50"),
        validity=Validity.DAY,
        tag="demo_order",
        disclosed_quantity=0
    )

    print("📋 Standardized Order Parameters:")
    print(f"   Symbol: {order_params.symbol}")
    print(f"   Exchange: {order_params.exchange}")
    print(f"   Quantity: {order_params.quantity}")
    print(f"   Side: {order_params.order_side.value}")
    print(f"   Type: {order_params.order_type.value}")
    print(f"   Product: {order_params.product_type.value}")
    print(f"   Price: ₹{order_params.price}")
    print(f"   Validity: {order_params.validity.value}")

    # Demo with different brokers
    brokers = [
        {"name": "Upstox", "service": UpstoxService, "config": {}},
        {"name": "XTS", "service": XTSService, "config": {"exchangeInstrumentID": 26000}},
        {"name": "Groww", "service": GrowwService, "config": {}}
    ]

    for broker in brokers:
        print(f"\n🏛️ {broker['name']} Broker:")

        # Add broker-specific extras if needed
        if broker['config']:
            order_params.extras.update(broker['config'])

        try:
            # This would work the same way for all brokers!
            service = broker['service']()

            # Get the broker-specific mapped parameters
            from src.network_test.services.parameters import \
                ParameterMapperFactory
            mapper = ParameterMapperFactory.get_mapper(service.get_service_name())
            mapped_params = mapper.map_order_params(order_params)

            print(f"   ✅ Mapped Parameters: {mapped_params}")
            print("   ℹ️ Would execute: await service.place_order_standard(order_params)")

        except Exception as e:
            print(f"   ❌ Error: {e}")


async def demo_standardized_quotes():
    """Demo: Getting quotes with standardized parameters"""
    print("\n📈 DEMO: Standardized Quote Retrieval\n")

    # Create standardized quote parameters
    quote_params = StandardQuoteParams(
        symbols=["RELIANCE", "TCS", "INFY"],
        exchange="NSE"
    )

    print("📋 Standardized Quote Parameters:")
    print(f"   Symbols: {quote_params.symbols}")
    print(f"   Exchange: {quote_params.exchange}")

    # Demo with different brokers
    brokers = ["upstox", "xts", "groww"]

    for broker_name in brokers:
        print(f"\n🏛️ {broker_name.title()} Broker:")

        try:
            from src.network_test.services.parameters import \
                ParameterMapperFactory
            mapper = ParameterMapperFactory.get_mapper(broker_name)
            mapped_params = mapper.map_quote_params(quote_params)

            print(f"   ✅ Mapped Parameters: {mapped_params}")
            print("   ℹ️ Would execute: await service.get_quotes_standard(quote_params)")

        except Exception as e:
            print(f"   ❌ Error: {e}")


async def demo_standardized_historical_data():
    """Demo: Getting historical data with standardized parameters"""
    print("\n📊 DEMO: Standardized Historical Data\n")

    # Create standardized historical data parameters
    historical_params = StandardHistoricalParams(
        symbol="RELIANCE",
        exchange="NSE",
        interval="1d",  # 1 day candles
        from_date="2024-01-01",
        to_date="2024-01-31",
        limit=100
    )

    print("📋 Standardized Historical Parameters:")
    print(f"   Symbol: {historical_params.symbol}")
    print(f"   Exchange: {historical_params.exchange}")
    print(f"   Interval: {historical_params.interval}")
    print(f"   From: {historical_params.from_date}")
    print(f"   To: {historical_params.to_date}")
    print(f"   Limit: {historical_params.limit}")

    # Demo with different brokers
    brokers = ["upstox", "xts", "groww"]

    for broker_name in brokers:
        print(f"\n🏛️ {broker_name.title()} Broker:")

        try:
            from src.network_test.services.parameters import \
                ParameterMapperFactory
            mapper = ParameterMapperFactory.get_mapper(broker_name)
            mapped_params = mapper.map_historical_params(historical_params)

            print(f"   ✅ Mapped Parameters: {mapped_params}")
            print("   ℹ️ Would execute: await service.get_historical_data_standard(historical_params)")

        except Exception as e:
            print(f"   ❌ Error: {e}")


async def demo_comparison_old_vs_new():
    """Demo: Comparison between old broker-specific and new standardized approach"""
    print("\n🔄 DEMO: Old vs New Approach Comparison\n")

    print("❌ OLD WAY - Broker-specific parameters:")
    print("   # Upstox")
    print("   await upstox.place_order(")
    print("       quantity=1, product='I', validity='DAY', price=2500.50,")
    print("       tag='demo', instrument_token='NSE_RELIANCE',")
    print("       order_type='LIMIT', transaction_type='BUY'")
    print("   )")
    print()
    print("   # XTS")
    print("   await xts.place_order(")
    print("       exchangeSegment='NSECM', exchangeInstrumentID=26000,")
    print("       productType='MIS', orderType='LIMIT', orderSide='BUY',")
    print("       timeInForce='DAY', orderQuantity=1, limitPrice=2500.50")
    print("   )")
    print()
    print("   # Groww")
    print("   await groww.place_order(")
    print("       symbol='RELIANCE', exchange='NSE', qty=1,")
    print("       side='buy', orderType='limit', price=2500.50")
    print("   )")

    print("\n✅ NEW WAY - Standardized parameters:")
    print("   # Works with ANY broker!")
    print("   order_params = StandardOrderParams(")
    print("       symbol='RELIANCE', exchange='NSE', quantity=1,")
    print("       order_side=OrderSide.BUY, order_type=OrderType.LIMIT,")
    print("       product_type=ProductType.INTRADAY, price=2500.50")
    print("   )")
    print()
    print("   await any_broker_service.place_order_standard(order_params)")

    print("\n🎯 Benefits of New Approach:")
    print("   ✅ Same code works with any broker")
    print("   ✅ Type-safe with enums")
    print("   ✅ Clear, readable parameter names")
    print("   ✅ Consistent validation")
    print("   ✅ Easy to switch brokers")
    print("   ✅ Reduced errors from wrong parameter names")


async def demo_advanced_usage():
    """Demo: Advanced usage with broker-specific extras"""
    print("\n🚀 DEMO: Advanced Usage with Broker-Specific Features\n")

    # Base order with standard parameters
    base_order = StandardOrderParams(
        symbol="RELIANCE",
        exchange="NSE",
        quantity=10,
        order_side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        product_type=ProductType.INTRADAY,
        price=2500.0
    )

    print("📋 Base Order (works everywhere):")
    print(f"   {base_order.symbol} {base_order.order_side.value} {base_order.quantity} @ ₹{base_order.price}")

    # Upstox-specific features
    upstox_order = StandardOrderParams(
        symbol=base_order.symbol,
        exchange=base_order.exchange,
        quantity=base_order.quantity,
        order_side=base_order.order_side,
        order_type=base_order.order_type,
        product_type=base_order.product_type,
        price=base_order.price,
        extras={
            "is_amo": True,  # After Market Order
            "user_order_id": "UPX123"  # Upstox custom field
        }
    )

    print("\n🏛️ Upstox-Enhanced Order:")
    print("   Base order + After Market Order + Custom User ID")
    print(f"   Extras: {upstox_order.extras}")

    # XTS-specific features
    xts_order = StandardOrderParams(
        symbol=base_order.symbol,
        exchange=base_order.exchange,
        quantity=base_order.quantity,
        order_side=base_order.order_side,
        order_type=base_order.order_type,
        product_type=base_order.product_type,
        price=base_order.price,
        extras={
            "exchangeInstrumentID": 26000,  # Required by XTS
            "parentOrderId": "XTS456",      # For bracket orders
            "orderUniqueIdentifier": "XTS_UNIQUE_123"
        }
    )

    print("\n🏛️ XTS-Enhanced Order:")
    print("   Base order + Instrument ID + Parent Order + Unique ID")
    print(f"   Extras: {xts_order.extras}")

    # Show how the same standardized interface handles all cases
    print("\n✅ Usage (same for all brokers):")
    print("   await upstox_service.place_order_standard(upstox_order)")
    print("   await xts_service.place_order_standard(xts_order)")
    print("   # Automatically maps extras to broker-specific format!")


async def main():
    """Run all demos"""
    await demo_standardized_order_placement()
    await demo_standardized_quotes()
    await demo_standardized_historical_data()
    await demo_comparison_old_vs_new()
    await demo_advanced_usage()

    print("\n🎉 All demos completed!")
    print("\n📚 Key Takeaways:")
    print("   1. Use StandardOrderParams for consistent order placement")
    print("   2. Use StandardQuoteParams for consistent quote retrieval")
    print("   3. Use StandardHistoricalParams for consistent historical data")
    print("   4. Add broker-specific features via 'extras' parameter")
    print("   5. Same code works across all supported brokers!")


if __name__ == "__main__":
    asyncio.run(main())
