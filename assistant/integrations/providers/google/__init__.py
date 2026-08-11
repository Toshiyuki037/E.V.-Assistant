"""
E.V.I.E. - Google Integration Provider

Created: August 10, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Package entry point for E.V.I.E.'s Phase 9 Google integrations.

Architecture:
    The provider registration function is exported here so the central
    Phase 9 integration registry can load Google's capabilities without
    depending on individual implementation modules.

Capabilities:
    - Google OAuth / identity
    - Gmail search/read when Gmail is available
    - Google Calendar read when Calendar is available
    - Google Contacts / People search
"""

from .provider import (
    load_google_provider,
)


__all__ = [
    "load_google_provider",
]