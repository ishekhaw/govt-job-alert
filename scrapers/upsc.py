from playwright.sync_api import sync_playwright

from db import save_job
from scrapers.utils import absolute_link, extract_listing_description, matches_keywords, extract_date, is_within_last_month


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

                description = extract_listing_description(link, title)
                
                # Check if the job is within last month
                combined_text = title + " " + description
                job_date = extract_date(combined_text)
                if job_date and not is_within_last_month(job_date):
                    continue  # Skip old jobs

                save_job(
                    title=title,
                    link=absolute_link(base_url, href),
                    source="UPSC",
                    description=description,
                )
            except Exception:
                continue

        browser.close()
