"""
Parameter Models and Mappers for Trading Services

This module provides standardized parameter structures and broker-specific
mappers to handle different parameter formats across various trading services.
"""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, Union


class OrderSide(Enum):
    """Standardized order side values"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Standardized order type values"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_MARKET = "STOP_LOSS_MARKET"


class ProductType(Enum):
    """Standardized product type values"""
    INTRADAY = "INTRADAY"  # MIS/I
    DELIVERY = "DELIVERY"  # CNC/D
    MARGIN = "MARGIN"      # NRML/M


class Validity(Enum):
    """Standardized order validity values"""
    DAY = "DAY"
    IOC = "IOC"  # Immediate or Cancel
    GTD = "GTD"  # Good Till Date


@dataclass
class StandardOrderParams:
    """
    Standardized order parameters that work across all brokers.

    These parameters will be mapped to broker-specific formats
    by the respective parameter mappers.
    """
    # Required parameters
    symbol: str                              # Trading symbol (e.g., "RELIANCE")
    exchange: str                           # Exchange (e.g., "NSE", "BSE")
    quantity: int                           # Order quantity
    order_side: OrderSide                   # BUY or SELL
    order_type: OrderType                   # MARKET, LIMIT, etc.
    product_type: ProductType               # INTRADAY, DELIVERY, MARGIN

    # Optional parameters
    price: Optional[Union[float, Decimal]] = None        # Limit price
    trigger_price: Optional[Union[float, Decimal]] = None # Stop loss trigger price
    disclosed_quantity: int = 0                          # Iceberg quantity
    validity: Validity = Validity.DAY                    # Order validity
    tag: Optional[str] = None                           # Order tag/reference

    # Advanced parameters
    is_amo: bool = False                                # After Market Order
    variety: Optional[str] = None                       # Order variety (regular, bo, co)

    # Broker-specific extras (will be ed through)
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, handling enums appropriately"""
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result


@dataclass
class StandardQuoteParams:
    """Standardized quote parameters"""
    symbols: list[str]                      # List of symbols to get quotes for
    exchange: Optional[str] = None          # Exchange filter
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class StandardHistoricalParams:
    """Standardized historical data parameters"""
    symbol: str                             # Trading symbol
    exchange: str                           # Exchange
    interval: str                           # Time interval (1m, 5m, 1d, etc.)
    from_date: str                          # Start date (YYYY-MM-DD or timestamp)
    to_date: Optional[str] = None           # End date (defaults to today)
    limit: int = 100                        # Maximum records
    extras: dict[str, Any] = field(default_factory=dict)


class IParameterMapper(ABC):
    """
    Interface for broker-specific parameter mappers.

    Each broker service should implement this to transform standardized
    parameters into broker-specific formats.
    """

    @abstractmethod
    def map_order_params(self, params: StandardOrderParams) -> dict[str, Any]:
        """Map standard order parameters to broker-specific format"""


    @abstractmethod
    def map_quote_params(self, params: StandardQuoteParams) -> dict[str, Any]:
        """Map standard quote parameters to broker-specific format"""


    @abstractmethod
    def map_historical_params(self, params: StandardHistoricalParams) -> dict[str, Any]:
        """Map standard historical parameters to broker-specific format"""


    @abstractmethod
    def get_broker_name(self) -> str:
        """Get the broker name this mapper handles"""



class UpstoxParameterMapper(IParameterMapper):
    """Parameter mapper for Upstox broker"""

    # Upstox-specific mappings
    ORDER_SIDE_MAP = {
        OrderSide.BUY: "BUY",
        OrderSide.SELL: "SELL"
    }

    ORDER_TYPE_MAP = {
        OrderType.MARKET: "MARKET",
        OrderType.LIMIT: "LIMIT",
        OrderType.STOP_LOSS: "SL",
        OrderType.STOP_LOSS_MARKET: "SL-M"
    }

    PRODUCT_TYPE_MAP = {
        ProductType.INTRADAY: "I",
        ProductType.DELIVERY: "D",
        ProductType.MARGIN: "M"
    }

    VALIDITY_MAP = {
        Validity.DAY: "DAY",
        Validity.IOC: "IOC",
        Validity.GTD: "GTD"
    }

    def map_order_params(self, params: StandardOrderParams) -> dict[str, Any]:
        """Map to Upstox order format"""
        mapped = {
            "quantity": params.quantity,
            "product": self.PRODUCT_TYPE_MAP[params.product_type],
            "validity": self.VALIDITY_MAP[params.validity],
            "price": float(params.price) if params.price else 0,
            "tag": params.tag or "",
            "instrument_token": f"{params.exchange}_{params.symbol}",  # Upstox format
            "order_type": self.ORDER_TYPE_MAP[params.order_type],
            "transaction_type": self.ORDER_SIDE_MAP[params.order_side],
            "disclosed_quantity": params.disclosed_quantity,
            "trigger_price": float(params.trigger_price) if params.trigger_price else 0,
            "is_amo": params.is_amo
        }

        # Add any extras
        mapped.update(params.extras)
        return mapped

    def map_quote_params(self, params: StandardQuoteParams) -> dict[str, Any]:
        """Map to Upstox quote format"""
        # Upstox uses comma-separated instrument keys
        instrument_keys = []
        exchange = params.exchange or "NSE"
        for symbol in params.symbols:
            instrument_keys.append(f"{exchange}_{symbol}")

        return {
            "instrument_key": ",".join(instrument_keys),
            **params.extras
        }

    def map_historical_params(self, params: StandardHistoricalParams) -> dict[str, Any]:
        """Map to Upstox historical data format"""
        return {
            "instrumentKey": f"{params.exchange}_{params.symbol}",
            "interval": params.interval,
            "from": params.from_date,
            "to": params.to_date,
            "limit": params.limit,
            **params.extras
        }

    def get_broker_name(self) -> str:
        return "upstox"


class XTSParameterMapper(IParameterMapper):
    """Parameter mapper for XTS broker"""

    ORDER_SIDE_MAP = {
        OrderSide.BUY: "BUY",
        OrderSide.SELL: "SELL"
    }

    ORDER_TYPE_MAP = {
        OrderType.MARKET: "MARKET",
        OrderType.LIMIT: "LIMIT",
        OrderType.STOP_LOSS: "STOPLOSS",
        OrderType.STOP_LOSS_MARKET: "STOPMARKET"
    }

    PRODUCT_TYPE_MAP = {
        ProductType.INTRADAY: "MIS",
        ProductType.DELIVERY: "CNC",
        ProductType.MARGIN: "NRML"
    }

    VALIDITY_MAP = {
        Validity.DAY: "DAY",
        Validity.IOC: "IOC",
        Validity.GTD: "GTD"
    }

    EXCHANGE_SEGMENT_MAP = {
        "NSE": "NSECM",
        "BSE": "BSECM",
        "NFO": "NSEFO",
        "BFO": "BSEFO"
    }

    def map_order_params(self, params: StandardOrderParams) -> dict[str, Any]:
        """Map to XTS order format"""
        # XTS needs exchangeSegment and exchangeInstrumentID
        exchange_segment = self.EXCHANGE_SEGMENT_MAP.get(params.exchange, params.exchange)

        # Note: In real implementation, you'd need to resolve symbol to instrument ID
        # For now, we'll put a placeholder or use extras
        instrument_id = params.extras.get("exchangeInstrumentID", 0)

        mapped = {
            "exchangeSegment": exchange_segment,
            "exchangeInstrumentID": instrument_id,
            "productType": self.PRODUCT_TYPE_MAP[params.product_type],
            "orderType": self.ORDER_TYPE_MAP[params.order_type],
            "orderSide": self.ORDER_SIDE_MAP[params.order_side],
            "timeInForce": self.VALIDITY_MAP[params.validity],
            "disclosedQuantity": params.disclosed_quantity,
            "orderQuantity": params.quantity,
            "limitPrice": float(params.price) if params.price else 0,
            "stopPrice": float(params.trigger_price) if params.trigger_price else 0
        }

        # Add any extras
        mapped.update(params.extras)
        return mapped

    def map_quote_params(self, params: StandardQuoteParams) -> dict[str, Any]:
        """Map to XTS quote format"""
        # XTS uses comma-separated instrument IDs
        # In real implementation, you'd resolve symbols to IDs
        instrument_ids = params.extras.get("instruments", "")

        return {
            "instruments": instrument_ids,
            "xtsMessageCode": params.extras.get("xtsMessageCode", 1512),
            **{k: v for k, v in params.extras.items() if k not in ["instruments", "xtsMessageCode"]}
        }

    def map_historical_params(self, params: StandardHistoricalParams) -> dict[str, Any]:
        """Map to XTS historical data format"""
        return {
            "exchangeSegment": self.EXCHANGE_SEGMENT_MAP.get(params.exchange, params.exchange),
            "exchangeInstrumentID": params.extras.get("exchangeInstrumentID", 0),
            "startTime": params.from_date,
            "endTime": params.to_date,
            "compressionType": params.interval,
            **params.extras
        }

    def get_broker_name(self) -> str:
        return "xts"


class GrowwParameterMapper(IParameterMapper):
    """Parameter mapper for Groww broker"""

    def map_order_params(self, params: StandardOrderParams) -> dict[str, Any]:
        """Map to Groww order format (if they have order APIs)"""
        # Groww typically doesn't have public order APIs
        # This is a placeholder implementation
        return {
            "symbol": params.symbol,
            "exchange": params.exchange,
            "qty": params.quantity,
            "side": params.order_side.value.lower(),
            "orderType": params.order_type.value.lower(),
            **params.extras
        }

    def map_quote_params(self, params: StandardQuoteParams) -> dict[str, Any]:
        """Map to Groww quote format"""
        # Groww uses specific format for market data
        return {
            "symbols": params.symbols,
            "exchange": params.exchange or "NSE",
            **params.extras
        }

    def map_historical_params(self, params: StandardHistoricalParams) -> dict[str, Any]:
        """Map to Groww historical data format"""
        return {
            "symbol": params.symbol,
            "exchange": params.exchange,
            "interval": params.interval,
            "from": params.from_date,
            "to": params.to_date,
            **params.extras
        }

    def get_broker_name(self) -> str:
        return "groww"


class ParameterMapperFactory:
    """Factory to get appropriate parameter mapper for a service"""

    _mappers = {
        "upstox": UpstoxParameterMapper(),
        "xts": XTSParameterMapper(),
        "groww": GrowwParameterMapper(),
    }

    @classmethod
    def get_mapper(cls, service_name: str) -> IParameterMapper:
        """Get parameter mapper for a service"""
        if service_name not in cls._mappers:
            raise ValueError(f"No parameter mapper found for service: {service_name}")
        return cls._mappers[service_name]

    @classmethod
    def register_mapper(cls, service_name: str, mapper: IParameterMapper):
        """Register a custom parameter mapper"""
        cls._mappers[service_name] = mapper

    @classmethod
    def list_supported_services(cls) -> list[str]:
        """List all supported services"""
        return list(cls._mappers.keys())
