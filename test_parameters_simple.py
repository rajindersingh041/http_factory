"""
Simple tests for Standardized Parameter Mapping

This module provides basic tests for the parameter mapping functionality
without requiring pytest or other testing frameworks.
"""

from decimal import Decimal

from src.network_test.services.parameters import (GrowwParameterMapper,
                                                  OrderSide, OrderType,
                                                  ParameterMapperFactory,
                                                  ProductType,
                                                  StandardHistoricalParams,
                                                  StandardOrderParams,
                                                  StandardQuoteParams,
                                                  UpstoxParameterMapper,
                                                  Validity, XTSParameterMapper)


def test_standard_order_params():
    """Test creating and using StandardOrderParams"""
    print("📋 Testing StandardOrderParams...")

    # Create standard order parameters
    params = StandardOrderParams(
        symbol="RELIANCE",
        exchange="NSE",
        quantity=10,
        order_side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        product_type=ProductType.INTRADAY,
        price=Decimal("2500.50"),
        validity=Validity.DAY,
        tag="test_order",
        disclosed_quantity=5,
        trigger_price=Decimal("2400.0"),
        is_amo=False
    )

    # Test basic properties
    assert params.symbol == "RELIANCE"
    assert params.exchange == "NSE"
    assert params.quantity == 10
    assert params.order_side == OrderSide.BUY
    assert params.order_type == OrderType.LIMIT
    assert params.product_type == ProductType.INTRADAY
    assert params.price == Decimal("2500.50")
    assert params.validity == Validity.DAY

    # Test to_dict conversion
    params_dict = params.to_dict()
    assert params_dict["symbol"] == "RELIANCE"
    assert params_dict["order_side"] == "BUY"  # Enum converted to value
    assert params_dict["order_type"] == "LIMIT"

    print("✅ StandardOrderParams: PASSED")


def test_upstox_parameter_mapper():
    """Test Upstox parameter mapping"""
    print("🏛️ Testing Upstox Parameter Mapper...")

    mapper = UpstoxParameterMapper()

    # Test order mapping
    params = StandardOrderParams(
        symbol="RELIANCE",
        exchange="NSE",
        quantity=10,
        order_side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        product_type=ProductType.INTRADAY,
        price=2500.50,
        validity=Validity.DAY,
        tag="upstox_test",
        disclosed_quantity=5,
        trigger_price=2400.0,
        is_amo=True
    )

    result = mapper.map_order_params(params)

    # Verify Upstox-specific mappings
    assert result["quantity"] == 10
    assert result["product"] == "I"  # INTRADAY -> I
    assert result["validity"] == "DAY"
    assert result["price"] == 2500.50
    assert result["tag"] == "upstox_test"
    assert result["instrument_token"] == "NSE_RELIANCE"
    assert result["order_type"] == "LIMIT"
    assert result["transaction_type"] == "BUY"
    assert result["disclosed_quantity"] == 5
    assert result["trigger_price"] == 2400.0
    assert result["is_amo"] is True

    # Test quote mapping
    quote_params = StandardQuoteParams(
        symbols=["RELIANCE", "TCS"],
        exchange="NSE"
    )

    quote_result = mapper.map_quote_params(quote_params)
    assert quote_result["instrument_key"] == "NSE_RELIANCE,NSE_TCS"

    print("✅ Upstox Parameter Mapper: PASSED")


def test_xts_parameter_mapper():
    """Test XTS parameter mapping"""
    print("🏛️ Testing XTS Parameter Mapper...")

    mapper = XTSParameterMapper()

    # Test order mapping
    params = StandardOrderParams(
        symbol="RELIANCE",
        exchange="NSE",
        quantity=10,
        order_side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        product_type=ProductType.INTRADAY,
        price=2500.50,
        validity=Validity.DAY,
        disclosed_quantity=5,
        trigger_price=2400.0,
        extras={"exchangeInstrumentID": 26000}
    )

    result = mapper.map_order_params(params)

    # Verify XTS-specific mappings
    assert result["exchangeSegment"] == "NSECM"  # NSE -> NSECM
    assert result["exchangeInstrumentID"] == 26000
    assert result["productType"] == "MIS"  # INTRADAY -> MIS
    assert result["orderType"] == "LIMIT"
    assert result["orderSide"] == "BUY"
    assert result["timeInForce"] == "DAY"  # Validity -> timeInForce
    assert result["disclosedQuantity"] == 5
    assert result["orderQuantity"] == 10  # quantity -> orderQuantity
    assert result["limitPrice"] == 2500.50  # price -> limitPrice
    assert result["stopPrice"] == 2400.0  # trigger_price -> stopPrice

    # Test exchange segment mapping
    exchange_tests = [
        ("NSE", "NSECM"),
        ("BSE", "BSECM"),
        ("NFO", "NSEFO"),
        ("BFO", "BSEFO"),
    ]

    for input_exchange, expected_segment in exchange_tests:
        test_params = StandardOrderParams(
            symbol="TEST",
            exchange=input_exchange,
            quantity=1,
            order_side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            product_type=ProductType.INTRADAY,
            extras={"exchangeInstrumentID": 123}
        )

        test_result = mapper.map_order_params(test_params)
        assert test_result["exchangeSegment"] == expected_segment

    print("✅ XTS Parameter Mapper: PASSED")


def test_groww_parameter_mapper():
    """Test Groww parameter mapping"""
    print("🏛️ Testing Groww Parameter Mapper...")

    mapper = GrowwParameterMapper()

    # Test order mapping
    params = StandardOrderParams(
        symbol="RELIANCE",
        exchange="NSE",
        quantity=10,
        order_side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        product_type=ProductType.INTRADAY,
        price=2500.50
    )

    result = mapper.map_order_params(params)

    assert result["symbol"] == "RELIANCE"
    assert result["exchange"] == "NSE"
    assert result["qty"] == 10
    assert result["side"] == "buy"  # Lowercase
    assert result["orderType"] == "limit"  # Lowercase

    print("✅ Groww Parameter Mapper: PASSED")


def test_parameter_mapper_factory():
    """Test ParameterMapperFactory functionality"""
    print("🏭 Testing ParameterMapperFactory...")

    # Test getting mappers
    upstox_mapper = ParameterMapperFactory.get_mapper("upstox")
    assert isinstance(upstox_mapper, UpstoxParameterMapper)
    assert upstox_mapper.get_broker_name() == "upstox"

    xts_mapper = ParameterMapperFactory.get_mapper("xts")
    assert isinstance(xts_mapper, XTSParameterMapper)
    assert xts_mapper.get_broker_name() == "xts"

    groww_mapper = ParameterMapperFactory.get_mapper("groww")
    assert isinstance(groww_mapper, GrowwParameterMapper)
    assert groww_mapper.get_broker_name() == "groww"

    # Test listing supported services
    services = ParameterMapperFactory.list_supported_services()
    assert "upstox" in services
    assert "xts" in services
    assert "groww" in services

    print("✅ ParameterMapperFactory: PASSED")


def test_end_to_end_mapping():
    """Test complete end-to-end parameter mapping"""
    print("🔄 Testing End-to-End Parameter Mapping...")

    # Create standard parameters
    standard_params = StandardOrderParams(
        symbol="RELIANCE",
        exchange="NSE",
        quantity=10,
        order_side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        product_type=ProductType.INTRADAY,
        price=2500.50,
        validity=Validity.DAY,
        tag="e2e_test",
        disclosed_quantity=5,
        trigger_price=2400.0,
        is_amo=False,
        extras={"exchangeInstrumentID": 26000}  # For XTS
    )

    # Test mapping for each broker
    brokers = ["upstox", "xts", "groww"]

    for broker_name in brokers:
        mapper = ParameterMapperFactory.get_mapper(broker_name)
        mapped_params = mapper.map_order_params(standard_params)

        # Each broker should have different mapped format
        assert isinstance(mapped_params, dict)
        assert len(mapped_params) > 0

        # But all should contain the core information
        if broker_name == "upstox":
            assert mapped_params["quantity"] == 10
            assert mapped_params["transaction_type"] == "BUY"
            assert mapped_params["order_type"] == "LIMIT"
        elif broker_name == "xts":
            assert mapped_params["orderQuantity"] == 10
            assert mapped_params["orderSide"] == "BUY"
            assert mapped_params["orderType"] == "LIMIT"
        elif broker_name == "groww":
            assert mapped_params["qty"] == 10
            assert mapped_params["side"] == "buy"
            assert mapped_params["orderType"] == "limit"

    print("✅ End-to-End Mapping: PASSED")


def demo_parameter_mapping():
    """Demonstrate parameter mapping for different brokers"""
    print("\n🚀 DEMO: Parameter Mapping Across Brokers\n")

    # Create standardized order parameters
    params = StandardOrderParams(
        symbol="RELIANCE",
        exchange="NSE",
        quantity=10,
        order_side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        product_type=ProductType.INTRADAY,
        price=2500.50,
        validity=Validity.DAY,
        tag="demo_order",
        disclosed_quantity=5,
        trigger_price=2400.0,
        is_amo=False,
        extras={"exchangeInstrumentID": 26000}  # For XTS
    )

    print("📋 Original Standardized Parameters:")
    print(f"   Symbol: {params.symbol}")
    print(f"   Exchange: {params.exchange}")
    print(f"   Quantity: {params.quantity}")
    print(f"   Side: {params.order_side.value}")
    print(f"   Type: {params.order_type.value}")
    print(f"   Product: {params.product_type.value}")
    print(f"   Price: ₹{params.price}")
    print(f"   Validity: {params.validity.value}")

    # Map to each broker format
    brokers = ["upstox", "xts", "groww"]

    for broker_name in brokers:
        print(f"\n🏛️ {broker_name.title()} Mapped Parameters:")

        mapper = ParameterMapperFactory.get_mapper(broker_name)
        mapped = mapper.map_order_params(params)

        for key, value in mapped.items():
            print(f"   {key}: {value}")


def main():
    """Run all tests"""
    print("🧪 Running Standardized Parameter Tests\n")

    try:
        # Run all tests
        test_standard_order_params()
        test_upstox_parameter_mapper()
        test_xts_parameter_mapper()
        test_groww_parameter_mapper()
        test_parameter_mapper_factory()
        test_end_to_end_mapping()

        print("\n🎉 All Tests PASSED!")

        # Run demo
        demo_parameter_mapping()

        print("\n✅ Parameter mapping system is working correctly!")
        print("\n📚 Key Benefits:")
        print("   1. Same StandardOrderParams work with any broker")
        print("   2. Automatic mapping to broker-specific formats")
        print("   3. Type-safe with enums")
        print("   4. Support for broker-specific extras")
        print("   5. Consistent interface across all brokers")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
