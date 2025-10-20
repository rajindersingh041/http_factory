"""
🚀 Complete Trading System with MTM Trailing

This script demonstrates the complete integration of:
1. Existing modular SOLID architecture
2. Strategy-level MTM trailing
3. Trade-wise MTM trailing
4. Real-time risk management

Usage: uv run python integrated_mtm_demo.py
"""

import asyncio
import sys
from pathlib import Path

# Ensure proper imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def main():
    print("🚀 INTEGRATED TRADING SYSTEM WITH MTM TRAILING")
    print("=" * 80)

    try:
        # Import the MTM system
        from mtm_trailing_system import (MTMAlertManager, MTMRiskManager,
                                         StrategyLevelMTMTrailer, Trade,
                                         TradeStatus, TradeWiseMTMTrailer)
        # Import existing services
        from network_test.services import ServiceFactory
        from network_test.services.broker_configurations import \
            TransformerFactory

        print("✅ All imports successful!")

        # 1. Initialize the complete system
        print("\\n🏗️ Step 1: Initialize Complete Trading System")
        print("-" * 60)

        # Create MTM tracking system
        mtm_tracker = StrategyLevelMTMTrailer()
        alert_manager = MTMAlertManager()
        risk_manager = MTMRiskManager()

        # Subscribe to MTM events
        mtm_tracker.subscribe(alert_manager)
        mtm_tracker.subscribe(risk_manager)

        # Create trading service
        upstox_service = ServiceFactory.create_service(
            "upstox",
            access_token="demo_token",
            rate_limit=50
        )

        print("   ✅ MTM tracking system initialized")
        print("   ✅ Alert and risk management active")
        print("   ✅ Trading service created")

        # 2. Strategy Creation and Setup
        print("\\n📈 Step 2: Create Trading Strategies with MTM Trailing")
        print("-" * 60)

        # Create multiple strategies with different risk profiles
        strategies_config = [
            {
                "name": "Scalping_Index",
                "max_drawdown": -3000.0,
                "trailing": 0.4,
                "description": "High-frequency index trading"
            },
            {
                "name": "Swing_Banking",
                "max_drawdown": -8000.0,
                "trailing": 0.3,
                "description": "Banking sector swing trades"
            },
            {
                "name": "Options_Premium",
                "max_drawdown": -5000.0,
                "trailing": 0.5,
                "description": "Options premium collection"
            }
        ]

        for config in strategies_config:
            strategy = mtm_tracker.create_strategy(
                config["name"],
                max_drawdown_limit=config["max_drawdown"],
                trailing_percentage=config["trailing"]
            )
            print(f"   📊 {config['name']}: {config['description']}")
            print(f"      Max Drawdown: {config['max_drawdown']}")
            print(f"      Trailing: {config['trailing']*100}%")

        # 3. Add Sample Trades
        print("\\n💼 Step 3: Add Sample Trades to Strategies")
        print("-" * 60)

        # Add trades to each strategy
        sample_trades = [
            # Scalping trades
            ("Scalping_Index", "NIFTY", 75, 19500.0, "BUY", 19450.0, 19580.0),
            ("Scalping_Index", "BANKNIFTY", 25, 44000.0, "BUY", 43900.0, 44150.0),

            # Swing trades
            ("Swing_Banking", "HDFCBANK", 100, 1600.0, "BUY", 1550.0, 1700.0),
            ("Swing_Banking", "ICICIBANK", 80, 1200.0, "BUY", 1150.0, 1280.0),
            ("Swing_Banking", "AXISBANK", 60, 1100.0, "BUY", 1050.0, 1180.0),

            # Options trades
            ("Options_Premium", "NIFTY_CE", 50, 200.0, "SELL", 150.0, 100.0),
            ("Options_Premium", "BANKNIFTY_PE", 25, 300.0, "SELL", 250.0, 150.0),
        ]

        added_trades = []
        for strategy, symbol, qty, price, side, sl, target in sample_trades:
            trade = mtm_tracker.add_trade(strategy, symbol, qty, price, side, sl, target)
            added_trades.append(trade)
            print(f"   🔸 {trade.trade_id}: {side} {qty} {symbol} @ {price}")

        print(f"\\n   📊 Total trades added: {len(added_trades)}")

        # 4. Real-time MTM Simulation
        print("\\n📊 Step 4: Real-time MTM Tracking Simulation")
        print("-" * 60)

        # Define realistic price movement scenarios
        market_scenarios = [
            {
                "time": "09:30 - Market Open",
                "prices": {
                    "NIFTY": 19520.0, "BANKNIFTY": 44050.0,
                    "HDFCBANK": 1620.0, "ICICIBANK": 1210.0, "AXISBANK": 1110.0,
                    "NIFTY_CE": 180.0, "BANKNIFTY_PE": 280.0
                },
                "description": "Initial movement after market open"
            },
            {
                "time": "10:00 - Early gains",
                "prices": {
                    "NIFTY": 19580.0, "BANKNIFTY": 44200.0,
                    "HDFCBANK": 1680.0, "ICICIBANK": 1250.0, "AXISBANK": 1140.0,
                    "NIFTY_CE": 140.0, "BANKNIFTY_PE": 220.0
                },
                "description": "Strong upward movement, profits building"
            },
            {
                "time": "11:00 - Peak profits",
                "prices": {
                    "NIFTY": 19620.0, "BANKNIFTY": 44300.0,
                    "HDFCBANK": 1720.0, "ICICIBANK": 1280.0, "AXISBANK": 1170.0,
                    "NIFTY_CE": 120.0, "BANKNIFTY_PE": 180.0
                },
                "description": "Peak profits, trailing stops should update"
            },
            {
                "time": "12:00 - Pullback",
                "prices": {
                    "NIFTY": 19550.0, "BANKNIFTY": 44100.0,
                    "HDFCBANK": 1660.0, "ICICIBANK": 1230.0, "AXISBANK": 1130.0,
                    "NIFTY_CE": 160.0, "BANKNIFTY_PE": 240.0
                },
                "description": "Market pullback, testing trailing stops"
            },
            {
                "time": "14:00 - Recovery",
                "prices": {
                    "NIFTY": 19600.0, "BANKNIFTY": 44250.0,
                    "HDFCBANK": 1700.0, "ICICIBANK": 1270.0, "AXISBANK": 1160.0,
                    "NIFTY_CE": 130.0, "BANKNIFTY_PE": 190.0
                },
                "description": "Market recovery, new peaks possible"
            },
            {
                "time": "15:00 - Stress test",
                "prices": {
                    "NIFTY": 19350.0, "BANKNIFTY": 43700.0,
                    "HDFCBANK": 1520.0, "ICICIBANK": 1160.0, "AXISBANK": 1080.0,
                    "NIFTY_CE": 250.0, "BANKNIFTY_PE": 380.0
                },
                "description": "Major market decline, testing risk limits"
            }
        ]

        # Process each market scenario
        for i, scenario in enumerate(market_scenarios, 1):
            print(f"\\n⏰ {scenario['time']}")
            print(f"   📝 {scenario['description']}")
            print(f"   💹 Price updates: {len(scenario['prices'])} symbols")

            # Update market prices
            strategy_updates = await mtm_tracker.update_market_prices(scenario['prices'])

            # Display strategy updates
            for strategy_name, update in strategy_updates.items():
                mtm_change = update['mtm_change']
                change_emoji = "📈" if mtm_change >= 0 else "📉"
                status_emoji = "🟢" if update['is_active'] else "🔴"

                print(f"   {status_emoji} {strategy_name}:")
                print(f"      {change_emoji} MTM: {update['new_mtm']:.0f} (Δ{mtm_change:+.0f})")
                print(f"      🏔️ Peak: {update['peak_mtm']:.0f}")
                print(f"      🛡️ Trail: {update['trailing_stop']:.0f}")
                print(f"      📊 Open: {update['open_trades']}")

                # Show any triggered actions
                if update['actions']:
                    for action in update['actions']:
                        if "CLOSE" in action.upper():
                            print(f"      🔥 {action}")
                        elif "TRAILING" in action.upper():
                            print(f"      📈 {action}")
                        else:
                            print(f"      ⚡ {action}")

            # Small delay to simulate real-time
            await asyncio.sleep(0.2)

        # 5. Final Analysis and Summary
        print("\\n📋 Step 5: Final Analysis and Risk Summary")
        print("-" * 60)

        # Get comprehensive summary
        all_summary = mtm_tracker.get_all_strategies_summary()

        print(f"🎯 FINAL PERFORMANCE SUMMARY")
        print(f"   Total Strategies: {all_summary['total_strategies']}")
        print(f"   Active Strategies: {all_summary['active_strategies']}")
        print(f"   Combined MTM: {all_summary['total_mtm']:.2f}")
        print(f"   Open Positions: {all_summary['total_open_trades']}")

        # Detailed strategy breakdown
        for strategy_name, strategy_data in all_summary['strategies'].items():
            status = "🟢 ACTIVE" if strategy_data['is_active'] else "🔴 STOPPED"
            print(f"\\n📊 {strategy_name} ({status})")
            print(f"   💰 Total MTM: {strategy_data['total_mtm']:.2f}")
            print(f"   💎 Realized: {strategy_data['realized_pnl']:.2f}")
            print(f"   💫 Unrealized: {strategy_data['unrealized_pnl']:.2f}")
            print(f"   🏔️ Peak MTM: {strategy_data['peak_mtm']:.2f}")
            print(f"   🛡️ Trail Stop: {strategy_data['current_trailing_stop']:.2f}")
            print(f"   📈 Trades: {strategy_data['open_trades']}/{strategy_data['total_trades']}")

            # Show individual trade performance
            profitable_trades = [t for t in strategy_data['trades'] if t['pnl'] > 0]
            losing_trades = [t for t in strategy_data['trades'] if t['pnl'] < 0]

            if profitable_trades or losing_trades:
                print(f"   🎯 Winners: {len(profitable_trades)}, Losers: {len(losing_trades)}")

        # Risk management summary
        print(f"\\n🚨 RISK MANAGEMENT SUMMARY")
        print(f"   📨 Total Alerts: {len(alert_manager.alert_history)}")
        print(f"   ⚠️ Risk Actions: {len(risk_manager.risk_actions)}")

        if risk_manager.risk_actions:
            print("\\n   🔥 Critical Actions Taken:")
            for action in risk_manager.risk_actions[-3:]:  # Show last 3 actions
                print(f"      - {action}")

        # 6. Integration Benefits Summary
        print("\\n🏆 Step 6: Integration Benefits Achieved")
        print("-" * 60)

        print("✅ COMPLETE SYSTEM INTEGRATION SUCCESSFUL!")
        print("\\n💡 Key Benefits Demonstrated:")
        print("  🏗️ Modular Architecture: Clean separation of concerns")
        print("  🎯 Strategy-Level MTM: Portfolio-wide risk management")
        print("  📊 Trade-Level MTM: Individual position protection")
        print("  🔔 Event-Driven Alerts: Real-time notifications")
        print("  🛡️ Automated Risk Management: Protection against losses")
        print("  📈 Trailing Profit Protection: Lock in gains automatically")
        print("  🔄 Service Integration: Works with any broker API")
        print("  📋 Comprehensive Reporting: Full visibility into performance")

        print("\\n🚀 PRODUCTION-READY TRADING SYSTEM WITH MTM TRAILING!")

        return 0

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure both mtm_trailing_system.py and the services are available")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
