"""
Compatibility module.

Settings, Notifications, and Insights are now rendered inside the main
application window by desktop_app.panels.
"""

from .panels import (
    InsightsPanel,
    NotificationsPanel,
    SettingsPanel,
)

__all__ = [
    "InsightsPanel",
    "NotificationsPanel",
    "SettingsPanel",
]
