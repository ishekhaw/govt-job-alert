from db import export_jobs_data, clear_old_data
from scrapers.ibps import scrape_ibps
from scrapers.kvs import scrape_kvs
from scrapers.nta import scrape_nta
from scrapers.rrb import scrape_rrb
from scrapers.ssc import scrape_ssc
from scrapers.upsc import scrape_upsc


def run_step(label, scraper):
    print(f"Running {label} scraper...")
    try:
        scraper()
    except Exception as error:
        print(f"{label} scraper failed: {error}")


def run_all():
    print("Clearing old data...")
    clear_old_data()
    
    run_step("SSC", scrape_ssc)
    run_step("IBPS", scrape_ibps)
    run_step("UPSC", scrape_upsc)
    run_step("KVS", scrape_kvs)
    run_step("NTA", scrape_nta)
    run_step("RRB", scrape_rrb)

    export_path = export_jobs_data()
    print(f"Exported site data to {export_path}.")
    print("All scrapers completed.")


if __name__ == "__main__":
    run_all()
