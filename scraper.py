import os
import json
import time
import csv
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service

def get_jobs():
    with open("config.json") as f:
        config = json.load(f)

    KEYWORDS = [kw.lower() for kw in config.get("keywords", [])]
    MAX_RESULTS = config.get("max_results", 50)
    location_filter = config.get("location_filter", "").lower()

    def location_allowed(text):
        if not location_filter.strip():
            return True
        return any(loc.strip() in text.lower() for loc in location_filter.split(","))

    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # ✅ FIXED: Use uc.install() to get a working binary path on Railway
    driver = uc.Chrome(service=Service(uc.install()), options=options)

    all_jobs = []

    def scrape_remoteok():
        print("[SCRAPE] RemoteOK...")
        jobs = []
        try:
            driver.get("https://remoteok.com/remote-dev-jobs")
            time.sleep(3)
            rows = driver.find_elements(By.CSS_SELECTOR, "tr.job")
            for row in rows[:MAX_RESULTS]:
                try:
                    title = row.get_attribute("data-position") or "Remote Job"
                    company = row.get_attribute("data-company") or "Unknown"
                    href = row.find_element(By.CSS_SELECTOR, "a.preventLink").get_attribute("href")
                    text = f"{title} {company} {href}".lower()
                    if any(kw in text for kw in KEYWORDS) and location_allowed(text):
                        jobs.append({"url": href, "title": title, "company": company})
                except Exception:
                    continue
        except Exception as e:
            print(f"[ERROR] RemoteOK: {e}")
        return jobs

    def scrape_simplyhired():
        print("[SCRAPE] SimplyHired (Local)...")
        jobs = []
        try:
            driver.get("https://www.simplyhired.com/search?q=developer&l=" + location_filter)
            time.sleep(3)
            cards = driver.find_elements(By.CSS_SELECTOR, "div.SerpJob-jobCard")
            for card in cards[:MAX_RESULTS]:
                try:
                    title = card.find_element(By.CSS_SELECTOR, "a").text
                    href = card.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    company = card.find_element(By.CSS_SELECTOR, "span.JobPosting-labelWithIcon").text
                    text = f"{title} {company} {href}".lower()
                    if any(kw in text for kw in KEYWORDS) and location_allowed(text):
                        jobs.append({"url": href, "title": title, "company": company})
                except Exception:
                    continue
        except Exception as e:
            print(f"[ERROR] SimplyHired: {e}")
        return jobs

    def scrape_remoteco():
        print("[SCRAPE] Remote.co...")
        jobs = []
        try:
            driver.get("https://remote.co/remote-jobs/developer/")
            time.sleep(3)
            listings = driver.find_elements(By.CSS_SELECTOR, "li.job_listing")
            for row in listings[:MAX_RESULTS]:
                try:
                    a_tag = row.find_element(By.CSS_SELECTOR, "a")
                    href = a_tag.get_attribute("href")
                    title = a_tag.get_attribute("title")
                    company = row.find_element(By.CLASS_NAME, "company").text
                    text = f"{title} {company} {href}".lower()
                    if any(kw in title.lower() for kw in KEYWORDS) and location_allowed(text):
                        jobs.append({"url": href, "title": title, "company": company})
                except Exception:
                    continue
        except Exception as e:
            print(f"[ERROR] Remote.co: {e}")
        return jobs

    def scrape_local_usajobs():
        print("[SCRAPE] USAJobs (Local)...")
        jobs = []
        try:
            driver.get("https://www.usajobs.gov/Search/Results?k=developer&l=" + location_filter)
            time.sleep(3)
            cards = driver.find_elements(By.CSS_SELECTOR, "usajobs-search-result-item")
            for card in cards[:MAX_RESULTS]:
                try:
                    href = card.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    title = card.find_element(By.CSS_SELECTOR, "a").text
                    agency = card.find_element(By.CSS_SELECTOR, ".usajobs-search-result--agency-name").text
                    text = f"{title} {agency} {href}".lower()
                    if any(kw in text for kw in KEYWORDS) and location_allowed(text):
                        jobs.append({"url": href, "title": title, "company": agency})
                except Exception:
                    continue
        except Exception as e:
            print(f"[ERROR] USAJobs: {e}")
        return jobs

    for fn in [scrape_remoteok, scrape_remoteco, scrape_simplyhired, scrape_local_usajobs]:
        try:
            jobs = fn()
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[SCRAPE ERROR] {fn.__name__}: {e}")
        time.sleep(2)

    driver.quit()

    seen, unique = set(), []
    for j in all_jobs:
        if j["url"] not in seen:
            seen.add(j["url"])
            unique.append(j)
        if len(unique) >= MAX_RESULTS:
            break

    print(f"[SCRAPE] {len(unique)} unique jobs found")
    return unique
