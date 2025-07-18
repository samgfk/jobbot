import os
import json
import time
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

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

    def init_driver():
        options = uc.ChromeOptions()
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/google-chrome")
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
        return uc.Chrome(
            options=options,
            driver_executable_path=driver_path,
            browser_executable_path="/usr/bin/chromium"
        )

        


    all_jobs = []

    def scrape_remoteok():
        print("[SCRAPE] RemoteOK...", flush=True)
        jobs = []
        driver = init_driver()
        try:
            driver.get("https://remoteok.com/remote-dev-jobs")
            time.sleep(3)
            print("[DEBUG] Page Source Length:", len(driver.page_source))
            print(driver.page_source[:500])

            rows = driver.find_elements(By.CSS_SELECTOR, "tr.job")
            for row in rows:
                try:
                    title = row.get_attribute("data-position") or "Remote Job"
                    company = row.get_attribute("data-company") or "Unknown"
                    href = row.find_element(By.CSS_SELECTOR, "a.preventLink").get_attribute("href")
                    text = f"{title} {company} {href}".lower()
                    if any(kw in text for kw in KEYWORDS) and location_allowed(text):
                        jobs.append({"url": href, "title": title, "company": company})
                except:
                    continue
        except Exception as e:
            print(f"[ERROR] RemoteOK: {e}", flush=True)
        driver.quit()
        return jobs

    def scrape_remoteco():
        print("[SCRAPE] Remote.co...", flush=True)
        jobs = []
        driver = init_driver()
        try:
            driver.get("https://remote.co/remote-jobs/developer/")
            time.sleep(3)
            print("[DEBUG] Page Source Length:", len(driver.page_source))
            print(driver.page_source[:500])

            listings = driver.find_elements(By.CSS_SELECTOR, "li.job_listing")
            for row in listings:
                try:
                    a_tag = row.find_element(By.CSS_SELECTOR, "a")
                    href = a_tag.get_attribute("href")
                    title = a_tag.get_attribute("title")
                    company = row.find_element(By.CLASS_NAME, "company").text
                    text = f"{title} {company} {href}".lower()
                    if any(kw in title.lower() for kw in KEYWORDS) and location_allowed(text):
                        jobs.append({"url": href, "title": title, "company": company})
                except:
                    continue
        except Exception as e:
            print(f"[ERROR] Remote.co: {e}", flush=True)
        driver.quit()
        return jobs

    def scrape_simplyhired():
        print("[SCRAPE] SimplyHired...", flush=True)
        jobs = []
        driver = init_driver()
        try:
            driver.get(f"https://www.simplyhired.com/search?q=developer&l={location_filter}")
            time.sleep(3)
            print("[DEBUG] Page Source Length:", len(driver.page_source))
            print(driver.page_source[:500])

            cards = driver.find_elements(By.CSS_SELECTOR, "div.SerpJob-jobCard")
            for card in cards:
                try:
                    title = card.find_element(By.CSS_SELECTOR, "a").text
                    href = card.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    company = card.find_element(By.CSS_SELECTOR, "span.JobPosting-labelWithIcon").text
                    text = f"{title} {company} {href}".lower()
                    if any(kw in text for kw in KEYWORDS) and location_allowed(text):
                        jobs.append({"url": href, "title": title, "company": company})
                except:
                    continue
        except Exception as e:
            print(f"[ERROR] SimplyHired: {e}", flush=True)
        driver.quit()
        return jobs

    def scrape_usajobs():
        print("[SCRAPE] USAJobs...", flush=True)
        jobs = []
        driver = init_driver()
        try:
            driver.get(f"https://www.usajobs.gov/Search/Results?k=developer&l={location_filter}")
            time.sleep(3)
            print("[DEBUG] Page Source Length:", len(driver.page_source))
            print(driver.page_source[:500])

            cards = driver.find_elements(By.CSS_SELECTOR, "usajobs-search-result-item")
            for card in cards:
                try:
                    href = card.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    title = card.find_element(By.CSS_SELECTOR, "a").text
                    agency = card.find_element(By.CSS_SELECTOR, ".usajobs-search-result--agency-name").text
                    text = f"{title} {agency} {href}".lower()
                    if any(kw in text for kw in KEYWORDS) and location_allowed(text):
                        jobs.append({"url": href, "title": title, "company": agency})
                except:
                    continue
        except Exception as e:
            print(f"[ERROR] USAJobs: {e}", flush=True)
        driver.quit()
        return jobs

    def scrape_remotive():
        print("[SCRAPE] Remotive...", flush=True)
        jobs = []
        driver = init_driver()
        try:
            driver.get("https://remotive.io/remote-jobs/software-dev")
            time.sleep(3)
            print("[DEBUG] Page Source Length:", len(driver.page_source))
            print(driver.page_source[:500])

            job_cards = driver.find_elements(By.CSS_SELECTOR, "a[data-job-id]")

            for card in job_cards:
                try:
                    title = card.find_element(By.CSS_SELECTOR, "div.job-tile-title").text
                    company = card.find_element(By.CSS_SELECTOR, "div.job-tile-company").text
                    href = card.get_attribute("href")
                    text = f"{title} {company} {href}".lower()
                    if any(kw in text for kw in KEYWORDS) and location_allowed(text):
                        jobs.append({"url": href, "title": title, "company": company})
                except:
                    continue

        except Exception as e:
            print(f"[ERROR] Remotive: {e}", flush=True)
        driver.quit()
        return jobs

    for fn in [scrape_remoteok, scrape_remoteco, scrape_remotive, scrape_simplyhired, scrape_usajobs]:
        try:
            jobs = fn()
            print(f"[DEBUG] {fn.__name__}() → {len(jobs)} jobs", flush=True)
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[SCRAPE ERROR] {fn.__name__}: {e}", flush=True)
        time.sleep(2)

    seen, unique = set(), []
    for j in all_jobs:
        if j["url"] not in seen:
            seen.add(j["url"])
            unique.append(j)
        if len(unique) >= MAX_RESULTS:
            break

    print(f"[SCRAPE] {len(unique)} unique jobs found", flush=True)
    return unique
