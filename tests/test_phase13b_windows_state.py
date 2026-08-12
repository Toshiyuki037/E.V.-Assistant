import sys, pytest
from assistant.computer import windows
from assistant.computer.windows_models import WindowInfo,MonitorInfo

def _w(h,t,minimized=False): return WindowInfo(h,t,h+100,10,20,800,600,True,minimized,False)

def test_find_windows_case_insensitive(monkeypatch):
    monkeypatch.setattr(windows,'list_windows',lambda:[_w(1,'Visual Studio Code'),_w(2,'Spotify Premium')])
    r=windows.find_windows('studio'); assert len(r)==1 and r[0].title=='Visual Studio Code'

def test_resolve_window_prefers_exact(monkeypatch):
    monkeypatch.setattr(windows,'list_windows',lambda:[_w(1,'Visual Studio Code'),_w(2,'Code')])
    assert windows.resolve_window('Code').handle==2

def test_desktop_state_serializes(monkeypatch):
    monkeypatch.setattr(windows,'get_foreground_window',lambda:_w(10,'Foreground'))
    monkeypatch.setattr(windows,'list_windows',lambda:[_w(10,'Foreground'),_w(11,'Other')])
    monkeypatch.setattr(windows,'list_monitors',lambda:[MonitorInfo(0,0,0,1920,1080,0,0,1920,1040,True)])
    s=windows.desktop_state(); assert s['foreground']['title']=='Foreground'; assert s['window_count']==2; assert s['monitor_count']==1

@pytest.mark.skipif(sys.platform!='win32',reason='Native Windows smoke test')
def test_native_windows_backend_reads_desktop():
    from assistant.computer.windows_backend import get_foreground_window,list_monitors,list_windows
    assert len(list_monitors())>=1; assert isinstance(list_windows(),list)
    fg=get_foreground_window(); assert fg is None or fg.handle>0
