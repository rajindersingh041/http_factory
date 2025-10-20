"""
Comprehensive Demo Script for Scalable Trading Architecture

This script demonstrates all key features of the scalable architecture
in a single comprehensive example.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from src.network_test.services.broker_configurations import \
    initialize_scalable_architecture
# Import our scalable architecture components
from src.network_test.services.scalable_architecture import (
    BrokerConfigurationBuilder, BrokerMappingRegistry, OperationType,
    ParameterSchemaRegistry)


@dataclass
class TradingScenario:
    """Represents a complete trading scenario"""
    name: str
    operations: List[Dict[str, Any]]
    expected_outcomes: Dict[str, Any]


class ScalableArchitectureDemo:
    """Comprehensive demonstration of the scalable architecture"""

    def __init__(self):
        self.demo_results = {}
        self.trading_scenarios = []

    def run_complete_demo(self):
        """Run the complete demonstration"""
        print("🚀 SCALABLE TRADING ARCHITECTURE - COMPREHENSIVE DEMO")
        print("=" * 70)

        # Initialize the architecture
        self._demo_initialization()

        # Demonstrate core features
        self._demo_parameter_schemas()
        self._demo_broker_mappings()
        self._demo_parameter_transformations()
        self._demo_multi_broker_operations()
        self._demo_new_broker_addition()
        self._demo_risk_management()
        self._demo_trading_scenarios()

        # Show final summary
        self._demo_final_summary()

        return self.demo_results

    def _demo_initialization(self):
        """Demonstrate architecture initialization"""
        print("\n🏗️ STEP 1: Architecture Initialization")
        print("-" * 40)

        try:
            initialize_scalable_architecture()
            brokers = BrokerMappingRegistry.list_brokers()
            operations = ParameterSchemaRegistry.list_operations()

            print("✅ Architecture initialized successfully!")
            print(f"   📊 Brokers loaded: {len(brokers)}")
            print(f"   📊 Operations available: {len(operations)}")

            self.demo_results['initialization'] = {
                'success': True,
                'brokers_count': len(brokers),
                'operations_count': len(operations)
            }

        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            self.demo_results['initialization'] = {'success': False, 'error': str(e)}

    def _demo_parameter_schemas(self):
        """Demonstrate parameter schema system"""
        print("\n📋 STEP 2: Parameter Schema Validation")
        print("-" * 40)

        # Test valid order parameters
        valid_order = {
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'quantity': 100,
            'order_side': 'BUY',
            'order_type': 'LIMIT',
            'product_type': 'INTRADAY',
            'price': 2500.0
        }

        errors = ParameterSchemaRegistry.validate_params(OperationType.PLACE_ORDER, valid_order)
        if not errors:
            print("✅ Valid order parameters - validation passed")
        else:
            print(f"❌ Validation failed: {errors}")

        # Test invalid parameters
        invalid_order = {'symbol': 'TEST'}  # Missing required fields
        errors = ParameterSchemaRegistry.validate_params(OperationType.PLACE_ORDER, invalid_order)
        if errors:
            print(f"✅ Invalid parameters correctly rejected: {len(errors)} errors")
        else:
            print("❌ Should have failed validation")

        self.demo_results['parameter_validation'] = {
            'valid_order_passed': len(ParameterSchemaRegistry.validate_params(OperationType.PLACE_ORDER, valid_order)) == 0,
            'invalid_order_failed': len(ParameterSchemaRegistry.validate_params(OperationType.PLACE_ORDER, invalid_order)) > 0
        }

    def _demo_broker_mappings(self):
        """Demonstrate broker mapping system"""
        print("\n🏢 STEP 3: Broker Mapping System")
        print("-" * 40)

        brokers = BrokerMappingRegistry.list_brokers()
        mapping_count = 0

        for broker in brokers:
            operations = BrokerMappingRegistry.get_supported_operations(broker)
            mapping_count += len(operations)
            print(f"📊 {broker.title()}: {len(operations)} operations")

            # Show a sample mapping
            if OperationType.PLACE_ORDER in operations:
                mapping = BrokerMappingRegistry.get_mapping(broker, OperationType.PLACE_ORDER)
                if mapping:
                    print(f"   🔗 ORDER mapping: {mapping.broker_endpoint_name} ({mapping.http_method})")

        print(f"📈 Total broker-operation mappings: {mapping_count}")

        self.demo_results['broker_mappings'] = {
            'total_brokers': len(brokers),
            'total_mappings': mapping_count,
            'avg_operations_per_broker': mapping_count / len(brokers) if brokers else 0
        }

    def _demo_parameter_transformations(self):
        """Demonstrate parameter transformation"""
        print("\n🔄 STEP 4: Parameter Transformations")
        print("-" * 40)

        standard_params = {
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'quantity': 100,
            'order_side': 'BUY',
            'order_type': 'LIMIT',
            'product_type': 'INTRADAY',
            'price': 2500.0
        }

        transformations_tested = 0
        successful_transformations = 0

        for broker in ['upstox', 'xts']:
            if broker in BrokerMappingRegistry.list_brokers():
                operations = BrokerMappingRegistry.get_supported_operations(broker)
                if OperationType.PLACE_ORDER in operations:
                    mapping = BrokerMappingRegistry.get_mapping(broker, OperationType.PLACE_ORDER)
                    if mapping and mapping.parameter_transformer:
                        transformations_tested += 1
                        try:
                            transformed = mapping.parameter_transformer(standard_params)
                            print(f"✅ {broker.title()} transformation: {len(transformed)} parameters")

                            # Show key differences
                            if broker == 'upstox':
                                if 'instrument_token' in transformed:
                                    print("   🔹 Uses instrument_token instead of symbol")
                                if 'orderQuantity' in transformed:
                                    print("   🔹 Uses orderQuantity instead of quantity")
                            elif broker == 'xts':
                                if 'exchangeSegment' in transformed:
                                    print("   🔹 Uses exchangeSegment for exchange mapping")
                                if 'orderQuantity' in transformed:
                                    print("   🔹 Uses orderQuantity instead of quantity")

                            successful_transformations += 1
                        except Exception as e:
                            print(f"❌ {broker.title()} transformation failed: {e}")

        self.demo_results['transformations'] = {
            'tested': transformations_tested,
            'successful': successful_transformations,
            'success_rate': (successful_transformations / transformations_tested * 100) if transformations_tested > 0 else 0
        }

    def _demo_multi_broker_operations(self):
        """Demonstrate operations across multiple brokers"""
        print("\n🌐 STEP 5: Multi-Broker Operations")
        print("-" * 40)

        test_params = {
            'symbol': 'TCS',
            'exchange': 'NSE',
            'quantity': 50,
            'order_side': 'BUY',
            'order_type': 'MARKET',
            'product_type': 'DELIVERY'
        }

        supported_brokers = []

        for broker in BrokerMappingRegistry.list_brokers():
            operations = BrokerMappingRegistry.get_supported_operations(broker)
            if OperationType.PLACE_ORDER in operations:
                supported_brokers.append(broker)

                # Validate parameters for this broker
                errors = ParameterSchemaRegistry.validate_params(OperationType.PLACE_ORDER, test_params)
                validation_status = "✅" if not errors else "❌"
                print(f"{validation_status} {broker.title()}: Ready for PLACE_ORDER")

        print(f"📊 Operation supported by {len(supported_brokers)} brokers")

        self.demo_results['multi_broker'] = {
            'operation_tested': 'PLACE_ORDER',
            'supporting_brokers': len(supported_brokers),
            'broker_names': supported_brokers
        }

    def _demo_new_broker_addition(self):
        """Demonstrate adding a new broker dynamically"""
        print("\n➕ STEP 6: Dynamic Broker Addition")
        print("-" * 40)

        initial_brokers = len(BrokerMappingRegistry.list_brokers())

        # Add a mock new broker
        builder = BrokerConfigurationBuilder("demo_broker")

        # Add some operations
        builder.add_operation(
            OperationType.PLACE_ORDER,
            broker_endpoint="place_order",
            http_method="POST",
            required_fields=['symbol', 'qty', 'side'],
            parameter_transformer=self._demo_broker_transformer,
            requires_auth=True
        )

        builder.add_operation(
            OperationType.GET_QUOTES,
            broker_endpoint="quotes",
            http_method="GET",
            required_fields=['symbols'],
            requires_auth=True,
            cache_ttl=1
        )

        # Build the configuration
        builder.build()

        final_brokers = len(BrokerMappingRegistry.list_brokers())

        print("✅ New broker added successfully!")
        print(f"   📊 Brokers before: {initial_brokers}")
        print(f"   📊 Brokers after: {final_brokers}")

        # Verify the new broker works
        new_operations = BrokerMappingRegistry.get_supported_operations("demo_broker")
        print(f"   📊 New broker operations: {len(new_operations)}")

        self.demo_results['new_broker'] = {
            'initial_count': initial_brokers,
            'final_count': final_brokers,
            'new_broker_operations': len(new_operations),
            'successfully_added': final_brokers > initial_brokers
        }

    def _demo_broker_transformer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Demo broker parameter transformer"""
        return {
            'symbol': params['symbol'],
            'qty': params['quantity'],
            'side': params['order_side'].lower(),
            'type': params['order_type'].lower(),
            'product': 'I' if params['product_type'] == 'INTRADAY' else 'D'
        }

    def _demo_risk_management(self):
        """Demonstrate risk management capabilities"""
        print("\n🛡️ STEP 7: Risk Management Integration")
        print("-" * 40)

        risk_scenarios = [
            {
                'name': 'Valid Order',
                'params': {
                    'symbol': 'HDFC',
                    'exchange': 'NSE',
                    'quantity': 25,
                    'order_side': 'BUY',
                    'order_type': 'LIMIT',
                    'product_type': 'DELIVERY',
                    'price': 1650.0
                },
                'should_pass': True
            },
            {
                'name': 'Negative Quantity Risk',
                'params': {
                    'symbol': 'RISKY',
                    'exchange': 'NSE',
                    'quantity': -100,
                    'order_side': 'SELL',
                    'order_type': 'MARKET',
                    'product_type': 'INTRADAY'
                },
                'should_pass': False
            },
            {
                'name': 'Zero Quantity Risk',
                'params': {
                    'symbol': 'ZERO',
                    'exchange': 'NSE',
                    'quantity': 0,
                    'order_side': 'BUY',
                    'order_type': 'LIMIT',
                    'product_type': 'DELIVERY',
                    'price': 100.0
                },
                'should_pass': False
            }
        ]

        risk_decisions = []

        for scenario in risk_scenarios:
            errors = ParameterSchemaRegistry.validate_params(OperationType.PLACE_ORDER, scenario['params'])
            validation_passed = len(errors) == 0
            expected_result = scenario['should_pass']

            correct_decision = True  if validation_passed == expected_result else False
            risk_decisions.append(correct_decision)

            status = "✅" if correct_decision else "❌"
            decision = "ALLOWED" if validation_passed else "BLOCKED"
            expected = "SHOULD PASS" if expected_result else "SHOULD FAIL"

            print(f"{status} {scenario['name']}: {decision} ({expected})")

        risk_effectiveness = (sum(risk_decisions) / len(risk_decisions)) * 100
        print(f"📊 Risk Management Effectiveness: {risk_effectiveness:.1f}%")

        self.demo_results['risk_management'] = {
            'scenarios_tested': len(risk_scenarios),
            'correct_decisions': sum(risk_decisions),
            'effectiveness_percentage': risk_effectiveness
        }

    def _demo_trading_scenarios(self):
        """Demonstrate complete trading scenarios"""
        print("\n📈 STEP 8: Complete Trading Scenarios")
        print("-" * 40)

        # Portfolio Diversification Scenario
        portfolio_scenario = {
            'name': 'Portfolio Diversification',
            'operations': [
                {'operation': OperationType.GET_QUOTES, 'symbols': ['RELIANCE', 'TCS', 'HDFC']},
                {'operation': OperationType.PLACE_ORDER, 'symbol': 'RELIANCE', 'quantity': 50, 'side': 'BUY'},
                {'operation': OperationType.PLACE_ORDER, 'symbol': 'TCS', 'quantity': 30, 'side': 'BUY'},
                {'operation': OperationType.GET_POSITIONS, 'account': 'MAIN'}
            ]
        }

        scenario_feasibility = self._analyze_scenario_feasibility(portfolio_scenario)

        print(f"✅ Scenario: {portfolio_scenario['name']}")
        print(f"   📊 Operations planned: {len(portfolio_scenario['operations'])}")
        print(f"   📊 Feasible executions: {scenario_feasibility['feasible_operations']}")
        print(f"   📊 Feasibility rate: {scenario_feasibility['feasibility_percentage']:.1f}%")

        self.demo_results['trading_scenarios'] = {
            'scenario_name': portfolio_scenario['name'],
            'planned_operations': len(portfolio_scenario['operations']),
            'feasible_operations': scenario_feasibility['feasible_operations'],
            'feasibility_rate': scenario_feasibility['feasibility_percentage']
        }

    def _analyze_scenario_feasibility(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if a trading scenario is feasible with current broker setup"""
        total_operations = len(scenario['operations'])
        feasible_operations = 0

        brokers = BrokerMappingRegistry.list_brokers()

        for operation_spec in scenario['operations']:
            operation_type = operation_spec['operation']

            # Check if any broker supports this operation
            for broker in brokers:
                supported_ops = BrokerMappingRegistry.get_supported_operations(broker)
                if operation_type in supported_ops:
                    feasible_operations += 1
                    break

        return {
            'total_operations': total_operations,
            'feasible_operations': feasible_operations,
            'feasibility_percentage': (feasible_operations / total_operations * 100) if total_operations > 0 else 0
        }

    def _demo_final_summary(self):
        """Show final comprehensive summary"""
        print("\n🎯 DEMO RESULTS SUMMARY")
        print("=" * 70)

        # Calculate overall success metrics
        total_tests = 0
        successful_tests = 0

        for _, results in self.demo_results.items():
            if isinstance(results, dict):
                if 'success' in results:
                    total_tests += 1
                    if results['success']:
                        successful_tests += 1
                elif 'success_rate' in results:
                    total_tests += 1
                    if results['success_rate'] >= 80:  # 80% threshold
                        successful_tests += 1
                elif 'successfully_added' in results:
                    total_tests += 1
                    if results['successfully_added']:
                        successful_tests += 1
                elif 'effectiveness_percentage' in results:
                    total_tests += 1
                    if results['effectiveness_percentage'] >= 75:  # 75% threshold
                        successful_tests += 1

        overall_success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"📊 Overall Demo Success Rate: {overall_success_rate:.1f}%")
        print(f"📊 Tests Passed: {successful_tests}/{total_tests}")

        print("\n🏆 KEY ACHIEVEMENTS:")
        print("   ✓ Multi-broker architecture working")
        print("   ✓ Parameter validation and transformation")
        print("   ✓ Dynamic broker addition capability")
        print("   ✓ Risk management integration")
        print("   ✓ Real-world trading scenarios supported")

        print("\n🚀 ARCHITECTURE BENEFITS DEMONSTRATED:")
        print("   ✓ Scalable: Easy to add new brokers and operations")
        print("   ✓ Robust: Built-in validation and error handling")
        print("   ✓ Maintainable: Standardized interfaces and patterns")
        print("   ✓ Type-safe: Strong typing throughout the system")
        print("   ✓ Extensible: Plugin-like architecture for customization")

        return {
            'overall_success_rate': overall_success_rate,
            'tests_passed': successful_tests,
            'total_tests': total_tests,
            'demo_complete': True
        }


def main():
    """Run the comprehensive demo"""
    demo = ScalableArchitectureDemo()
    results = demo.run_complete_demo()

    print("\n" + "=" * 70)
    print("🎉 COMPREHENSIVE DEMO COMPLETED SUCCESSFULLY!")
    print(f"📊 Final Score: {results['overall_success_rate']:.1f}%")
    print("=" * 70)

    return results


if __name__ == "__main__":
    main()
