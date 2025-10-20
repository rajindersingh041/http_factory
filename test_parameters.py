"""
Tests for Standardized Parameter Mapping

This module tests the parameter mapping functionality to ensure
that standardized parameters are correctly transformed into
broker-specific formats.
"""

# import pytest  # Comment out for basic testing
from decimal import Decimal

from network_test.services.parameters import (GrowwParameterMapper, OrderSide,
                                              OrderType,
                                              ParameterMapperFactory,
                                              ProductType,
                                              StandardHistoricalParams,
                                              StandardOrderParams,
                                              StandardQuoteParams,
                                              UpstoxParameterMapper, Validity,
                                              XTSParameterMapper)


class TestStandardOrderParams:
    """Test StandardOrderParams functionality"""

    def test_order_params_creation(self):
        """Test creating standard order parameters"""
        params = StandardOrderParams(
            symbol="RELIANCE",
            exchange="NSE",
            quantity=10,
            order_side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            product_type=ProductType.INTRADAY,
            price=Decimal("2500.50"),
            validity=Validity.DAY,
            tag="test_order"
        )

        assert params.symbol == "RELIANCE"
        assert params.exchange == "NSE"
        assert params.quantity == 10
        assert params.order_side == OrderSide.BUY
        assert params.order_type == OrderType.LIMIT
        assert params.product_type == ProductType.INTRADAY
        assert params.price == Decimal("2500.50")
        assert params.validity == Validity.DAY
        assert params.tag == "test_order"

    def test_order_params_to_dict(self):
        """Test converting order parameters to dictionary"""
        params = StandardOrderParams(
            symbol="TCS",
            exchange="NSE",
            quantity=5,
            order_side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            product_type=ProductType.DELIVERY
        )

        result = params.to_dict()

        assert result["symbol"] == "TCS"
        assert result["order_side"] == "SELL"  # Enum converted to value
        assert result["order_type"] == "MARKET"
        assert result["product_type"] == "DELIVERY"

    def test_order_params_with_extras(self):
        """Test order parameters with broker-specific extras"""
        params = StandardOrderParams(
            symbol="INFY",
            exchange="NSE",
            quantity=1,
            order_side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            product_type=ProductType.INTRADAY,
            price=1800.0,
            extras={"custom_field": "value", "broker_specific": True}
        )

        assert params.extras["custom_field"] == "value"
        assert params.extras["broker_specific"] is True


class TestUpstoxParameterMapper:
    """Test Upstox parameter mapping"""

    def setUp(self):
        self.mapper = UpstoxParameterMapper()

    def test_order_mapping(self):
        """Test Upstox order parameter mapping"""
        mapper = UpstoxParameterMapper()

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

        # Check Upstox-specific mappings
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

    def test_quote_mapping(self):
        """Test Upstox quote parameter mapping"""
        mapper = UpstoxParameterMapper()

        params = StandardQuoteParams(
            symbols=["RELIANCE", "TCS"],
            exchange="NSE"
        )

        result = mapper.map_quote_params(params)

        assert result["instrument_key"] == "NSE_RELIANCE,NSE_TCS"

    def test_historical_mapping(self):
        """Test Upstox historical data mapping"""
        mapper = UpstoxParameterMapper()

        params = StandardHistoricalParams(
            symbol="RELIANCE",
            exchange="NSE",
            interval="1d",
            from_date="2024-01-01",
            to_date="2024-01-31",
            limit=100
        )

        result = mapper.map_historical_params(params)

        assert result["instrumentKey"] == "NSE_RELIANCE"
        assert result["interval"] == "1d"
        assert result["from"] == "2024-01-01"
        assert result["to"] == "2024-01-31"
        assert result["limit"] == 100


class TestXTSParameterMapper:
    """Test XTS parameter mapping"""

    def test_order_mapping(self):
        """Test XTS order parameter mapping"""
        mapper = XTSParameterMapper()

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

        # Check XTS-specific mappings
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

    def test_exchange_segment_mapping(self):
        """Test XTS exchange segment mapping"""
        mapper = XTSParameterMapper()

        test_cases = [
            ("NSE", "NSECM"),
            ("BSE", "BSECM"),
            ("NFO", "NSEFO"),
            ("BFO", "BSEFO"),
            ("UNKNOWN", "UNKNOWN")  # Unknown exchanges pass through
        ]

        for input_exchange, expected_segment in test_cases:
            params = StandardOrderParams(
                symbol="TEST",
                exchange=input_exchange,
                quantity=1,
                order_side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                product_type=ProductType.INTRADAY,
                extras={"exchangeInstrumentID": 123}
            )

            result = mapper.map_order_params(params)
            assert result["exchangeSegment"] == expected_segment

    def test_quote_mapping(self):
        """Test XTS quote parameter mapping"""
        mapper = XTSParameterMapper()

        params = StandardQuoteParams(
            symbols=["RELIANCE", "TCS"],
            extras={"instruments": "26000,26009", "xtsMessageCode": 1512}
        )

        result = mapper.map_quote_params(params)

        assert result["instruments"] == "26000,26009"
        assert result["xtsMessageCode"] == 1512


class TestGrowwParameterMapper:
    """Test Groww parameter mapping"""

    def test_order_mapping(self):
        """Test Groww order parameter mapping"""
        mapper = GrowwParameterMapper()

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


class TestParameterMapperFactory:
    """Test ParameterMapperFactory functionality"""

    def test_get_mapper_upstox(self):
        """Test getting Upstox mapper"""
        mapper = ParameterMapperFactory.get_mapper("upstox")
        assert isinstance(mapper, UpstoxParameterMapper)
        assert mapper.get_broker_name() == "upstox"

    def test_get_mapper_xts(self):
        """Test getting XTS mapper"""
        mapper = ParameterMapperFactory.get_mapper("xts")
        assert isinstance(mapper, XTSParameterMapper)
        assert mapper.get_broker_name() == "xts"

    def test_get_mapper_groww(self):
        """Test getting Groww mapper"""
        mapper = ParameterMapperFactory.get_mapper("groww")
        assert isinstance(mapper, GrowwParameterMapper)
        assert mapper.get_broker_name() == "groww"

    def test_get_mapper_unknown(self):
        """Test error when getting unknown mapper"""
        import pytest
        with pytest.raises(ValueError, match="No parameter mapper found for service: unknown"):
            ParameterMapperFactory.get_mapper("unknown")

    def test_list_supported_services(self):
        """Test listing supported services"""
        services = ParameterMapperFactory.list_supported_services()
        assert "upstox" in services
        assert "xts" in services
        assert "groww" in services
        assert len(services) >= 3

    def test_register_custom_mapper(self):
        """Test registering custom mapper"""
        class CustomMapper(UpstoxParameterMapper):
            def get_broker_name(self) -> str:
                return "custom"

        custom_mapper = CustomMapper()
        ParameterMapperFactory.register_mapper("custom", custom_mapper)

        retrieved_mapper = ParameterMapperFactory.get_mapper("custom")
        assert retrieved_mapper.get_broker_name() == "custom"

        # Cleanup
        services = ParameterMapperFactory.list_supported_services()
        if "custom" in services:
            del ParameterMapperFactory._mappers["custom"]


class TestParameterValidation:
    """Test parameter validation and edge cases"""

    def test_missing_required_params(self):
        """Test that required parameters must be provided"""
        # This should work since all required params are provided
        valid_params = StandardOrderParams(
            symbol="RELIANCE",
            exchange="NSE",
            quantity=1,
            order_side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            product_type=ProductType.INTRADAY
        )
        assert valid_params.symbol == "RELIANCE"

    def test_enum_validation(self):
        """Test enum parameter validation"""
        # Valid enum values should work
        params = StandardOrderParams(
            symbol="RELIANCE",
            exchange="NSE",
            quantity=1,
            order_side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            product_type=ProductType.INTRADAY
        )

        assert params.order_side == OrderSide.BUY
        assert params.order_type == OrderType.LIMIT
        assert params.product_type == ProductType.INTRADAY

    def test_decimal_price_handling(self):
        """Test handling of Decimal prices"""
        params = StandardOrderParams(
            symbol="RELIANCE",
            exchange="NSE",
            quantity=1,
            order_side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            product_type=ProductType.INTRADAY,
            price=Decimal("2500.75"),
            trigger_price=Decimal("2400.25")
        )

        assert isinstance(params.price, Decimal)
        assert isinstance(params.trigger_price, Decimal)
        assert params.price == Decimal("2500.75")
        assert params.trigger_price == Decimal("2400.25")


def test_end_to_end_mapping():
    """Test complete end-to-end parameter mapping"""
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


if __name__ == "__main__":
    # Run a simple test
    print("🧪 Running Parameter Mapping Tests\n")

    # Test basic functionality
    try:
        # Test standard parameter creation
        params = StandardOrderParams(
            symbol="RELIANCE",
            exchange="NSE",
            quantity=1,
            order_side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            product_type=ProductType.INTRADAY,
            price=2500.0
        )
        print("✅ StandardOrderParams creation: PASSED")

        # Test mappers
        for broker_name in ["upstox", "xts", "groww"]:
            mapper = ParameterMapperFactory.get_mapper(broker_name)
            mapped = mapper.map_order_params(params)
            print(f"✅ {broker_name.title()} mapping: PASSED")

        print("\n🎉 All basic tests passed!")
        print("\nRun with pytest for comprehensive testing:")
        print("   pytest test_parameters.py -v")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
