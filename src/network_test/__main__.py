"""
Entry point for running the network_test module with uv
"""
import asyncio
import sys
from pathlib import Path

# Ensure proper module resolution
sys.path.insert(0, str(Path(__file__).parent.parent))

from network_test.main import main

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
