from __future__ import annotations

ACTION_SCHEMAS = {
    "monitor.list": {"arguments": {}, "risk": "read"},
    "window.focus": {"arguments": {}, "risk": "low"},
    "window.move": {"arguments": {"x": "<int>", "y": "<int>", "width": "<optional int>", "height": "<optional int>"}, "risk": "low"},
    "window.minimize": {"arguments": {}, "risk": "low"},
    "window.maximize": {"arguments": {}, "risk": "low"},
    "window.close": {"arguments": {}, "risk": "medium"},
    "window.place": {"arguments": {"monitor_index": "<1-based int>", "maximized": "<bool>"}, "risk": "low"},
    "application.launch": {"arguments": {"arguments": "<optional list[str]>", "cwd": "<optional path>"}, "risk": "low"},
    "filesystem.exists": {"arguments": {}, "risk": "read"},
    "filesystem.inspect": {"arguments": {}, "risk": "read"},
    "filesystem.create_directory": {"arguments": {}, "risk": "low"},
    "filesystem.write": {"arguments": {"content": "<string>", "overwrite": "<optional bool>"}, "risk": "medium"},
    "filesystem.copy": {"arguments": {"destination": "<path>", "overwrite": "<optional bool>"}, "risk": "medium"},
    "filesystem.move": {"arguments": {"destination": "<path>", "overwrite": "<optional bool>"}, "risk": "medium"},
    "filesystem.rename": {"arguments": {"new_name": "<name>"}, "risk": "medium"},
    "filesystem.delete": {"arguments": {}, "risk": "high"},
    "clipboard.read": {"arguments": {}, "risk": "read"},
    "clipboard.write": {"arguments": {"text": "<string>"}, "risk": "medium"},
    "notification.send": {"arguments": {"title": "<string>", "message": "<string>"}, "risk": "low"},
    "settings.open": {"arguments": {}, "risk": "low"},
    "process.terminate": {"arguments": {"pid": "<int>"}, "risk": "medium"},
    "accessibility.focus": {"arguments": {"selector": "<dict>"}, "risk": "low"},
    "accessibility.invoke": {"arguments": {"selector": "<dict>"}, "risk": "medium"},
    "accessibility.set_value": {"arguments": {"value": "<string>", "selector": "<dict>"}, "risk": "medium"},
    "accessibility.toggle": {"arguments": {"selector": "<dict>"}, "risk": "medium"},
    "accessibility.select": {"arguments": {"selector": "<dict>"}, "risk": "low"},
    "browser.navigate": {"arguments": {"url": "<http(s) URL>", "page_target": "<optional>"}, "risk": "low"},
    "browser.dom.click": {"arguments": {}, "risk": "medium"},
    "browser.dom.fill": {"arguments": {"value": "<string>"}, "risk": "medium"},
    "browser.dom.check": {"arguments": {"checked": "<bool>"}, "risk": "medium"},
    "browser.dom.select": {"arguments": {"value": "<string>"}, "risk": "medium"},
    "browser.dom.press": {"arguments": {"key": "<string>"}, "risk": "medium"},
    "vision.pointer_move": {"arguments": {}, "risk": "low"},
    "vision.click": {"arguments": {}, "risk": "medium"},
}


def planner_contract_text() -> str:
    lines = [
        "CANONICAL PHASE 13 COMPUTER ACTION CONTRACTS:",
        "Never invent an action name.",
        "Never include an approved argument.",
        "",
    ]
    for name, data in ACTION_SCHEMAS.items():
        lines.append(f"{name}: arguments={data['arguments']!r}; risk={data['risk']}")
    return "\n".join(lines)
