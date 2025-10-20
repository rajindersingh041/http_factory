"""
🎯 Advanced MTM Trailing System

This module implements sophisticated Mark-to-Market (MTM) trailing features:
1. Strategy-level MTM trailing - Track overall strategy performance
2. Trade-wise MTM trailing - Individual trade profit/loss tracking

Features:
- Real-time MTM calculation
- Trailing stop-loss based on MTM
- Strategy-level risk management
- Trade-level profit protection
- Event-driven architecture
- Observer pattern for notifications
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =====================================================
# 1. CORE DATA MODELS
# =====================================================

class TradeStatus(Enum):
    """Trade status enumeration"""
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"
    CANCELLED = "cancelled"


class MTMEventType(Enum):
    """MTM event types"""
    PRICE_UPDATE = "price_update"
    TRAILING_TRIGGERED = "trailing_triggered"
    STOP_LOSS_HIT = "stop_loss_hit"
    TARGET_ACHIEVED = "target_achieved"
    STRATEGY_LIMIT_BREACHED = "strategy_limit_breached"


@dataclass
class Trade:
    """Individual trade representation"""
    trade_id: str
    symbol: str
    quantity: int
    entry_price: float
    trade_type: str  # "BUY" or "SELL"
    strategy_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    status: TradeStatus = TradeStatus.OPEN
    current_price: float = 0.0
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    trailing_stop: Optional[float] = None
    max_profit: float = 0.0
    max_loss: float = 0.0

    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L"""
        if self.status != TradeStatus.OPEN:
            return 0.0

        if self.trade_type == "BUY":
            return (self.current_price - self.entry_price) * self.quantity
        else:  # SELL
            return (self.entry_price - self.current_price) * self.quantity

    @property
    def realized_pnl(self) -> float:
        """Calculate realized P&L"""
        if self.status != TradeStatus.CLOSED or not self.exit_price:
            return 0.0

        if self.trade_type == "BUY":
            return (self.exit_price - self.entry_price) * self.quantity
        else:  # SELL
            return (self.entry_price - self.exit_price) * self.quantity

    @property
    def current_pnl(self) -> float:
        """Get current P&L (realized or unrealized)"""
        return self.realized_pnl if self.status == TradeStatus.CLOSED else self.unrealized_pnl


@dataclass
class StrategyMTM:
    """Strategy-level MTM tracking"""
    strategy_name: str
    trades: List[Trade] = field(default_factory=list)
    max_drawdown_limit: float = -10000.0  # Maximum allowed loss
    trailing_percentage: float = 0.5  # 50% trailing
    peak_mtm: float = 0.0
    current_trailing_stop: float = 0.0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def total_unrealized_pnl(self) -> float:
        """Total unrealized P&L across all open trades"""
        return sum(trade.unrealized_pnl for trade in self.trades if trade.status == TradeStatus.OPEN)

    @property
    def total_realized_pnl(self) -> float:
        """Total realized P&L from closed trades"""
        return sum(trade.realized_pnl for trade in self.trades if trade.status == TradeStatus.CLOSED)

    @property
    def total_mtm(self) -> float:
        """Total MTM (realized + unrealized)"""
        return self.total_realized_pnl + self.total_unrealized_pnl

    @property
    def open_trades_count(self) -> int:
        """Number of open trades"""
        return len([t for t in self.trades if t.status == TradeStatus.OPEN])

    @property
    def total_trades_count(self) -> int:
        """Total number of trades"""
        return len(self.trades)


# =====================================================
# 2. MTM EVENT SYSTEM
# =====================================================

@dataclass
class MTMEvent:
    """MTM tracking event"""
    event_type: MTMEventType
    trade_id: Optional[str] = None
    strategy_name: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class MTMObserver(ABC):
    """Abstract observer for MTM events"""

    @abstractmethod
    async def on_mtm_event(self, event: MTMEvent) -> None:
        """Handle MTM event"""
        pass


class MTMAlertManager(MTMObserver):
    """Manages MTM alerts and notifications"""

    def __init__(self):
        self.alert_history: List[MTMEvent] = []

    async def on_mtm_event(self, event: MTMEvent) -> None:
        """Handle MTM events and generate alerts"""
        self.alert_history.append(event)

        if event.event_type == MTMEventType.TRAILING_TRIGGERED:
            logger.warning(f"🔥 TRAILING STOP TRIGGERED: {event.data}")
        elif event.event_type == MTMEventType.STOP_LOSS_HIT:
            logger.error(f"💥 STOP LOSS HIT: {event.data}")
        elif event.event_type == MTMEventType.TARGET_ACHIEVED:
            logger.info(f"🎯 TARGET ACHIEVED: {event.data}")
        elif event.event_type == MTMEventType.STRATEGY_LIMIT_BREACHED:
            logger.critical(f"⚠️ STRATEGY LIMIT BREACHED: {event.data}")


class MTMRiskManager(MTMObserver):
    """Risk management based on MTM"""

    def __init__(self):
        self.risk_actions: List[str] = []

    async def on_mtm_event(self, event: MTMEvent) -> None:
        """Handle risk management actions"""
        if event.event_type == MTMEventType.STRATEGY_LIMIT_BREACHED:
            action = f"EMERGENCY: Stop all trades for strategy {event.strategy_name}"
            self.risk_actions.append(action)
            logger.critical(f"🚨 Risk Action: {action}")

        elif event.event_type == MTMEventType.STOP_LOSS_HIT:
            action = f"Close trade {event.trade_id} due to stop loss"
            self.risk_actions.append(action)
            logger.warning(f"⚠️ Risk Action: {action}")


# =====================================================
# 3. TRADE-WISE MTM TRAILING
# =====================================================

class TradeWiseMTMTrailer:
    """Handles individual trade MTM trailing"""

    def __init__(self, trailing_percentage: float = 0.3):
        """
        Initialize trade-wise MTM trailer

        Args:
            trailing_percentage: Percentage of profit to trail (0.3 = 30%)
        """
        self.trailing_percentage = trailing_percentage
        self.observers: List[MTMObserver] = []

    def subscribe(self, observer: MTMObserver) -> None:
        """Subscribe to MTM events"""
        self.observers.append(observer)

    async def _notify_observers(self, event: MTMEvent) -> None:
        """Notify all observers of MTM event"""
        for observer in self.observers:
            await observer.on_mtm_event(event)

    async def update_trade_price(self, trade: Trade, new_price: float) -> Dict[str, Any]:
        """
        Update trade with new price and check trailing conditions

        Args:
            trade: Trade object to update
            new_price: New market price

        Returns:
            Dict with update results and any triggered actions
        """
        old_price = trade.current_price
        trade.current_price = new_price
        current_pnl = trade.unrealized_pnl

        # Track max profit and loss
        if current_pnl > trade.max_profit:
            trade.max_profit = current_pnl
        if current_pnl < trade.max_loss:
            trade.max_loss = current_pnl

        actions = []

        # Calculate trailing stop
        if trade.max_profit > 0:
            # Only set trailing stop if we're in profit
            profit_to_protect = trade.max_profit * self.trailing_percentage

            if trade.trade_type == "BUY":
                # For long positions, trailing stop moves up
                new_trailing_stop = trade.entry_price + profit_to_protect
                if not trade.trailing_stop or new_trailing_stop > trade.trailing_stop:
                    trade.trailing_stop = new_trailing_stop
                    actions.append(f"Updated trailing stop to {new_trailing_stop:.2f}")

                # Check if trailing stop is hit
                if trade.trailing_stop and new_price <= trade.trailing_stop:
                    actions.append("TRAILING STOP HIT - CLOSE POSITION")
                    await self._notify_observers(MTMEvent(
                        event_type=MTMEventType.TRAILING_TRIGGERED,
                        trade_id=trade.trade_id,
                        data={
                            "symbol": trade.symbol,
                            "trailing_stop": trade.trailing_stop,
                            "current_price": new_price,
                            "protected_profit": profit_to_protect
                        }
                    ))

            else:  # SELL position
                # For short positions, trailing stop moves down
                new_trailing_stop = trade.entry_price - profit_to_protect
                if not trade.trailing_stop or new_trailing_stop < trade.trailing_stop:
                    trade.trailing_stop = new_trailing_stop
                    actions.append(f"Updated trailing stop to {new_trailing_stop:.2f}")

                # Check if trailing stop is hit
                if trade.trailing_stop and new_price >= trade.trailing_stop:
                    actions.append("TRAILING STOP HIT - CLOSE POSITION")
                    await self._notify_observers(MTMEvent(
                        event_type=MTMEventType.TRAILING_TRIGGERED,
                        trade_id=trade.trade_id,
                        data={
                            "symbol": trade.symbol,
                            "trailing_stop": trade.trailing_stop,
                            "current_price": new_price,
                            "protected_profit": profit_to_protect
                        }
                    ))

        # Check stop loss
        if trade.stop_loss:
            if ((trade.trade_type == "BUY" and new_price <= trade.stop_loss) or
                (trade.trade_type == "SELL" and new_price >= trade.stop_loss)):
                actions.append("STOP LOSS HIT - CLOSE POSITION")
                await self._notify_observers(MTMEvent(
                    event_type=MTMEventType.STOP_LOSS_HIT,
                    trade_id=trade.trade_id,
                    data={
                        "symbol": trade.symbol,
                        "stop_loss": trade.stop_loss,
                        "current_price": new_price,
                        "loss": current_pnl
                    }
                ))

        # Check target
        if trade.target:
            if ((trade.trade_type == "BUY" and new_price >= trade.target) or
                (trade.trade_type == "SELL" and new_price <= trade.target)):
                actions.append("TARGET ACHIEVED - CLOSE POSITION")
                await self._notify_observers(MTMEvent(
                    event_type=MTMEventType.TARGET_ACHIEVED,
                    trade_id=trade.trade_id,
                    data={
                        "symbol": trade.symbol,
                        "target": trade.target,
                        "current_price": new_price,
                        "profit": current_pnl
                    }
                ))

        # Notify price update
        await self._notify_observers(MTMEvent(
            event_type=MTMEventType.PRICE_UPDATE,
            trade_id=trade.trade_id,
            data={
                "symbol": trade.symbol,
                "old_price": old_price,
                "new_price": new_price,
                "pnl": current_pnl,
                "max_profit": trade.max_profit,
                "max_loss": trade.max_loss
            }
        ))

        return {
            "trade_id": trade.trade_id,
            "symbol": trade.symbol,
            "price_change": new_price - old_price,
            "current_pnl": current_pnl,
            "max_profit": trade.max_profit,
            "max_loss": trade.max_loss,
            "trailing_stop": trade.trailing_stop,
            "actions": actions
        }


# =====================================================
# 4. STRATEGY-LEVEL MTM TRAILING
# =====================================================

class StrategyLevelMTMTrailer:
    """Manages strategy-level MTM trailing and risk management"""

    def __init__(self):
        self.strategies: Dict[str, StrategyMTM] = {}
        self.observers: List[MTMObserver] = []
        self.trade_trailer = TradeWiseMTMTrailer()

    def subscribe(self, observer: MTMObserver) -> None:
        """Subscribe to MTM events"""
        self.observers.append(observer)
        self.trade_trailer.subscribe(observer)

    async def _notify_observers(self, event: MTMEvent) -> None:
        """Notify all observers of MTM event"""
        for observer in self.observers:
            await observer.on_mtm_event(event)

    def create_strategy(self, strategy_name: str, max_drawdown_limit: float = -10000.0,
                       trailing_percentage: float = 0.5) -> StrategyMTM:
        """
        Create a new strategy for MTM tracking

        Args:
            strategy_name: Name of the strategy
            max_drawdown_limit: Maximum allowed loss for the strategy
            trailing_percentage: Percentage of peak profit to trail

        Returns:
            StrategyMTM object
        """
        strategy = StrategyMTM(
            strategy_name=strategy_name,
            max_drawdown_limit=max_drawdown_limit,
            trailing_percentage=trailing_percentage
        )
        self.strategies[strategy_name] = strategy
        logger.info(f"📈 Created strategy: {strategy_name} with max drawdown: {max_drawdown_limit}")
        return strategy

    def add_trade(self, strategy_name: str, symbol: str, quantity: int,
                  entry_price: float, trade_type: str, stop_loss: Optional[float] = None,
                  target: Optional[float] = None) -> Trade:
        """
        Add a new trade to a strategy

        Args:
            strategy_name: Name of the strategy
            symbol: Trading symbol
            quantity: Number of shares/contracts
            entry_price: Entry price
            trade_type: "BUY" or "SELL"
            stop_loss: Optional stop loss level
            target: Optional target level

        Returns:
            Trade object
        """
        if strategy_name not in self.strategies:
            self.create_strategy(strategy_name)

        trade = Trade(
            trade_id=str(uuid.uuid4())[:8],
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            trade_type=trade_type,
            strategy_name=strategy_name,
            current_price=entry_price,
            stop_loss=stop_loss,
            target=target
        )

        self.strategies[strategy_name].trades.append(trade)
        logger.info(f"📊 Added trade {trade.trade_id}: {trade_type} {quantity} {symbol} @ {entry_price}")
        return trade

    async def update_market_prices(self, price_updates: Dict[str, float]) -> Dict[str, Any]:
        """
        Update market prices for all symbols and recalculate MTM

        Args:
            price_updates: Dict of symbol -> new_price

        Returns:
            Dict with strategy updates and triggered actions
        """
        strategy_updates = {}

        for strategy_name, strategy in self.strategies.items():
            if not strategy.is_active:
                continue

            strategy_actions = []
            old_mtm = strategy.total_mtm

            # Update individual trades
            for trade in strategy.trades:
                if trade.status == TradeStatus.OPEN and trade.symbol in price_updates:
                    new_price = price_updates[trade.symbol]
                    trade_update = await self.trade_trailer.update_trade_price(trade, new_price)

                    # Check if trade needs to be closed based on trailing/stops
                    if any("CLOSE POSITION" in action for action in trade_update["actions"]):
                        trade.status = TradeStatus.CLOSED
                        trade.exit_price = new_price
                        strategy_actions.append(f"Closed trade {trade.trade_id}")

            # Calculate new strategy MTM
            new_mtm = strategy.total_mtm
            mtm_change = new_mtm - old_mtm

            # Update peak MTM and trailing stop
            if new_mtm > strategy.peak_mtm:
                strategy.peak_mtm = new_mtm
                # Update trailing stop
                if strategy.peak_mtm > 0:
                    strategy.current_trailing_stop = (
                        strategy.peak_mtm * (1 - strategy.trailing_percentage)
                    )
                    strategy_actions.append(f"Updated strategy trailing stop to {strategy.current_trailing_stop:.2f}")

            # Check strategy-level trailing stop
            if (strategy.current_trailing_stop > 0 and
                new_mtm <= strategy.current_trailing_stop):
                strategy.is_active = False
                strategy_actions.append("STRATEGY TRAILING STOP HIT - CLOSE ALL POSITIONS")

                await self._notify_observers(MTMEvent(
                    event_type=MTMEventType.TRAILING_TRIGGERED,
                    strategy_name=strategy_name,
                    data={
                        "current_mtm": new_mtm,
                        "trailing_stop": strategy.current_trailing_stop,
                        "peak_mtm": strategy.peak_mtm,
                        "open_trades": strategy.open_trades_count
                    }
                ))

            # Check maximum drawdown limit
            if new_mtm <= strategy.max_drawdown_limit:
                strategy.is_active = False
                strategy_actions.append("MAX DRAWDOWN BREACHED - EMERGENCY STOP")

                await self._notify_observers(MTMEvent(
                    event_type=MTMEventType.STRATEGY_LIMIT_BREACHED,
                    strategy_name=strategy_name,
                    data={
                        "current_mtm": new_mtm,
                        "max_drawdown_limit": strategy.max_drawdown_limit,
                        "breach_amount": new_mtm - strategy.max_drawdown_limit,
                        "open_trades": strategy.open_trades_count
                    }
                ))

            strategy_updates[strategy_name] = {
                "old_mtm": old_mtm,
                "new_mtm": new_mtm,
                "mtm_change": mtm_change,
                "peak_mtm": strategy.peak_mtm,
                "trailing_stop": strategy.current_trailing_stop,
                "open_trades": strategy.open_trades_count,
                "total_trades": strategy.total_trades_count,
                "is_active": strategy.is_active,
                "actions": strategy_actions
            }

        return strategy_updates

    def get_strategy_summary(self, strategy_name: str) -> Dict[str, Any]:
        """Get comprehensive strategy summary"""
        if strategy_name not in self.strategies:
            return {"error": "Strategy not found"}

        strategy = self.strategies[strategy_name]

        return {
            "strategy_name": strategy_name,
            "total_mtm": strategy.total_mtm,
            "realized_pnl": strategy.total_realized_pnl,
            "unrealized_pnl": strategy.total_unrealized_pnl,
            "peak_mtm": strategy.peak_mtm,
            "current_trailing_stop": strategy.current_trailing_stop,
            "max_drawdown_limit": strategy.max_drawdown_limit,
            "open_trades": strategy.open_trades_count,
            "total_trades": strategy.total_trades_count,
            "is_active": strategy.is_active,
            "created_at": strategy.created_at.isoformat(),
            "trades": [
                {
                    "trade_id": trade.trade_id,
                    "symbol": trade.symbol,
                    "quantity": trade.quantity,
                    "entry_price": trade.entry_price,
                    "current_price": trade.current_price,
                    "pnl": trade.current_pnl,
                    "status": trade.status.value,
                    "trailing_stop": trade.trailing_stop
                }
                for trade in strategy.trades
            ]
        }

    def get_all_strategies_summary(self) -> Dict[str, Any]:
        """Get summary of all strategies"""
        return {
            "total_strategies": len(self.strategies),
            "active_strategies": len([s for s in self.strategies.values() if s.is_active]),
            "total_mtm": sum(s.total_mtm for s in self.strategies.values()),
            "total_open_trades": sum(s.open_trades_count for s in self.strategies.values()),
            "strategies": {name: self.get_strategy_summary(name)
                         for name in self.strategies.keys()}
        }


# =====================================================
# 5. COMPREHENSIVE DEMO FUNCTION
# =====================================================

async def demonstrate_mtm_trailing():
    """
    🎯 Comprehensive MTM Trailing System Demo

    Demonstrates both strategy-level and trade-wise MTM trailing
    """
    print("🎯 ADVANCED MTM TRAILING SYSTEM DEMO")
    print("=" * 80)

    # Create MTM tracking system
    mtm_tracker = StrategyLevelMTMTrailer()

    # Create observers
    alert_manager = MTMAlertManager()
    risk_manager = MTMRiskManager()

    # Subscribe observers
    mtm_tracker.subscribe(alert_manager)
    mtm_tracker.subscribe(risk_manager)

    print("✅ MTM Tracking System Initialized")

    # Demo 1: Create strategies and add trades
    print("\n📈 Demo 1: Strategy Creation and Trade Addition")
    print("-" * 60)

    # Create scalping strategy
    scalping_strategy = mtm_tracker.create_strategy(
        "Scalping_NIFTY",
        max_drawdown_limit=-5000.0,
        trailing_percentage=0.3
    )

    # Create swing trading strategy
    swing_strategy = mtm_tracker.create_strategy(
        "Swing_Banking",
        max_drawdown_limit=-15000.0,
        trailing_percentage=0.5
    )

    # Add trades to scalping strategy
    trade1 = mtm_tracker.add_trade("Scalping_NIFTY", "NIFTY", 50, 19500.0, "BUY",
                                  stop_loss=19400.0, target=19600.0)
    trade2 = mtm_tracker.add_trade("Scalping_NIFTY", "BANKNIFTY", 25, 44000.0, "BUY",
                                  stop_loss=43800.0, target=44200.0)

    # Add trades to swing strategy
    trade3 = mtm_tracker.add_trade("Swing_Banking", "HDFCBANK", 100, 1600.0, "BUY",
                                  stop_loss=1520.0, target=1720.0)
    trade4 = mtm_tracker.add_trade("Swing_Banking", "ICICIBANK", 50, 1200.0, "BUY",
                                  stop_loss=1140.0, target=1300.0)

    print(f"📊 Added 4 trades across 2 strategies")

    # Demo 2: Simulate price movements and MTM tracking
    print("\n📊 Demo 2: Price Updates and MTM Tracking")
    print("-" * 60)

    # Simulate price updates over time
    price_scenarios = [
        # Scenario 1: Initial profits
        {"NIFTY": 19550.0, "BANKNIFTY": 44100.0, "HDFCBANK": 1650.0, "ICICIBANK": 1220.0},
        # Scenario 2: More profits (trailing stops should update)
        {"NIFTY": 19580.0, "BANKNIFTY": 44150.0, "HDFCBANK": 1680.0, "ICICIBANK": 1250.0},
        # Scenario 3: Pullback (should trigger some trailing stops)
        {"NIFTY": 19520.0, "BANKNIFTY": 44050.0, "HDFCBANK": 1640.0, "ICICIBANK": 1210.0},
        # Scenario 4: Recovery
        {"NIFTY": 19590.0, "BANKNIFTY": 44200.0, "HDFCBANK": 1700.0, "ICICIBANK": 1270.0},
        # Scenario 5: Major drawdown
        {"NIFTY": 19300.0, "BANKNIFTY": 43500.0, "HDFCBANK": 1450.0, "ICICIBANK": 1100.0}
    ]

    for i, prices in enumerate(price_scenarios, 1):
        print(f"\n⏰ Time {i}: Price Update")
        print(f"   Prices: {prices}")

        # Update prices and get strategy updates
        updates = await mtm_tracker.update_market_prices(prices)

        for strategy_name, update in updates.items():
            print(f"   📈 {strategy_name}:")
            print(f"      MTM: {update['old_mtm']:.2f} → {update['new_mtm']:.2f} "
                  f"(Change: {update['mtm_change']:.2f})")
            print(f"      Peak MTM: {update['peak_mtm']:.2f}")
            print(f"      Trailing Stop: {update['trailing_stop']:.2f}")
            print(f"      Open Trades: {update['open_trades']}")
            print(f"      Active: {update['is_active']}")

            if update['actions']:
                print(f"      🔥 Actions: {update['actions']}")

        # Small delay to simulate real-time
        await asyncio.sleep(0.1)

    # Demo 3: Final summary
    print("\n📋 Demo 3: Final Strategy Summary")
    print("-" * 60)

    all_summary = mtm_tracker.get_all_strategies_summary()
    print(f"📊 Total Strategies: {all_summary['total_strategies']}")
    print(f"📊 Active Strategies: {all_summary['active_strategies']}")
    print(f"💰 Total MTM: {all_summary['total_mtm']:.2f}")
    print(f"📈 Total Open Trades: {all_summary['total_open_trades']}")

    for strategy_name in mtm_tracker.strategies.keys():
        summary = mtm_tracker.get_strategy_summary(strategy_name)
        print(f"\n🎯 {strategy_name}:")
        print(f"   Total MTM: {summary['total_mtm']:.2f}")
        print(f"   Realized P&L: {summary['realized_pnl']:.2f}")
        print(f"   Unrealized P&L: {summary['unrealized_pnl']:.2f}")
        print(f"   Peak MTM: {summary['peak_mtm']:.2f}")
        print(f"   Status: {'✅ Active' if summary['is_active'] else '🛑 Stopped'}")

        for trade in summary['trades']:
            status_emoji = "🟢" if trade['status'] == 'open' else "🔴"
            print(f"     {status_emoji} {trade['symbol']}: P&L {trade['pnl']:.2f}")

    # Demo 4: Risk Management Summary
    print("\n⚠️ Demo 4: Risk Management Actions")
    print("-" * 60)

    print(f"📨 Total Alerts Generated: {len(alert_manager.alert_history)}")
    print(f"🚨 Risk Actions Taken: {len(risk_manager.risk_actions)}")

    if risk_manager.risk_actions:
        print("\n🔥 Risk Actions:")
        for action in risk_manager.risk_actions:
            print(f"   - {action}")

    print("\n🎉 MTM TRAILING SYSTEM DEMO COMPLETED!")
    print("\n💡 Key Features Demonstrated:")
    print("  ✓ Strategy-level MTM tracking with trailing stops")
    print("  ✓ Trade-wise profit protection")
    print("  ✓ Real-time risk management")
    print("  ✓ Event-driven alert system")
    print("  ✓ Automatic position closure on limits")
    print("  ✓ Comprehensive reporting and monitoring")


if __name__ == "__main__":
    asyncio.run(demonstrate_mtm_trailing())
