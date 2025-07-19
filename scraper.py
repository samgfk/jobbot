# scraper.py (FINAL with 4 proven scrapers)
import requests
from bs4 import BeautifulSoup
import json
import os

API_KEY = os.getenv("SCRAPERAPI_KEY")

def fetch_html(url):
    proxy_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}&render=true"
    response = requests.get(proxy_url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"[ERROR] Failed to fetch {url}: {response.status_code}")
        return ""

def scrape_remoteok():
    print("[SCRAPE] RemoteOK...", flush=True)
    html = fetch_html("https://remoteok.com")
    soup = BeautifulSoup(html, "html.parser")
    job_rows = soup.select("tr.job")

    print(f"[DEBUG] Found {len(job_rows)} jobs on RemoteOK", flush=True)
    jobs = []
    for row in job_rows:
        try:
            title = row.select_one("h2").text.strip()
            company = row.select_one(".companyLink").text.strip()
            link = "https://remoteok.com" + row.select_one("a")["href"]
            jobs.append({"title": title, "company": company, "url": link})
        except Exception as e:
            print(f"[ERROR] Skipping RemoteOK row: {e}", flush=True)
    return jobs

def scrape_weworkremotely():
    print("[SCRAPE] WeWorkRemotely...", flush=True)
    html = fetch_html("https://weworkremotely.com/remote-jobs")
    soup = BeautifulSoup(html, "html.parser")
    job_sections = soup.select("section.jobs li.feature")

    print(f"[DEBUG] Found {len(job_sections)} jobs on WWR", flush=True)
    jobs = []
    for job in job_sections:
        try:
            title = job.select_one("span.title").text.strip()
            company = job.select_one("span.company").text.strip()
            link = "https://weworkremotely.com" + job.select_one("a")["href"]
            jobs.append({"title": title, "company": company, "url": link})
        except Exception as e:
            print(f"[ERROR] Skipping WWR job: {e}", flush=True)
    return jobs

def scrape_remotive():
    print("[SCRAPE] Remotive...", flush=True)
    html = fetch_html("https://remotive.com/remote-jobs")
    soup = BeautifulSoup(html, "html.parser")
    job_cards = soup.select("div.job-list-card")

    print(f"[DEBUG] Found {len(job_cards)} jobs on Remotive", flush=True)
    jobs = []
    for card in job_cards:
        try:
            title = card.select_one("span.job-title").text.strip()
            company = card.select_one("span.company").text.strip()
            link = "https://remotive.com" + card.select_one("a")["href"]
            jobs.append({"title": title, "company": company, "url": link})
        except Exception as e:
            print(f"[ERROR] Skipping Remotive card: {e}", flush=True)
    return jobs

def scrape_jobspresso():
    print("[SCRAPE] Jobspresso...", flush=True)
    html = fetch_html("https://jobspresso.co/remote-work/")
    soup = BeautifulSoup(html, "html.parser")
    job_cards = soup.select("div.job_listing")

    print(f"[DEBUG] Found {len(job_cards)} jobs on Jobspresso", flush=True)
    jobs = []
    for card in job_cards:
        try:
            title = card.select_one("h3").text.strip()
            company = card.select_one("div.company").text.strip()
            link = card.select_one("a")["href"]
            jobs.append({"title": title, "company": company, "url": link})
        except Exception as e:
            print(f"[ERROR] Skipping Jobspresso job: {e}", flush=True)
    return jobs

def get_jobs():
    with open("config.json") as f:
        config = json.load(f)

    KEYWORDS = [kw.lower() for kw in config.get("keywords", [])]
    location_filter = config.get("location_filter", "").lower()
    MAX_RESULTS = config.get("max_results", 50)

    def location_allowed(text):
        if not location_filter.strip():
            return True
        return any(loc.strip() in text.lower() for loc in location_filter.split(","))

    all_jobs = []
    try:
        sources = [scrape_remoteok, scrape_weworkremotely, scrape_remotive, scrape_jobspresso]
        for scrape_fn in sources:
            scraped_jobs = scrape_fn()
            for job in scraped_jobs:
                combined_text = f"{job['title']} {job['company']} {job['url']}".lower()
                if any(kw in combined_text for kw in KEYWORDS) and location_allowed(combined_text):
                    all_jobs.append(job)
                    if len(all_jobs) >= MAX_RESULTS:
                        print("[LIMIT] Reached max results")
                        return all_jobs

        print(f"[SCRAPE] {len(all_jobs)} total jobs scraped", flush=True)
        return all_jobs

    except Exception as e:
        print(f"[ERROR] get_jobs failed: {e}", flush=True)
        return []
