# scraper.py (Updated with Jobicy + Himalayas)
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

def scrape_jobicy():
    print("[SCRAPE] Jobicy...", flush=True)
    html = fetch_html("https://jobicy.com/remote-jobs")
    soup = BeautifulSoup(html, "html.parser")
    job_cards = soup.select("article.job-list li")

    print(f"[DEBUG] Found {len(job_cards)} jobs on Jobicy", flush=True)

    jobs = []
    for card in job_cards:
        try:
            title = card.select_one(".job-title a").text.strip()
            company = card.select_one(".job-company").text.strip()
            link = card.select_one(".job-title a")["href"]
            jobs.append({"title": title, "company": company, "url": link})
        except Exception as e:
            print(f"[ERROR] Skipping Jobicy card: {e}", flush=True)

    return jobs

def scrape_himalayas():
    print("[SCRAPE] Himalayas...", flush=True)
    html = fetch_html("https://himalayas.app/jobs")
    soup = BeautifulSoup(html, "html.parser")
    job_cards = soup.select("a[class*='JobPreview']")

    print(f"[DEBUG] Found {len(job_cards)} jobs on Himalayas", flush=True)

    jobs = []
    for card in job_cards:
        try:
            title = card.select_one("h3").text.strip()
            company = card.select_one(".styles_company__Q0w6Y").text.strip()
            link = "https://himalayas.app" + card["href"]
            jobs.append({"title": title, "company": company, "url": link})
        except Exception as e:
            print(f"[ERROR] Skipping Himalayas card: {e}", flush=True)

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
        sources = [scrape_remoteok, scrape_jobicy, scrape_himalayas]
        for scrape_fn in sources:
            scraped_jobs = scrape_fn()
            for job in scraped_jobs:
                combined_text = f"{job['title']} {job['company']} {job['url']}".lower()
                if any(kw in combined_text for kw in KEYWORDS) and location_allowed(combined_text):
                    all_jobs.append(job)
                    if len(all_jobs) >= MAX_RESULTS:
                        print("[LIMIT] Reached max results")
                        return all_jobs

        print(f"[SCRAPE] {len(all_jobs)} unique jobs found", flush=True)
        return all_jobs

    except Exception as e:
        print(f"[ERROR] get_jobs failed: {e}", flush=True)
        return []
