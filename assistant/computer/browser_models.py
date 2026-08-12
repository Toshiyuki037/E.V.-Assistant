from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class BrowserPageInfo:
    index: int
    title: str
    url: str
    def to_dict(self) -> dict[str, Any]:
        return {"index": self.index, "title": self.title, "url": self.url}

@dataclass
class DOMElementInfo:
    selector: str
    tag: str
    text: str
    role: str = ""
    name: str = ""
    input_type: str = ""
    value: str = ""
    checked: bool | None = None
    disabled: bool = False
    visible: bool = False
    editable: bool = False
    def to_dict(self) -> dict[str, Any]:
        return {
            "selector": self.selector, "tag": self.tag, "text": self.text,
            "role": self.role, "name": self.name, "input_type": self.input_type,
            "value": self.value, "checked": self.checked, "disabled": self.disabled,
            "visible": self.visible, "editable": self.editable,
        }

@dataclass
class DOMActionResult:
    action: str
    page_url: str
    target: dict[str, Any]
    success: bool
    verified: bool = False
    detail: str = ""
    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action, "page_url": self.page_url, "target": dict(self.target),
            "success": self.success, "verified": self.verified, "detail": self.detail,
        }
