"""
XTS Service Usage Examples

This demonstrates how to use the XTS (Symphony Fintech) service
with both Interactive API and Market Data API endpoints.
"""

import asyncio

from network_test.services import XTSService


async def demo_xts_authentication():
    """Demo: XTS authentication for both APIs"""
    print("🏛️ DEMO: XTS Authentication\n")

    # XTS configuration
    xts_config = {
        "interactive_base_url": "https://developers.symphonyfintech.in/interactive/",
        "market_base_url": "https://developers.symphonyfintech.in/marketdata/",
        "user_id": "your_user_id",
        "password": "your_password",
        "public_key": "your_public_key",
        "private_key": "your_private_key",
        "source": "WebAPI",
        "rate_limit": 10,
        "timeout": 30
    }

    async with XTSService(config=xts_config) as xts:
        print("✅ XTS Service initialized")
        print(f"   Interactive base URL: {xts.config.get('interactive_base_url')}")
        print(f"   Market Data base URL: {xts.config.get('market_base_url')}")
        print(f"   Available endpoints: {len(xts.list_endpoints())} total")

        # List some key endpoints
        interactive_endpoints = [k for k in xts.list_endpoints().keys() if not k.startswith('market.')]
        market_endpoints = [k for k in xts.list_endpoints().keys() if k.startswith('market.')]

        print(f"   Interactive API endpoints: {len(interactive_endpoints)}")
        print(f"   Market Data API endpoints: {len(market_endpoints)}")

        # Show login process (would work with real credentials)
        try:
            # Note: These would fail with dummy credentials, but shows the process
            print("\n🔐 Authentication Process:")
            print("   1. Login to Interactive API...")
            # interactive_response = await xts.login_interactive()
            print("   2. Login to Market Data API...")
            # market_response = await xts.login_market()
            print("   ℹ️ Would authenticate with real credentials")

        except Exception:
            print("   ⚠️ Expected auth error with dummy credentials")


async def demo_interactive_api_usage():
    """Demo: Interactive API usage patterns"""
    print("\n📊 DEMO: Interactive API Usage\n")

    xts_config = {
        "interactive_base_url": "https://developers.symphonyfintech.in/interactive/",
        "user_id": "demo_user",
        "password": "demo_pass",
        "public_key": "demo_public",
        "private_key": "demo_private",
        "source": "WebAPI"
    }

    async with XTSService(config=xts_config) as xts:

        # Show Interactive API endpoints
        interactive_endpoints = {
            k: v for k, v in xts.list_endpoints().items()
            if not k.startswith('market.')
        }

        print("📋 Interactive API Endpoints:")
        for category in ['user', 'order', 'bracket', 'portfolio']:
            category_endpoints = {k: v for k, v in interactive_endpoints.items() if k.startswith(category)}
            if category_endpoints:
                print(f"\n   {category.upper()} Operations:")
                for name, desc in category_endpoints.items():
                    print(f"     • {name}: {desc}")

        # Example order placement (would work after authentication)
        print("\n💼 Example Order Placement:")
        order_data = {
            "exchangeSegment": "NSECM",
            "exchangeInstrumentID": 26000,  # RELIANCE
            "productType": "MIS",
            "orderType": "LIMIT",
            "orderSide": "BUY",
            "timeInForce": "DAY",
            "disclosedQuantity": 0,
            "orderQuantity": 1,
            "limitPrice": 2500.0,
            "stopPrice": 0
        }

        print(f"   Order details: {order_data}")
        print("   ℹ️ Would place order with: await xts.place_order(**order_data)")

        # Example using direct endpoint call
        print("\n📈 Example Portfolio Query:")
        print("   ℹ️ Would get positions with: await xts.call_endpoint('portfolio.positions')")
        print("   ℹ️ Would get holdings with: await xts.call_endpoint('portfolio.holdings')")


async def demo_market_data_api_usage():
    """Demo: Market Data API usage patterns"""
    print("\n📈 DEMO: Market Data API Usage\n")

    xts_config = {
        "market_base_url": "https://developers.symphonyfintech.in/marketdata/",
        "user_id": "demo_user",
        "password": "demo_pass",
        "public_key": "demo_public",
        "private_key": "demo_private",
        "source": "WebAPI"
    }

    async with XTSService(config=xts_config) as xts:

        # Show Market Data API endpoints
        market_endpoints = {
            k: v for k, v in xts.list_endpoints().items()
            if k.startswith('market.')
        }

        print("📋 Market Data API Endpoints:")
        categories = {
            'market.instruments': 'Instrument Operations',
            'market.search': 'Search Operations',
            'market.config': 'Configuration'
        }

        for prefix, category_name in categories.items():
            category_endpoints = {k: v for k, v in market_endpoints.items() if k.startswith(prefix)}
            if category_endpoints:
                print(f"\n   {category_name}:")
                for name, desc in category_endpoints.items():
                    short_name = name.replace('market.', '')
                    print(f"     • {short_name}: {desc}")

        # Example quotes usage
        print("\n💹 Example Market Data Queries:")
        print("   ℹ️ Get quotes: await xts.get_quotes('26000,26009')")  # RELIANCE, TCS
        print("   ℹ️ Search instruments: await xts.search_instruments('RELIANCE')")
        print("   ℹ️ Get OHLC: await xts.call_endpoint('market.instruments.ohlc', query_params={'instruments': '26000'})")
        print("   ℹ️ Get master data: await xts.call_endpoint('market.instruments.master')")


async def demo_dual_api_workflow():
    """Demo: Using both APIs in a complete workflow"""
    print("\n🔄 DEMO: Complete Trading Workflow\n")

    xts_config = {
        "interactive_base_url": "https://developers.symphonyfintech.in/interactive/",
        "market_base_url": "https://developers.symphonyfintech.in/marketdata/",
        "user_id": "demo_user",
        "password": "demo_pass",
        "public_key": "demo_public",
        "private_key": "demo_private",
        "source": "WebAPI",
        "rate_limit": 10
    }

    async with XTSService(config=xts_config) as _:
        print("🔗 Complete Trading Workflow Example:")

        workflow_steps = [
            "1. 🔐 Login to both APIs",
            "   • await xts.login_interactive()",
            "   • await xts.login_market()",
            "",
            "2. 📊 Get market data",
            "   • quotes = await xts.get_quotes('26000')  # RELIANCE quotes",
            "   • ohlc = await xts.call_endpoint('market.instruments.ohlc', query_params={'instruments': '26000'})",
            "",
            "3. 📈 Check current positions",
            "   • positions = await xts.call_endpoint('portfolio.positions')",
            "   • balance = await xts.call_endpoint('user.balance')",
            "",
            "4. 💼 Place order based on analysis",
            "   • order_response = await xts.place_order(",
            "       exchangeSegment='NSECM',",
            "       exchangeInstrumentID=26000,",
            "       productType='MIS',",
            "       orderType='LIMIT',",
            "       orderSide='BUY',",
            "       timeInForce='DAY',",
            "       disclosedQuantity=0,",
            "       orderQuantity=1,",
            "       limitPrice=2500.0",
            "   )",
            "",
            "5. 📋 Monitor order status",
            "   • orders = await xts.call_endpoint('orders')",
            "   • trades = await xts.call_endpoint('trades')",
            "",
            "6. 🚪 Logout when done",
            "   • await xts.logout_interactive()",
            "   • await xts.logout_market()"
        ]

        for step in workflow_steps:
            print(f"   {step}")


async def demo_xts_endpoint_categories():
    """Demo: Show all XTS endpoint categories"""
    print("\n📚 DEMO: XTS Endpoint Categories\n")

    async with XTSService() as xts:
        all_endpoints = xts.list_endpoints()

        # Categorize endpoints
        categories = {
            "Authentication": [],
            "User Management": [],
            "Order Management": [],
            "Portfolio & Positions": [],
            "Market Data": [],
            "Instruments": [],
            "Search": []
        }

        for name, desc in all_endpoints.items():
            if any(auth_word in name for auth_word in ['login', 'logout']):
                categories["Authentication"].append((name, desc))
            elif name.startswith('user.'):
                categories["User Management"].append((name, desc))
            elif any(order_word in name for order_word in ['order', 'bracket', 'trade']):
                categories["Order Management"].append((name, desc))
            elif name.startswith('portfolio.') or name.startswith('dealer.'):
                categories["Portfolio & Positions"].append((name, desc))
            elif name.startswith('market.instruments'):
                categories["Instruments"].append((name, desc))
            elif name.startswith('market.search'):
                categories["Search"].append((name, desc))
            elif name.startswith('market.'):
                categories["Market Data"].append((name, desc))

        # Display categories
        for category, endpoints in categories.items():
            if endpoints:
                print(f"📂 {category} ({len(endpoints)} endpoints):")
                for name, desc in sorted(endpoints)[:5]:  # Show first 5
                    short_name = name.replace('market.', '').replace('instruments.', '')
                    print(f"   • {short_name}: {desc}")
                if len(endpoints) > 5:
                    print(f"   ... and {len(endpoints) - 5} more")
                print()


async def main():
    """Run all XTS demos"""
    await demo_xts_authentication()
    await demo_interactive_api_usage()
    await demo_market_data_api_usage()
    await demo_dual_api_workflow()
    await demo_xts_endpoint_categories()

    print("🎉 All XTS service demos completed!")
    print("\n📋 XTS Service Summary:")
    print("   ✅ Dual API support (Interactive + Market Data)")
    print("   ✅ Comprehensive order management (regular, bracket, cover)")
    print("   ✅ Real-time market data and quotes")
    print("   ✅ Portfolio and position management")
    print("   ✅ Instrument search and master data")
    print("   ✅ Separate authentication for each API")
    print("   ✅ All standard service features (rate limiting, caching, retries)")


if __name__ == "__main__":
    asyncio.run(main())
