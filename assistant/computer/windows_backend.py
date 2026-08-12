from __future__ import annotations
import ctypes, sys
from ctypes import wintypes
from .windows_models import WindowInfo, MonitorInfo

IS_WINDOWS = sys.platform == 'win32'
class WindowsBackendUnavailable(RuntimeError): pass

if IS_WINDOWS:
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    SW_SHOWMINIMIZED=2; SW_SHOWMAXIMIZED=3; SW_RESTORE=9; MONITORINFOF_PRIMARY=1
    class RECT(ctypes.Structure):
        _fields_=[('left',wintypes.LONG),('top',wintypes.LONG),('right',wintypes.LONG),('bottom',wintypes.LONG)]
    class MONITORINFO(ctypes.Structure):
        _fields_=[('cbSize',wintypes.DWORD),('rcMonitor',RECT),('rcWork',RECT),('dwFlags',wintypes.DWORD)]
    WNDENUMPROC=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    MONITORENUMPROC=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HMONITOR,wintypes.HDC,ctypes.POINTER(RECT),wintypes.LPARAM)

def _require_windows():
    if not IS_WINDOWS: raise WindowsBackendUnavailable('Native Windows control is only available on Windows.')

def _valid(handle:int):
    _require_windows()
    if not handle or not user32.IsWindow(wintypes.HWND(handle)):
        raise ValueError(f'Invalid window handle: {handle}')

def _title(handle:int)->str:
    n=user32.GetWindowTextLengthW(wintypes.HWND(handle))
    if n<=0: return ''
    b=ctypes.create_unicode_buffer(n+1)
    user32.GetWindowTextW(wintypes.HWND(handle),b,len(b))
    return b.value.strip()

def get_window_info(handle:int)->WindowInfo:
    _valid(handle)
    r=RECT(); user32.GetWindowRect(wintypes.HWND(handle),ctypes.byref(r))
    pid=wintypes.DWORD(); user32.GetWindowThreadProcessId(wintypes.HWND(handle),ctypes.byref(pid))
    return WindowInfo(handle,_title(handle),int(pid.value),int(r.left),int(r.top),max(0,int(r.right-r.left)),max(0,int(r.bottom-r.top)),bool(user32.IsWindowVisible(wintypes.HWND(handle))),bool(user32.IsIconic(wintypes.HWND(handle))),bool(user32.IsZoomed(wintypes.HWND(handle))))

def list_windows(*,visible_only:bool=True,titled_only:bool=True):
    _require_windows(); handles=[]
    @WNDENUMPROC
    def cb(hwnd,_):
        if visible_only and not user32.IsWindowVisible(hwnd): return True
        t=_title(int(hwnd))
        if titled_only and not t: return True
        handles.append(int(hwnd)); return True
    user32.EnumWindows(cb,0)
    out=[]
    for h in handles:
        try: out.append(get_window_info(h))
        except Exception: pass
    return out

def get_foreground_window():
    _require_windows(); h=user32.GetForegroundWindow()
    if not h: return None
    try: return get_window_info(int(h))
    except Exception: return None

def focus_window(handle:int):
    _valid(handle); hwnd=wintypes.HWND(handle)
    if user32.IsIconic(hwnd): user32.ShowWindow(hwnd,SW_RESTORE)
    return bool(user32.SetForegroundWindow(hwnd))

def minimize_window(handle:int): _valid(handle); user32.ShowWindow(wintypes.HWND(handle),SW_SHOWMINIMIZED); return True

def maximize_window(handle:int): _valid(handle); user32.ShowWindow(wintypes.HWND(handle),SW_SHOWMAXIMIZED); return True

def restore_window(handle:int): _valid(handle); user32.ShowWindow(wintypes.HWND(handle),SW_RESTORE); return True

def move_window(handle:int,*,x:int,y:int,width:int|None=None,height:int|None=None):
    _valid(handle); cur=get_window_info(handle); w=cur.width if width is None else int(width); h=cur.height if height is None else int(height)
    if w<=0 or h<=0: raise ValueError('Window width and height must be positive.')
    if not user32.MoveWindow(wintypes.HWND(handle),int(x),int(y),w,h,True): raise RuntimeError('MoveWindow failed.')
    return True

def list_monitors():
    _require_windows(); out=[]
    @MONITORENUMPROC
    def cb(mon,_hdc,_rect,_):
        info=MONITORINFO(); info.cbSize=ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(mon,ctypes.byref(info)):
            a,b=info.rcMonitor,info.rcWork
            out.append(MonitorInfo(len(out),int(a.left),int(a.top),int(a.right-a.left),int(a.bottom-a.top),int(b.left),int(b.top),int(b.right-b.left),int(b.bottom-b.top),bool(info.dwFlags & MONITORINFOF_PRIMARY)))
        return True
    user32.EnumDisplayMonitors(None,None,cb,0)
    return out
