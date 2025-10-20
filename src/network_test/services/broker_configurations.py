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

from typing import Any, Callable, Dict

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
# MAPPING CONFIGURATIONS (Following SOLID Principles)
# =====================================================

class BrokerMappingConfig:
    """
    🗺️ Broker Mapping Configuration - The Universal Dictionary!

    This follows the Single Responsibility Principle (SRP):
    - ONLY responsible for storing mapping configurations
    - NOT responsible for doing transformations
    - Easy to modify without breaking transformation logic

    Think of this like a dictionary book:
    - English → French dictionary
    - English → Spanish dictionary
    - If French changes, Spanish dictionary is unaffected!
    """
    pass

class UpstoxMappings:
    """
    🏦 Upstox-Specific Mappings

    All Upstox mappings in one place - easy to find and modify!
    Following Single Responsibility: ONLY handles Upstox mappings.
    """

    # Product type mappings
    PRODUCT_TYPE_MAP = {
        'INTRADAY': 'I',    # I = Intraday (like renting for a day)
        'DELIVERY': 'D',    # D = Delivery (like buying to keep)
        'MARGIN': 'M'       # M = Margin (like buying with borrowed money)
    }

    # Order type mappings
    ORDER_TYPE_MAP = {
        'MARKET': 'MARKET',         # Same as normal!
        'LIMIT': 'LIMIT',           # Same as normal!
        'STOP_LOSS': 'SL',          # They use short form "SL"
        'STOP_LOSS_MARKET': 'SL-M'  # They use "SL-M" for this
    }

    # Field name mappings
    FIELD_MAP = {
        'symbol': 'instrument_token',
        'quantity': 'quantity',  # Same
        'order_side': 'transaction_type',
        'order_type': 'order_type',
        'product_type': 'product',
        'price': 'price',
        'trigger_price': 'trigger_price',
        'validity': 'validity',
        'disclosed_quantity': 'disclosed_quantity',
        'tag': 'tag',
        'is_amo': 'is_amo'
    }

class XTSMappings:
    """
    🏢 XTS-Specific Mappings

    All XTS mappings in one place - completely separate from Upstox!
    Following Single Responsibility and Open/Closed principles.
    """

    # Product type mappings
    PRODUCT_TYPE_MAP = {
        'INTRADAY': 'MIS',   # MIS = Margin Intraday Square-off
        'DELIVERY': 'CNC',   # CNC = Cash and Carry (delivery)
        'MARGIN': 'NRML'     # NRML = Normal (margin trading)
    }

    # Exchange mappings
    EXCHANGE_MAP = {
        'NSE': 'NSECM',      # NSECM = NSE Capital Market
        'BSE': 'BSECM',      # BSECM = BSE Capital Market
        'NFO': 'NSEFO',      # NSEFO = NSE Futures & Options
        'BFO': 'BSEFO'       # BSEFO = BSE Futures & Options
    }

    # Field name mappings
    FIELD_MAP = {
        'exchange': 'exchangeSegment',
        'instrument_id': 'exchangeInstrumentID',
        'product_type': 'productType',
        'order_type': 'orderType',
        'order_side': 'orderSide',
        'validity': 'timeInForce',
        'disclosed_quantity': 'disclosedQuantity',
        'quantity': 'orderQuantity',
        'price': 'limitPrice',
        'trigger_price': 'stopPrice'
    }

# =====================================================
# GENERIC TRANSFORMER CLASSES (Following SOLID)
# =====================================================

from abc import ABC, abstractmethod


class IParameterTransformer(ABC):
    """
    🔧 Parameter Transformer Interface

    Following Interface Segregation Principle (ISP):
    - Simple, focused interface
    - Easy to implement for any broker
    - Clients depend only on methods they use
    """

    @abstractmethod
    def transform(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform standard parameters to broker-specific format"""
        pass

class MappingBasedTransformer(IParameterTransformer):
    """
    🎭 Mapping-Based Transformer - The Universal Translator!

    Following Dependency Inversion Principle (DIP):
    - Depends on abstractions (mappings), not concrete implementations
    - Can work with ANY broker's mappings
    - High-level logic doesn't change when mappings change

    Following Open/Closed Principle (OCP):
    - Open for extension (new brokers)
    - Closed for modification (core logic never changes)
    """

    def __init__(self, mappings_class):
        """
        Initialize with broker-specific mappings

        Args:
            mappings_class: Broker mapping class (UpstoxMappings, XTSMappings, etc.)
        """
        self.mappings = mappings_class

    def transform(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        🔄 Universal Transform Method

        This method works for ANY broker because it uses dependency injection!
        The magic happens through the mappings, not hardcoded logic.
        """
        result = {}

        # Transform field names
        for standard_field, value in params.items():
            broker_field = getattr(self.mappings, 'FIELD_MAP', {}).get(standard_field, standard_field)
            result[broker_field] = value

        # Apply value mappings
        if hasattr(self.mappings, 'PRODUCT_TYPE_MAP') and 'product_type' in params:
            mapped_field = getattr(self.mappings, 'FIELD_MAP', {}).get('product_type', 'product_type')
            result[mapped_field] = self.mappings.PRODUCT_TYPE_MAP.get(params['product_type'], params['product_type'])

        if hasattr(self.mappings, 'ORDER_TYPE_MAP') and 'order_type' in params:
            mapped_field = getattr(self.mappings, 'FIELD_MAP', {}).get('order_type', 'order_type')
            result[mapped_field] = self.mappings.ORDER_TYPE_MAP.get(params['order_type'], params['order_type'])

        if hasattr(self.mappings, 'EXCHANGE_MAP') and 'exchange' in params:
            mapped_field = getattr(self.mappings, 'FIELD_MAP', {}).get('exchange', 'exchange')
            result[mapped_field] = self.mappings.EXCHANGE_MAP.get(params['exchange'], params['exchange'])

        # Special handling for symbol → instrument_token
        if 'symbol' in params and 'exchange' in params:
            if hasattr(self.mappings, 'FIELD_MAP') and self.mappings.FIELD_MAP.get('symbol') == 'instrument_token':
                result['instrument_token'] = f"{params['exchange']}_{params['symbol']}"
                if 'symbol' in result:
                    del result['symbol']  # Remove the original field

        return result

# =====================================================
# BROKER-SPECIFIC TRANSFORMER INSTANCES
# =====================================================

def upstox_order_transformer(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    🔄 Upstox Order Transformer - Now Following SOLID Principles!

    Before: Hardcoded mappings mixed with logic (violates SRP, OCP, DIP)
    After: Uses dependency injection and separation of concerns

    Benefits:
    - Easy to modify mappings without touching transformation logic
    - Can reuse transformation logic for other brokers
    - Easy to test and maintain
    """
    transformer = MappingBasedTransformer(UpstoxMappings)
    result = transformer.transform(params)

    # Add default values specific to Upstox
    result.setdefault('validity', 'DAY')
    result.setdefault('price', 0)
    result.setdefault('tag', '')
    result.setdefault('disclosed_quantity', 0)
    result.setdefault('trigger_price', 0)
    result.setdefault('is_amo', False)

    return result

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
    🔄 XTS Order Transformer - Now Following SOLID Principles!

    Before: Hardcoded mappings everywhere (violates SRP, makes changes risky)
    After: Clean separation using dependency injection

    Benefits:
    - All XTS mappings in XTSMappings class (easy to find and modify)
    - Reuses the same transformation logic as Upstox
    - Adding new field mappings doesn't require code changes
    """
    transformer = MappingBasedTransformer(XTSMappings)
    result = transformer.transform(params)

    # Add XTS-specific defaults
    result.setdefault('exchangeInstrumentID', 0)
    result.setdefault('timeInForce', 'DAY')
    result.setdefault('disclosedQuantity', 0)
    result.setdefault('limitPrice', 0)
    result.setdefault('stopPrice', 0)

    return result


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
# TRANSFORMER FACTORY (Following SOLID Principles)
# =====================================================

class TransformerFactory:
    """
    🏭 Transformer Factory - Following SOLID Principles!

    Benefits of this approach:
    1. Single Responsibility: Only creates transformers
    2. Open/Closed: Easy to add new brokers without modifying existing code
    3. Dependency Inversion: High-level code doesn't depend on concrete transformers

    Adding a new broker is now SUPER easy:
    ```python
    # 1. Create mappings class
    class NewBrokerMappings:
        PRODUCT_TYPE_MAP = {'INTRADAY': 'INTRA'}
        FIELD_MAP = {'quantity': 'qty'}

    # 2. Register in factory (just one line!)
    TransformerFactory.register('newbroker', NewBrokerMappings)

    # 3. Done! No other code changes needed!
    ```
    """

    _transformers = {
        'upstox': UpstoxMappings,
        'xts': XTSMappings,
        # Easy to add more: 'zerodha': ZerodhaMappings, etc.
    }

    @classmethod
    def create_transformer(cls, broker_name: str) -> IParameterTransformer:
        """
        Create transformer for specified broker

        Args:
            broker_name: Name of the broker

        Returns:
            Configured transformer instance

        Raises:
            ValueError: If broker not supported
        """
        if broker_name not in cls._transformers:
            available = ', '.join(cls._transformers.keys())
            raise ValueError(f"Unsupported broker: {broker_name}. Available: {available}")

        mappings_class = cls._transformers[broker_name]
        return MappingBasedTransformer(mappings_class)

    @classmethod
    def register_broker(cls, broker_name: str, mappings_class) -> None:
        """
        Register a new broker (following Open/Closed Principle)

        Args:
            broker_name: Name of the new broker
            mappings_class: Mappings class for the broker
        """
        cls._transformers[broker_name] = mappings_class
        print(f"✅ Registered new broker: {broker_name}")

    @classmethod
    def list_supported_brokers(cls) -> list[str]:
        """Get list of supported brokers"""
        return list(cls._transformers.keys())

# =====================================================
# UPDATED TRANSFORMER FUNCTIONS (Using Factory)
# =====================================================

def create_upstox_order_transformer() -> IParameterTransformer:
    """Create Upstox order transformer using factory pattern"""
    return TransformerFactory.create_transformer('upstox')

def create_xts_order_transformer() -> IParameterTransformer:
    """Create XTS order transformer using factory pattern"""
    return TransformerFactory.create_transformer('xts')


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
# CONFIGURATION REGISTRY (Following SOLID Principles)
# =====================================================

class BrokerConfigurationRegistry:
    """
    📚 Broker Configuration Registry - Following SOLID Principles!

    Single Responsibility: Only manages broker configurations
    Open/Closed: Easy to add new brokers without modifying existing code
    Dependency Inversion: Configurations are injected, not hardcoded

    Benefits:
    - All broker configs in one place
    - Easy to add new brokers
    - Configuration changes don't affect other brokers
    - Easy to test individual broker configurations
    """

    _configurations = {}

    @classmethod
    def register_configuration(cls, broker_name: str, config_func: Callable[[], None]):
        """
        Register a broker configuration function

        Args:
            broker_name: Name of the broker
            config_func: Function that configures the broker
        """
        cls._configurations[broker_name] = config_func
        print(f"✅ Registered configuration for: {broker_name}")

    @classmethod
    def configure_broker(cls, broker_name: str):
        """Configure a specific broker"""
        if broker_name not in cls._configurations:
            available = ', '.join(cls._configurations.keys())
            raise ValueError(f"No configuration found for: {broker_name}. Available: {available}")

        cls._configurations[broker_name]()

    @classmethod
    def configure_all_brokers(cls):
        """Configure all registered brokers"""
        for broker_name, config_func in cls._configurations.items():
            try:
                config_func()
                print(f"✅ {broker_name.title()} configuration loaded")
            except Exception as e:
                print(f"❌ Failed to configure {broker_name}: {e}")

    @classmethod
    def list_registered_brokers(cls) -> list[str]:
        """Get list of registered brokers"""
        return list(cls._configurations.keys())

# Register all broker configurations
BrokerConfigurationRegistry.register_configuration('upstox', configure_upstox_broker)
BrokerConfigurationRegistry.register_configuration('xts', configure_xts_broker)
BrokerConfigurationRegistry.register_configuration('groww', configure_groww_broker)

# =====================================================
# INITIALIZATION FUNCTION (Following SOLID Principles)
# =====================================================

def initialize_scalable_architecture():
    """
    🏗️ Initialize the Complete Scalable Architecture

    Now following SOLID principles:
    - Single Responsibility: Each component has one job
    - Open/Closed: Easy to extend without modifying existing code
    - Liskov Substitution: All transformers are interchangeable
    - Interface Segregation: Clean, focused interfaces
    - Dependency Inversion: Depends on abstractions, not concretions
    """
    print("🏗️ Initializing Scalable Trading Architecture...")

    # Register global schemas
    register_global_schemas()
    print("✅ Global parameter schemas registered")

    # Configure all brokers using registry (SOLID approach!)
    BrokerConfigurationRegistry.configure_all_brokers()

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
