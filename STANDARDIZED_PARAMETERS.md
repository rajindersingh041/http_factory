# Standardized Parameter System for Trading Services

## Problem Solved

Each broker/trading service has different parameter names and payload formats for the same operations:

**Before (Broker-specific parameters):**

```python
# Upstox order
await upstox.place_order(
    quantity=1, product='I', validity='DAY', price=2500.50,
    tag='demo', instrument_token='NSE_RELIANCE',
    order_type='LIMIT', transaction_type='BUY'
)

# XTS order
await xts.place_order(
    exchangeSegment='NSECM', exchangeInstrumentID=26000,
    productType='MIS', orderType='LIMIT', orderSide='BUY',
    timeInForce='DAY', orderQuantity=1, limitPrice=2500.50
)

# Different parameter names, different formats!
```

**After (Standardized parameters):**

```python
# Works with ANY broker!
order_params = StandardOrderParams(
    symbol='RELIANCE', exchange='NSE', quantity=1,
    order_side=OrderSide.BUY, order_type=OrderType.LIMIT,
    product_type=ProductType.INTRADAY, price=2500.50
)

await any_broker_service.place_order_standard(order_params)
```

## Architecture

### 1. Standardized Parameter Models

Located in `src/network_test/services/parameters.py`:

- **`StandardOrderParams`** - Universal order parameters
- **`StandardQuoteParams`** - Universal quote parameters
- **`StandardHistoricalParams`** - Universal historical data parameters
- **Enums** - Type-safe values (OrderSide, OrderType, ProductType, Validity)

### 2. Parameter Mappers

Each broker has a dedicated mapper that converts standardized parameters to broker-specific format:

- **`UpstoxParameterMapper`** - Maps to Upstox API format
- **`XTSParameterMapper`** - Maps to XTS API format
- **`GrowwParameterMapper`** - Maps to Groww API format

### 3. Enhanced Interface

The `ITradingService` interface now includes standardized methods:

- `place_order_standard(params: StandardOrderParams)`
- `get_quotes_standard(params: StandardQuoteParams)`
- `get_historical_data_standard(params: StandardHistoricalParams)`

### 4. Automatic Mapping

The `BaseTradingService` automatically:

1. Gets the appropriate mapper for the service
2. Maps standardized parameters to broker-specific format
3. Calls the correct endpoint with mapped parameters

## Usage Examples

### Basic Order Placement

```python
from network_test.services import UpstoxService, StandardOrderParams, OrderSide, OrderType, ProductType

# Create standardized parameters
order_params = StandardOrderParams(
    symbol="RELIANCE",
    exchange="NSE",
    quantity=10,
    order_side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    product_type=ProductType.INTRADAY,
    price=2500.50
)

# Works with any broker service
async with UpstoxService() as upstox:
    result = await upstox.place_order_standard(order_params)
```

### Multi-Broker Quote Retrieval

```python
from network_test.services import StandardQuoteParams

quote_params = StandardQuoteParams(
    symbols=["RELIANCE", "TCS", "INFY"],
    exchange="NSE"
)

# Same code works with all brokers
for service_class in [UpstoxService, XTSService, GrowwService]:
    async with service_class() as service:
        quotes = await service.get_quotes_standard(quote_params)
        print(f"{service.get_service_name()}: {quotes}")
```

### Broker-Specific Extras

```python
# Add broker-specific parameters via extras
order_params = StandardOrderParams(
    symbol="RELIANCE",
    exchange="NSE",
    quantity=1,
    order_side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    product_type=ProductType.INTRADAY,
    price=2500.0,
    extras={
        "exchangeInstrumentID": 26000,  # Required by XTS
        "is_amo": True,                 # Upstox After Market Order
        "user_order_id": "CUSTOM123"    # Custom reference
    }
)
```

## Key Benefits

### 1. **Unified Interface**

- Same code works with any broker
- No need to remember different parameter names
- Consistent behavior across services

### 2. **Type Safety**

- Enums prevent invalid values
- IDE autocompletion and validation
- Compile-time error checking

### 3. **Easy Broker Switching**

- Change broker without changing order logic
- A/B test different brokers easily
- Failover between brokers

### 4. **Reduced Errors**

- No more wrong parameter names
- Standardized validation
- Clear documentation

### 5. **Extensible**

- Easy to add new brokers
- Support for broker-specific features via `extras`
- Backward compatible with existing code

## Parameter Mapping Examples

### Order Parameters

| Standard       | Upstox             | XTS                    | Groww       |
| -------------- | ------------------ | ---------------------- | ----------- |
| `symbol`       | `instrument_token` | `exchangeInstrumentID` | `symbol`    |
| `quantity`     | `quantity`         | `orderQuantity`        | `qty`       |
| `order_side`   | `transaction_type` | `orderSide`            | `side`      |
| `order_type`   | `order_type`       | `orderType`            | `orderType` |
| `product_type` | `product`          | `productType`          | N/A         |
| `price`        | `price`            | `limitPrice`           | `price`     |
| `validity`     | `validity`         | `timeInForce`          | N/A         |

### Enum Mappings

**ProductType:**

- `INTRADAY` → Upstox: `"I"`, XTS: `"MIS"`, Groww: N/A
- `DELIVERY` → Upstox: `"D"`, XTS: `"CNC"`, Groww: N/A
- `MARGIN` → Upstox: `"M"`, XTS: `"NRML"`, Groww: N/A

**OrderType:**

- `MARKET` → All: `"MARKET"`
- `LIMIT` → All: `"LIMIT"`
- `STOP_LOSS` → Upstox: `"SL"`, XTS: `"STOPLOSS"`, Groww: `"stop_loss"`

## Implementation Details

### Adding a New Broker

1. **Create Parameter Mapper:**

```python
class NewBrokerParameterMapper(IParameterMapper):
    def map_order_params(self, params: StandardOrderParams) -> Dict[str, Any]:
        return {
            "broker_symbol": params.symbol,
            "broker_qty": params.quantity,
            # ... more mappings
        }

    def get_broker_name(self) -> str:
        return "new_broker"
```

2. **Register Mapper:**

```python
ParameterMapperFactory.register_mapper("new_broker", NewBrokerParameterMapper())
```

3. **Create Service:**

```python
class NewBrokerService(BaseTradingService):
    def get_service_name(self) -> str:
        return "new_broker"
    # ... implement other abstract methods
```

### Custom Validation

```python
class CustomOrderParams(StandardOrderParams):
    def __post_init__(self):
        # Custom validation
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.order_type == OrderType.LIMIT and not self.price:
            raise ValueError("Limit orders require price")
```

## Testing

### Running Tests

```bash
# Basic tests (no dependencies)
python test_parameters_simple.py

# Full test suite (requires pytest)
pytest test_parameters.py -v
```

### Example Test

```python
def test_broker_mapping():
    params = StandardOrderParams(
        symbol="RELIANCE", exchange="NSE", quantity=1,
        order_side=OrderSide.BUY, order_type=OrderType.LIMIT,
        product_type=ProductType.INTRADAY, price=2500.0
    )

    upstox_mapper = ParameterMapperFactory.get_mapper("upstox")
    upstox_params = upstox_mapper.map_order_params(params)

    assert upstox_params["instrument_token"] == "NSE_RELIANCE"
    assert upstox_params["transaction_type"] == "BUY"
    assert upstox_params["product"] == "I"
```

## Migration Guide

### Existing Code

```python
# OLD: Broker-specific
await upstox.place_order(
    quantity=1, product='I', validity='DAY',
    price=2500, instrument_token='NSE_RELIANCE',
    order_type='LIMIT', transaction_type='BUY'
)
```

### New Code

```python
# NEW: Standardized
order_params = StandardOrderParams(
    symbol='RELIANCE', exchange='NSE', quantity=1,
    order_side=OrderSide.BUY, order_type=OrderType.LIMIT,
    product_type=ProductType.INTRADAY, price=2500
)

await upstox.place_order_standard(order_params)
```

### Gradual Migration

Both old and new methods work simultaneously:

```python
# Still works
await service.place_order(quantity=1, product='I', ...)

# New standardized way
await service.place_order_standard(StandardOrderParams(...))
```

## Best Practices

### 1. Use Enums

```python
# ✅ Good - Type safe
order_side=OrderSide.BUY

# ❌ Avoid - String literals
order_side="BUY"
```

### 2. Handle Broker-Specific Features

```python
# Use extras for broker-specific parameters
order_params = StandardOrderParams(
    # ... standard params
    extras={"exchangeInstrumentID": 26000}  # XTS specific
)
```

### 3. Error Handling

```python
try:
    result = await service.place_order_standard(params)
except ValueError as e:
    print(f"Parameter validation error: {e}")
except Exception as e:
    print(f"Order placement failed: {e}")
```

### 4. Validation

```python
# Validate before placing orders
if params.order_type == OrderType.LIMIT and not params.price:
    raise ValueError("Limit orders require price")
```

## Future Enhancements

1. **Additional Operations**

   - Cancel order standardization
   - Modify order standardization
   - Portfolio operations

2. **Advanced Features**

   - Order validation rules
   - Parameter transformation pipelines
   - Dynamic mapper configuration

3. **Performance**

   - Parameter mapping caching
   - Bulk operation support
   - Async validation

4. **Integration**
   - WebSocket standardization
   - Real-time data parameters
   - Strategy execution parameters

## Conclusion

The standardized parameter system solves the core issue of different brokers requiring different parameter formats. It provides:

- **Consistency** - Same interface across all brokers
- **Type Safety** - Enum-based parameters prevent errors
- **Flexibility** - Support for broker-specific features
- **Maintainability** - Easy to add new brokers
- **Migration Path** - Gradual adoption possible

This makes the trading service interface truly broker-agnostic while maintaining the flexibility to use broker-specific features when needed.
