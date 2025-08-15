#!/usr/bin/env python3
"""
Entry point for excalidraw-mcp-server when run as a module.
"""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())