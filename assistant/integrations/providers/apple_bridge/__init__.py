"""
E.V.I.E. - Apple Bridge Provider

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Package entry point for the Phase 9H Apple device bridge.
"""

from .provider import (
    load_apple_bridge_provider,
)


__all__ = [
    "load_apple_bridge_provider",
]