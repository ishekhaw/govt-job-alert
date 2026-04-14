from playwright.sync_api import sync_playwright
from db import save_job
from scrapers.utils import absolute_link, extract_listing_description

def scrape_ibps():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        base_url = "https://www.ibps.in/"
        page.goto(base_url)

        page.wait_for_load_state("networkidle")

        links = page.query_selector_all("a")

        for link in links:
            text = link.inner_text()

            if text and ("Recruitment" in text or "CRP" in text):
                href = link.get_attribute("href")

                if href:
                    title = text.strip()
                    description = extract_listing_description(link, title)
                    save_job(title, absolute_link(base_url, href), "IBPS", description)

        browser.close()
