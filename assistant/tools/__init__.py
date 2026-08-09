"""
E.V.I.E. - Tool System

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Provides controlled computer-action capabilities for E.V.I.E.

Phase:
    Phase 6 - Tool & Computer Control

Current Capabilities:
    - tool registry
    - permission / risk classification
    - workspace-scoped filesystem access
    - safe terminal execution
    - centralized tool execution
    - audit logging

Important:
    E.V.I.E.'s reasoning model does not directly execute arbitrary
    operating-system actions.

    All actions must pass through the tool registry, permission
    system, executor, and audit layer.
"""