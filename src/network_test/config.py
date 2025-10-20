"""
Configuration file for trading services.

This file contains all API configurations, endpoints, and settings
that can be easily modified without changing the code.
"""


# ============================================================================
# UPSTOX API CONFIGURATION
# ============================================================================

UPSTOX_API_CONFIG = {
    "base_url": "https://api.upstox.com/",
    "rate_limit": 25,  # Requests per second
    "timeout": 10,
    "max_connections": 20,
    "max_retries": 3,
    "cache_ttl": 30,
    "enable_circuit_breaker": True,

    # Authentication (set these when you have credentials)
    "api_key": None,  # "your_api_key_here"
    "access_token": None,  # "your_access_token_here"

    # Default headers for all requests
    "default_headers": {
        "User-Agent": "NetworkTest/1.0",
        "Accept": "application/json",
    },

    # Custom endpoints (you can add more here)
    "endpoints": {
        "custom_portfolio": {
            "path": "portfolio/long-term-holdings",
            "method": "GET",
            "cache_ttl": 60,
            "description": "Custom portfolio endpoint with longer cache"
        },
        "intraday_candles": {
            "path": "chart/open/v3/candles/",
            "method": "GET",
            "cache_ttl": 1,  # Very fresh data for intraday trading
            "description": "Real-time candles for intraday trading"
        },
        "bulk_quotes": {
            "path": "market-quote/quotes",
            "method": "GET",
            "cache_ttl": 2,
            "description": "Bulk quotes for multiple instruments"
        }
    }
}


UPSTOX_SERVICE_CONFIG = {
    "base_url": "https://service.upstox.com/",
    "rate_limit": 25,  # Requests per second
    "timeout": 10,
    "max_connections": 20,
    "max_retries": 3,
    "cache_ttl": 30,
    "enable_circuit_breaker": True,

    # Authentication (set these when you have credentials)
    "api_key": None,  # "your_api_key_here"
    "access_token": None,  # "your_access_token_here"

    # Default headers for all requests
    "default_headers": {
        "User-Agent": "NetworkTest/1.0",
        "Accept": "application/json",
    },

    # Custom endpoints (you can add more here)
    "endpoints": {
        "market_timing": {
            "path": "v2/market/timings/",
            "method": "POST",
            "cache_ttl": 86400,  # Cache for 1 day
            "description": "Market timings information"
        },
        "holiday_timing": {
            "path": "v2/market/holidays/",
            "method": "GET",
            "cache_ttl": 86400,  # Cache for 1 day
            "description": "Market holidays information"
        }
    }
}

# ============================================================================
# GROWW API CONFIGURATION
# ============================================================================

GROWW_CONFIG = {
    "base_url": "https://groww.in/",
    "rate_limit": 50,
    "timeout": 5,
    "max_connections": 10,
    "max_retries": 2,
    "cache_ttl": 300,
    "enable_circuit_breaker": True,

    # Default headers
    "default_headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
    },

    "endpoints": {
        "all_indices": {
            "path": "v1/api/stocks_data/v1/accord_points/exchange/NSE/segment/CASH/latest_indices_ohlc/{index}",
            "method": "GET",
            "cache_ttl": 30,
            "description": "Get data for any NSE index"
        },
        "sector_data": {
            "path": "v1/api/stocks_data/v1/sector/latest",
            "method": "GET",
            "cache_ttl": 120,
            "description": "Get sectoral performance data"
        }
    }
}

# ============================================================================
# ZERODHA KITE CONFIGURATION (Example for future expansion)
# ============================================================================

ZERODHA_CONFIG = {
    "base_url": "https://api.kite.trade/",
    "rate_limit": 3,  # Zerodha is very strict
    "timeout": 15,
    "max_connections": 5,
    "cache_ttl": 30,

    "endpoints": {
        "quotes": {
            "path": "quote",
            "method": "GET",
            "cache_ttl": 1,
            "description": "Get live quotes"
        },
        "orders": {
            "path": "orders",
            "method": "GET",
            "cache_ttl": 5,
            "description": "Get all orders"
        },
        "place_order": {
            "path": "orders/regular",
            "method": "POST",
            "use_cache": False,
            "description": "Place regular order"
        }
    }
}

# ============================================================================
# COMMON TRADING PARAMETERS
# ============================================================================

# Standard intervals for candlestick data
INTERVALS = {
    "1MIN": "I1",
    "5MIN": "I5",
    "15MIN": "I15",
    "30MIN": "I30",
    "1HOUR": "I60",
    "1DAY": "1D",
    "1WEEK": "1W",
    "1MONTH": "1M"
}

# Popular NSE instruments (for quick testing)
POPULAR_INSTRUMENTS = {
    "RELIANCE": "NSE_EQ|INE002A01018",
    "TCS": "NSE_EQ|INE467B01029",
    "INFY": "NSE_EQ|INE009A01021",
    "HDFCBANK": "NSE_EQ|INE040A01034",
    "ICICIBANK": "NSE_EQ|INE090A01021",
    "HDFC": "NSE_EQ|INE001A01036",
    "KOTAKBANK": "NSE_EQ|INE237A01028",
    "BHARTIARTL": "NSE_EQ|INE397D01024",
    "ITC": "NSE_EQ|INE154A01025",
    "LT": "NSE_EQ|INE018A01030"
}

# Market segments
SEGMENTS = [
    "NSE_EQ",    # NSE Equity
    "NSE_FO",    # NSE Futures & Options
    "BSE_EQ",    # BSE Equity
    "NSE_CD",    # NSE Currency Derivatives
    "MCX_FO"     # MCX Commodity Derivatives
]
