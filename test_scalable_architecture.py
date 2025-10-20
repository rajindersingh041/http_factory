"""
Pytest Demo Tests for Scalable Trading Architecture

This module contains comprehensive tests that demonstrate the scalable
architecture for trading services with standardized parameters.
"""

import asyncio

import pytest

from src.network_test.services.broker_configurations import (
    initialize_scalable_architecture, upstox_order_transformer,
    validate_order_params, validate_quote_params, xts_order_transformer)
from src.network_test.services.scalable_architecture import (
    BrokerConfigurationBuilder, BrokerEndpointMapping, BrokerMappingRegistry,
    EndpointCategory, OperationType, ParameterSchema,
    ParameterSchemaRegistry, StandardResponse)


@pytest.fixture(scope="session", autouse=True)
def setup_architecture():
    """Initialize the scalable architecture for all tests"""
    initialize_scalable_architecture()
    yield
    # Cleanup if needed


class TestParameterSchemaRegistry:
    """Test parameter schema registry functionality"""

    def test_schema_registration(self):
        """Test registering and retrieving parameter schemas"""
        # Create a test schema
        test_schema = ParameterSchema(
            operation=OperationType.PLACE_ORDER,
            category=EndpointCategory.ORDERS,
            required_fields=['symbol', 'quantity'],
            optional_fields=['price'],
            description="Test order schema"
        )

        # Register it
        ParameterSchemaRegistry.register_schema(test_schema)

        # Retrieve and verify
        retrieved_schema = ParameterSchemaRegistry.get_schema(OperationType.PLACE_ORDER)
        assert retrieved_schema is not None
        assert retrieved_schema.operation == OperationType.PLACE_ORDER
        assert 'symbol' in retrieved_schema.required_fields
        assert 'quantity' in retrieved_schema.required_fields
        assert 'price' in retrieved_schema.optional_fields

    def test_parameter_validation_success(self):
        """Test successful parameter validation"""
        params = {
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'quantity': 10,
            'order_side': 'BUY',
            'order_type': 'LIMIT',
            'product_type': 'INTRADAY',
            'price': 2500.0
        }

        errors = ParameterSchemaRegistry.validate_params(OperationType.PLACE_ORDER, params)
        assert len(errors) == 0

    def test_parameter_validation_missing_required(self):
        """Test parameter validation with missing required fields"""
        params = {
            'symbol': 'RELIANCE',
            # Missing required fields
        }

        errors = ParameterSchemaRegistry.validate_params(OperationType.PLACE_ORDER, params)
        assert len(errors) > 0
        assert any('Missing required field' in error for error in errors)

    def test_parameter_validation_custom_rules(self):
        """Test parameter validation with custom validation rules"""
        # Test with invalid quantity (should trigger validation rule)
        params = {
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'quantity': -5,  # Invalid negative quantity
            'order_side': 'BUY',
            'order_type': 'LIMIT',
            'product_type': 'INTRADAY'
        }

        errors = ParameterSchemaRegistry.validate_params(OperationType.PLACE_ORDER, params)
        assert len(errors) > 0
        assert any('Quantity must be positive' in error for error in errors)

    def test_list_operations(self):
        """Test listing all registered operations"""
        operations = ParameterSchemaRegistry.list_operations()
        assert len(operations) > 0
        assert OperationType.PLACE_ORDER in operations
        assert OperationType.GET_QUOTES in operations


class TestBrokerMappingRegistry:
    """Test broker mapping registry functionality"""

    def test_broker_mapping_registration(self):
        """Test registering and retrieving broker mappings"""
        # Create a test mapping
        test_mapping = BrokerEndpointMapping(
            operation=OperationType.PLACE_ORDER,
            broker_endpoint_name="test_place_order",
            http_method="POST",
            requires_auth=True,
            cache_ttl=0
        )

        # Register it
        BrokerMappingRegistry.register_broker_mapping("test_broker", test_mapping)

        # Retrieve and verify
        retrieved_mapping = BrokerMappingRegistry.get_mapping("test_broker", OperationType.PLACE_ORDER)
        assert retrieved_mapping is not None
        assert retrieved_mapping.broker_endpoint_name == "test_place_order"
        assert retrieved_mapping.http_method == "POST"
        assert retrieved_mapping.requires_auth is True

    def test_supported_operations(self):
        """Test getting supported operations for a broker"""
        operations = BrokerMappingRegistry.get_supported_operations("upstox")
        assert len(operations) > 0
        assert OperationType.PLACE_ORDER in operations
        assert OperationType.GET_QUOTES in operations
        assert OperationType.GET_POSITIONS in operations

    def test_list_brokers(self):
        """Test listing all registered brokers"""
        brokers = BrokerMappingRegistry.list_brokers()
        assert len(brokers) >= 3  # upstox, xts, groww
        assert "upstox" in brokers
        assert "xts" in brokers
        assert "groww" in brokers


class TestParameterTransformers:
    """Test parameter transformation functions"""

    def test_upstox_order_transformer(self):
        """Test Upstox order parameter transformation"""
        standard_params = {
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'quantity': 10,
            'order_side': 'BUY',
            'order_type': 'LIMIT',
            'product_type': 'INTRADAY',
            'price': 2500.50,
            'validity': 'DAY',
            'tag': 'test_order',
            'disclosed_quantity': 5,
            'trigger_price': 2400.0,
            'is_amo': False
        }

        upstox_params = upstox_order_transformer(standard_params)

        # Verify Upstox-specific mappings
        assert upstox_params['quantity'] == 10
        assert upstox_params['product'] == 'I'  # INTRADAY -> I
        assert upstox_params['validity'] == 'DAY'
        assert upstox_params['price'] == 2500.50
        assert upstox_params['instrument_token'] == 'NSE_RELIANCE'
        assert upstox_params['order_type'] == 'LIMIT'
        assert upstox_params['transaction_type'] == 'BUY'
        assert upstox_params['disclosed_quantity'] == 5
        assert upstox_params['trigger_price'] == 2400.0
        assert upstox_params['is_amo'] is False

    def test_xts_order_transformer(self):
        """Test XTS order parameter transformation"""
        standard_params = {
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'quantity': 10,
            'order_side': 'BUY',
            'order_type': 'LIMIT',
            'product_type': 'INTRADAY',
            'price': 2500.50,
            'validity': 'DAY',
            'disclosed_quantity': 5,
            'trigger_price': 2400.0,
            'instrument_id': 26000
        }

        xts_params = xts_order_transformer(standard_params)

        # Verify XTS-specific mappings
        assert xts_params['exchangeSegment'] == 'NSECM'  # NSE -> NSECM
        assert xts_params['exchangeInstrumentID'] == 26000
        assert xts_params['productType'] == 'MIS'  # INTRADAY -> MIS
        assert xts_params['orderType'] == 'LIMIT'
        assert xts_params['orderSide'] == 'BUY'
        assert xts_params['timeInForce'] == 'DAY'
        assert xts_params['disclosedQuantity'] == 5
        assert xts_params['orderQuantity'] == 10
        assert xts_params['limitPrice'] == 2500.50
        assert xts_params['stopPrice'] == 2400.0

    def test_exchange_segment_mapping(self):
        """Test XTS exchange segment mapping"""
        test_cases = [
            ('NSE', 'NSECM'),
            ('BSE', 'BSECM'),
            ('NFO', 'NSEFO'),
            ('BFO', 'BSEFO')
        ]

        for input_exchange, expected_segment in test_cases:
            params = {
                'symbol': 'TEST',
                'exchange': input_exchange,
                'quantity': 1,
                'order_side': 'BUY',
                'order_type': 'MARKET',
                'product_type': 'INTRADAY',
                'instrument_id': 123
            }

            result = xts_order_transformer(params)
            assert result['exchangeSegment'] == expected_segment


class TestValidationRules:
    """Test custom validation rules"""

    def test_order_validation_success(self):
        """Test successful order validation"""
        params = {
            'quantity': 10,
            'order_type': 'LIMIT',
            'price': 2500.0,
            'trigger_price': 2400.0
        }

        errors = validate_order_params(params)
        assert len(errors) == 0

    def test_order_validation_negative_quantity(self):
        """Test order validation with negative quantity"""
        params = {
            'quantity': -5,
            'order_type': 'LIMIT',
            'price': 2500.0
        }

        errors = validate_order_params(params)
        assert len(errors) > 0
        assert 'Quantity must be positive' in errors

    def test_order_validation_limit_without_price(self):
        """Test order validation for limit order without price"""
        params = {
            'quantity': 10,
            'order_type': 'LIMIT'
            # Missing price for LIMIT order
        }

        errors = validate_order_params(params)
        assert len(errors) > 0
        assert 'Limit orders require price' in errors

    def test_quote_validation_success(self):
        """Test successful quote validation"""
        params = {
            'symbols': ['RELIANCE', 'TCS', 'INFY']
        }

        errors = validate_quote_params(params)
        assert len(errors) == 0

    def test_quote_validation_no_symbols(self):
        """Test quote validation with no symbols"""
        params = {
            'symbols': []
        }

        errors = validate_quote_params(params)
        assert len(errors) > 0
        assert 'At least one symbol is required' in errors

    def test_quote_validation_too_many_symbols(self):
        """Test quote validation with too many symbols"""
        params = {
            'symbols': [f'SYMBOL_{i}' for i in range(100)]  # 100 symbols > 50 limit
        }

        errors = validate_quote_params(params)
        assert len(errors) > 0
        assert 'Too many symbols requested' in errors


class TestBrokerConfigurationBuilder:
    """Test broker configuration builder"""

    def test_configuration_builder(self):
        """Test building broker configuration"""
        builder = BrokerConfigurationBuilder("test_broker")

        # Add some operations
        builder.add_operation(
            OperationType.PLACE_ORDER,
            broker_endpoint="place_order",
            http_method="POST",
            required_fields=['symbol', 'quantity'],
            optional_fields=['price']
        )

        builder.add_operation(
            OperationType.GET_QUOTES,
            broker_endpoint="quotes",
            http_method="GET",
            required_fields=['symbols']
        )

        # Build the configuration
        builder.build()

        # Verify the configuration was registered
        operations = BrokerMappingRegistry.get_supported_operations("test_broker")
        assert OperationType.PLACE_ORDER in operations
        assert OperationType.GET_QUOTES in operations

        # Verify specific mappings
        place_order_mapping = BrokerMappingRegistry.get_mapping("test_broker", OperationType.PLACE_ORDER)
        assert place_order_mapping.broker_endpoint_name == "place_order"
        assert place_order_mapping.http_method == "POST"


class TestEndToEndScenarios:
    """Test complete end-to-end scenarios"""

    def test_multi_broker_order_placement_simulation(self):
        """Test simulated order placement across multiple brokers"""
        # Standard order parameters
        standard_order = {
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'quantity': 10,
            'order_side': 'BUY',
            'order_type': 'LIMIT',
            'product_type': 'INTRADAY',
            'price': 2500.50,
            'validity': 'DAY',
            'tag': 'multi_broker_test'
        }

        # Test with different brokers
        brokers = ['upstox', 'xts']

        for broker_name in brokers:
            # Validate parameters
            errors = ParameterSchemaRegistry.validate_params(OperationType.PLACE_ORDER, standard_order)
            assert len(errors) == 0, f"Validation failed for {broker_name}: {errors}"

            # Get broker mapping
            mapping = BrokerMappingRegistry.get_mapping(broker_name, OperationType.PLACE_ORDER)
            assert mapping is not None, f"No mapping found for {broker_name}"

            # Transform parameters
            if broker_name == 'upstox':
                transformed = upstox_order_transformer(standard_order)
                assert transformed['instrument_token'] == 'NSE_RELIANCE'
                assert transformed['product'] == 'I'
            elif broker_name == 'xts':
                order_with_instrument = {**standard_order, 'instrument_id': 26000}
                transformed = xts_order_transformer(order_with_instrument)
                assert transformed['exchangeSegment'] == 'NSECM'
                assert transformed['productType'] == 'MIS'

            print(f"✅ {broker_name.title()}: Order simulation successful")

    def test_quote_retrieval_simulation(self):
        """Test simulated quote retrieval across brokers"""
        standard_quote = {
            'symbols': ['RELIANCE', 'TCS', 'INFY'],
            'exchange': 'NSE'
        }

        # Validate parameters
        errors = ParameterSchemaRegistry.validate_params(OperationType.GET_QUOTES, standard_quote)
        assert len(errors) == 0

        # Test with different brokers
        for broker_name in ['upstox', 'xts', 'groww']:
            mapping = BrokerMappingRegistry.get_mapping(broker_name, OperationType.GET_QUOTES)
            if mapping:  # Some brokers might not support all operations
                print(f"✅ {broker_name.title()}: Quote mapping available")
            else:
                print(f"ℹ️ {broker_name.title()}: Quote mapping not configured")

    def test_architecture_scalability_demonstration(self):
        """Demonstrate the scalability of the architecture"""
        # Show all registered brokers and their operations
        brokers = BrokerMappingRegistry.list_brokers()
        total_operations = 0

        print("\n📊 Architecture Scalability Report:")
        print(f"   Total Brokers: {len(brokers)}")

        for broker in brokers:
            operations = BrokerMappingRegistry.get_supported_operations(broker)
            total_operations += len(operations)
            print(f"   {broker.title()}: {len(operations)} operations")

        print(f"   Total Operations: {total_operations}")

        # Show all registered schemas
        all_operations = ParameterSchemaRegistry.list_operations()
        print(f"   Global Schemas: {len(all_operations)}")

        # Demonstrate that adding a new broker is easy
        new_broker_builder = BrokerConfigurationBuilder("demo_new_broker")
        new_broker_builder.add_operation(
            OperationType.PLACE_ORDER,
            broker_endpoint="new_broker_place_order",
            http_method="POST",
            required_fields=['symbol', 'qty'],  # Different field names
            parameter_transformer=lambda params: {
                'symbol': params['symbol'],
                'qty': params['quantity'],
                'side': params['order_side'].lower()
            }
        )
        new_broker_builder.build()

        # Verify new broker was added
        updated_brokers = BrokerMappingRegistry.list_brokers()
        assert "demo_new_broker" in updated_brokers

        print("✅ New broker added successfully!")
        print(f"   Updated broker count: {len(updated_brokers)}")


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test asynchronous operations (simulated)"""

    async def test_simulated_async_execution(self):
        """Test simulated asynchronous execution flow"""
        # This simulates what would happen in real async execution

        async def simulate_broker_call(broker_name: str, operation: str, params: dict) -> StandardResponse:
            """Simulate an async broker API call"""
            await asyncio.sleep(0.01)  # Simulate network delay

            return StandardResponse(
                success=True,
                data={"order_id": f"{broker_name}_12345", "status": "SUCCESS"},
                broker_name=broker_name,
                operation=OperationType.PLACE_ORDER,
                execution_time_ms=10.5
            )

        # Simulate parallel execution across multiple brokers
        standard_params = {
            'symbol': 'RELIANCE',
            'quantity': 10,
            'order_side': 'BUY',
            'order_type': 'LIMIT',
            'product_type': 'INTRADAY',
            'price': 2500.0
        }

        # Execute in parallel
        tasks = []
        for broker in ['upstox', 'xts']:
            task = simulate_broker_call(broker, 'place_order', standard_params)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Verify all executions succeeded
        assert len(results) == 2
        for result in results:
            assert result.success is True
            assert "order_id" in result.data
            assert result.execution_time_ms > 0

        print("✅ Simulated async execution completed successfully")


class TestRealWorldScenarios:
    """Test real-world trading scenarios"""

    def test_portfolio_rebalancing_scenario(self):
        """Test portfolio rebalancing across multiple brokers"""
        # Scenario: Rebalance portfolio by placing orders across different brokers

        portfolio_orders = [
            {'symbol': 'RELIANCE', 'action': 'SELL', 'quantity': 50, 'broker': 'upstox'},
            {'symbol': 'TCS', 'action': 'BUY', 'quantity': 30, 'broker': 'xts'},
            {'symbol': 'INFY', 'action': 'BUY', 'quantity': 20, 'broker': 'upstox'},
        ]

        for order in portfolio_orders:
            standard_params = {
                'symbol': order['symbol'],
                'exchange': 'NSE',
                'quantity': order['quantity'],
                'order_side': order['action'],
                'order_type': 'MARKET',
                'product_type': 'DELIVERY'
            }

            # Validate parameters
            errors = ParameterSchemaRegistry.validate_params(OperationType.PLACE_ORDER, standard_params)
            assert len(errors) == 0

            # Get broker mapping
            mapping = BrokerMappingRegistry.get_mapping(order['broker'], OperationType.PLACE_ORDER)
            assert mapping is not None

            print(f"✅ {order['symbol']} {order['action']} {order['quantity']} via {order['broker']}")

        print("✅ Portfolio rebalancing scenario validated")

    def test_risk_management_scenario(self):
        """Test risk management with parameter validation"""
        # Scenario: Prevent risky orders through validation

        risky_orders = [
            {'symbol': 'PENNY_STOCK', 'quantity': -10, 'expected_error': 'Quantity must be positive'},
            {'symbol': 'VOLATILE', 'order_type': 'LIMIT', 'expected_error': 'Limit orders require price'},
            {'symbols': [], 'expected_error': 'At least one symbol is required'},  # Quote request
        ]

        # Test order validations
        for i, order in enumerate(risky_orders[:2]):  # First two are order tests
            if 'symbols' not in order:  # It's an order test
                order_params = {
                    'symbol': order['symbol'],
                    'exchange': 'NSE',
                    'quantity': order.get('quantity', 1),
                    'order_side': 'BUY',
                    'order_type': order.get('order_type', 'MARKET'),
                    'product_type': 'INTRADAY'
                }
                if order.get('order_type') == 'LIMIT' and 'price' not in order:
                    # Intentionally omit price for LIMIT order
                    pass

                errors = ParameterSchemaRegistry.validate_params(OperationType.PLACE_ORDER, order_params)
                assert len(errors) > 0
                assert any(order['expected_error'] in error for error in errors)
                print(f"✅ Risk check {i+1}: {order['expected_error']} - BLOCKED")

        # Test quote validation
        quote_params = {'symbols': []}
        errors = ParameterSchemaRegistry.validate_params(OperationType.GET_QUOTES, quote_params)
        assert len(errors) > 0
        assert any('At least one symbol is required' in error for error in errors)
        print("✅ Risk check 3: Empty symbols list - BLOCKED")

        print("✅ Risk management scenario completed")


def test_architecture_summary():
    """Test and display architecture summary"""
    print("\n🏗️ SCALABLE ARCHITECTURE SUMMARY")
    print(f"{'='*50}")

    # Get statistics
    brokers = BrokerMappingRegistry.list_brokers()
    operations = ParameterSchemaRegistry.list_operations()

    print("📊 Statistics:")
    print(f"   Registered Brokers: {len(brokers)}")
    print(f"   Global Operations: {len(operations)}")

    total_mappings = 0
    print("\n🏛️ Broker Details:")
    for broker in sorted(brokers):
        broker_ops = BrokerMappingRegistry.get_supported_operations(broker)
        total_mappings += len(broker_ops)
        print(f"   {broker.title()}: {len(broker_ops)} operations")

    print("\n📈 Scalability Metrics:")
    print(f"   Total Endpoint Mappings: {total_mappings}")
    print(f"   Average Operations per Broker: {total_mappings/len(brokers):.1f}")

    print("\n✅ Architecture Features:")
    print("   ✓ Standardized parameter validation")
    print("   ✓ Automatic parameter transformation")
    print("   ✓ Broker-agnostic operation interface")
    print("   ✓ Configurable endpoint mappings")
    print("   ✓ Extensible for new brokers")
    print("   ✓ Type-safe responses")
    print("   ✓ Built-in error handling")

    # Assertions for the test
    assert len(brokers) >= 3
    assert len(operations) >= 2
    assert total_mappings >= 10


if __name__ == "__main__":
    # Run some demo functions directly
    print("🧪 Running Scalable Architecture Demo...")
    initialize_scalable_architecture()
    test_architecture_summary()
    print("✅ Demo completed!")
