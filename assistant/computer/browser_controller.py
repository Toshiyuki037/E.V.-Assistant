from .browser_dom import (
    BrowserDOMSession, click_dom_element, connect_chrome_cdp, fill_dom_element,
    find_dom_elements, inspect_dom_element, launch_managed_browser,
    list_browser_pages, navigate_page, press_dom_key, select_dom_option,
    set_dom_checked,
)

def launch_local_managed_browser(*, headless: bool = False):
    return launch_managed_browser(headless=headless)

def connect_local_chrome_dom(endpoint: str = "http://127.0.0.1:9222"):
    return connect_chrome_cdp(endpoint)

def list_local_browser_pages(session: BrowserDOMSession):
    return [p.to_dict() for p in list_browser_pages(session)]

def navigate_local_browser_page(session: BrowserDOMSession, url: str, *, page_target=None):
    return navigate_page(session, url, page_target=page_target)

def inspect_local_dom_element(session: BrowserDOMSession, selector: str, *, page_target=None):
    return inspect_dom_element(session, selector, page_target=page_target).to_dict()

def find_local_dom_elements(session: BrowserDOMSession, **kwargs):
    return [e.to_dict() for e in find_dom_elements(session, **kwargs)]

def click_local_dom_element(session: BrowserDOMSession, **kwargs):
    return click_dom_element(session, **kwargs).to_dict()

def fill_local_dom_element(session: BrowserDOMSession, value: str, **kwargs):
    return fill_dom_element(session, value, **kwargs).to_dict()

def set_local_dom_checked(session: BrowserDOMSession, checked: bool, **kwargs):
    return set_dom_checked(session, checked, **kwargs).to_dict()

def select_local_dom_option(session: BrowserDOMSession, value: str, **kwargs):
    return select_dom_option(session, value, **kwargs).to_dict()

def press_local_dom_key(session: BrowserDOMSession, key: str, **kwargs):
    return press_dom_key(session, key, **kwargs).to_dict()
