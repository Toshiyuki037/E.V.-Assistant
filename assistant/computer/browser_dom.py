from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .browser_models import BrowserPageInfo, DOMActionResult, DOMElementInfo

try:
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
except ImportError:
    Browser = BrowserContext = Page = Playwright = Any
    sync_playwright = None

class BrowserDOMUnavailable(RuntimeError):
    pass

@dataclass
class BrowserDOMSession:
    playwright: Playwright
    browser: Browser
    context: BrowserContext
    managed: bool = False

    def pages(self) -> list[Page]:
        return list(self.context.pages)

    def close(self):
        if self.managed:
            try:
                self.browser.close()
            except Exception:
                pass
        try:
            self.playwright.stop()
        except Exception:
            pass

def _require_playwright():
    if sync_playwright is None:
        raise BrowserDOMUnavailable(
            "Phase 13H requires Playwright. Install it with: python -m pip install playwright"
        )

def launch_managed_browser(*, headless: bool = False) -> BrowserDOMSession:
    _require_playwright()
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=bool(headless))
    context = browser.new_context()
    if not context.pages:
        context.new_page()
    return BrowserDOMSession(p, browser, context, True)

def connect_chrome_cdp(endpoint: str = "http://127.0.0.1:9222") -> BrowserDOMSession:
    _require_playwright()
    p = sync_playwright().start()
    try:
        browser = p.chromium.connect_over_cdp(str(endpoint))
        if not browser.contexts:
            raise BrowserDOMUnavailable("Connected to Chrome but no browser context was exposed.")
        return BrowserDOMSession(p, browser, browser.contexts[0], False)
    except Exception:
        try:
            p.stop()
        except Exception:
            pass
        raise

def list_browser_pages(session: BrowserDOMSession) -> list[BrowserPageInfo]:
    out = []
    for i, page in enumerate(session.pages()):
        try:
            title = page.title()
        except Exception:
            title = ""
        out.append(BrowserPageInfo(i, title, str(page.url or "")))
    return out

def resolve_page(session: BrowserDOMSession, target: int | str | None = None) -> Page:
    pages = session.pages()
    if not pages:
        raise LookupError("Browser session has no open pages.")
    if target is None:
        return pages[-1]
    if isinstance(target, int):
        if target < 0 or target >= len(pages):
            raise IndexError(f"Browser page index out of range: {target}")
        return pages[target]
    text = str(target or "").strip().lower()
    if not text:
        return pages[-1]
    matches = []
    for page in pages:
        try:
            title = page.title().lower()
        except Exception:
            title = ""
        url = str(page.url or "").lower()
        if text in title or text in url:
            matches.append(page)
    if not matches:
        raise LookupError(f"No browser page matched: {target}")
    return matches[-1]

def navigate_page(session: BrowserDOMSession, url: str, *, page_target=None,
                  wait_until: str = "domcontentloaded") -> dict:
    page = resolve_page(session, page_target)
    destination = str(url or "").strip()
    if not destination:
        raise ValueError("Browser navigation URL cannot be empty.")
    if not (destination.startswith("http://") or destination.startswith("https://")):
        raise ValueError("Phase 13H navigation only allows http:// or https:// URLs.")
    response = page.goto(destination, wait_until=wait_until)
    return {
        "url": str(page.url or ""),
        "title": page.title(),
        "status": int(response.status) if response is not None else None,
    }

def _single(locator, description: str):
    count = locator.count()
    if count == 0:
        raise LookupError(f"No DOM element matched {description}.")
    if count > 1:
        raise LookupError(f"DOM selector is ambiguous; {count} elements matched {description}.")
    return locator.first

def _info(locator, selector: str) -> DOMElementInfo:
    tag = str(locator.evaluate("el => el.tagName ? el.tagName.toLowerCase() : ''") or "")
    try:
        text = str(locator.inner_text() or "")
    except Exception:
        text = ""
    role = str(locator.get_attribute("role") or "")
    name = str(locator.get_attribute("aria-label") or locator.get_attribute("name") or "")
    input_type = str(locator.get_attribute("type") or "")
    try:
        value = str(locator.input_value() or "")
    except Exception:
        value = ""
    checked = None
    try:
        if tag == "input" and input_type.lower() in {"checkbox", "radio"}:
            checked = bool(locator.is_checked())
    except Exception:
        pass
    try:
        disabled = bool(locator.is_disabled())
    except Exception:
        disabled = False
    try:
        visible = bool(locator.is_visible())
    except Exception:
        visible = False
    try:
        editable = bool(locator.is_editable())
    except Exception:
        editable = False
    return DOMElementInfo(selector, tag, text, role, name, input_type, value,
                          checked, disabled, visible, editable)

def inspect_dom_element(session: BrowserDOMSession, selector: str, *, page_target=None) -> DOMElementInfo:
    page = resolve_page(session, page_target)
    return _info(_single(page.locator(selector), f"selector {selector!r}"), selector)

def find_dom_elements(session: BrowserDOMSession, *, page_target=None, role: str = "",
                      name: str = "", text: str = "", selector: str = "",
                      exact: bool = False, limit: int = 100) -> list[DOMElementInfo]:
    page = resolve_page(session, page_target)
    if selector:
        locator = page.locator(selector)
        desc = selector
    elif role:
        locator = page.get_by_role(role, name=(name or None), exact=bool(exact))
        desc = f"role={role!r}, name={name!r}"
    elif text:
        locator = page.get_by_text(text, exact=bool(exact))
        desc = f"text={text!r}"
    else:
        raise ValueError("Provide selector, role, or text for DOM search.")
    result = []
    for i in range(min(locator.count(), max(1, int(limit)))):
        result.append(_info(locator.nth(i), f"{desc} [index={i}]"))
    return result

def click_dom_element(session: BrowserDOMSession, *, page_target=None,
                      selector: str = "", role: str = "", name: str = "",
                      exact: bool = True) -> DOMActionResult:
    page = resolve_page(session, page_target)
    if selector:
        loc = _single(page.locator(selector), f"selector {selector!r}")
        desc = selector
    elif role:
        loc = _single(page.get_by_role(role, name=(name or None), exact=bool(exact)),
                      f"role={role!r}, name={name!r}")
        desc = f"role={role!r}, name={name!r}"
    else:
        raise ValueError("click_dom_element requires selector or role.")
    before = _info(loc, desc)
    loc.click()
    return DOMActionResult("click", str(page.url or ""), before.to_dict(), True, True,
                           "DOM click executed through Playwright.")

def fill_dom_element(session: BrowserDOMSession, value: str, *, page_target=None,
                     selector: str = "", role: str = "", name: str = "",
                     exact: bool = True) -> DOMActionResult:
    page = resolve_page(session, page_target)
    if selector:
        loc = _single(page.locator(selector), f"selector {selector!r}")
        desc = selector
    elif role:
        loc = _single(page.get_by_role(role, name=(name or None), exact=bool(exact)),
                      f"role={role!r}, name={name!r}")
        desc = f"role={role!r}, name={name!r}"
    else:
        raise ValueError("fill_dom_element requires selector or role.")
    text = str(value)
    loc.fill(text)
    after = _info(loc, desc)
    verified = after.value == text
    return DOMActionResult("fill", str(page.url or ""), after.to_dict(), True, verified,
                           f"DOM value filled through Playwright. Verification: {verified}.")

def set_dom_checked(session: BrowserDOMSession, checked: bool, *, page_target=None,
                    selector: str) -> DOMActionResult:
    page = resolve_page(session, page_target)
    loc = _single(page.locator(selector), f"selector {selector!r}")
    desired = bool(checked)
    loc.set_checked(desired)
    after = _info(loc, selector)
    verified = after.checked is desired
    return DOMActionResult("set_checked", str(page.url or ""), after.to_dict(), True,
                           verified, f"DOM checked state updated. Verification: {verified}.")

def select_dom_option(session: BrowserDOMSession, value: str, *, page_target=None,
                      selector: str) -> DOMActionResult:
    page = resolve_page(session, page_target)
    loc = _single(page.locator(selector), f"selector {selector!r}")
    selected = loc.select_option(value=str(value))
    after = _info(loc, selector)
    verified = str(value) in selected
    return DOMActionResult("select_option", str(page.url or ""), after.to_dict(), True,
                           verified, f"DOM select option updated. Verification: {verified}.")

def press_dom_key(session: BrowserDOMSession, key: str, *, page_target=None,
                  selector: str) -> DOMActionResult:
    page = resolve_page(session, page_target)
    loc = _single(page.locator(selector), f"selector {selector!r}")
    info = _info(loc, selector)
    loc.press(str(key))
    return DOMActionResult("press", str(page.url or ""), info.to_dict(), True, True,
                           f"DOM key press executed: {key}")
