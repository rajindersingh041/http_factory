# 🎯 Complete Modular Trading Architecture - Usage Guide

## 🚀 Quick Start with `uv`

```bash
# Run the complete demo
uv run python complete_demo.py

# Run the design patterns demo
uv run python design_patterns_demo.py

# Run the main application
uv run python -m network_test
```

## 🏗️ Architecture Overview

This is a complete, production-ready modular trading system built with:

- ✅ **SOLID Principles** - All five principles implemented
- ✅ **Design Patterns** - Factory, Strategy, Observer, Command, Builder, Adapter, Template Method
- ✅ **Modular Design** - Easy to extend and maintain
- ✅ **Type Safety** - Full type hints and protocols
- ✅ **Async Support** - Built for high-performance trading
- ✅ **Broker Agnostic** - Works with any trading API

## 🔧 Key Components

### 1. Service Factory Pattern

```python
from network_test.services import ServiceFactory

# Create any service using the factory
upstox_service = ServiceFactory.create_service(
    "upstox",
    access_token="your_token",
    rate_limit=50
)

groww_service = ServiceFactory.create_service(
    "groww",
    session_token="your_session",
    rate_limit=15
)

# Custom API service for any REST API
custom_service = ServiceFactory.create_service(
    "custom",
    base_url="https://api.example.com",
    endpoints={
        "status": {"path": "/status", "method": "GET"}
    }
)
```

### 2. Unified Interface (Liskov Substitution)

```python
# All services implement ITradingService interface
async def use_any_service(service: ITradingService):
    async with service:
        endpoints = service.list_endpoints()
        service_name = service.get_service_name()

        # Call any endpoint
        result = await service.call_endpoint("endpoint_name")
        return result

# Works with ANY service implementation
await use_any_service(upstox_service)
await use_any_service(groww_service)
await use_any_service(custom_service)
```

### 3. Parameter Transformation (Strategy Pattern)

```python
from network_test.services.broker_configurations import TransformerFactory

# Standard parameters work with any broker
standard_params = {
    'symbol': 'RELIANCE',
    'quantity': 100,
    'product_type': 'INTRADAY',
    'order_type': 'LIMIT',
    'price': 2500.0
}

# Automatically transforms to broker-specific format
upstox_transformer = TransformerFactory.create_transformer('upstox')
upstox_params = upstox_transformer.transform(standard_params)
# Result: {'instrument_token': 'NSE_RELIANCE', 'quantity': 100, ...}

xts_transformer = TransformerFactory.create_transformer('xts')
xts_params = xts_transformer.transform(standard_params)
# Result: {'exchangeInstrumentID': 0, 'orderQuantity': 100, ...}
```

### 4. Easy Extension (Open/Closed Principle)

```python
# Add a new broker WITHOUT modifying existing code

# 1. Create mappings
class AngelMappings:
    PRODUCT_TYPE_MAP = {'INTRADAY': 'MIS', 'DELIVERY': 'CNC'}
    FIELD_MAP = {'symbol': 'trading_symbol', 'quantity': 'qty'}

# 2. Register with factory (one line!)
TransformerFactory.register_broker('angel', AngelMappings)

# 3. Done! Now you can use it
angel_transformer = TransformerFactory.create_transformer('angel')
```

## 🎨 Design Patterns in Action

### Strategy Pattern - Trading Strategies

```python
from design_patterns_demo import ScalpingStrategy, SwingTradingStrategy

# Different strategies for different trading styles
scalping = ScalpingStrategy()
swing = SwingTradingStrategy()

# Both implement the same interface but behave differently
scalping_order = scalping.execute_trade("RELIANCE", 100, 2500.0)
swing_order = swing.execute_trade("RELIANCE", 100, 2500.0)
```

### Observer Pattern - Event System

```python
from design_patterns_demo import TradingEventPublisher, RiskManager

publisher = TradingEventPublisher()
risk_manager = RiskManager()

# Subscribe to events
publisher.subscribe(risk_manager)

# Events are automatically distributed
await publisher.publish(TradingEvent("order_placed", {"order_id": "123"}))
```

### Command Pattern - Undo/Redo

```python
from design_patterns_demo import TradingCommandInvoker, PlaceOrderCommand

invoker = TradingCommandInvoker()
place_order = PlaceOrderCommand(service, {"symbol": "RELIANCE"})

# Execute command
await invoker.execute_command(place_order)

# Undo if needed
await invoker.undo_last_command()
```

### Builder Pattern - Complex Objects

```python
from design_patterns_demo import PortfolioBuilder

# Build complex portfolios step by step
portfolio = (PortfolioBuilder()
            .with_scalping_strategy()
            .with_swing_trading_strategy()
            .with_risk_management(max_position_size=50000)
            .with_logging()
            .build())
```

## 📈 Real-World Usage Examples

### 1. Multi-Broker Trading Application

```python
class TradingApp:
    def __init__(self):
        self.services = {
            'upstox': ServiceFactory.create_service('upstox', access_token="..."),
            'zerodha': ServiceFactory.create_service('custom',
                base_url="https://kite.zerodha.com",
                endpoints={...}),
        }

    async def place_order_on_best_broker(self, symbol: str, quantity: int):
        """Place order on the broker with best execution"""
        for broker_name, service in self.services.items():
            async with service:
                try:
                    result = await service.call_endpoint('place_order',
                        json_data={'symbol': symbol, 'quantity': quantity})
                    return f"Order placed on {broker_name}: {result}"
                except Exception:
                    continue
        return "All brokers failed"
```

### 2. Algorithm Trading System

```python
from design_patterns_demo import MomentumTradingAlgorithm

class AlgoTradingSystem:
    def __init__(self, service: ITradingService):
        self.service = service
        self.algorithm = MomentumTradingAlgorithm()

    async def run_algorithm(self):
        """Run trading algorithm"""
        session_result = await self.algorithm.execute_trading_session()

        # Execute orders through any broker service
        for order in session_result['orders']:
            await self.service.call_endpoint('place_order', json_data=order)
```

### 3. Risk Management System

```python
from design_patterns_demo import RiskManager, TradingEventPublisher

class RiskManagedTradingSystem:
    def __init__(self):
        self.publisher = TradingEventPublisher()
        self.risk_manager = RiskManager()
        self.publisher.subscribe(self.risk_manager)

    async def place_order_with_risk_check(self, order_params):
        """Place order with automatic risk management"""
        # Risk manager automatically gets notified
        await self.publisher.publish(
            TradingEvent("order_placed", order_params)
        )
```

## 🧪 Testing

```python
# Easy to test with dependency injection
async def test_any_service():
    mock_service = MockTradingService()  # Implements ITradingService
    app = TradingApp(mock_service)

    result = await app.place_order("RELIANCE", 100)
    assert result is not None
```

## 🔧 Configuration

### Environment Setup

```bash
# Install with uv
uv add aiohttp pytest pytest-asyncio

# Run tests
uv run pytest

# Run with specific configuration
uv run python -m network_test --config production.json
```

### Adding New Brokers

1. **Create Service Class**:

```python
class NewBrokerService(BaseTradingService):
    def get_service_name(self) -> str:
        return "new_broker"
```

2. **Create Parameter Mappings**:

```python
class NewBrokerMappings:
    PRODUCT_TYPE_MAP = {'INTRADAY': 'I'}
    FIELD_MAP = {'symbol': 'token'}
```

3. **Register with Factories**:

```python
ServiceFactory.register_service("new_broker", NewBrokerService)
TransformerFactory.register_broker("new_broker", NewBrokerMappings)
```

## 📊 Benefits Summary

| Benefit             | Implementation              | Real-World Impact                |
| ------------------- | --------------------------- | -------------------------------- |
| **Modularity**      | Independent components      | Easy maintenance                 |
| **Extensibility**   | Factory + Strategy patterns | Add brokers without code changes |
| **Testability**     | Dependency injection        | Isolated unit tests              |
| **Reusability**     | Interface segregation       | Same code for all brokers        |
| **Maintainability** | Single responsibility       | Easy to debug and fix            |
| **Scalability**     | Async architecture          | Handle high-frequency trading    |

## 🎯 Conclusion

This architecture provides:

- ✅ **Production Ready**: Used design patterns and SOLID principles
- ✅ **Broker Agnostic**: Works with any trading API
- ✅ **Easy to Extend**: Add new features without breaking existing code
- ✅ **Type Safe**: Full type hints for better IDE support
- ✅ **Well Tested**: Clean architecture makes testing easy
- ✅ **High Performance**: Async support for concurrent operations

Perfect for building scalable trading applications that need to work with multiple brokers and handle complex trading scenarios.
