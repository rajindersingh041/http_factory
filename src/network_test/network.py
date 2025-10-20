# pylint: disable=W0105,C0302

"""
Comprehensive Async HTTP Client for Trading Applications

This module provides a professional-grade asynchronous HTTP client specifically designed
for trading applications that need to communicate with broker APIs. It implements several
critical patterns and features that are essential for reliable, high-performance trading systems.

=== WHY ASYNC? ===
Traditional synchronous HTTP requests block the entire program while waiting for responses.
In trading, you might need to:
- Fetch live prices for 100+ stocks simultaneously
- Place multiple orders concurrently
- Monitor positions while streaming market data

Async programming allows your program to handle thousands of concurrent operations without
blocking. While one request waits for a response, your program can start other requests
or perform other tasks.

Example of the difference:
- Synchronous: Request A (2s) -> Request B (2s) -> Request C (2s) = 6 seconds total
- Asynchronous: Request A, B, C all start together -> All complete in ~2 seconds

=== KEY FEATURES EXPLAINED ===

1. RATE LIMITING: Prevents your program from making too many requests too quickly
   - Why needed: Broker APIs limit requests (e.g., 10 per second)
   - What happens without it: API blocks your requests, trading bot stops working
   - How it works: Uses "token bucket" algorithm to space out requests

2. CIRCUIT BREAKER: Stops making requests when the API is failing repeatedly
   - Why needed: If broker API is down, don't waste time/resources on failed requests
   - What happens without it: Your bot keeps trying failed requests, wastes resources
   - How it works: After N failures, "opens" circuit and blocks requests temporarily

3. RETRY LOGIC: Automatically retries failed requests with smart backoff
   - Why needed: Network issues, temporary API glitches are common
   - What happens without it: Single network hiccup kills your trade
   - How it works: Waits progressively longer between retries (1s, 2s, 4s, 8s...)

4. CACHING: Stores recent responses to avoid repeated identical requests
   - Why needed: Market data doesn't change every millisecond
   - What happens without it: Waste bandwidth fetching same price repeatedly
   - How it works: Stores responses with expiration time (TTL = Time To Live)

5. CONNECTION POOLING: Reuses HTTP connections instead of creating new ones
   - Why needed: Creating new connections is slow (TCP handshake, SSL, etc.)
   - What happens without it: Each request takes extra time to establish connection
   - How it works: Maintains pool of open connections ready for use

=== DEPENDENCIES EXPLAINED ===

aiohttp: The asyncio-compatible HTTP client library
- asyncio: Python's built-in library for asynchronous programming
- Why aiohttp vs requests: requests is synchronous only, aiohttp supports async/await
- What it provides: Non-blocking HTTP requests, connection pooling, streaming

Core concepts:
- async/await: Keywords that make functions "pausable" during I/O operations
- Event loop: The engine that manages and executes async operations
- Coroutines: Special functions that can be paused and resumed
"""

import asyncio  # Python's built-in async programming library
import json  # For JSON parsing
import logging  # For recording what the program is doing (debugging, monitoring)
import time  # For timestamps and timing operations
from collections import \
    deque  # Fast queue data structure for recent request tracking
from typing import Dict  # Type hints for better code documentation
from typing import Any, List, Optional

try:
    # aiohttp: The async HTTP client library (like requests, but async)
    import aiohttp
    from aiohttp import ClientSession, ClientTimeout, TCPConnector
except ImportError as exc:
    # If aiohttp isn't installed, provide clear installation instructions
    raise ImportError(
        "aiohttp is required for async networking. Install with: pip install aiohttp\n"
        "aiohttp is the most popular async HTTP client for Python, enabling non-blocking "
        "HTTP requests essential for high-performance trading applications."
    ) from exc

# Logger for recording what's happening in our network operations
# Essential for debugging trading issues ("Why did my order fail?")
logger = logging.getLogger(__name__)


class SimpleResponse:
    """Simple response object to hold response data after the aiohttp context closes"""

    def __init__(self, text: str, status: int, url, headers):
        self.text = text
        self.status = status
        self.url = url
        self.headers = headers


class RateLimiter:
    """
    Async Token Bucket Rate Limiter

    === WHAT IS RATE LIMITING? ===
    Rate limiting controls how many requests you can make per second to prevent overwhelming
    an API server. Think of it like a speed limit for your network requests.

    === WHY DO WE NEED IT? ===
    1. Broker APIs have limits (e.g., Zerodha allows 3 requests/second)
    2. Exceeding limits gets your API key banned or throttled
    3. Protects the broker's servers from being overloaded
    4. Ensures fair usage among all users

    === HOW TOKEN BUCKET WORKS ===
    Imagine a bucket that:
    1. Gets filled with tokens at a steady rate (e.g., 10 tokens per second)
    2. Each API request consumes 1 token
    3. If bucket is empty, you must wait for new tokens
    4. If bucket is full, extra tokens overflow (you can't save unlimited requests)

    Our simplified version:
    - Instead of actual tokens, we just track time between requests
    - If not enough time has passed, we wait (async sleep)
    - Uses minimum interval = 1 / requests_per_second

    === EXAMPLE ===
    If limit is 10 requests/second:
    - Minimum interval = 1/10 = 0.1 seconds = 100ms
    - Request at time 0.0s -> next allowed at 0.1s
    - If you try to request at 0.05s -> wait 0.05s more

    === THREAD SAFETY ===
    Uses asyncio.Lock() to prevent race conditions when multiple async functions
    try to make requests simultaneously.
    """

    def __init__(self, requests_per_second: float = 10):
        """
        Initialize the rate limiter.

        Args:
            requests_per_second: Maximum requests allowed per second
                                Common values:
                                - Zerodha: 3 RPS (very strict)
                                - Upstox: 25 RPS
                                - Angel One: 20 RPS
                                - Paper trading: 100+ RPS (no real limits)
        """
        self.requests_per_second = requests_per_second

        # Calculate minimum time that must pass between requests
        # If 10 RPS allowed -> min 0.1 seconds between requests
        # If 0 RPS (disabled) -> no minimum interval
        self.min_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0

        # Track when the last request was made (Unix timestamp)
        self.last_request_time = 0

        # Async lock to prevent multiple coroutines from interfering with each other
        # Without this, two concurrent requests might both think they can go at the same time
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Acquire permission to make a request. Will wait if necessary to respect rate limit.

        This is the core method that enforces the rate limit. Every request should
        call this before making an HTTP request.

        === HOW IT WORKS ===
        1. Check if rate limiting is disabled (min_interval = 0)
        2. Calculate time since last request
        3. If not enough time has passed, sleep until we can proceed
        4. Update last request time

        === ASYNC LOCK EXPLANATION ===
        The lock ensures only one coroutine can check/update timing at once:

        Without lock (PROBLEMATIC):
        - Coroutine A checks: last request was 0.05s ago, needs to wait 0.05s
        - Coroutine B checks: last request was 0.05s ago, needs to wait 0.05s
        - Both sleep 0.05s and proceed simultaneously -> rate limit violated!

        With lock (CORRECT):
        - Coroutine A acquires lock, checks timing, waits if needed, updates timestamp
        - Coroutine B waits for lock, then gets updated timestamp, calculates new wait time
        - Requests are properly spaced apart
        """
        # If rate limiting is disabled, don't wait at all
        if self.min_interval == 0:
            return

        # Only one coroutine can execute this block at a time
        async with self._lock:
            current_time = time.time()  # Get current Unix timestamp
            time_since_last = current_time - self.last_request_time

            # If not enough time has passed since last request, we need to wait
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last

                # async sleep: Pause this coroutine, let other coroutines run
                # This is non-blocking - other parts of your program keep working
                await asyncio.sleep(sleep_time)

            # Update timestamp to now (when we're actually allowing the request)
            self.last_request_time = time.time()


class CircuitBreakerOpenError(Exception):
    """
    Custom exception raised when the circuit breaker is OPEN and blocking requests.

    This helps distinguish between API failures and circuit breaker protection,
    so your trading bot can handle each situation appropriately.
    """


class CircuitBreaker:
    """
    Circuit Breaker Pattern for Fault Tolerance

    === WHAT IS A CIRCUIT BREAKER? ===
    Inspired by electrical circuit breakers that cut power when there's a problem,
    this pattern "opens" to stop requests when an API is failing repeatedly.

    Think of it like a smart switch that:
    1. Normally lets electricity (requests) flow through (CLOSED state)
    2. If too many failures occur, cuts the power (OPEN state)
    3. After some time, tries again carefully (HALF_OPEN state)
    4. If it works, goes back to normal (CLOSED state)

    === WHY DO WE NEED IT? ===
    Without circuit breaker:
    - Broker API goes down
    - Your bot keeps sending requests every 100ms
    - All requests fail and consume resources
    - Your bot wastes time/bandwidth/CPU on hopeless requests
    - Might make the problem worse by overwhelming the failing API

    With circuit breaker:
    - After 5 failures, circuit "opens"
    - No more requests sent for 60 seconds
    - API has time to recover
    - After timeout, try one request (HALF_OPEN)
    - If it works, resume normal operation

    === THREE STATES EXPLAINED ===

    1. CLOSED (Normal operation):
       - Requests flow through normally
       - Failures are counted but don't block requests
       - Most of the time, circuit should be in this state

    2. OPEN (Protection mode):
       - All requests are immediately blocked
       - Prevents wasting resources on a failing API
       - Gives remote system time to recover
       - Stays open for recovery_timeout seconds

    3. HALF_OPEN (Testing recovery):
       - Allows one request to test if API is back up
       - If successful -> back to CLOSED
       - If fails -> back to OPEN
       - Like carefully testing if power is back on

    === REAL TRADING EXAMPLE ===
    Your bot is fetching live prices every second:
    - 9:15 AM: Market opens, everything works (CLOSED)
    - 9:30 AM: Broker API starts having issues
    - 9:30:01-9:30:05: 5 requests fail
    - 9:30:05: Circuit opens, stops sending requests (OPEN)
    - 9:31:05: After 60s timeout, try one request (HALF_OPEN)
    - 9:31:05: Request succeeds, API is back up (CLOSED)

    This prevented 55 wasted requests during the 60-second outage!
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Initialize the circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures before opening circuit
                              Common values:
                              - 3-5 for critical APIs (fail fast)
                              - 10+ for non-critical APIs (more tolerant)

            recovery_timeout: Seconds to wait before trying again after opening
                             Common values:
                             - 30-60s for temporary glitches
                             - 300s (5min) for major outages
                             - 3600s (1hr) for maintenance windows
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        # Track consecutive failures (resets on success)
        self.failure_count = 0

        # When the last failure occurred (for timeout calculation)
        self.last_failure_time = 0

        # Current state: CLOSED (normal), OPEN (blocking), HALF_OPEN (testing)
        self.state = "CLOSED"

        # Async lock to prevent race conditions between concurrent requests
        self._lock = asyncio.Lock()

    async def call(self, func, *args, **kwargs):
        """
        Execute a function through the circuit breaker protection.

        This wraps any function call (like HTTP requests) with circuit breaker logic.
        The function will only be called if the circuit is closed or half-open.

        Args:
            func: The async function to execute (e.g., HTTP request function)
            *args, **kwargs: Arguments to pass to the function

        Returns:
            Result of the function call

        Raises:
            CircuitBreakerOpenError: If circuit is open (protecting from failures)
            Any exception from the wrapped function

        === STATE TRANSITION LOGIC ===

        CLOSED -> OPEN:
        - When failure_count >= failure_threshold
        - Immediately blocks all future requests

        OPEN -> HALF_OPEN:
        - After recovery_timeout seconds have passed
        - Allows exactly one test request

        HALF_OPEN -> CLOSED:
        - When the test request succeeds
        - Resets failure count to 0

        HALF_OPEN -> OPEN:
        - When the test request fails
        - Updates last_failure_time and increments failure_count
        """
        # Use lock to prevent multiple coroutines from changing state simultaneously
        async with self._lock:
            # Check if we should transition from OPEN to HALF_OPEN
            if self.state == "OPEN":
                current_time = time.time()
                time_since_failure = current_time - self.last_failure_time

                if time_since_failure >= self.recovery_timeout:
                    # Enough time has passed, try one test request
                    self.state = "HALF_OPEN"
                else:
                    # Still in timeout period, block the request
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN. Tried {self.failure_count} times. "
                        f"Will retry in {self.recovery_timeout - time_since_failure:.1f}s"
                    )

            try:
                # Execute the wrapped function (e.g., HTTP request)
                result = await func(*args, **kwargs)

                # Success! If we were testing (HALF_OPEN), go back to normal
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0  # Reset failure counter

                return result

            except Exception as e:
                # Function failed, record the failure
                self.failure_count += 1
                self.last_failure_time = time.time()

                # If we've hit the failure threshold, open the circuit
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(
                        f"Circuit breaker OPENED after {self.failure_count} failures. "
                        f"Will retry in {self.recovery_timeout}s"
                    )

                # Re-raise the original exception so caller knows what went wrong
                raise e


class AsyncCache:
    """
    Async-Safe In-Memory Cache with TTL (Time To Live) Support

    === WHAT IS CACHING? ===
    Caching stores frequently requested data in memory so you don't have to
    fetch it again from the original source (like an API). It's like keeping
    a photocopy of important documents on your desk instead of walking to
    the filing cabinet every time.

    === WHY DO WE NEED CACHING IN TRADING? ===

    1. PERFORMANCE: Network requests are slow (50-200ms), memory access is fast (<1ms)
    2. COST REDUCTION: Many APIs charge per request
    3. RATE LIMIT CONSERVATION: Don't waste rate limit on duplicate requests
    4. RELIABILITY: If API is temporarily down, serve from cache

    === REAL TRADING EXAMPLES ===

    Good candidates for caching:
    - Stock prices (cache for 1-5 seconds)
    - Account balance (cache for 30 seconds)
    - Available instruments list (cache for 1 hour)
    - Company fundamentals (cache for 1 day)

    Bad candidates for caching:
    - Order placement (never cache, always fresh)
    - Real-time order status (changes too quickly)
    - Authentication tokens (security risk)

    === TTL (TIME TO LIVE) EXPLAINED ===
    TTL determines how long cached data stays valid:
    - TTL = 60 means data expires after 60 seconds
    - After expiry, next request fetches fresh data
    - Like milk with expiration date - don't use after it expires!

    === ASYNC SAFETY ===
    Multiple async functions might try to read/write cache simultaneously.
    We use asyncio.Lock() to prevent corruption:

    Without lock (DANGEROUS):
    - Coroutine A starts writing cache entry
    - Coroutine B starts reading same entry while A is writing
    - B gets corrupted/incomplete data

    With lock (SAFE):
    - Coroutine A locks cache, writes entry, unlocks
    - Coroutine B waits for lock, then reads complete entry

    === DATA STRUCTURE ===
    Cache stores: Dict[key, (value, expiry_timestamp)]
    - key: String identifier (e.g., "AAPL_price", "account_balance")
    - value: The actual cached data (price, balance, etc.)
    - expiry_timestamp: Unix timestamp when this data expires
    """

    def __init__(self, default_ttl: int = 300):
        """
        Initialize the async cache.

        Args:
            default_ttl: Default time-to-live in seconds for cached items
                        Common values:
                        - 1-5s: Live market data
                        - 30-60s: Account info
                        - 300s (5min): Static reference data
                        - 3600s (1hr): Rarely changing data
        """
        self.default_ttl = default_ttl

        # Internal cache storage: key -> (value, expiry_timestamp)
        # Example: {"AAPL_price": (150.25, 1697890865.123)}
        self._cache: Dict[str, tuple] = {}

        # Async lock to prevent concurrent access issues
        self._lock = asyncio.Lock()

    def size(self) -> int:
        """
        Return the number of items currently in the cache.

        Useful for monitoring cache usage and debugging.
        Note: This count includes expired items that haven't been cleaned up yet.
        """
        return len(self._cache)

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache if it exists and hasn't expired.

        Args:
            key: The cache key to look up (e.g., "AAPL_price")

        Returns:
            The cached value if found and not expired, None otherwise

        === HOW IT WORKS ===
        1. Check if key exists in cache
        2. If exists, check if it's expired (current_time > expiry_time)
        3. If not expired, return the value
        4. If expired, delete it and return None
        5. If key doesn't exist, return None

        === EXPIRY CHECK LOGIC ===
        We store expiry as Unix timestamp (seconds since 1970):
        - time.time() returns current timestamp: 1697890865.123
        - If expiry is 1697890800.000 and current is 1697890865.123
        - Then current > expiry, so data is expired (65 seconds old)
        """
        async with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]

                # Check if data is still fresh
                if time.time() < expiry:
                    return value  # Cache hit! Return fresh data
                else:
                    # Data expired, remove it and act like it never existed
                    del self._cache[key]
                    # This cleanup prevents the cache from growing indefinitely

            return None  # Cache miss - key doesn't exist or was expired

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store a value in the cache with expiration time.

        Args:
            key: Cache key identifier (should be descriptive and unique)
            value: The data to cache (can be any Python object)
            ttl: Time-to-live in seconds (uses default_ttl if not specified)

        === KEY NAMING BEST PRACTICES ===
        Use descriptive, hierarchical keys:
        - Good: "zerodha_quote_AAPL", "account_balance_live", "instruments_NSE"
        - Bad: "data", "temp", "x"

        === TTL CALCULATION ===
        If TTL is 60 seconds:
        - Current time: 1697890800
        - Expiry time: 1697890800 + 60 = 1697890860
        - Data valid until timestamp 1697890860
        """
        ttl = ttl or self.default_ttl  # Use provided TTL or default
        expiry = time.time() + ttl  # Calculate when this data expires

        async with self._lock:
            # Store as tuple: (actual_data, expiry_timestamp)
            self._cache[key] = (value, expiry)

    async def clear(self) -> None:
        """
        Remove all items from the cache.

        Useful for:
        - Testing (clean slate between tests)
        - Memory management (free up RAM)
        - Security (clear sensitive data)
        - Configuration changes (invalidate all cached data)
        """
        async with self._lock:
            self._cache.clear()

    async def cleanup_expired(self) -> None:
        """
        Remove all expired entries from the cache.

        === WHY CLEANUP IS NEEDED ===
        When items expire, we don't immediately delete them (for performance).
        Over time, expired items accumulate and waste memory:
        - Cache size: 1000 items
        - 800 are expired but still taking up memory
        - Only 200 are actually useful

        === WHEN TO CALL CLEANUP ===
        - Periodically (every few minutes) in a background task
        - When cache grows too large
        - During low-activity periods (after market hours)
        - Never during high-frequency trading (too slow)

        === HOW IT WORKS ===
        1. Get current timestamp
        2. Scan all cache entries
        3. Identify entries where current_time >= expiry_time
        4. Delete all expired entries in one operation
        """
        current_time = time.time()

        async with self._lock:
            # Find all expired keys (list comprehension for efficiency)
            expired_keys = [
                key
                for key, (value, expiry) in self._cache.items()
                if current_time >= expiry
            ]

            # Delete all expired entries
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


class AsyncNetworkClient:
    """
    Professional-Grade Async HTTP Client for Trading Applications

    This is the core networking component that your trading bot uses to communicate
    with broker APIs. It implements multiple enterprise-grade patterns to ensure
    reliable, fast, and efficient communication.

    === ENTERPRISE FEATURES EXPLAINED ===

    1. CONNECTION POOLING:
       - Reuses HTTP connections instead of creating new ones for each request
       - Why: Creating connections is expensive (TCP handshake, SSL negotiation)
       - Example: Without pooling, 100 requests = 100 new connections (slow)
                  With pooling, 100 requests = reuse 5-10 connections (fast)

    2. RATE LIMITING:
       - Controls request frequency to respect API limits
       - Prevents your API key from being banned

    3. CIRCUIT BREAKER:
       - Stops requests when API is failing repeatedly
       - Prevents resource waste during outages

    4. RETRY WITH EXPONENTIAL BACKOFF:
       - Automatically retries failed requests
       - Waits progressively longer: 1s, 2s, 4s, 8s...
       - Why exponential: If server is overloaded, give it more time to recover

    5. RESPONSE CACHING:
       - Stores recent responses to avoid repeated identical requests
       - Reduces latency and conserves rate limits

    6. TIMEOUT MANAGEMENT:
       - Prevents requests from hanging forever
       - Different timeouts for connection vs total request

    7. REQUEST/RESPONSE LOGGING:
       - Records all network activity for debugging
       - Essential for troubleshooting trading issues

    === REAL-WORLD TRADING USAGE ===

    ```python
    # Create client for Zerodha API
    client = AsyncNetworkClient(
        base_url="https://api.kite.trade",
        rate_limit=3.0,  # Zerodha allows 3 requests/second
        timeout=10,      # 10 second timeout for trading operations
        max_retries=2    # Retry twice for critical operations
    )

    # Get live price (will be cached for 1 second)
    price = await client.get("/quote/NSE:RELIANCE", use_cache=True, cache_ttl=1)

    # Place order (never cached, always fresh)
    order = await client.post("/orders", json_data={"symbol": "RELIANCE", "qty": 100})
    ```

    === CONFIGURATION GUIDELINES ===

    Rate Limits by Broker:
    - Zerodha: 3 RPS (very strict)
    - Upstox: 25 RPS
    - Angel One: 20 RPS
    - Interactive Brokers: 50 RPS

    Timeout Recommendations:
    - Market data: 5-10 seconds
    - Order operations: 15-30 seconds
    - Account queries: 10-15 seconds

    Connection Pool Sizing:
    - Small bot (1-10 stocks): 10-20 connections
    - Medium bot (10-100 stocks): 50-100 connections
    - Large bot (100+ stocks): 100-200 connections
    """

    def __init__(
        self,
        base_url: str = "",
        rate_limit: float = 10.0,
        timeout: int = 30,
        max_connections: int = 100,
        max_retries: int = 3,
        cache_ttl: int = 60,
        enable_circuit_breaker: bool = True,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the async network client with trading-optimized defaults.

        Args:
            base_url: Base URL for all requests (e.g., "https://api.kite.trade")
                     Can be empty if you'll use full URLs in requests

            rate_limit: Maximum requests per second (float for sub-second precision)
                       Examples: 3.0 (Zerodha), 25.0 (Upstox), 0.5 (one request every 2s)

            timeout: Total timeout for requests in seconds
                    Includes connection time + data transfer time
                    Trade-off: Too low = failed requests, too high = slow failure detection

            max_connections: Maximum concurrent HTTP connections in the pool
                           More connections = more parallel requests
                           Too many = resource waste, too few = bottleneck

            max_retries: Number of times to retry failed requests (0 = no retries)
                        Common values: 2-3 for critical operations, 0-1 for real-time data

            cache_ttl: Default cache time-to-live in seconds
                      How long to store responses before fetching fresh data

            enable_circuit_breaker: Whether to use circuit breaker protection
                                  True = recommended for production
                                  False = only for testing/debugging

            default_headers: Default headers to include in all requests
                           Examples: {"User-Agent": "MyBot/1.0", "Authorization": "Bearer token"}
                           Request-specific headers will override these defaults
        """
        # Store base URL and ensure it ends with slash for consistent URL building
        self.base_url = base_url.rstrip("/") + "/" if base_url else ""

        # Store default headers for all requests
        self.default_headers = default_headers or {}

        # Initialize all the protective/performance components
        self.rate_limiter = RateLimiter(
            rate_limit
        )  # Prevents API rate limit violations
        self.cache = AsyncCache(
            cache_ttl
        )  # Stores responses to avoid redundant requests
        self.max_retries = max_retries  # How many times to retry failed requests

        # Circuit breaker for fault tolerance (optional but recommended)
        self.circuit_breaker = CircuitBreaker() if enable_circuit_breaker else None

        # === AIOHTTP SESSION CONFIGURATION ===
        # ClientTimeout: Controls how long to wait for responses
        timeout_config = ClientTimeout(
            total=timeout,  # Total time for entire request (connection + data transfer)
            connect=2,  # 🚀 Faster connection timeout (was 10s, now 2s)
        )

        # TCPConnector: Manages the HTTP connection pool
        connector = TCPConnector(
            limit=max_connections,  # Total connections across all hosts
            limit_per_host=max_connections,  # 🚀 Match total limit for single-host usage
            keepalive_timeout=60,  # 🚀 Longer keep-alive (was 30s, now 60s)
            enable_cleanup_closed=True,  # Automatically clean up closed connections
            use_dns_cache=True,    # 🚀 Enable DNS caching for faster lookups
            ttl_dns_cache=300,     # 🚀 Cache DNS for 5 minutes
        )
        # Why connection limits matter:
        # - Too many: Waste system resources (memory, file descriptors)
        # - Too few: Bottleneck your trading bot's performance
        # - Per-host limit prevents overwhelming any single API server

        # Session will be created lazily (on first request) for better resource management
        self._session: Optional[ClientSession] = None
        self._timeout = timeout_config
        self._connector = connector

        # === REQUEST TRACKING FOR MONITORING ===
        # These help you understand your bot's network behavior
        self.request_count = 0  # Total requests made (for monitoring)
        self.error_count = 0  # Total errors encountered (for health monitoring)

        # Keep details of last 100 requests for debugging
        # deque is more efficient than list for this use case (fixed size, FIFO)
        self.last_requests = deque(maxlen=100)

    async def _get_session(self) -> ClientSession:
        """
        Get or create the aiohttp ClientSession using lazy initialization.

        === LAZY INITIALIZATION EXPLAINED ===
        Instead of creating the HTTP session in __init__, we create it only when
        the first request is made. This is better because:

        1. RESOURCE EFFICIENCY: Don't waste memory if client is never used
        2. ASYNC CONTEXT: ClientSession should be created within async context
        3. ERROR HANDLING: Can handle session creation errors at request time

        === SESSION REUSE ===
        Once created, the same session is reused for all requests. This enables:
        - Connection pooling (reuse TCP connections)
        - Cookie persistence (if needed for authentication)
        - Shared configuration (headers, timeouts, etc.)

        === SESSION RECOVERY ===
        If session gets closed (due to errors, cleanup, etc.), we automatically
        create a new one. This makes the client self-healing.

        === DEFAULT HEADERS EXPLAINED ===
        - User-Agent: Identifies our client to the server (some APIs require this)
        - Accept: Tells server we expect JSON responses
        - Content-Type: For POST/PUT requests, indicates we're sending JSON

        These headers are added to every request automatically.
        """
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                timeout=self._timeout,
                connector=self._connector,
                # headers=self.he,
                # headers={
                #     # Identify our trading bot to the API server
                #     "User-Agent": "TradingSDK/1.0",
                #     # Tell server we expect JSON responses (most trading APIs use JSON)
                #     "Accept": "application/json",
                #     # For requests with body, indicate we're sending JSON
                #     "Content-Type": "application/json",
                # },
            )
        return self._session

    async def close(self):
        """
        Properly close the HTTP session and cleanup resources.

        === WHY CLEANUP IS CRITICAL ===
        HTTP sessions hold system resources:
        - Open TCP connections
        - Memory buffers
        - File descriptors
        - SSL contexts

        If not closed properly, these resources leak and can cause:
        - "Too many open files" errors
        - Memory leaks
        - Connection exhaustion
        - Poor system performance

        === WHEN TO CALL CLOSE ===
        - At the end of your trading bot's lifecycle
        - When switching to a different broker
        - In exception handlers (cleanup on errors)
        - In tests (clean state between tests)

        === SAFE TO CALL MULTIPLE TIMES ===
        This method checks if session exists and isn't already closed,
        so it's safe to call multiple times without errors.
        """
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        """
        Async context manager entry. Allows using 'async with' syntax.

        Example usage:
        ```python
        async with AsyncNetworkClient("https://api.broker.com") as client:
            prices = await client.get("/quotes/AAPL")
            # Session automatically closed when exiting this block
        ```

        This pattern ensures proper cleanup even if exceptions occur.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit. Automatically closes session.

        Parameters are exception information if an exception occurred
        within the 'async with' block. We don't handle the exception,
        just ensure cleanup happens.
        """
        await self.close()

    async def get_cache_stats(self) -> dict:
        """
        Get cache statistics for monitoring and debugging.

        Returns:
            Dictionary with cache statistics including:
            - cache_size: Number of items currently in cache
            - request_count: Total requests made
            - error_count: Total errors encountered
        """
        return {
            "cache_size": self.cache.size(),
            "request_count": self.request_count,
            "error_count": self.error_count,
        }

    def _build_url(self, endpoint: str) -> str:
        """
        Build complete URL from endpoint, handling both relative and absolute URLs.

        === URL BUILDING LOGIC ===
        1. If endpoint is already a full URL (starts with http:// or https://)
           -> Return it as-is (allows flexibility for external APIs)

        2. If endpoint is relative (like "/orders" or "quotes/AAPL")
           -> Combine with base_url to create full URL

        === EXAMPLES ===
        Base URL: "https://api.kite.trade/" (always ends with slash)

        Endpoint: "/orders" -> "https://api.kite.trade/orders" (removes leading slash from endpoint)
        Endpoint: "orders" -> "https://api.kite.trade/orders" (no leading slash needed)
        Endpoint: "/path/to/resource" -> "https://api.kite.trade/path/to/resource"
        Endpoint: "https://other-api.com/data" -> "https://other-api.com/data" (unchanged)

        === SLASH HANDLING ===
        We carefully handle slashes to avoid double slashes:
        - base_url always ends with slash: "https://api.com/"
        - endpoint leading slash is stripped: "/orders" -> "orders"
        - Result: "https://api.com/" + "orders" = "https://api.com/orders"

        This ensures URLs are always well-formed without double slashes.
        """
        if endpoint.startswith(("http://", "https://")):
            return endpoint  # Already a complete URL

        # Remove leading slash from endpoint to avoid double slashes
        # since base_url always ends with slash
        clean_endpoint = endpoint.lstrip("/")
        return f"{self.base_url}{clean_endpoint}"

    def _generate_cache_key(
        self, method: str, url: str, params: Optional[dict] = None
    ) -> str:
        """
        Generate a unique cache key for this request.

        === WHY CACHE KEYS MATTER ===
        Cache keys must uniquely identify each different request:
        - Same key = same request = can use cached response
        - Different key = different request = need fresh response

        === KEY COMPONENTS ===
        1. HTTP METHOD: GET vs POST are different even for same URL
        2. URL: Different endpoints are obviously different
        3. PARAMETERS: Same URL with different params = different data

        === EXAMPLES ===
        GET https://api.com/quote?symbol=AAPL -> "GET:https://api.com/quote:[('symbol', 'AAPL')]"
        GET https://api.com/quote?symbol=MSFT -> "GET:https://api.com/quote:[('symbol', 'MSFT')]"
        POST https://api.com/orders -> "POST:https://api.com/orders"

        === PARAMETER SORTING ===
        We sort parameters to ensure consistent keys:
        - ?symbol=AAPL&limit=10 and ?limit=10&symbol=AAPL are the same request
        - Without sorting, they'd have different cache keys
        - With sorting, both become [('limit', '10'), ('symbol', 'AAPL')]

        This prevents cache misses due to parameter order differences.
        """
        key_parts = [method.upper(), url]
        if params:
            # Sort parameters for consistent cache keys regardless of order
            sorted_params = sorted(params.items())
            key_parts.append(str(sorted_params))
        return ":".join(key_parts)

    async def _log_request(
        self,
        method: str,
        url: str,
        status: int,
        duration: float,
        error: Optional[Exception] = None,
    ):
        """
        Log request details for monitoring, debugging, and performance analysis.

        === WHY REQUEST LOGGING IS CRITICAL IN TRADING ===

        1. DEBUGGING FAILURES:
           - "Why did my order fail?" -> Check logs for exact error
           - "Is the API down?" -> Check recent request success rates

        2. PERFORMANCE MONITORING:
           - "Why is my bot slow?" -> Check request durations
           - "Which API calls are bottlenecks?" -> Analyze timing patterns

        3. RATE LIMIT MONITORING:
           - Track request frequency to avoid violations
           - Identify which endpoints consume most quota

        4. AUDIT TRAIL:
           - Required for regulatory compliance in some markets
           - Track all trading-related API calls

        === LOG LEVELS EXPLAINED ===
        - ERROR: Failed requests (network issues, API errors, timeouts)
        - DEBUG: Successful requests (verbose, usually disabled in production)
        - INFO: Important events (orders placed, positions changed)

        === METRICS TRACKING ===
        We maintain running counters for:
        - Total requests: Overall API usage
        - Error count: Health monitoring (high errors = problem)
        - Recent requests: Detailed history for debugging

        === REQUEST HISTORY STORAGE ===
        We keep the last 100 requests in memory (deque with maxlen=100):
        - Enough history for debugging recent issues
        - Limited size prevents memory leaks
        - FIFO: Old requests automatically removed when full

        Each request record includes:
        - timestamp: When the request was made (Unix time)
        - method: HTTP method (GET, POST, etc.)
        - url: Full URL that was requested
        - status: HTTP status code (200 = success, 4xx = client error, 5xx = server error)
        - duration: How long the request took (in seconds)
        - error: Exception details if request failed
        """
        # Update counters for monitoring
        self.request_count += 1
        if error:
            self.error_count += 1

        # Store detailed request information for debugging
        self.last_requests.append(
            {
                "timestamp": time.time(),  # Unix timestamp for precise timing
                "method": method,  # GET, POST, PUT, DELETE
                "url": url,  # Full URL including parameters
                "status": status,  # HTTP status code (200, 404, 500, etc.)
                "duration": duration,  # Request time in seconds (float for precision)
                "error": str(error) if error else None,  # Error message if failed
            }
        )

        # Log to standard Python logging system
        if error:
            # ERROR level: Always visible, indicates problems that need attention
            logger.error(f"{method} {url} failed: {error} (took {duration:.3f}s)")
        else:
            # DEBUG level: Verbose logging, usually disabled in production
            # Format: "GET /quotes/AAPL -> 200 (took 0.156s)"
            logger.debug(f"{method} {url} -> {status} (took {duration:.3f}s)")

    async def _make_request_with_retry(
        self, method: str, url: str, **kwargs
    ) -> SimpleResponse:
        """
        Make HTTP request with intelligent retry logic and exponential backoff.

        === WHY RETRY LOGIC IS ESSENTIAL IN TRADING ===

        Networks are unreliable, especially for real-time trading:
        - Internet hiccups (WiFi drops, ISP issues)
        - Broker API temporary overload
        - Server restarts or deployments
        - Load balancer failovers

        Without retries: Single network glitch kills your trade
        With retries: Temporary issues are automatically handled

        === EXPONENTIAL BACKOFF EXPLAINED ===

        Instead of retrying immediately, we wait progressively longer:
        - Attempt 1 fails -> wait 1 second -> retry
        - Attempt 2 fails -> wait 2 seconds -> retry
        - Attempt 3 fails -> wait 4 seconds -> retry
        - Attempt 4 fails -> wait 8 seconds -> retry

        Why exponential?
        1. AVOID THUNDERING HERD: If API is overloaded, immediate retries make it worse
        2. GIVE TIME TO RECOVER: Servers need time to handle existing load
        3. REDUCE CASCADING FAILURES: Spread out retry attempts

        === RETRY STRATEGY BY ERROR TYPE ===

        SHOULD RETRY (temporary issues):
        - Network timeouts
        - Connection errors
        - 500 Internal Server Error
        - 502 Bad Gateway
        - 503 Service Unavailable

        SHOULD NOT RETRY (permanent issues):
        - 400 Bad Request (malformed request)
        - 401 Unauthorized (invalid API key)
        - 403 Forbidden (insufficient permissions)
        - 404 Not Found (wrong endpoint)

        === RATE LIMITING INTEGRATION ===
        Before each attempt (including retries), we respect rate limits.
        This prevents retry storms from violating API quotas.

        === TIMING AND LOGGING ===
        We measure and log timing for each attempt:
        - Successful requests: Log response time for performance monitoring
        - Failed requests: Log error and timing for debugging
        - Retry attempts: Log backoff time so you know what's happening
        """
        session = await self._get_session()
        last_exception = None
        # Try the request up to (max_retries + 1) times total
        # Example: max_retries=3 means 4 total attempts (initial + 3 retries)
        for attempt in range(self.max_retries + 1):
            # Initialize start_time before any operations that might fail
            start_time = time.time()

            try:
                # STEP 1: Respect rate limits before making request
                # This prevents retry storms from violating API quotas
                await self.rate_limiter.acquire()

                # STEP 2: Make the actual HTTP request with timing
                # start_time was set before the try block to ensure it's always available

                async with session.request(method, url, **kwargs) as response:
                    duration = time.time() - start_time

                    # Log successful response (status code, timing)
                    await self._log_request(method, url, response.status, duration)

                    # Raise exception if HTTP error status (4xx, 5xx)
                    # This converts HTTP errors into Python exceptions for uniform handling
                    response.raise_for_status()

                    # Read response body inside the context to avoid connection closed errors
                    response_text = await response.text()

                    # Return a simple response object with the data we need
                    return SimpleResponse(
                        text=response_text,
                        status=response.status,
                        url=response.url,
                        headers=response.headers,
                    )

            except Exception as e:
                # STEP 3: Handle request failure
                duration = (
                    time.time() - start_time
                )  # How long did the failed request take?

                # Log the failure with timing information
                await self._log_request(method, url, 0, duration, e)

                last_exception = e  # Remember this error in case all retries fail

                # STEP 4: Decide whether to retry based on error type
                if isinstance(e, aiohttp.ClientResponseError):
                    # HTTP error responses (4xx, 5xx)
                    if 400 <= e.status < 500:
                        # 4xx errors are client mistakes (bad request, auth, etc.)
                        # These won't be fixed by retrying, so fail immediately
                        logger.error(f"Client error {e.status}, not retrying: {e}")
                        break
                    # 5xx errors are server issues - these might be temporary, so retry

                # STEP 5: Exponential backoff before retry
                if attempt < self.max_retries:
                    # Calculate backoff time: 2^attempt seconds, max 30 seconds
                    # attempt 0: 2^0 = 1 second
                    # attempt 1: 2^1 = 2 seconds
                    # attempt 2: 2^2 = 4 seconds
                    # attempt 3: 2^3 = 8 seconds
                    # attempt 4: 2^4 = 16 seconds
                    # attempt 5+: capped at 30 seconds
                    backoff = min(2**attempt, 30)

                    logger.warning(
                        f"Request failed, retrying in {backoff}s "
                        f"(attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                    )

                    # Sleep before retry (non-blocking, other coroutines can run)
                    await asyncio.sleep(backoff)

        # STEP 6: All retries exhausted, raise the last exception
        if last_exception is not None:
            raise last_exception
        else:
            # This should never happen, but just in case...
            raise aiohttp.ClientError("Request failed but no exception was captured.")

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        use_cache: bool = False,
        cache_ttl: Optional[int] = None,
    ) -> Any:
        """
        Make an HTTP request with the full enterprise feature set.

        This is the core method that orchestrates all the features:
        - Caching (check cache first, store results)
        - Rate limiting (respect API limits)
        - Circuit breaker (fail fast when API is down)
        - Retry logic (handle temporary failures)
        - Request/response logging (monitoring and debugging)

        === PARAMETER EXPLANATIONS ===

        method: HTTP method string
        - "GET": Retrieve data (quotes, positions, account info)
        - "POST": Create new resources (place orders, create watchlists)
        - "PUT": Update existing resources (modify orders, update settings)
        - "DELETE": Remove resources (cancel orders, delete watchlists)

        endpoint: API endpoint or full URL
        - Relative: "/orders", "quotes/AAPL" (combined with base_url)
        - Absolute: "https://other-api.com/data" (used as-is)

        params: Query parameters (URL parameters after ?)
        - Example: {"symbol": "AAPL", "limit": 10} -> "?symbol=AAPL&limit=10"
        - Used for filtering, pagination, options

        data: Form data (application/x-www-form-urlencoded)
        - Traditional web form data
        - Some older APIs require this format
        - Example: {"username": "user", "password": "pass"}

        json_data: JSON payload (application/json)
        - Modern API standard for structured data
        - Used for complex requests like order placement
        - Example: {"symbol": "AAPL", "quantity": 100, "price": 150.00}

        headers: Additional HTTP headers
        - Authentication: {"Authorization": "Bearer token123"}
        - Custom headers: {"X-API-Key": "key123"}
        - Merged with default headers (User-Agent, Content-Type, etc.)

        use_cache: Whether to use response caching
        - True: Check cache first, store successful responses
        - False: Always make fresh request (default for non-GET)
        - Only effective for GET requests (POST/PUT/DELETE never cached)

        cache_ttl: Cache time-to-live override (seconds)
        - Overrides the default cache TTL for this request
        - Use short TTL (1-5s) for live data
        - Use long TTL (300s+) for static reference data

        === RETURN VALUE ===
        Returns parsed JSON response as Python dictionary.
        - Successful API responses are automatically parsed from JSON
        - Complex nested data structures are preserved
        - If response isn't valid JSON, raises ValueError with details

        === CACHING BEHAVIOR ===

        For GET requests with use_cache=True:
        1. Generate cache key from method + URL + parameters
        2. Check if cached response exists and isn't expired
        3. If cache hit: return cached data immediately (no network request)
        4. If cache miss: make network request and cache the response

        For non-GET requests or use_cache=False:
        - Always make fresh network request
        - Never check cache or store results
        - Ensures data consistency for state-changing operations

        === ERROR HANDLING ===

        This method can raise several types of exceptions:
        - CircuitBreakerOpenError: Circuit breaker is protecting from failures
        - aiohttp.ClientResponseError: HTTP errors (4xx, 5xx status codes)
        - aiohttp.ClientError: Network issues (timeouts, connection errors)
        - ValueError: Response isn't valid JSON
        - asyncio.TimeoutError: Request took too long

        === REAL TRADING EXAMPLES ===

        # Get live stock price (cached for 1 second)
        price = await client.request(
            "GET", "/quote/NSE:RELIANCE",
            use_cache=True, cache_ttl=1
        )

        # Place a buy order (never cached)
        order = await client.request(
            "POST", "/orders",
            json_data={
                "symbol": "NSE:RELIANCE",
                "quantity": 100,
                "price": 2500.00,
                "order_type": "LIMIT",
                "side": "BUY"
            }
        )

        # Get account positions (cached for 30 seconds)
        positions = await client.request(
            "GET", "/positions",
            use_cache=True, cache_ttl=30
        )
        """
        url = self._build_url(endpoint)
        print("----", url)

        # === STEP 1: CHECK CACHE FOR GET REQUESTS ===
        # Only GET requests can be cached (POST/PUT/DELETE change state)
        if method.upper() == "GET" and use_cache:
            cache_key = self._generate_cache_key(method, url, params)
            cached_response = await self.cache.get(cache_key)
            if cached_response is not None:
                logger.info(f"🎯 CACHE HIT: {method} {url}")
                return (
                    cached_response  # Return cached data, skip network request entirely
                )
            else:
                logger.info(f"❌ CACHE MISS: {method} {url}")

        # === STEP 2: PREPARE REQUEST PARAMETERS ===
        # Build kwargs dictionary for aiohttp.request()
        request_kwargs = {}

        if params:
            # Query parameters: ?symbol=AAPL&limit=10
            request_kwargs["params"] = params

        if data:
            # Form data: application/x-www-form-urlencoded
            # Used by some older APIs or authentication endpoints
            request_kwargs["data"] = data

        if json_data:
            # JSON payload: application/json (most common for modern APIs)
            # aiohttp automatically sets Content-Type and serializes to JSON
            request_kwargs["json"] = json_data

        # Merge default headers with request-specific headers
        # Request headers take precedence over default headers
        merged_headers = self.default_headers.copy()
        if headers:
            merged_headers.update(headers)

        if merged_headers:
            request_kwargs["headers"] = merged_headers

        # === STEP 3: MAKE REQUEST WITH PROTECTION ===
        # Route through circuit breaker if enabled for fault tolerance
        if self.circuit_breaker:
            response = await self.circuit_breaker.call(
                self._make_request_with_retry, method, url, **request_kwargs
            )
        else:
            # Direct request without circuit breaker protection
            response = await self._make_request_with_retry(
                method, url, **request_kwargs
            )

        # === STEP 4: PARSE RESPONSE CONTENT ===
        # Check content type and response to determine how to parse
        text_response = response.text
        content_type = response.headers.get('content-type', '').lower()

        # Handle empty responses
        if not text_response.strip():
            logger.warning(f"Empty response from {method} {url}")
            return None

        # Try to parse as JSON if content-type suggests JSON or if it looks like JSON
        if ('application/json' in content_type or
            'application/javascript' in content_type or
            text_response.strip().startswith(('{', '['))):
            try:
                json_response = json.loads(text_response)
                logger.debug(f"Successfully parsed JSON response from {url}")
            except (json.JSONDecodeError, ValueError) as e:
                # JSON parsing failed - return raw text instead
                logger.warning(
                    f"Failed to parse as JSON despite content-type, returning raw text: {e}"
                )
                logger.debug(f"Raw response: {text_response[:500]}")
                return text_response
        else:
            # Non-JSON content type - return raw text
            logger.info(f"Non-JSON response from {url}, content-type: {content_type}")
            return text_response
        # === STEP 5: CACHE SUCCESSFUL GET RESPONSES ===
        # Only cache GET requests to avoid caching state-changing operations
        if method.upper() == "GET" and use_cache:
            cache_key = self._generate_cache_key(method, url, params)
            # Cache the response (whether it's JSON, text, or None)
            response_to_cache = json_response if 'json_response' in locals() else text_response
            await self.cache.set(cache_key, response_to_cache, cache_ttl)

        return json_response if 'json_response' in locals() else text_response

    # === CONVENIENCE METHODS ===
    # These methods wrap the main request() method with sensible defaults for each HTTP method

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make a GET request - used for retrieving data without side effects.

        === WHEN TO USE GET ===
        GET requests are for reading/retrieving data:
        - Stock prices and market data
        - Account balance and positions
        - Order history and status
        - Available instruments lists
        - User profile information

        === CACHING BY DEFAULT ===
        GET requests enable caching by default because:
        - Reading data doesn't change server state
        - Same request often returns same data
        - Caching improves performance and reduces API usage

        === EXAMPLES ===
        ```python
        # Get current stock price (cached for default TTL)
        price = await client.get("/quote/NSE:RELIANCE")

        # Get account balance with fresh data (no cache)
        balance = await client.get("/user/balance", use_cache=False)

        # Get market data with short cache (1 second)
        market = await client.get("/market/status", cache_ttl=1)

        # Get historical data with parameters
        history = await client.get("/historical/AAPL", params={
            "from": "2023-01-01",
            "to": "2023-12-31",
            "interval": "1d"
        })
        ```

        Args:
            endpoint: API endpoint (e.g., "/quotes/AAPL")
            params: Query parameters for filtering/pagination
            use_cache: Whether to cache the response (default: True)
            cache_ttl: Cache expiration time in seconds (uses default if None)
            **kwargs: Additional arguments passed to request()

        Returns:
            Parsed JSON response as dictionary
        """
        return await self.request(
            "GET",
            endpoint,
            params=params,
            use_cache=use_cache,
            cache_ttl=cache_ttl,
            **kwargs,
        )

    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict] = None,
        data: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make a POST request - used for creating new resources or submitting data.

        === WHEN TO USE POST ===
        POST requests are for creating or submitting data:
        - Placing new orders
        - Creating watchlists
        - Logging in (authentication)
        - Submitting forms
        - Uploading files

        === NO CACHING ===
        POST requests are never cached because:
        - They have side effects (create orders, change state)
        - Same request might have different results each time
        - You want to know the current status, not a cached one

        === JSON vs FORM DATA ===

        json_data (preferred for modern APIs):
        ```python
        await client.post("/orders", json_data={
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.0,
            "side": "BUY"
        })
        ```

        data (for traditional form submissions):
        ```python
        await client.post("/login", data={
            "username": "user123",
            "password": "secret"
        })
        ```

        === TRADING EXAMPLES ===
        ```python
        # Place a market buy order
        order = await client.post("/orders", json_data={
            "symbol": "NSE:RELIANCE",
            "quantity": 10,
            "order_type": "MARKET",
            "side": "BUY",
            "product": "MIS"  # Intraday
        })

        # Create a new watchlist
        watchlist = await client.post("/watchlists", json_data={
            "name": "Tech Stocks",
            "symbols": ["AAPL", "GOOGL", "MSFT"]
        })

        # Authenticate with broker
        auth = await client.post("/session/token", data={
            "api_key": "your_api_key",
            "access_token": "your_token"
        })
        ```

        Args:
            endpoint: API endpoint (e.g., "/orders")
            json_data: JSON payload for modern APIs (preferred)
            data: Form data for traditional APIs
            **kwargs: Additional arguments passed to request()

        Returns:
            Parsed JSON response as dictionary
        """
        return await self.request(
            "POST", endpoint, json_data=json_data, data=data, **kwargs
        )

    async def put(
        self,
        endpoint: str,
        json_data: Optional[Dict] = None,
        data: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make a PUT request - used for updating existing resources.

        === WHEN TO USE PUT ===
        PUT requests are for updating/replacing existing data:
        - Modifying existing orders (change price/quantity)
        - Updating user profile/settings
        - Replacing watchlist contents
        - Updating stop-loss levels

        === PUT vs POST ===
        - POST: Create new resources ("add a new order")
        - PUT: Update existing resources ("change order #12345")

        === TRADING EXAMPLES ===
        ```python
        # Modify existing order price
        updated_order = await client.put(f"/orders/{order_id}", json_data={
            "price": 155.0,  # New price
            "quantity": 50   # New quantity
        })

        # Update user trading preferences
        settings = await client.put("/user/preferences", json_data={
            "risk_level": "moderate",
            "default_quantity": 100,
            "auto_square_off": True
        })
        ```

        Args:
            endpoint: API endpoint (e.g., "/orders/12345")
            json_data: JSON payload with updated data
            data: Form data (rarely used with PUT)
            **kwargs: Additional arguments passed to request()

        Returns:
            Parsed JSON response as dictionary
        """
        return await self.request(
            "PUT", endpoint, json_data=json_data, data=data, **kwargs
        )

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a DELETE request - used for removing/canceling resources.

        === WHEN TO USE DELETE ===
        DELETE requests are for removing or canceling:
        - Canceling pending orders
        - Removing stocks from watchlists
        - Deleting saved searches
        - Closing positions (some brokers)

        === TRADING EXAMPLES ===
        ```python
        # Cancel a pending order
        result = await client.delete(f"/orders/{order_id}")

        # Remove stock from watchlist
        result = await client.delete(f"/watchlists/{watchlist_id}/symbols/AAPL")

        # Cancel all pending orders for a symbol
        result = await client.delete("/orders", params={"symbol": "RELIANCE"})
        ```

        === RETURN VALUES ===
        DELETE usually returns:
        - Success confirmation: {"status": "success", "message": "Order canceled"}
        - Updated resource state: Current order status after cancellation
        - Error details if cancellation failed

        Args:
            endpoint: API endpoint (e.g., "/orders/12345")
            **kwargs: Additional arguments passed to request()

        Returns:
            Parsed JSON response as dictionary
        """
        return await self.request("DELETE", endpoint, **kwargs)

    # === BATCH OPERATIONS ===
    # These methods allow efficient parallel processing of multiple requests

    async def get_multiple(
        self, endpoints: List[str], **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch multiple endpoints concurrently for maximum performance.

        === WHY CONCURRENT REQUESTS? ===

        Sequential approach (slow):
        ```python
        # This takes 3+ seconds if each request takes 1 second
        price1 = await client.get("/quote/AAPL")  # 1 second
        price2 = await client.get("/quote/GOOGL") # 1 second
        price3 = await client.get("/quote/MSFT")  # 1 second
        ```

        Concurrent approach (fast):
        ```python
        # This takes ~1 second total (all requests run in parallel)
        prices = await client.get_multiple([
            "/quote/AAPL",
            "/quote/GOOGL",
            "/quote/MSFT"
        ])
        ```

        === HOW IT WORKS ===
        1. Creates async tasks for each endpoint
        2. Launches all tasks concurrently using asyncio.gather()
        3. Each task runs independently (rate limits still respected)
        4. Returns when ALL tasks complete (or fail)

        === ERROR HANDLING ===
        If some requests fail:
        - Successful requests return normal data
        - Failed requests return {"error": "error message"}
        - You get partial results instead of total failure

        This is better than stopping everything when one request fails.

        === TRADING EXAMPLES ===
        ```python
        # Get prices for entire portfolio
        portfolio_prices = await client.get_multiple([
            "/quote/NSE:RELIANCE",
            "/quote/NSE:TCS",
            "/quote/NSE:INFY",
            "/quote/NSE:HDFC"
        ])

        # Get account info from multiple endpoints
        account_data = await client.get_multiple([
            "/user/profile",
            "/user/balance",
            "/user/positions",
            "/user/orders"
        ])

        # Check market status for multiple exchanges
        market_status = await client.get_multiple([
            "/market/status/NSE",
            "/market/status/BSE",
            "/market/status/MCX"
        ])
        ```

        === RATE LIMITING CONSIDERATION ===
        Even though requests run concurrently, each still respects rate limits.
        If your rate limit is 10 RPS and you request 50 endpoints:
        - Requests will be spread over ~5 seconds
        - Still much faster than 50 seconds sequentially
        - Rate limiter ensures you don't get banned

        Args:
            endpoints: List of API endpoints to fetch
            **kwargs: Additional arguments passed to each GET request

        Returns:
            Dictionary mapping endpoint to response:
            {
                "/quote/AAPL": {"price": 150.0, "change": 2.5},
                "/quote/GOOGL": {"price": 2800.0, "change": -15.0},
                "/quote/MSFT": {"error": "Symbol not found"}
            }
        """

        async def fetch_one(endpoint: str):
            """
            Fetch a single endpoint with error handling.

            Returns tuple of (endpoint, response) so we can map results back.
            If request fails, returns error info instead of raising exception.
            """
            try:
                return endpoint, await self.get(endpoint, **kwargs)
            except Exception as e:
                logger.error(f"Failed to fetch {endpoint}: {e}")
                # Return error info instead of crashing the entire batch
                return endpoint, {"error": str(e)}

        # Create async tasks for all endpoints
        tasks = [fetch_one(endpoint) for endpoint in endpoints]

        # Run all tasks concurrently and wait for all to complete
        results = await asyncio.gather(*tasks)

        # Convert list of tuples to dictionary for easy access
        return dict(results)

    # === MONITORING AND DIAGNOSTICS ===
    # These methods help you understand and debug your bot's network behavior

    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive client statistics for monitoring and debugging.

        === WHY MONITORING IS CRUCIAL IN TRADING ===

        Your trading bot's success depends on reliable network communication.
        These statistics help you:

        1. PERFORMANCE MONITORING:
           - Is my bot making too many requests?
           - Are requests taking too long?
           - Which endpoints are slowest?

        2. ERROR TRACKING:
           - What's my error rate?
           - Are errors increasing over time?
           - Which operations fail most often?

        3. CIRCUIT BREAKER STATUS:
           - Is the circuit breaker protecting from failures?
           - How often does it open?
           - Are APIs recovering properly?

        4. CACHE EFFECTIVENESS:
           - How much data is cached?
           - Is caching reducing API calls?
           - Do I need to adjust cache TTL?

        === STATISTICS BREAKDOWN ===

        request_count: Total requests made since client creation
        - Use for: Overall usage monitoring
        - Alert if: Sudden spikes (possible runaway loop)

        error_count: Total requests that failed
        - Use for: Reliability monitoring
        - Alert if: Error rate > 5-10%

        circuit_breaker_state: Current circuit breaker status
        - "CLOSED": Normal operation
        - "OPEN": Blocking requests due to failures
        - "HALF_OPEN": Testing if API recovered
        - Alert if: Frequently OPEN (API reliability issues)

        cache_size: Number of items currently cached
        - Use for: Memory usage monitoring
        - Alert if: Grows without bounds (cache not expiring)

        recent_requests: Last 10 requests with full details
        - Use for: Debugging specific failures
        - Contains: timestamp, method, URL, status, duration, errors

        === USAGE EXAMPLES ===
        ```python
        # Monitor your trading bot's health
        stats = client.get_stats()

        # Check error rate
        error_rate = stats['error_count'] / stats['request_count']
        if error_rate > 0.1:  # More than 10% errors
            print("High error rate detected!")

        # Check if circuit breaker is active
        if stats['circuit_breaker_state'] == 'OPEN':
            print("Circuit breaker is open - API may be down")

        # Log recent failures for debugging
        for req in stats['recent_requests']:
            if req['error']:
                print(f"Failed: {req['method']} {req['url']} - {req['error']}")
        ```

        Returns:
            Dictionary with comprehensive client statistics
        """
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            # Circuit breaker state (if enabled)
            "circuit_breaker_state": self.circuit_breaker.state
            if self.circuit_breaker
            else None,
            # Cache usage
            "cache_size": self.cache.size(),
            # Recent request history (last 10 for debugging)
            "recent_requests": list(self.last_requests)[-10:],
            # Calculated metrics
            "error_rate": self.error_count / max(self.request_count, 1),
            "requests_per_minute": self._calculate_recent_rps() * 60
            if self.last_requests
            else 0,
        }

    def _calculate_recent_rps(self) -> float:
        """
        Calculate recent requests per second for monitoring.

        Uses requests from the last 60 seconds to get current rate.
        """
        if len(self.last_requests) < 2:
            return 0.0

        current_time = time.time()
        recent_requests = [
            req
            for req in self.last_requests
            if current_time - req["timestamp"] <= 60  # Last 60 seconds
        ]

        if len(recent_requests) < 2:
            return 0.0

        time_span = recent_requests[-1]["timestamp"] - recent_requests[0]["timestamp"]
        return len(recent_requests) / max(time_span, 1)

    async def health_check(self, endpoint: str = "/health") -> bool:
        """
        Perform a health check to verify API connectivity and responsiveness.

        === WHY HEALTH CHECKS MATTER ===

        Before starting trading operations, you should verify:
        1. Network connectivity is working
        2. API server is responding
        3. Authentication is valid
        4. No circuit breaker issues

        Regular health checks help detect:
        - API outages before they affect trading
        - Authentication token expiration
        - Network connectivity issues
        - Circuit breaker activation

        === HEALTH CHECK STRATEGIES ===

        Most APIs provide dedicated health endpoints:
        - "/health" - Basic server status
        - "/ping" - Simple connectivity test
        - "/status" - Detailed system status
        - "/user/profile" - Test authentication

        If no dedicated endpoint exists, use a lightweight GET request
        that doesn't consume significant API quota.

        === USAGE PATTERNS ===
        ```python
        # Check health before starting trading
        if not await client.health_check():
            print("API is not responding - check connectivity")
            return

        # Periodic health monitoring
        async def monitor_health():
            while True:
                is_healthy = await client.health_check()
                if not is_healthy:
                    # Alert, log, or take corrective action
                    await notify_admin("API health check failed")
                await asyncio.sleep(60)  # Check every minute

        # Test specific broker endpoints
        zerodha_healthy = await client.health_check("/user/profile")
        upstox_healthy = await client.health_check("/user/get-profile")
        ```

        Args:
            endpoint: Health check endpoint (default: "/health")
                     Common alternatives: "/ping", "/status", "/user/profile"

        Returns:
            True if health check passed, False if failed

        Note:
            This method never raises exceptions - it catches all errors
            and returns False, making it safe for monitoring loops.
        """
        try:
            await self.get(endpoint, use_cache=False)  # Always fresh for health checks
            return True
        except Exception as e:
            logger.warning(f"Health check failed for {endpoint}: {e}")
            return False

    # Cleanup
    async def clear_cache(self):
        """Clear all cached data"""
        await self.cache.clear()

    async def cleanup_expired_cache(self):
        """Remove expired cache entries"""
        await self.cache.cleanup_expired()


class BrokerNetworkClient(AsyncNetworkClient):
    """
    Specialized network client for broker APIs with trading-specific features.
    """

    def __init__(self, broker_name: str, base_url: str, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.broker_name = broker_name
        self._access_token: Optional[str] = None
        self._session_headers: Dict[str, str] = {}

    def set_access_token(self, token: str):
        """Set access token for authentication"""
        self._access_token = token
        self._session_headers["Authorization"] = f"Bearer {token}"

    def set_api_key(self, api_key: str, header_name: str = "X-API-Key"):
        """Set API key header"""
        self._session_headers[header_name] = api_key

    def add_session_header(self, name: str, value: str):
        """Add persistent session header"""
        self._session_headers[name] = value

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        use_cache: bool = False,
        cache_ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Override to add session headers"""
        if headers is None:
            headers = {}
        headers.update(self._session_headers)

        return await super().request(
            method,
            endpoint,
            params=params,
            data=data,
            json_data=json_data,
            headers=headers,
            use_cache=use_cache,
            cache_ttl=cache_ttl,
        )

    # Trading-specific methods
    async def place_order_request(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        """Place order with broker-specific handling"""
        try:
            response = await self.post("/orders", json_data=order_params)
            logger.info(f"Order placed successfully: {response.get('order_id')}")
            return response
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            raise

    async def get_positions_request(self) -> Dict[str, Any]:
        """Get positions with caching"""
        return await self.get(
            "/positions", use_cache=True, cache_ttl=5
        )  # Cache for 5 seconds

    async def get_quote_request(self, symbol: str) -> Dict[str, Any]:
        """Get quote with short-term caching"""
        return await self.get(
            f"/quote/{symbol}", use_cache=True, cache_ttl=1
        )  # 1 second cache

    async def get_quotes_batch(self, symbols: List[str]) -> Dict[str, Any]:
        """Get multiple quotes efficiently"""
        # If broker supports batch quotes
        symbol_list = ",".join(symbols)
        return await self.get(
            "/quotes", params={"symbols": symbol_list}, use_cache=True, cache_ttl=1
        )


# Factory function for creating clients
def create_broker_client(
    broker_name: str, base_url: str, rate_limit: float = 10.0, **kwargs
) -> BrokerNetworkClient:
    """
    Factory function to create broker-specific network clients.

    Args:
        broker_name: Name of the broker (zerodha, upstox, etc.)
        base_url: Base URL for broker API
        rate_limit: Requests per second limit
        **kwargs: Additional client configuration

    Returns:
        Configured BrokerNetworkClient instance
    """
    # Broker-specific rate limits
    broker_limits = {
        "zerodha": 10.0,  # 10 RPS for Zerodha
        "upstox": 25.0,  # 25 RPS for Upstox
        "angel": 20.0,  # 20 RPS for Angel One
        "fyers": 15.0,  # 15 RPS for Fyers
    }

    if broker_name.lower() in broker_limits:
        rate_limit = broker_limits[broker_name.lower()]

    return BrokerNetworkClient(
        broker_name=broker_name, base_url=base_url, rate_limit=rate_limit, **kwargs
    )


# === COMPREHENSIVE USAGE GUIDE ===
"""
TRADING NETWORK CLIENT - COMPLETE USAGE GUIDE

This documentation provides everything you need to use this professional-grade
async HTTP client for trading applications. No external documentation needed!

=== QUICK START EXAMPLE ===

```python
import asyncio
from trading_sdk.network import create_broker_client

async def main():
    # 1. Create broker client with automatic rate limiting
    client = create_broker_client("zerodha", "https://api.kite.trade")

    # 2. Set up authentication (get token from broker's OAuth flow)
    client.set_access_token("your_access_token_here")

    # 3. Start making trading requests
    try:
        # Get account positions
        positions = await client.get_positions_request()
        print(f"Current positions: {len(positions.get('data', []))}")

        # Get live stock price
        quote = await client.get_quote_request("NSE:RELIANCE")
        price = quote['data']['last_price']
        print(f"RELIANCE price: ₹{price}")

        # Place a buy order
        order = await client.place_order_request({
            "tradingsymbol": "RELIANCE",
            "quantity": 1,
            "price": price * 0.99,  # 1% below current price
            "order_type": "LIMIT",
            "transaction_type": "BUY",
            "product": "MIS"  # Intraday
        })
        print(f"Order placed: {order.get('order_id')}")

    except Exception as e:
        print(f"Trading operation failed: {e}")

    finally:
        # Always clean up resources
        await client.close()

# Run the trading bot
if __name__ == "__main__":
    asyncio.run(main())
```

=== ADVANCED USAGE PATTERNS ===

1. EFFICIENT BATCH OPERATIONS:
```python
# Instead of multiple individual requests (slow):
price1 = await client.get_quote_request("AAPL")
price2 = await client.get_quote_request("GOOGL")
price3 = await client.get_quote_request("MSFT")

# Use batch requests (fast):
prices = await client.get_quotes_batch(["AAPL", "GOOGL", "MSFT"])

# Or fetch different endpoints concurrently:
account_data = await client.get_multiple([
    "/user/profile", "/user/balance", "/positions", "/orders"
])
```

2. SMART CACHING STRATEGIES:
```python
# Live market data - short cache (1 second)
price = await client.get("/quote/AAPL", use_cache=True, cache_ttl=1)

# Account info - medium cache (30 seconds)
balance = await client.get("/user/balance", use_cache=True, cache_ttl=30)

# Static reference data - long cache (1 hour)
instruments = await client.get("/instruments", use_cache=True, cache_ttl=3600)

# Critical operations - always fresh (no cache)
order_status = await client.get(f"/orders/{order_id}", use_cache=False)
```

3. COMPREHENSIVE ERROR HANDLING:
```python
from trading_sdk.network import CircuitBreakerOpenError
import aiohttp

try:
    order = await client.place_order_request(order_params)
    print("Order successful!")

except CircuitBreakerOpenError:
    print("API is down - circuit breaker is protecting us")
    # Wait and try again later, or switch to backup broker

except aiohttp.ClientResponseError as e:
    if e.status == 400:
        print(f"Invalid order parameters: {e}")
    elif e.status == 401:
        print("Authentication failed - refresh token")
    elif e.status == 429:
        print("Rate limit exceeded - slow down requests")
    elif e.status >= 500:
        print(f"Broker server error: {e}")
    else:
        print(f"HTTP error {e.status}: {e}")

except aiohttp.ClientError as e:
    print(f"Network error: {e}")
    # Retry with exponential backoff, check internet connection

except Exception as e:
    print(f"Unexpected error: {e}")
    # Log full stack trace for debugging
```

4. MONITORING AND HEALTH CHECKS:
```python
# Check API health before starting trading
if not await client.health_check():
    print("API is not responding - aborting trading session")
    return

# Monitor client performance
stats = client.get_stats()
print(f"Total requests: {stats['request_count']}")
print(f"Error rate: {stats['error_rate']:.2%}")
print(f"Circuit breaker: {stats['circuit_breaker_state']}")
print(f"Cache size: {stats['cache_size']} entries")

# Alert on high error rates
if stats['error_rate'] > 0.1:  # More than 10% errors
    print("WARNING: High error rate detected!")
    # Send alert, reduce trading frequency, investigate issues
```

=== BROKER-SPECIFIC EXAMPLES ===

ZERODHA KITE:
```python
client = create_broker_client("zerodha", "https://api.kite.trade")
client.set_access_token("your_kite_access_token")
client.add_session_header("X-Kite-Version", "3")

# Zerodha-specific order format
order = await client.place_order_request({
    "tradingsymbol": "RELIANCE",
    "exchange": "NSE",
    "quantity": 1,
    "price": 2500,
    "order_type": "LIMIT",
    "transaction_type": "BUY",
    "product": "MIS",
    "validity": "DAY"
})
```

UPSTOX:
```python
client = create_broker_client("upstox", "https://api.upstox.com")
client.set_access_token("your_upstox_token")

# Upstox-specific order format
order = await client.place_order_request({
    "instrument_token": "NSE_EQ|INE002A01018",
    "quantity": 1,
    "price": 2500,
    "order_type": "LIMIT",
    "transaction_type": "BUY",
    "product": "I",  # Intraday
    "validity": "DAY"
})
```

=== PERFORMANCE OPTIMIZATION ===

1. CONNECTION POOLING:
```python
# Good: Reuse client for multiple requests
client = create_broker_client("zerodha", "https://api.kite.trade")
for symbol in portfolio:
    price = await client.get_quote_request(symbol)
await client.close()

# Bad: Creating new client for each request
for symbol in portfolio:
    client = create_broker_client("zerodha", "https://api.kite.trade")
    price = await client.get_quote_request(symbol)
    await client.close()  # Wastes connections
```

2. RATE LIMIT OPTIMIZATION:
```python
# Monitor your rate limit usage
stats = client.get_stats()
recent_rps = stats['requests_per_minute'] / 60

# Adjust request frequency based on limits
if recent_rps > 8:  # Close to Zerodha's 10 RPS limit
    await asyncio.sleep(0.2)  # Slow down requests
```

3. CACHE OPTIMIZATION:
```python
# Periodic cache cleanup to free memory
async def maintain_cache():
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        await client.cleanup_expired_cache()

        # Monitor cache effectiveness
        stats = client.get_stats()
        if stats['cache_size'] > 1000:
            print("Cache getting large, consider shorter TTL")

asyncio.create_task(maintain_cache())
```

=== SECURITY BEST PRACTICES ===

1. TOKEN SECURITY:
```python
import os

# Store tokens in environment variables, not code
access_token = os.getenv("BROKER_ACCESS_TOKEN")
if not access_token:
    raise ValueError("BROKER_ACCESS_TOKEN environment variable required")

client.set_access_token(access_token)

# Refresh tokens before expiry
async def refresh_token_periodically():
    while True:
        await asyncio.sleep(3600)  # Check every hour
        new_token = await get_fresh_token_from_broker()
        client.set_access_token(new_token)
```

2. NETWORK SECURITY:
```python
# Always use HTTPS for real money operations
assert client.base_url.startswith("https://"), "Must use HTTPS for trading"

# Log security events
import logging
logging.basicConfig(level=logging.INFO)

# The client automatically logs all network activity
```

=== TESTING AND DEBUGGING ===

1. PAPER TRADING SETUP:
```python
# Test with paper trading URLs first
paper_client = create_broker_client(
    "zerodha",
    "https://api-sandbox.kite.trade",  # Sandbox URL
    rate_limit=100.0  # Higher limits in sandbox
)

# Test all operations before going live
await paper_client.place_order_request(test_order)
```

2. MOCK TESTING:
```python
# For unit tests, mock the network responses
from unittest.mock import AsyncMock

client._make_request_with_retry = AsyncMock(return_value=mock_response)
result = await client.get("/test")
assert result == expected_result
```

3. DEBUG LOGGING:
```python
import logging
logging.getLogger("trading_sdk.network").setLevel(logging.DEBUG)

# Now all requests/responses will be logged in detail
```

=== COMMON TROUBLESHOOTING ===

PROBLEM: "Rate limit exceeded" errors
SOLUTION:
- Check your rate limit with stats['requests_per_minute']
- Reduce request frequency or use caching
- Verify broker-specific limits

PROBLEM: "Circuit breaker is OPEN"
SOLUTION:
- API is experiencing failures
- Wait for recovery timeout (usually 60 seconds)
- Check broker status page/announcements

PROBLEM: Authentication errors
SOLUTION:
- Verify token is valid and not expired
- Check if token has required permissions
- Refresh token if needed

PROBLEM: Slow performance
SOLUTION:
- Use batch requests where possible
- Enable caching for frequently accessed data
- Monitor connection pool usage

This comprehensive client handles all the complexity of reliable trading API
communication, so you can focus on your trading strategy instead of
networking issues!
"""
