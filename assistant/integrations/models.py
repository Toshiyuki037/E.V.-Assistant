"""
E.V.I.E. - Integration Models

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Shared Phase 9 data structures.

These models normalize provider-specific information so the rest of
E.V.I.E. does not need to know whether an object came from Google,
Microsoft, Apple, Spotify, Schwab, or another provider.
"""

from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import Any


# ---------------------------------------------------------------------------
# Person
# ---------------------------------------------------------------------------

@dataclass
class Person:
    id: str

    display_name: str

    emails: list[str] = field(
        default_factory=list
    )

    phone_numbers: list[str] = field(
        default_factory=list
    )

    provider_ids: dict[str, str] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------

@dataclass
class Message:
    id: str

    provider: str

    account_id: str

    sender: str = ""

    recipients: list[str] = field(
        default_factory=list
    )

    subject: str = ""

    body: str = ""

    timestamp: str = ""

    conversation_id: str = ""

    attachments: list[dict[str, Any]] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Calendar Event
# ---------------------------------------------------------------------------

@dataclass
class Event:
    id: str

    provider: str

    account_id: str

    title: str

    start_time: str

    end_time: str

    location: str = ""

    attendees: list[str] = field(
        default_factory=list
    )

    description: str = ""

    calendar_name: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    id: str

    provider: str

    account_id: str

    title: str

    due_time: str = ""

    completed: bool = False

    notes: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

@dataclass
class Document:
    id: str

    provider: str

    account_id: str

    name: str

    mime_type: str = ""

    modified_time: str = ""

    url: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Device Location
# ---------------------------------------------------------------------------

@dataclass
class Location:
    id: str

    provider: str

    label: str

    latitude: float | None = None

    longitude: float | None = None

    address: str = ""

    timestamp: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Financial Position
# ---------------------------------------------------------------------------

@dataclass
class FinancialPosition:
    symbol: str

    quantity: float

    market_value: float

    day_change: float | None = None

    day_change_percent: float | None = None

    cost_basis: float | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def model_to_dict(
    value,
):
    return asdict(
        value
    )