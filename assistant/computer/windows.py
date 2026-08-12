from __future__ import annotations
from .windows_backend import *

def find_windows(query:str):
    q=str(query or '').strip().lower()
    if not q: return []
    return sorted([w for w in list_windows() if q in w.title.lower()], key=lambda w:(w.minimized,-len(w.title)))

def resolve_window(target:str|int):
    if isinstance(target,int): return get_window_info(target)
    t=str(target or '').strip()
    if not t: raise ValueError('Window target cannot be empty.')
    if t.isdigit(): return get_window_info(int(t))
    matches=find_windows(t)
    if not matches: raise LookupError(f'No visible window matched: {target}')
    exact=[w for w in matches if w.title.lower()==t.lower()]
    return exact[0] if len(exact)==1 else matches[0]

def focus_window_target(target):
    w=resolve_window(target); focus_window(w.handle); return get_window_info(w.handle)

def minimize_window_target(target):
    w=resolve_window(target); minimize_window(w.handle); return get_window_info(w.handle)

def maximize_window_target(target):
    w=resolve_window(target); maximize_window(w.handle); return get_window_info(w.handle)

def restore_window_target(target):
    w=resolve_window(target); restore_window(w.handle); return get_window_info(w.handle)

def move_window_target(target,*,x:int,y:int,width:int|None=None,height:int|None=None):
    w=resolve_window(target); move_window(w.handle,x=x,y=y,width=width,height=height); return get_window_info(w.handle)

def desktop_state():
    fg=get_foreground_window(); ws=list_windows(); ms=list_monitors()
    return {'foreground': fg.to_dict() if fg else None,'windows':[w.to_dict() for w in ws],'monitors':[m.to_dict() for m in ms],'window_count':len(ws),'monitor_count':len(ms)}
