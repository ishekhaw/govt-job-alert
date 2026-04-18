from playwright.sync_api import sync_playwright
from db import save_job
from scrapers.utils import absolute_link, extract_listing_description, extract_date, is_within_last_month

def scrape_ssc():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        base_url = "https://ssc.nic.in/"
        page.goto(base_url)

        # Wait for notices section
        page.wait_for_selector("a")

        links = page.query_selector_all("a")

        keywords = ["notice", "exam", "recruitment", "vacancy"]

        for link in links:
            try:
                text = link.inner_text().strip()
                href = link.get_attribute("href")

                if not text or not href:
                    continue

                text_lower = text.lower()

                # Smart filtering
                if any(k in text_lower for k in keywords):

                    # Avoid junk
                    if len(text) < 15:
                        continue

                    description = extract_listing_description(link, text)
                    
                    # Check if the job is within last month
                    combined_text = text + " " + description
                    job_date = extract_date(combined_text)
                    if job_date and not is_within_last_month(job_date):
                        continue  # Skip old jobs

                    save_job(
                        title=text,
                        link=absolute_link(base_url, href),
                        source="SSC",
                        description=description,
                    )

            except:
                continue

        browser.close()
