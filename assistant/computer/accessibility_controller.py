"""
E.V.I.E. - Accessibility Controller

Phase 13G
"""

from __future__ import annotations

from .accessibility import (
    find_ui_elements,
    inspect_ui_tree,
)
from .ui_actions import (
    focus_ui_element,
    invoke_ui_element,
    select_ui_element,
    set_ui_value,
    toggle_ui_element,
)


def inspect_local_ui(
    target: str | int,
    *,
    max_depth: int = 5,
    max_elements: int = 500,
):
    return inspect_ui_tree(
        target,
        max_depth=max_depth,
        max_elements=max_elements,
    )


def find_local_ui_elements(
    target: str | int,
    *,
    name: str = "",
    control_type: str = "",
    automation_id: str = "",
    exact_name: bool = False,
    max_depth: int = 8,
    limit: int = 100,
):
    return find_ui_elements(
        target,
        name=name,
        control_type=control_type,
        automation_id=automation_id,
        exact_name=exact_name,
        max_depth=max_depth,
        limit=limit,
    )


def focus_local_ui_element(
    target: str | int,
    **selector,
):
    return focus_ui_element(
        target,
        **selector,
    ).to_dict()


def invoke_local_ui_element(
    target: str | int,
    **selector,
):
    return invoke_ui_element(
        target,
        **selector,
    ).to_dict()


def set_local_ui_value(
    target: str | int,
    value: str,
    **selector,
):
    return set_ui_value(
        target,
        value,
        **selector,
    ).to_dict()


def toggle_local_ui_element(
    target: str | int,
    **selector,
):
    return toggle_ui_element(
        target,
        **selector,
    ).to_dict()


def select_local_ui_element(
    target: str | int,
    **selector,
):
    return select_ui_element(
        target,
        **selector,
    ).to_dict()
