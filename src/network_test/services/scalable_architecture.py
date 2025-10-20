"""
Scalable Endpoint Architecture for Trading Services

This module provides a comprehensive, scalable architecture for handling
all trading endpoints across multiple brokers with standardized parameters,
automatic mapping, validation, and robust error handling.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# =====================================================
# 1. ENDPOINT CATEGORIES AND OPERATIONS
# =====================================================

class EndpointCategory(Enum):
    """Categories of trading operations"""
    ORDERS = "orders"
    PORTFOLIO = "portfolio"
    MARKET_DATA = "market_data"
    USER_PROFILE = "user_profile"
    INSTRUMENTS = "instruments"
    FUNDS = "funds"
    HISTORICAL = "historical"
    WEBSOCKET = "websocket"


class OperationType(Enum):
    """
    🎯 Trading Operation Types - Like a Universal Menu!

    Imagine you're at different restaurants (brokers) around the world.
    Each restaurant has their own language and way of taking orders.
    But what if there was a universal menu that worked everywhere?

    That's what OperationType does! No matter which broker you use,
    you can always ask for the same things using the same words.

    For example:
    - PLACE_ORDER = "I want to buy/sell something"
    - GET_QUOTES = "What's the current price?"
    - GET_POSITIONS = "What do I currently own?"

    The magic happens behind the scenes - each broker translates
    your request into their own special language!
    """

    # 📦 Order Operations (The main trading actions)
    PLACE_ORDER = "place_order"          # 🛒 Buy or sell stocks
    MODIFY_ORDER = "modify_order"        # ✏️ Change an existing order
    CANCEL_ORDER = "cancel_order"        # ❌ Cancel an order
    GET_ORDERS = "get_orders"            # 📋 See all my orders
    GET_ORDER_HISTORY = "get_order_history"  # 📅 See past orders
    GET_TRADES = "get_trades"            # 📊 See completed trades

    # 💼 Portfolio Operations (What do I own?)
    GET_POSITIONS = "get_positions"      # 📊 Current active positions
    GET_HOLDINGS = "get_holdings"        # 🏦 Long-term investments
    SQUARE_OFF_POSITION = "square_off_position"  # 🔄 Close a position
    CONVERT_POSITION = "convert_position"  # 🔁 Change position type

    # Market Data Operations
    GET_QUOTES = "get_quotes"
    GET_MARKET_STATUS = "get_market_status"
    GET_INDICES = "get_indices"
    SEARCH_INSTRUMENTS = "search_instruments"

    # Historical Data
    GET_CANDLES = "get_candles"
    GET_HISTORICAL_DATA = "get_historical_data"

    # User & Funds
    GET_PROFILE = "get_profile"
    GET_FUNDS = "get_funds"
    GET_MARGINS = "get_margins"

    # WebSocket Operations
    SUBSCRIBE_QUOTES = "subscribe_quotes"
    UNSUBSCRIBE_QUOTES = "unsubscribe_quotes"


# =====================================================
# 2. PARAMETER SCHEMAS REGISTRY
# =====================================================

@dataclass
class ParameterSchema:
    """
    📋 Parameter Schema - Like a Recipe Card!

    Think of this like a recipe card that tells you:
    - What ingredients (parameters) you MUST have 🥕
    - What ingredients are optional (nice to have) 🧂
    - What rules to follow (like "don't use expired milk") 📏

    For example, to PLACE_ORDER you might need:
    - Required: symbol, quantity, order_side (like flour, eggs, milk for cake)
    - Optional: price, validity (like chocolate chips - nice but not required)
    - Rules: quantity > 0, price > 0 (like "bake at 350°F")

    This ensures everyone follows the same recipe and gets good results!

    Attributes:
        operation: What cooking operation (PLACE_ORDER, GET_QUOTES, etc.)
        category: What type of dish (ORDERS, PORTFOLIO, etc.)
        required_fields: Ingredients you MUST have
        optional_fields: Ingredients that are nice to have
        validation_rules: Rules to follow for success
    """
    operation: OperationType
    category: EndpointCategory
    required_fields: List[str]
    optional_fields: List[str] = field(default_factory=list)
    validation_rules: List[Callable[[Dict[str, Any]], List[str]]] = field(default_factory=list)
    description: str = ""

    def validate(self, params: Dict[str, Any]) -> List[str]:
        """Validate parameters against schema"""
        errors = []

        # Check required fields
        for field_name in self.required_fields:
            if field_name not in params:
                errors.append(f"Missing required field: {field_name}")

        # Run custom validation rules
        for rule in self.validation_rules:
            try:
                rule_errors = rule(params)
                if rule_errors:
                    errors.extend(rule_errors)
            except Exception as e:
                errors.append(f"Validation rule error: {e}")

        return errors


class ParameterSchemaRegistry:
    """Registry for all parameter schemas"""

    _schemas: Dict[OperationType, ParameterSchema] = {}

    @classmethod
    def register_schema(cls, schema: ParameterSchema):
        """Register a parameter schema"""
        cls._schemas[schema.operation] = schema

    @classmethod
    def get_schema(cls, operation: OperationType) -> Optional[ParameterSchema]:
        """Get schema for an operation"""
        return cls._schemas.get(operation)

    @classmethod
    def list_operations(cls) -> List[OperationType]:
        """List all registered operations"""
        return list(cls._schemas.keys())

    @classmethod
    def validate_params(cls, operation: OperationType, params: Dict[str, Any]) -> List[str]:
        """Validate parameters for an operation"""
        schema = cls.get_schema(operation)
        if not schema:
            return [f"No schema found for operation: {operation}"]
        return schema.validate(params)


# =====================================================
# 3. BROKER ENDPOINT MAPPING SYSTEM
# =====================================================

@dataclass
class BrokerEndpointMapping:
    """Maps standard operation to broker-specific endpoint details"""
    operation: OperationType
    broker_endpoint_name: str
    http_method: str = "GET"
    parameter_transformer: Optional[Callable] = None
    response_transformer: Optional[Callable] = None
    requires_auth: bool = True
    rate_limit_group: str = "default"
    cache_ttl: int = 0
    extra_config: Dict[str, Any] = field(default_factory=dict)


class BrokerMappingRegistry:
    """Registry for broker-specific endpoint mappings"""

    _mappings: Dict[str, Dict[OperationType, BrokerEndpointMapping]] = {}

    @classmethod
    def register_broker_mapping(cls, broker_name: str, mapping: BrokerEndpointMapping):
        """Register a broker endpoint mapping"""
        if broker_name not in cls._mappings:
            cls._mappings[broker_name] = {}
        cls._mappings[broker_name][mapping.operation] = mapping

    @classmethod
    def get_mapping(cls, broker_name: str, operation: OperationType) -> Optional[BrokerEndpointMapping]:
        """Get broker mapping for an operation"""
        broker_mappings = cls._mappings.get(broker_name, {})
        return broker_mappings.get(operation)

    @classmethod
    def get_supported_operations(cls, broker_name: str) -> List[OperationType]:
        """Get all supported operations for a broker"""
        return list(cls._mappings.get(broker_name, {}).keys())

    @classmethod
    def list_brokers(cls) -> List[str]:
        """List all registered brokers"""
        return list(cls._mappings.keys())


# =====================================================
# 4. PARAMETER TRANSFORMATION PIPELINE
# =====================================================

class IParameterTransformer(ABC):
    """Interface for parameter transformers"""

    @abstractmethod
    def transform(self, operation: OperationType, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform standardized parameters to broker-specific format"""
        pass

    @abstractmethod
    def get_broker_name(self) -> str:
        """Get the broker name this transformer handles"""
        pass


class TransformationPipeline:
    """Pipeline for transforming parameters through multiple stages"""

    def __init__(self):
        self.stages: List[Callable] = []

    def add_stage(self, transformer: Callable):
        """Add a transformation stage"""
        self.stages.append(transformer)

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all transformation stages"""
        result = params.copy()
        for stage in self.stages:
            result = stage(result)
        return result


# =====================================================
# 5. RESPONSE STANDARDIZATION
# =====================================================

@dataclass
class StandardResponse:
    """Standardized response format"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    broker_name: Optional[str] = None
    operation: Optional[OperationType] = None
    execution_time_ms: Optional[float] = None


class ResponseTransformer(ABC):
    """Base class for response transformers"""

    @abstractmethod
    def transform(self, operation: OperationType, raw_response: Any) -> StandardResponse:
        """Transform broker-specific response to standard format"""
        pass


# =====================================================
# 6. ENDPOINT EXECUTOR
# =====================================================

class EndpointExecutor:
    """Executes standardized operations across different brokers"""

    def __init__(self, broker_name: str):
        self.broker_name = broker_name
        self.parameter_transformer: Optional[IParameterTransformer] = None
        self.response_transformer: Optional[ResponseTransformer] = None

    def set_parameter_transformer(self, transformer: IParameterTransformer):
        """Set parameter transformer for this broker"""
        self.parameter_transformer = transformer

    def set_response_transformer(self, transformer: ResponseTransformer):
        """Set response transformer for this broker"""
        self.response_transformer = transformer

    async def execute_operation(self,
                              operation: OperationType,
                              params: Dict[str, Any],
                              service_instance: Any) -> StandardResponse:
        """Execute a standardized operation"""
        import time
        start_time = time.time()

        try:
            # 1. Validate parameters
            validation_errors = ParameterSchemaRegistry.validate_params(operation, params)
            if validation_errors:
                return StandardResponse(
                    success=False,
                    error=f"Parameter validation failed: {'; '.join(validation_errors)}",
                    broker_name=self.broker_name,
                    operation=operation
                )

            # 2. Get broker mapping
            mapping = BrokerMappingRegistry.get_mapping(self.broker_name, operation)
            if not mapping:
                return StandardResponse(
                    success=False,
                    error=f"Operation {operation} not supported by broker {self.broker_name}",
                    broker_name=self.broker_name,
                    operation=operation
                )

            # 3. Transform parameters
            transformed_params = params.copy()
            if self.parameter_transformer:
                transformed_params = self.parameter_transformer.transform(operation, params)
            elif mapping.parameter_transformer:
                transformed_params = mapping.parameter_transformer(params)

            # 4. Execute broker-specific call
            raw_response = await service_instance.call_endpoint(
                mapping.broker_endpoint_name,
                **(transformed_params if mapping.http_method in ["GET"] else {"json_data": transformed_params})
            )

            # 5. Transform response
            if self.response_transformer:
                result = self.response_transformer.transform(operation, raw_response)
            else:
                result = StandardResponse(
                    success=True,
                    data=raw_response,
                    raw_response=raw_response,
                    broker_name=self.broker_name,
                    operation=operation
                )

            result.execution_time_ms = (time.time() - start_time) * 1000
            return result

        except Exception as e:
            return StandardResponse(
                success=False,
                error=str(e),
                broker_name=self.broker_name,
                operation=operation,
                execution_time_ms=(time.time() - start_time) * 1000
            )


# =====================================================
# 7. OPERATION DECORATORS
# =====================================================

def standard_operation(operation: OperationType):
    """Decorator to mark methods as standard operations"""
    def decorator(func):
        func._standard_operation = operation

        @wraps(func)
        async def wrapper(self, **kwargs):
            if hasattr(self, '_endpoint_executor'):
                return await self._endpoint_executor.execute_operation(operation, kwargs, self)
            else:
                # Fallback to original method
                return await func(self, **kwargs)

        return wrapper
    return decorator


# =====================================================
# 8. CONFIGURATION BUILDER
# =====================================================

class BrokerConfigurationBuilder:
    """Builder for setting up broker configurations"""

    def __init__(self, broker_name: str):
        self.broker_name = broker_name
        self.mappings: List[BrokerEndpointMapping] = []
        self.schemas: List[ParameterSchema] = []

    def add_operation(self,
                     operation: OperationType,
                     broker_endpoint: str,
                     http_method: str = "GET",
                     required_fields: Optional[List[str]] = None,
                     optional_fields: Optional[List[str]] = None,
                     parameter_transformer: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
                     **kwargs: Any) -> 'BrokerConfigurationBuilder':
        """Add an operation configuration"""

        # Create mapping
        mapping = BrokerEndpointMapping(
            operation=operation,
            broker_endpoint_name=broker_endpoint,
            http_method=http_method,
            parameter_transformer=parameter_transformer,
            **kwargs
        )
        self.mappings.append(mapping)

        # Create schema if not exists
        existing_schema = ParameterSchemaRegistry.get_schema(operation)
        if not existing_schema and required_fields:
            schema = ParameterSchema(
                operation=operation,
                category=self._get_category_for_operation(operation),
                required_fields=required_fields or [],
                optional_fields=optional_fields or []
            )
            self.schemas.append(schema)

        return self

    def _get_category_for_operation(self, operation: OperationType) -> EndpointCategory:
        """Determine category for an operation"""
        if operation.value.startswith(('place_', 'modify_', 'cancel_', 'get_order')):
            return EndpointCategory.ORDERS
        elif operation.value.startswith(('get_position', 'get_holding')):
            return EndpointCategory.PORTFOLIO
        elif operation.value.startswith(('get_quote', 'get_market', 'search_')):
            return EndpointCategory.MARKET_DATA
        elif operation.value.startswith(('get_candle', 'get_historical')):
            return EndpointCategory.HISTORICAL
        elif operation.value.startswith(('get_profile', 'get_fund')):
            return EndpointCategory.USER_PROFILE
        else:
            return EndpointCategory.MARKET_DATA

    def build(self):
        """Build and register the configuration"""
        # Register all mappings
        for mapping in self.mappings:
            BrokerMappingRegistry.register_broker_mapping(self.broker_name, mapping)

        # Register all schemas
        for schema in self.schemas:
            ParameterSchemaRegistry.register_schema(schema)

        logger.info(f"Registered {len(self.mappings)} operations for broker {self.broker_name}")


# =====================================================
# 9. UNIFIED SERVICE MIXIN
# =====================================================

class StandardizedOperationsMixin:
    """Mixin to add standardized operations to any service"""

    def __init_standardized_operations__(self, broker_name: str):
        """Initialize standardized operations support"""
        self._endpoint_executor = EndpointExecutor(broker_name)

        # Set up transformers if available
        from .parameters import ParameterMapperFactory
        try:
            mapper = ParameterMapperFactory.get_mapper(broker_name)
            if hasattr(mapper, 'transform'):
                self._endpoint_executor.set_parameter_transformer(mapper)
        except AttributeError:
            pass  # No transformer available

    @standard_operation(OperationType.PLACE_ORDER)
    async def place_order_standard(self, **kwargs) -> StandardResponse:
        """Standardized place order operation"""
        pass  # Implementation handled by decorator

    @standard_operation(OperationType.GET_QUOTES)
    async def get_quotes_standard(self, **kwargs) -> StandardResponse:
        """Standardized get quotes operation"""
        pass

    @standard_operation(OperationType.GET_ORDERS)
    async def get_orders_standard(self, **kwargs) -> StandardResponse:
        """Standardized get orders operation"""
        pass

    @standard_operation(OperationType.CANCEL_ORDER)
    async def cancel_order_standard(self, **kwargs) -> StandardResponse:
        """Standardized cancel order operation"""
        pass

    @standard_operation(OperationType.GET_POSITIONS)
    async def get_positions_standard(self, **kwargs) -> StandardResponse:
        """Standardized get positions operation"""
        pass

    @standard_operation(OperationType.GET_HOLDINGS)
    async def get_holdings_standard(self, **kwargs) -> StandardResponse:
        """Standardized get holdings operation"""
        pass

    # Add more standardized operations as needed...
