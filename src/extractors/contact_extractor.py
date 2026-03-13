"""
JavaScript-based contact extraction from LinkedIn search results pages.
"""
from typing import List, Dict
from src.utils.browser import BrowserManager
from src.utils.logger import setup_logger

log = setup_logger("extractor.contacts")


# The core JS extraction script — exactly what was used in the manual sessions
EXTRACT_CONTACTS_JS = """
(() => {
    const links = Array.from(document.querySelectorAll('a[href*="/in/"]'));
    const seen = new Set();
    const results = links.filter(a => {
        const h = a.href.split('?')[0];
        if (seen.has(h) || !h.includes('/in/')) return false;
        seen.add(h);
        return a.textContent.trim().length > 3;
    }).map(a => {
        const t = a.textContent.trim().replace(/\\s+/g, ' ');
        return {
            n: t.split('\\u2022')[0].split('View')[0].trim().substring(0, 60),
            u: a.href.split('?')[0]
        };
    }).filter(x =>
        x.n.length > 2 &&
        !x.n.includes('LinkedIn') &&
        !x.n.includes('Sign') &&
        !x.n.includes('Join')
    ).slice(0, MAX_CONTACTS);
    return results;
})()
"""


class ContactExtractor:
    """Extracts LinkedIn contact info (name + URL) from current page."""

    def __init__(self, browser: BrowserManager, max_contacts: int = 10):
        self.browser = browser
        self.max_contacts = max_contacts

    def extract_from_current_page(self) -> List[Dict[str, str]]:
        """Extract contacts from the currently loaded LinkedIn search page."""
        js = EXTRACT_CONTACTS_JS.replace("MAX_CONTACTS", str(self.max_contacts))
        result = self.browser.execute_js(js)

        if not result or not isinstance(result, list):
            return []

        contacts = []
        for item in result:
            name = item.get("n", "").strip()
            url = item.get("u", "").strip()
            if name and url and len(name) > 2 and "/in/" in url:
                contacts.append({"name": name, "url": url})

        log.debug("Extracted %d contacts from page", len(contacts))
        return contacts
