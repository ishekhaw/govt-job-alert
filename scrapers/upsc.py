from playwright.sync_api import sync_playwright

from db import save_job
from scrapers.utils import absolute_link, extract_listing_description, matches_keywords


def scrape_upsc():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        base_url = "https://upsc.gov.in/"
        page.goto(base_url, wait_until="domcontentloaded")
        page.wait_for_selector("a", state="attached", timeout=15000)

        keywords = [
            "exam",
            "examination",
            "recruitment",
            "admit card",
            "notification",
            "result",
            "vacancy",
            "apply online",
            "advertisement",
        ]

        for link in page.query_selector_all("a"):
            try:
                title = link.inner_text().strip()
                href = link.get_attribute("href")

                if not title or not href or len(title) < 12:
                    continue

                if not matches_keywords(title, keywords):
                    continue

                save_job(
                    title=title,
                    link=absolute_link(base_url, href),
                    source="UPSC",
                    description=extract_listing_description(link, title),
                )
            except Exception:
                continue

        browser.close()
