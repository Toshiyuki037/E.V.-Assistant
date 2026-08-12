import pytest
import assistant.computer.browser_dom as browser_dom
from assistant.computer.capabilities import get_action_risk
from assistant.computer.models import DeviceRisk

def test_dom_inspection_is_read_only():
    assert get_action_risk("browser.dom.inspect") == DeviceRisk.READ

def test_dom_click_is_medium_risk():
    assert get_action_risk("browser.dom.click") == DeviceRisk.MEDIUM

def test_navigation_rejects_non_http_urls(monkeypatch):
    class FakePage:
        url = "about:blank"
    monkeypatch.setattr(browser_dom, "resolve_page", lambda *a, **k: FakePage())
    with pytest.raises(ValueError):
        browser_dom.navigate_page(object(), "file:///C:/Windows/System32")

def test_managed_browser_dom_round_trip():
    if browser_dom.sync_playwright is None:
        pytest.skip("Playwright unavailable")
    try:
        session = browser_dom.launch_managed_browser(headless=True)
    except Exception as error:
        pytest.skip(f"Playwright browser unavailable: {error}")
    try:
        page = browser_dom.resolve_page(session)
        page.set_content("""
        <html><body>
          <label for="name">Name</label>
          <input id="name" value="">
          <button id="hello">Hello</button>
          <input id="agree" type="checkbox">
          <select id="choice">
            <option value="a">A</option>
            <option value="b">B</option>
          </select>
        </body></html>
        """)
        filled = browser_dom.fill_dom_element(session, "E.V.I.E.", selector="#name")
        assert filled.success is True and filled.verified is True
        checked = browser_dom.set_dom_checked(session, True, selector="#agree")
        assert checked.verified is True
        selected = browser_dom.select_dom_option(session, "b", selector="#choice")
        assert selected.success is True
        found = browser_dom.find_dom_elements(
            session, role="button", name="Hello", exact=True
        )
        assert len(found) == 1 and found[0].tag == "button"
    finally:
        session.close()
