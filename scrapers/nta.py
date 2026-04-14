from playwright.sync_api import sync_playwright

from db import save_job
from scrapers.utils import absolute_link, extract_listing_description, matches_keywords


def scrape_nta():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        base_url = "https://nta.ac.in/"
        page.goto(base_url, wait_until="domcontentloaded")
        page.wait_for_selector("a", state="attached", timeout=15000)

        keywords = [
            "exam",
            "examination",
            "nta",
            "ugc net",
            "neet",
            "jee",
            "cuet",
            "notification",
            "public notice",
            "result",
            "admit card",
            "answer key",
        ]

        for link in page.query_selector_all("a"):
            try:
                title = link.inner_text().strip()
                href = link.get_attribute("href")

                if not title or not href or len(title) < 10:
                    continue

                if not matches_keywords(title, keywords):
                    continue

                save_job(
                    title=title,
                    link=absolute_link(base_url, href),
                    source="NTA",
                    description=extract_listing_description(link, title),
                )
            except Exception:
                continue

        browser.close()
