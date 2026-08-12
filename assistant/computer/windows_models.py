from __future__ import annotations
from dataclasses import dataclass

@dataclass
class WindowInfo:
    handle: int
    title: str
    process_id: int
    x: int
    y: int
    width: int
    height: int
    visible: bool = True
    minimized: bool = False
    maximized: bool = False
    def to_dict(self):
        return self.__dict__.copy()

@dataclass
class MonitorInfo:
    index: int
    x: int
    y: int
    width: int
    height: int
    work_x: int
    work_y: int
    work_width: int
    work_height: int
    primary: bool = False
    def to_dict(self):
        return self.__dict__.copy()
