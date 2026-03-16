"""
Ultron Browser Control Module
Uses Playwright to interact with browser elements accurately.
Created by Aditeya Mitra's Ultron AI.
"""

import asyncio
import logging
import threading
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright


class BrowserController:
    """
    Controls the browser using Playwright.
    Connects to an existing Chrome instance via CDP (Chrome DevTools Protocol)
    so Ultron controls the user's actual browser, not a headless one.
    
    SETUP REQUIRED:
    The user must launch Chrome with remote debugging enabled:
        chrome.exe --remote-debugging-port=9222
    Or add it to Chrome's shortcut target.
    """
    
    def __init__(self, cdp_url="http://localhost:9222"):
        self.cdp_url = cdp_url
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._lock = threading.Lock()
        self._initialized = False
        logging.info("BrowserController created (lazy initialization)")
    
    def _ensure_connected(self):
        """Lazily connect to the browser on first use."""
        if self._initialized and self._page and not self._page.is_closed():
            return True
        
        try:
            if self._playwright is None:
                self._playwright = sync_playwright().start()
            
            # Connect to existing Chrome via CDP
            self._browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
            
            # Get the default context (first window)
            contexts = self._browser.contexts
            if contexts:
                self._context = contexts[0]
                pages = self._context.pages
                if pages:
                    self._page = pages[-1]  # Use the last active page
                else:
                    self._page = self._context.new_page()
            else:
                self._context = self._browser.new_context()
                self._page = self._context.new_page()
            
            self._initialized = True
            logging.info("BrowserController connected to Chrome via CDP")
            return True
            
        except Exception as e:
            logging.error(f"BrowserController connection failed: {e}")
            self._initialized = False
            return False
    
    def _get_active_page(self):
        """Get the currently active page, reconnecting if needed."""
        if not self._ensure_connected():
            return None
        
        try:
            # Try to get the most recent page from the context
            pages = self._context.pages
            if pages:
                # Return the last page (most recently created/focused)
                self._page = pages[-1]
                return self._page
        except:
            # Context might be stale, try reconnecting
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
                    return False, "Browser not connected. Launch Chrome with --remote-debugging-port=9222"
                
                # Add protocol if missing
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                title = page.title()
                return True, f"Navigated to: {title}"
            except Exception as e:
                logging.error(f"Navigate error: {e}")
                return False, f"Navigation failed: {str(e)}"
    
    def search(self, query):
        """Type a search query into the browser's address bar and submit."""
        with self._lock:
            try:
                page = self._get_active_page()
                if not page:
                    return False, "Browser not connected"
                
                # Navigate to Google search
                search_url = f"https://www.google.com/search?q={query}"
                page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
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
        """Click an element by selector (CSS, text=, etc.)."""
        with self._lock:
            try:
                page = self._get_active_page()
                if not page:
                    return False, "Browser not connected"
                
                # Try multiple selector strategies
                clicked = False
                strategies = [
                    selector,                                    # Direct selector
                    f"text={selector}",                          # Text content
                    f"[aria-label='{selector}']",               # Aria label
                    f"button:has-text('{selector}')",           # Button with text
                    f"a:has-text('{selector}')",                # Link with text
                    f"input[placeholder='{selector}']",         # Input placeholder
                ]
                
                for strat in strategies:
                    try:
                        element = page.locator(strat).first
                        if element.is_visible(timeout=2000):
                            element.click(timeout=3000)
                            clicked = True
                            break
                    except:
                        continue
                
                if clicked:
                    return True, f"Clicked element: {selector}"
                else:
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
                
                # Switch to the next available page
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
            except:
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
