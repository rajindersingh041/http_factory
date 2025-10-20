"""
🏗️ Broker Configurations - The Magic Configuration Factory!

This is like having a factory that builds custom adapters for each broker.
Think of it like having different types of phone chargers:
- iPhone uses Lightning ⚡
- Android uses USB-C 🔌
- Old phones use Micro-USB 📱

But what if you had a universal adapter that could automatically figure out
which type of charger each phone needs? That's what this module does!

🎯 What This Module Does:
1. Creates "adapters" for each broker (Upstox, XTS, Groww)
2. Tells each adapter how to "translate" your requests
3. Sets up validation rules (like "don't charge a phone at 1000 volts!")
4. Registers everything so it works automatically

🔧 How It Works (Like LEGO Instructions):
Step 1: Define validation rules (safety first!)
Step 2: Create parameter transformers (the translators)
Step 3: Build configurations for each broker
Step 4: Register everything in the system

After running this once, you can use ANY broker with the same simple commands!

Example:
```python
# Before this module: Different code for each broker 😫
upstox_result = await upstox.place_order(instrument_token=123, orderQuantity=10)
xts_result = await xts.place_order(exchangeSegment=1, orderQuantity=10)

# After this module: Same code for all brokers! 🎉
result = await any_broker.place_order_standard(symbol="RELIANCE", quantity=10)
```

The magic happens automatically behind the scenes!
"""

from typing import Any, Dict

from .scalable_architecture import (BrokerConfigurationBuilder,
                                    EndpointCategory, OperationType,
                                    ParameterSchema, ParameterSchemaRegistry)

# =====================================================
# PARAMETER VALIDATION RULES
# =====================================================

def validate_order_params(params: Dict[str, Any]) -> list[str]:
    """
    🛡️ Order Validation - Like a Safety Inspector!

    Think of this like a safety inspector at a playground who checks:
    - Are you wearing a helmet? ⛑️
    - Are your shoelaces tied? 👟
    - Do you have a grown-up with you? 👨‍👩‍👧‍👦

    This function checks your order before sending it to make sure:
    - You're not trying to buy negative stocks (impossible!)
    - If you want a specific price, you actually provided one
    - You're not doing anything that might break the system

    Args:
        params: Your order details (like a shopping list)

    Returns:
        List of problems found (empty list = everything is perfect!)

    Example:
        validate_order_params({'quantity': -5}) → ["Quantity must be positive"]
        validate_order_params({'quantity': 10}) → [] (all good!)
    """
    errors = []

    # Check quantity is positive (you can't buy -5 apples!)
    if params.get('quantity', 0) <= 0:
        errors.append("Quantity must be positive")

    # Check limit orders have prices (like asking for "expensive food" but not saying how much)
    if params.get('order_type') == 'LIMIT' and not params.get('price'):
        errors.append("Limit orders require price")

    # Check trigger price isn't negative (can't trigger at negative money!)
    if params.get('trigger_price', 0) < 0:
        errors.append("Trigger price cannot be negative")

    return errors


def validate_quote_params(params: Dict[str, Any]) -> list[str]:
    """
    📊 Quote Validation - Like Checking Your Shopping List!

    Think of this like a helpful store clerk who checks your shopping list:
    - Did you write anything on your list? 📝
    - Are you trying to buy too many things at once? 🛒

    This function makes sure your quote request makes sense:
    - You asked for at least one stock price
    - You didn't ask for too many (brokers get tired!)

    Args:
        params: Your quote request (like asking "How much do these cost?")

    Returns:
        List of problems found (empty = ready to go!)

    Example:
        validate_quote_params({'symbols': []}) → ["At least one symbol required"]
        validate_quote_params({'symbols': ['RELIANCE']}) → [] (perfect!)
    """
    errors = []

    symbols = params.get('symbols', [])

    # Check you asked for at least one stock (like going to store with empty list)
    if not symbols or len(symbols) == 0:
        errors.append("At least one symbol is required")

    # Check you didn't ask for too many (brokers have limits, like store cashiers!)
    if len(symbols) > 50:  # Most brokers have limits
        errors.append("Too many symbols requested (max 50)")

    return errors


# =====================================================
# PARAMETER TRANSFORMERS
# =====================================================

def upstox_order_transformer(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    🔄 Upstox Order Transformer - Like a Language Translator!

    This is like having a friend who speaks both English and Upstox-ese!

    You say: "I want to buy 10 RELIANCE shares for delivery"
    Upstox needs: {"instrument_token": "NSE_RELIANCE", "product": "D", "quantity": 10}

    This function translates your normal words into Upstox's special language:
    - "DELIVERY" becomes "D" (Upstox's secret code for delivery)
    - "RELIANCE" becomes "NSE_RELIANCE" (Upstox's way of saying NSE stock)
    - "BUY" stays "BUY" (some things are the same!)

    Args:
        params: Your order in normal human language

    Returns:
        Same order but in Upstox's special format

    Example:
        Input: {'symbol': 'RELIANCE', 'quantity': 10, 'product_type': 'DELIVERY'}
        Output: {'instrument_token': 'NSE_RELIANCE', 'quantity': 10, 'product': 'D'}
    """
    # Upstox's secret codes for product types
    product_map = {
        'INTRADAY': 'I',    # I = Intraday (like renting for a day)
        'DELIVERY': 'D',    # D = Delivery (like buying to keep)
        'MARGIN': 'M'       # M = Margin (like buying with borrowed money)
    }

    # Upstox's way of saying order types
    order_type_map = {
        'MARKET': 'MARKET',         # Same as normal!
        'LIMIT': 'LIMIT',           # Same as normal!
        'STOP_LOSS': 'SL',          # They use short form "SL"
        'STOP_LOSS_MARKET': 'SL-M'  # They use "SL-M" for this
    }

    return {
        'quantity': params['quantity'],
        'product': product_map.get(params['product_type'], 'I'),
        'validity': params.get('validity', 'DAY'),
        'price': params.get('price', 0),
        'tag': params.get('tag', ''),
        'instrument_token': f"{params['exchange']}_{params['symbol']}",
        'order_type': order_type_map.get(params['order_type'], 'MARKET'),
        'transaction_type': params['order_side'],
        'disclosed_quantity': params.get('disclosed_quantity', 0),
        'trigger_price': params.get('trigger_price', 0),
        'is_amo': params.get('is_amo', False)
    }


def xts_order_transformer(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    🔄 XTS Order Transformer - Another Language Translator!

    XTS speaks a completely different language than Upstox!

    You say: "I want to buy 10 RELIANCE shares for delivery"
    XTS needs: {"exchangeSegment": "NSECM", "productType": "CNC", "orderQuantity": 10}

    This function translates your words into XTS's special language:
    - "NSE" becomes "NSECM" (XTS's fancy name for NSE)
    - "DELIVERY" becomes "CNC" (XTS's code for delivery)
    - "quantity" becomes "orderQuantity" (XTS likes longer names)

    It's like having different restaurants with different ways to order:
    - McDonald's: "I want a Big Mac"
    - Fancy Restaurant: "I would like to order the signature beef sandwich"
    - Same food, different way to ask!

    Args:
        params: Your order in normal language

    Returns:
        Same order in XTS's fancy language
    """
    # XTS's fancy codes for product types
    product_map = {
        'INTRADAY': 'MIS',   # MIS = Margin Intraday Square-off
        'DELIVERY': 'CNC',   # CNC = Cash and Carry (delivery)
        'MARGIN': 'NRML'     # NRML = Normal (margin trading)
    }

    # XTS's fancy names for exchanges
    exchange_map = {
        'NSE': 'NSECM',      # NSECM = NSE Capital Market
        'BSE': 'BSECM',      # BSECM = BSE Capital Market
        'NFO': 'NSEFO',      # NSEFO = NSE Futures & Options
        'BFO': 'BSEFO'       # BSEFO = BSE Futures & Options
    }

    return {
        'exchangeSegment': exchange_map.get(params['exchange'], params['exchange']),
        'exchangeInstrumentID': params.get('instrument_id', 0),
        'productType': product_map.get(params['product_type'], 'MIS'),
        'orderType': params['order_type'],
        'orderSide': params['order_side'],
        'timeInForce': params.get('validity', 'DAY'),
        'disclosedQuantity': params.get('disclosed_quantity', 0),
        'orderQuantity': params['quantity'],
        'limitPrice': params.get('price', 0),
        'stopPrice': params.get('trigger_price', 0)
    }


def upstox_quote_transformer(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    💹 Upstox Quote Transformer - Like Asking for Prices!

    When you want to know prices, different stores have different ways:
    - Normal store: "How much is apple, banana?"
    - Upstox store: "How much is FRUIT_apple,FRUIT_banana?"

    This function changes your simple request into Upstox's format:
    - You ask: ["RELIANCE", "TCS"]
    - Upstox needs: "NSE_RELIANCE,NSE_TCS"

    It's like adding the store section to each item:
    - "milk" becomes "DAIRY_milk"
    - "bread" becomes "BAKERY_bread"

    Args:
        params: List of stocks you want prices for

    Returns:
        Upstox's format with exchange prefixes and commas

    Example:
        Input: {'symbols': ['RELIANCE', 'TCS']}
        Output: {'instrument_key': 'NSE_RELIANCE,NSE_TCS'}
    """
    exchange = params.get('exchange', 'NSE')  # Default to NSE if not specified

    # Add exchange prefix to each symbol (like adding store section)
    instrument_keys = [f"{exchange}_{symbol}" for symbol in params['symbols']]

    return {
        'instrument_key': ','.join(instrument_keys)  # Join with commas for Upstox
    }


def xts_quote_transformer(params: Dict[str, Any]) -> Dict[str, Any]:
    """Transform standard quote params to XTS format"""
    return {
        'instruments': params.get('instruments', ''),
        'xtsMessageCode': params.get('message_code', 1512)
    }


# =====================================================
# UPSTOX CONFIGURATION
# =====================================================

def configure_upstox_broker():
    """Configure all Upstox endpoints"""
    builder = BrokerConfigurationBuilder("upstox")

    # Order Operations
    builder.add_operation(
        OperationType.PLACE_ORDER,
        broker_endpoint="place_order",
        http_method="POST",
        required_fields=['symbol', 'exchange', 'quantity', 'order_side', 'order_type', 'product_type'],
        optional_fields=['price', 'trigger_price', 'validity', 'disclosed_quantity', 'tag', 'is_amo'],
        parameter_transformer=upstox_order_transformer,
        requires_auth=True,
        cache_ttl=0
    )

    builder.add_operation(
        OperationType.MODIFY_ORDER,
        broker_endpoint="modify_order",
        http_method="PUT",
        required_fields=['order_id'],
        optional_fields=['quantity', 'price', 'trigger_price', 'validity'],
        requires_auth=True,
        cache_ttl=0
    )

    builder.add_operation(
        OperationType.CANCEL_ORDER,
        broker_endpoint="cancel_order",
        http_method="DELETE",
        required_fields=['order_id'],
        requires_auth=True,
        cache_ttl=0
    )

    builder.add_operation(
        OperationType.GET_ORDERS,
        broker_endpoint="orders",
        http_method="GET",
        required_fields=[],
        requires_auth=True,
        cache_ttl=5
    )

    # Portfolio Operations
    builder.add_operation(
        OperationType.GET_POSITIONS,
        broker_endpoint="positions",
        http_method="GET",
        required_fields=[],
        requires_auth=True,
        cache_ttl=10
    )

    builder.add_operation(
        OperationType.GET_HOLDINGS,
        broker_endpoint="holdings",
        http_method="GET",
        required_fields=[],
        requires_auth=True,
        cache_ttl=30
    )

    # Market Data Operations
    builder.add_operation(
        OperationType.GET_QUOTES,
        broker_endpoint="quote",
        http_method="GET",
        required_fields=['symbols'],
        optional_fields=['exchange'],
        parameter_transformer=upstox_quote_transformer,
        requires_auth=True,
        cache_ttl=1
    )

    builder.add_operation(
        OperationType.GET_MARKET_STATUS,
        broker_endpoint="market_status",
        http_method="GET",
        required_fields=[],
        optional_fields=['segment'],
        requires_auth=True,
        cache_ttl=60
    )

    # Historical Data
    builder.add_operation(
        OperationType.GET_CANDLES,
        broker_endpoint="candles",
        http_method="GET",
        required_fields=['symbol', 'exchange', 'interval'],
        optional_fields=['from_date', 'to_date', 'limit'],
        requires_auth=True,
        cache_ttl=300
    )

    # User Profile
    builder.add_operation(
        OperationType.GET_PROFILE,
        broker_endpoint="profile",
        http_method="GET",
        required_fields=[],
        requires_auth=True,
        cache_ttl=3600
    )

    builder.add_operation(
        OperationType.GET_FUNDS,
        broker_endpoint="funds",
        http_method="GET",
        required_fields=[],
        requires_auth=True,
        cache_ttl=10
    )

    builder.build()


# =====================================================
# XTS CONFIGURATION
# =====================================================

def configure_xts_broker():
    """Configure all XTS endpoints"""
    builder = BrokerConfigurationBuilder("xts")

    # Order Operations
    builder.add_operation(
        OperationType.PLACE_ORDER,
        broker_endpoint="order.place",
        http_method="POST",
        required_fields=['symbol', 'exchange', 'quantity', 'order_side', 'order_type', 'product_type', 'instrument_id'],
        optional_fields=['price', 'trigger_price', 'validity', 'disclosed_quantity'],
        parameter_transformer=xts_order_transformer,
        requires_auth=True,
        cache_ttl=0
    )

    builder.add_operation(
        OperationType.MODIFY_ORDER,
        broker_endpoint="order.modify",
        http_method="PUT",
        required_fields=['order_id'],
        requires_auth=True,
        cache_ttl=0
    )

    builder.add_operation(
        OperationType.CANCEL_ORDER,
        broker_endpoint="order.cancel",
        http_method="DELETE",
        required_fields=['order_id'],
        requires_auth=True,
        cache_ttl=0
    )

    builder.add_operation(
        OperationType.GET_ORDERS,
        broker_endpoint="orders",
        http_method="GET",
        required_fields=[],
        requires_auth=True,
        cache_ttl=5
    )

    builder.add_operation(
        OperationType.GET_TRADES,
        broker_endpoint="trades",
        http_method="GET",
        required_fields=[],
        requires_auth=True,
        cache_ttl=5
    )

    # Portfolio Operations
    builder.add_operation(
        OperationType.GET_POSITIONS,
        broker_endpoint="portfolio.positions",
        http_method="GET",
        required_fields=[],
        requires_auth=True,
        cache_ttl=10
    )

    builder.add_operation(
        OperationType.GET_HOLDINGS,
        broker_endpoint="portfolio.holdings",
        http_method="GET",
        required_fields=[],
        requires_auth=True,
        cache_ttl=30
    )

    # Market Data Operations
    builder.add_operation(
        OperationType.GET_QUOTES,
        broker_endpoint="market.instruments.quotes",
        http_method="GET",
        required_fields=['instruments'],
        optional_fields=['message_code'],
        parameter_transformer=xts_quote_transformer,
        requires_auth=True,
        cache_ttl=1
    )

    builder.add_operation(
        OperationType.SEARCH_INSTRUMENTS,
        broker_endpoint="market.search.instrumentsbystring",
        http_method="GET",
        required_fields=['search_string'],
        requires_auth=True,
        cache_ttl=300
    )

    # User Operations
    builder.add_operation(
        OperationType.GET_PROFILE,
        broker_endpoint="user.profile",
        http_method="GET",
        required_fields=[],
        requires_auth=True,
        cache_ttl=3600
    )

    builder.add_operation(
        OperationType.GET_FUNDS,
        broker_endpoint="user.balance",
        http_method="GET",
        required_fields=[],
        requires_auth=True,
        cache_ttl=60
    )

    builder.build()


# =====================================================
# GROWW CONFIGURATION
# =====================================================

def configure_groww_broker():
    """Configure all Groww endpoints"""
    builder = BrokerConfigurationBuilder("groww")

    # Market Data Operations (Groww is primarily market data)
    builder.add_operation(
        OperationType.GET_QUOTES,
        broker_endpoint="live_aggregated",
        http_method="POST",
        required_fields=['symbols'],
        optional_fields=['exchange'],
        requires_auth=False,
        cache_ttl=5
    )

    builder.add_operation(
        OperationType.GET_INDICES,
        broker_endpoint="nifty_data",
        http_method="GET",
        required_fields=[],
        optional_fields=['index_name'],
        requires_auth=False,
        cache_ttl=60
    )

    builder.build()


# =====================================================
# REGISTER ALL PARAMETER SCHEMAS
# =====================================================

def register_global_schemas():
    """Register global parameter schemas with validation"""

    # Order schema
    order_schema = ParameterSchema(
        operation=OperationType.PLACE_ORDER,
        category=EndpointCategory.ORDERS,
        required_fields=['symbol', 'exchange', 'quantity', 'order_side', 'order_type', 'product_type'],
        optional_fields=['price', 'trigger_price', 'validity', 'disclosed_quantity', 'tag', 'is_amo'],
        validation_rules=[validate_order_params],
        description="Standard order placement parameters"
    )
    ParameterSchemaRegistry.register_schema(order_schema)

    # Quote schema
    quote_schema = ParameterSchema(
        operation=OperationType.GET_QUOTES,
        category=EndpointCategory.MARKET_DATA,
        required_fields=['symbols'],
        optional_fields=['exchange', 'message_code'],
        validation_rules=[validate_quote_params],
        description="Standard quote retrieval parameters"
    )
    ParameterSchemaRegistry.register_schema(quote_schema)

    # Position schema
    position_schema = ParameterSchema(
        operation=OperationType.GET_POSITIONS,
        category=EndpointCategory.PORTFOLIO,
        required_fields=[],
        optional_fields=['account_id'],
        description="Standard position retrieval parameters"
    )
    ParameterSchemaRegistry.register_schema(position_schema)

    # Add more schemas as needed...


# =====================================================
# INITIALIZATION FUNCTION
# =====================================================

def initialize_scalable_architecture():
    """Initialize the complete scalable architecture"""
    print("🏗️ Initializing Scalable Trading Architecture...")

    # Register global schemas
    register_global_schemas()
    print("✅ Global parameter schemas registered")

    # Configure all brokers
    configure_upstox_broker()
    print("✅ Upstox configuration loaded")

    configure_xts_broker()
    print("✅ XTS configuration loaded")

    configure_groww_broker()
    print("✅ Groww configuration loaded")

    # Print summary
    from .scalable_architecture import (BrokerMappingRegistry,
                                        ParameterSchemaRegistry)

    print("\n📊 Architecture Summary:")
    print(f"   Registered Brokers: {len(BrokerMappingRegistry.list_brokers())}")
    print(f"   Registered Operations: {len(ParameterSchemaRegistry.list_operations())}")

    for broker in BrokerMappingRegistry.list_brokers():
        operations = BrokerMappingRegistry.get_supported_operations(broker)
        print(f"   {broker.title()}: {len(operations)} operations")

    print("\n🚀 Scalable architecture ready!")


if __name__ == "__main__":
    initialize_scalable_architecture()
