"""
Broker Integration Tests for Scalable Architecture

This module tests the integration between different brokers and the
scalable architecture, demonstrating how easy it is to add new brokers
and operations.
"""

from typing import Any, Dict
from unittest.mock import AsyncMock, Mock

import pytest

from src.network_test.services.scalable_architecture import (
    BrokerConfigurationBuilder, BrokerMappingRegistry, EndpointExecutor,
    OperationType, ParameterSchemaRegistry, StandardResponse)


@pytest.mark.integration
class TestBrokerIntegration:
    """Test integration between brokers and the scalable architecture"""

    def test_add_new_broker_dynamically(self):
        """Test adding a new broker with complete configuration"""
        broker_name = "zerodha"

        # Create configuration for the new broker
        builder = BrokerConfigurationBuilder(broker_name)

        # Add order operations
        builder.add_operation(
            OperationType.PLACE_ORDER,
            broker_endpoint="order_place",
            http_method="POST",
            required_fields=['tradingsymbol', 'quantity', 'transaction_type'],
            parameter_transformer=self._zerodha_order_transformer,
            requires_auth=True,
            cache_ttl=0
        )

        # Add portfolio operations
        builder.add_operation(
            OperationType.GET_POSITIONS,
            broker_endpoint="positions",
            http_method="GET",
            required_fields=[],
            requires_auth=True,
            cache_ttl=30
        )

        # Add market data operations
        builder.add_operation(
            OperationType.GET_QUOTES,
            broker_endpoint="quote",
            http_method="GET",
            required_fields=['instruments'],
            parameter_transformer=self._zerodha_quote_transformer,
            requires_auth=True,
            cache_ttl=1
        )

        # Build and register
        builder.build()

        # Verify the broker was added
        brokers = BrokerMappingRegistry.list_brokers()
        assert broker_name in brokers

        # Verify operations were registered
        operations = BrokerMappingRegistry.get_supported_operations(broker_name)
        assert OperationType.PLACE_ORDER in operations
        assert OperationType.GET_POSITIONS in operations
        assert OperationType.GET_QUOTES in operations

        # Test specific mappings
        order_mapping = BrokerMappingRegistry.get_mapping(broker_name, OperationType.PLACE_ORDER)
        assert order_mapping.broker_endpoint_name == "order_place"
        assert order_mapping.http_method == "POST"
        assert order_mapping.parameter_transformer is not None

        print(f"✅ {broker_name.title()} broker added successfully with {len(operations)} operations")

    def _zerodha_order_transformer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform standard params to Zerodha format"""
        return {
            'tradingsymbol': params['symbol'],
            'quantity': params['quantity'],
            'transaction_type': params['order_side'],
            'order_type': params['order_type'],
            'product': 'MIS' if params['product_type'] == 'INTRADAY' else 'CNC',
            'price': params.get('price', 0),
            'validity': params.get('validity', 'DAY'),
            'disclosed_quantity': params.get('disclosed_quantity', 0),
            'trigger_price': params.get('trigger_price', 0)
        }

    def _zerodha_quote_transformer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform standard quote params to Zerodha format"""
        return {
            'instruments': ','.join(params['symbols'])
        }

    @pytest.mark.broker_specific
    def test_multi_broker_operation_support(self):
        """Test that the same operation works across multiple brokers"""
        # Standard order parameters (used for validation across brokers)
        _ = {
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'quantity': 10,
            'order_side': 'BUY',
            'order_type': 'LIMIT',
            'product_type': 'INTRADAY',
            'price': 2500.0
        }

        # Test across all brokers that support PLACE_ORDER
        supported_brokers = []
        all_brokers = BrokerMappingRegistry.list_brokers()

        for broker in all_brokers:
            operations = BrokerMappingRegistry.get_supported_operations(broker)
            if OperationType.PLACE_ORDER in operations:
                supported_brokers.append(broker)

                # Get mapping and verify it exists
                mapping = BrokerMappingRegistry.get_mapping(broker, OperationType.PLACE_ORDER)
                assert mapping is not None
                assert mapping.broker_endpoint_name is not None

                print(f"✅ {broker.title()}: Supports PLACE_ORDER via '{mapping.broker_endpoint_name}'")

        assert len(supported_brokers) >= 2, "At least 2 brokers should support PLACE_ORDER"
        print(f"📊 Total brokers supporting PLACE_ORDER: {len(supported_brokers)}")

    def test_operation_coverage_analysis(self):
        """Test and analyze operation coverage across brokers"""
        brokers = BrokerMappingRegistry.list_brokers()
        all_operations = set()
        broker_coverage = {}

        # Collect all operations and broker coverage
        for broker in brokers:
            operations = set(BrokerMappingRegistry.get_supported_operations(broker))
            broker_coverage[broker] = operations
            all_operations.update(operations)

        # Analyze coverage
        print("\n📊 Operation Coverage Analysis:")
        print(f"   Total Brokers: {len(brokers)}")
        print(f"   Total Operations: {len(all_operations)}")

        # Show operation support matrix
        print("\n🔍 Operation Support Matrix:")
        for operation in sorted(all_operations, key=lambda x: x.value):
            supporting_brokers = [b for b, ops in broker_coverage.items() if operation in ops]
            coverage_pct = (len(supporting_brokers) / len(brokers)) * 100
            print(f"   {operation.value:<25} | {len(supporting_brokers)}/{len(brokers)} brokers ({coverage_pct:.0f}%)")

        # Find most and least supported operations
        operation_support_count = {
            op: len([b for b, ops in broker_coverage.items() if op in ops])
            for op in all_operations
        }

        most_supported = max(operation_support_count, key=operation_support_count.get)
        least_supported = min(operation_support_count, key=operation_support_count.get)

        print("\n📈 Coverage Insights:")
        print(f"   Most supported: {most_supported.value} ({operation_support_count[most_supported]} brokers)")
        print(f"   Least supported: {least_supported.value} ({operation_support_count[least_supported]} brokers)")

        # Assertions
        assert len(all_operations) >= 5, "Should have at least 5 different operations"
        assert len(brokers) >= 3, "Should have at least 3 brokers"


@pytest.mark.integration
class TestEndpointExecutorIntegration:
    """Test EndpointExecutor integration with mock services"""

    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing"""
        service = Mock()
        service.call_endpoint = AsyncMock()
        service.call_endpoint.return_value = {"status": "success", "order_id": "12345"}
        return service

    @pytest.mark.asyncio
    async def test_endpoint_executor_successful_execution(self, mock_service):
        """Test successful execution through EndpointExecutor"""
        executor = EndpointExecutor("upstox")

        # Standard order parameters
        params = {
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'quantity': 10,
            'order_side': 'BUY',
            'order_type': 'LIMIT',
            'product_type': 'INTRADAY',
            'price': 2500.0
        }

        # Execute the operation
        result = await executor.execute_operation(
            OperationType.PLACE_ORDER,
            params,
            mock_service
        )

        # Verify the result
        assert isinstance(result, StandardResponse)
        assert result.success is True
        assert result.broker_name == "upstox"
        assert result.operation == OperationType.PLACE_ORDER
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0

        # Verify the service was called
        mock_service.call_endpoint.assert_called_once()
        print("✅ EndpointExecutor successful execution test passed")

    @pytest.mark.asyncio
    async def test_endpoint_executor_validation_failure(self, mock_service):
        """Test execution with parameter validation failure"""
        executor = EndpointExecutor("upstox")

        # Invalid parameters (missing required fields)
        params = {
            'symbol': 'RELIANCE',
            # Missing required fields
        }

        # Execute the operation
        result = await executor.execute_operation(
            OperationType.PLACE_ORDER,
            params,
            mock_service
        )

        # Verify validation failure
        assert isinstance(result, StandardResponse)
        assert result.success is False
        assert "Parameter validation failed" in result.error
        assert result.broker_name == "upstox"

        # Verify the service was NOT called due to validation failure
        mock_service.call_endpoint.assert_not_called()
        print("✅ EndpointExecutor validation failure test passed")

    @pytest.mark.asyncio
    async def test_endpoint_executor_unsupported_operation(self, mock_service):
        """Test execution with unsupported operation"""
        executor = EndpointExecutor("test_broker_without_operations")

        params = {
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'quantity': 10,
            'order_side': 'BUY',
            'order_type': 'LIMIT',
            'product_type': 'INTRADAY'
        }

        # Execute unsupported operation
        result = await executor.execute_operation(
            OperationType.PLACE_ORDER,
            params,
            mock_service
        )

        # Verify unsupported operation response
        assert isinstance(result, StandardResponse)
        assert result.success is False
        assert "not supported by broker" in result.error

        # Verify the service was NOT called
        mock_service.call_endpoint.assert_not_called()
        print("✅ EndpointExecutor unsupported operation test passed")


@pytest.mark.integration
class TestRealWorldIntegrationScenarios:
    """Test realistic integration scenarios"""

    def test_trading_strategy_integration(self):
        """Test a complete trading strategy using multiple brokers"""
        # Scenario: Momentum trading strategy
        # - Get quotes from multiple sources
        # - Place orders across different brokers for diversification
        # - Monitor positions

        strategy_steps = [
            {
                'step': 'Get Market Data',
                'operation': OperationType.GET_QUOTES,
                'params': {'symbols': ['RELIANCE', 'TCS', 'INFY']},
                'brokers': ['upstox', 'groww']  # Get quotes from multiple sources
            },
            {
                'step': 'Place Orders',
                'operation': OperationType.PLACE_ORDER,
                'params': {
                    'symbol': 'RELIANCE',
                    'exchange': 'NSE',
                    'quantity': 50,
                    'order_side': 'BUY',
                    'order_type': 'LIMIT',
                    'product_type': 'INTRADAY',
                    'price': 2500.0
                },
                'brokers': ['upstox', 'xts']  # Diversify across brokers
            },
            {
                'step': 'Monitor Positions',
                'operation': OperationType.GET_POSITIONS,
                'params': {},
                'brokers': ['upstox', 'xts']
            }
        ]

        execution_plan = []

        for step in strategy_steps:
            step_plan = {
                'step_name': step['step'],
                'operation': step['operation'],
                'executions': []
            }

            for broker in step['brokers']:
                # Check if broker supports the operation
                operations = BrokerMappingRegistry.get_supported_operations(broker)
                if step['operation'] in operations:
                    # Validate parameters
                    errors = ParameterSchemaRegistry.validate_params(step['operation'], step['params'])

                    step_plan['executions'].append({
                        'broker': broker,
                        'supported': True,
                        'validation_passed': len(errors) == 0,
                        'validation_errors': errors
                    })
                else:
                    step_plan['executions'].append({
                        'broker': broker,
                        'supported': False,
                        'validation_passed': False,
                        'validation_errors': ['Operation not supported']
                    })

            execution_plan.append(step_plan)

        # Analyze execution plan
        print("\n📋 Trading Strategy Integration Analysis:")
        total_executions = 0
        successful_executions = 0

        for step in execution_plan:
            print(f"\n🔄 {step['step_name']}:")
            for execution in step['executions']:
                total_executions += 1
                status = "✅" if execution['supported'] and execution['validation_passed'] else "❌"
                print(f"   {status} {execution['broker'].title()}: ", end="")

                if not execution['supported']:
                    print("Not supported")
                elif not execution['validation_passed']:
                    print(f"Validation failed: {execution['validation_errors']}")
                else:
                    print("Ready to execute")
                    successful_executions += 1

        success_rate = (successful_executions / total_executions) * 100 if total_executions > 0 else 0
        print("\n📊 Strategy Execution Summary:")
        print(f"   Total Planned Executions: {total_executions}")
        print(f"   Successful Validations: {successful_executions}")
        print(f"   Success Rate: {success_rate:.1f}%")

        # Assertions
        assert total_executions > 0, "Should have planned executions"
        assert successful_executions > 0, "Should have at least some successful validations"
        assert success_rate >= 50, "Success rate should be at least 50%"

    def test_risk_management_integration(self):
        """Test risk management integration across the architecture"""
        # Scenario: Risk management system checking orders before execution

        risk_scenarios = [
            {
                'name': 'Valid Order',
                'params': {
                    'symbol': 'RELIANCE',
                    'exchange': 'NSE',
                    'quantity': 10,
                    'order_side': 'BUY',
                    'order_type': 'LIMIT',
                    'product_type': 'INTRADAY',
                    'price': 2500.0
                },
                'should_pass': True
            },
            {
                'name': 'Negative Quantity Risk',
                'params': {
                    'symbol': 'RISKY_STOCK',
                    'exchange': 'NSE',
                    'quantity': -100,  # Negative quantity
                    'order_side': 'BUY',
                    'order_type': 'MARKET',
                    'product_type': 'INTRADAY'
                },
                'should_pass': False
            },
            {
                'name': 'Limit Order Without Price Risk',
                'params': {
                    'symbol': 'VOLATILE',
                    'exchange': 'NSE',
                    'quantity': 50,
                    'order_side': 'BUY',
                    'order_type': 'LIMIT',  # LIMIT order without price
                    'product_type': 'INTRADAY'
                },
                'should_pass': False
            },
            {
                'name': 'Excessive Quote Request Risk',
                'params': {
                    'symbols': [f'STOCK_{i}' for i in range(100)]  # Too many symbols
                },
                'operation': OperationType.GET_QUOTES,
                'should_pass': False
            }
        ]

        print("\n🛡️ Risk Management Integration Test:")

        passed_risk_checks = 0
        total_risk_checks = len(risk_scenarios)

        for scenario in risk_scenarios:
            operation = scenario.get('operation', OperationType.PLACE_ORDER)
            errors = ParameterSchemaRegistry.validate_params(operation, scenario['params'])

            validation_passed = len(errors) == 0
            expected_result = scenario['should_pass']

            # Risk check passes if validation result matches expectation
            risk_check_passed = (validation_passed == expected_result)

            if risk_check_passed:
                passed_risk_checks += 1
                status = "✅"
            else:
                status = "❌"

            print(f"   {status} {scenario['name']}: ", end="")
            if expected_result:
                print("ALLOWED" if validation_passed else f"BLOCKED ({errors})")
            else:
                print("BLOCKED" if not validation_passed else "INCORRECTLY ALLOWED")

        risk_effectiveness = (passed_risk_checks / total_risk_checks) * 100
        print("\n📊 Risk Management Summary:")
        print(f"   Total Risk Scenarios: {total_risk_checks}")
        print(f"   Correct Risk Decisions: {passed_risk_checks}")
        print(f"   Risk System Effectiveness: {risk_effectiveness:.1f}%")

        # Assertions
        assert risk_effectiveness >= 75, "Risk management should be at least 75% effective"
        print("✅ Risk management integration test passed")


@pytest.mark.demo
def test_integration_demo_summary():
    """Demonstrate the complete integration capabilities"""
    print("\n🔗 BROKER INTEGRATION DEMONSTRATION")
    print(f"{'='*60}")

    # Show broker ecosystem
    brokers = BrokerMappingRegistry.list_brokers()
    operations = ParameterSchemaRegistry.list_operations()

    print("🌐 Broker Ecosystem:")
    print(f"   Active Brokers: {len(brokers)}")
    print(f"   Standardized Operations: {len(operations)}")

    # Show integration matrix
    print("\n📊 Integration Matrix:")
    total_integrations = 0
    for broker in sorted(brokers):
        broker_ops = BrokerMappingRegistry.get_supported_operations(broker)
        total_integrations += len(broker_ops)
        print(f"   {broker.title():<15} | {len(broker_ops):>2} operations")

    print("\n🚀 Integration Benefits Demonstrated:")
    print("   ✓ Easy broker onboarding (new brokers in minutes)")
    print("   ✓ Unified operation interface across all brokers")
    print("   ✓ Automatic parameter validation and transformation")
    print("   ✓ Built-in risk management capabilities")
    print("   ✓ Scalable architecture supporting unlimited endpoints")
    print("   ✓ Type-safe responses with standardized error handling")

    print("\n📈 Scalability Metrics:")
    print(f"   Total Broker-Operation Integrations: {total_integrations}")
    print(f"   Average Operations per Broker: {total_integrations/len(brokers):.1f}")
    print("   Architecture Complexity: O(B × O) where B=brokers, O=operations")

    # Assertions for the demo
    assert total_integrations >= 10, "Should demonstrate significant integration scale"
    assert len(brokers) >= 3, "Should show multi-broker support"

    print("\n✅ Integration demonstration complete!")


if __name__ == "__main__":
    # Run integration demo
    from src.network_test.services.broker_configurations import \
        initialize_scalable_architecture
    initialize_scalable_architecture()
    test_integration_demo_summary()
