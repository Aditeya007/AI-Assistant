"""
Ultron Browser Control Module
Uses Playwright's bundled Chromium directly - no Chrome installation needed.
Created by Aditeya Mitra's Ultron AI.
"""

import logging
import threading
import time
from playwright.sync_api import sync_playwright


class BrowserController:
    """
    Controls a Playwright-managed Chromium browser window.
    No external Chrome installation required — uses Playwright's bundled Chromium.
    The browser window opens automatically when the first command is executed.
    """

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._lock = threading.Lock()
        self._initialized = False
        logging.info("BrowserController ready (uses Playwright's bundled Chromium)")

    def _ensure_connected(self):
        """Lazily launch Playwright Chromium on first use."""
        if self._initialized and self._page and not self._page.is_closed():
            return True

        try:
            if self._playwright is None:
                self._playwright = sync_playwright().start()

            if self._browser is None or not self._browser.is_connected():
                logging.info("Launching Playwright Chromium...")
                self._browser = self._playwright.chromium.launch(
                    headless=False,
                    args=["--start-maximized"]
                )

            if not self._context:
                self._context = self._browser.new_context(no_viewport=True)

            if not self._page or self._page.is_closed():
                self._page = self._context.new_page()

            self._initialized = True
            logging.info("Playwright Chromium launched successfully")
            return True

        except Exception as e:
            logging.error(f"BrowserController launch failed: {e}")
            self._initialized = False
            return False

    def _get_active_page(self):
        """Get the currently active page, reconnecting if needed."""
        if not self._ensure_connected():
            return None

        try:
            pages = self._context.pages
            if pages:
                self._page = pages[-1]
                return self._page
        except Exception:
            self._initialized = False
            if self._ensure_connected():
                return self._page

        return None

    def navigate(self, url):
        """Navigate to a URL."""
        with self._lock:
            try:
                page = self._get_active_page()
                if not page:
                    return False, "Browser could not start."

                if not url.startswith(("http://", "https://")):
                    url = "https://" + url

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                except Exception as nav_err:
                    if "ERR_ABORTED" in str(nav_err) or "net::" in str(nav_err):
                        # Fallback: JS redirect for redirect-heavy sites (e.g. YouTube)
                        try:
                            page.evaluate(f"window.location.href = '{url}'")
                            time.sleep(2)
                        except Exception:
                            pass
                    else:
                        raise nav_err

                title = page.title()
                return True, f"Navigated to: {title}"
            except Exception as e:
                logging.error(f"Navigate error: {e}")
                return False, f"Navigation failed: {str(e)}"

    def search(self, query):
        """Navigate to search results for the query, supporting multiple sites."""
        with self._lock:
            try:
                page = self._get_active_page()
                if not page:
                    return False, "Browser not connected"

                lower_query = query.lower()
                clean_query = query.strip().replace(" ", "+")
                
                # Site-specific search patterns
                site_searches = {
                    "youtube": "https://www.youtube.com/results?search_query=",
                    "amazon": "https://www.amazon.com/s?k=",
                    "flipkart": "https://www.flipkart.com/search?q=",
                    "reddit": "https://www.reddit.com/search/?q=",
                    "twitter": "https://twitter.com/search?q=",
                    "github": "https://github.com/search?q=",
                    "wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search=",
                    "stackoverflow": "https://stackoverflow.com/search?q="
                }

                # 1. Check if the query itself specifies a site (e.g., "cats on youtube")
                target_url = None
                for site, base_url in site_searches.items():
                    if f" on {site}" in lower_query or f" in {site}" in lower_query:
                        # Extract query part (e.g., "cats" from "cats on youtube")
                        core_query = lower_query.split(f" on {site}")[0].split(f" in {site}")[0].strip()
                        target_url = base_url + core_query.replace(" ", "+")
                        break
                
                # 2. If no explicit site in query, check if we are already ON one of these sites
                if not target_url:
                    current_url = page.url.lower()
                    for site, base_url in site_searches.items():
                        if site in current_url:
                            target_url = base_url + clean_query
                            break
                
                # 3. Fallback to Google
                if not target_url:
                    target_url = f"https://www.google.com/search?q={clean_query}"

                page.goto(target_url, wait_until="domcontentloaded", timeout=20000)
                return True, f"Searched for: {query}"
            except Exception as e:
                logging.error(f"Search error: {e}")
                return False, f"Search failed: {str(e)}"

    def scroll(self, direction="down", amount=500):
        """Scroll the page up or down."""
        with self._lock:
            try:
                page = self._get_active_page()
                if not page:
                    return False, "Browser not connected"

                scroll_amount = amount if direction == "down" else -amount
                page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                return True, f"Scrolled {direction} by {amount}px"
            except Exception as e:
                logging.error(f"Scroll error: {e}")
                return False, f"Scroll failed: {str(e)}"

    def click(self, selector):
        """Click an element by selector, text, or semantic target."""
        with self._lock:
            try:
                page = self._get_active_page()
                if not page:
                    return False, "Browser not connected"

                lower_sel = selector.lower()
                
                # --- 1. Semantic / Video Specific Handling ---
                if "video" in lower_sel:
                    # YouTube specific selectors
                    yt_selectors = [
                        "ytd-video-renderer #video-title", 
                        "ytd-grid-video-renderer #video-title",
                        "a#video-title",
                        ".ytp-play-button"
                    ]
                    
                    index = 0
                    if "first" in lower_sel or "1st" in lower_sel: index = 0
                    elif "second" in lower_sel or "2nd" in lower_sel: index = 1
                    elif "third" in lower_sel or "3rd" in lower_sel: index = 2
                    
                    for yt_sel in yt_selectors:
                        try:
                            elements = page.locator(yt_sel)
                            count = elements.count()
                            if count > index:
                                elements.nth(index).click(timeout=3000)
                                return True, f"Clicked {lower_sel} using {yt_sel}"
                        except: continue

                # --- 2. Generic Strategies ---
                strategies = [
                    selector,
                    f"text={selector}",
                    f"[aria-label='{selector}']",
                    f"button:has-text('{selector}')",
                    f"a:has-text('{selector}')",
                    f"input[placeholder='{selector}']",
                    f"role=button[name='{selector}' i]",
                    f"role=link[name='{selector}' i]"
                ]

                for strat in strategies:
                    try:
                        element = page.locator(strat).first
                        if element.is_visible(timeout=1000):
                            element.click(timeout=3000)
                            return True, f"Clicked element: {strat}"
                    except Exception:
                        continue

                return False, f"Could not find clickable element: {selector}"
            except Exception as e:
                logging.error(f"Click error: {e}")
                return False, f"Click failed: {str(e)}"

    def type_text(self, text):
        """Type text into the currently focused element."""
        with self._lock:
            try:
                page = self._get_active_page()
                if not page:
                    return False, "Browser not connected"

                page.keyboard.type(text, delay=30)
                return True, f"Typed: {text}"
            except Exception as e:
                logging.error(f"Type error: {e}")
                return False, f"Type failed: {str(e)}"

    def go_back(self):
        """Navigate back in browser history."""
        with self._lock:
            try:
                page = self._get_active_page()
                if not page:
                    return False, "Browser not connected"
                page.go_back(timeout=10000)
                return True, f"Went back to: {page.title()}"
            except Exception as e:
                logging.error(f"Back error: {e}")
                return False, f"Back navigation failed: {str(e)}"

    def go_forward(self):
        """Navigate forward in browser history."""
        with self._lock:
            try:
                page = self._get_active_page()
                if not page:
                    return False, "Browser not connected"
                page.go_forward(timeout=10000)
                return True, f"Went forward to: {page.title()}"
            except Exception as e:
                logging.error(f"Forward error: {e}")
                return False, f"Forward navigation failed: {str(e)}"

    def new_tab(self):
        """Open a new tab."""
        with self._lock:
            try:
                if not self._ensure_connected():
                    return False, "Browser not connected"

                self._page = self._context.new_page()
                self._page.goto("about:blank")
                return True, "New tab opened"
            except Exception as e:
                logging.error(f"New tab error: {e}")
                return False, f"New tab failed: {str(e)}"

    def close_tab(self):
        """Close the current tab."""
        with self._lock:
            try:
                page = self._get_active_page()
                if not page:
                    return False, "Browser not connected"

                page.close()
                pages = self._context.pages
                if pages:
                    self._page = pages[-1]
                    return True, f"Tab closed. Now on: {self._page.title()}"
                else:
                    return True, "Tab closed. No tabs remaining."
            except Exception as e:
                logging.error(f"Close tab error: {e}")
                return False, f"Close tab failed: {str(e)}"

    def get_page_info(self):
        """Get info about the current page."""
        with self._lock:
            try:
                page = self._get_active_page()
                if not page:
                    return None
                return {
                    "title": page.title(),
                    "url": page.url,
                }
            except Exception:
                return None

    def cleanup(self):
        """Clean up Playwright resources."""
        try:
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
            logging.info("BrowserController cleaned up")
        except Exception as e:
            logging.error(f"Cleanup error: {e}")
