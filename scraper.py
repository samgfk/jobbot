import os
import json
import time
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
# You might need to import requests if you use it in scrape_simplyhired
# import requests 

def init_driver():
    """
    Initializes and returns an undetected_chromedriver instance
    with necessary options for headless execution in a Docker/Railway environment.
    Explicitly points to pre-installed Chromium and Chromedriver executables.
    """
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")

    # Explicitly define paths based on your Dockerfile installation
    # This is CRITICAL for undetected_chromedriver to find them in the container
    driver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    browser_path = '/usr/bin/chromium'

    print(f"[DEBUG] Initializing uc.Chrome with browser_executable_path: {browser_path}", flush=True)
    print(f"[DEBUG] Initializing uc.Chrome with driver_executable_path: {driver_path}", flush=True)

    return uc.Chrome(
        options=options,
        driver_executable_path=driver_path,
        browser_executable_path=browser_path
    )

def scrape_remoteok(driver):
    """
    Scrapes job listings from RemoteOK.com using the provided driver.
    Note: Selectors might need manual verification against the live site.
    """
    print("[SCRAPE] RemoteOK...", flush=True)

    driver.get("https://remoteok.com/")
    time.sleep(3) # Consider increasing this or using WebDriverWait if content loads slowly

    job_rows = driver.find_elements(By.XPATH, '//tr[@class="job"]')
    print(f"[DEBUG] Found {len(job_rows)} job rows on RemoteOK.com", flush=True)

    jobs = []

    for row in job_rows:
        try:
            # Example of how to potentially filter sponsored jobs if they have a distinct class or attribute
            # This is a common pattern, but you need to verify it on the live site.
            if "featured" in row.get_attribute("class") or row.get_attribute("data-promoted") == "true":
                continue # Skip featured/promoted jobs

            title = row.find_element(By.TAG_NAME, "h2").text.strip()
            company = row.find_element(By.CLASS_NAME, "companyLink").text.strip()
            link = row.find_element(By.TAG_NAME, "a").get_attribute("href")

            jobs.append({
                "title": title,
                "company": company,
                "link": link
            })

        except Exception as e:
            # Log the specific error for debugging individual rows
            print(f"[ERROR] RemoteOK: Skipping row due to error: {e}", flush=True)
            continue # Continue to the next row even if one fails

    return jobs

# --- Original get_jobs function (modified to integrate the new scrape_xxx structure) ---
def get_jobs():
    with open("config.json") as f:
        config = json.load(f)
        print("[DEBUG] config =", config, flush=True)

    KEYWORDS = [kw.lower() for kw in config.get("keywords", [])]
    MAX_RESULTS = config.get("max_results", 50)
    location_filter = config.get("location_filter", "").lower()

    def location_allowed(text):
        if not location_filter.strip():
            return True
        return any(loc.strip() in text.lower() for loc in location_filter.split(","))

    all_jobs = []

    # Initialize the driver once and pass it to functions
    driver = None
    try:
        driver = init_driver()

        # List of scraper functions to run
        # Note: You need to implement/re-add scrape_remoteco, scrape_remotive, etc.,
        # similar to scrape_remoteok if they are still part of your overall plan.
        # For this example, we'll just run scrape_remoteok.
        scraper_functions = [
            # Each function should accept 'driver' as an argument
            lambda d: scrape_remoteok(d),
            # Add other scraper functions here once they are updated and verified
            # lambda d: scrape_remoteco(d),
            # lambda d: scrape_remotive(d),
            # lambda d: scrape_simplyhired(d), # Likely still blocked by Cloudflare
            # lambda d: scrape_usajobs(d),
        ]

        for fn_wrapper in scraper_functions:
            try:
                jobs = fn_wrapper(driver) # Pass the shared driver instance
                # Apply your filtering logic here after scraping
                filtered_jobs = []
                for job in jobs:
                    combined_text = f"{job.get('title', '')} {job.get('company', '')} {job.get('link', '')}".lower()
                    if any(kw in combined_text for kw in KEYWORDS) and location_allowed(combined_text):
                        filtered_jobs.append(job)
                
                print(f"[DEBUG] {fn_wrapper.__name__}() -> {len(filtered_jobs)} filtered jobs", flush=True)
                all_jobs.extend(filtered_jobs)
            except Exception as e:
                # Catch specific errors from within the scrape_xxx functions
                print(f"[SCRAPE ERROR] {fn_wrapper.__name__}: {e}", flush=True)
            time.sleep(2) # Short delay between scraping different sites

    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to initialize driver or run scrapers: {e}", flush=True)
    finally:
        if driver:
            driver.quit() # Ensure the browser is closed even if errors occur

    seen, unique = set(), []
    for j in all_jobs:
        if j["link"] not in seen: # Use 'link' for uniqueness, not 'url' as per your scrape_remoteok output
            seen.add(j["link"])
            unique.append(j)
        if len(unique) >= MAX_RESULTS:
            break

    print(f"[SCRAPE] {len(unique)} unique jobs found total", flush=True)
    return unique

# Example usage if you want to test this file directly
if __name__ == "__main__":
    # Create a dummy config.json for testing if it doesn't exist
    if not os.path.exists("config.json"):
        dummy_config = {
            "keywords": ["engineer", "developer"],
            "location_filter": "",
            "max_results": 5
        }
        with open("config.json", "w") as f:
            json.dump(dummy_config, f, indent=4)
        print("Created a dummy config.json for testing.", flush=True)

    scraped_data = get_jobs()
    print("\n--- Final Scraped Jobs ---", flush=True)
    for job in scraped_data:
        print(job, flush=True)

    # Example of writing to CSV (your original code might already do this in main.py)
    # csv_file = "applied_jobs.csv"
    # fieldnames = ["title", "company", "link"] # Adjust based on your actual data keys
    #
    # try:
    #     with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    #         writer = csv.DictWriter(f, fieldnames=fieldnames)
    #         writer.writeheader()
    #         writer.writerows(scraped_data)
    #     print(f"\nScraped data saved to {csv_file}", flush=True)
    # except Exception as e:
    #     print(f"Error writing to CSV: {e}", flush=True)
