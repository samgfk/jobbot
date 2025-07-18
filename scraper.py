import os
import csv
import time
import json
import requests
import datetime
from bs4 import BeautifulSoup

CONFIG_FILE = "config.json"
with open(CONFIG_FILE) as f:
    config = json.load(f)

KEYWORDS = [kw.lower() for kw in config.get("keywords", [])]
MAX_RESULTS = config.get("max_results", 50)
CSV_PATH = "applied_jobs.csv"

def location_allowed(text):
    raw = config.get("location_filter", "")
    if not raw.strip():
        return True
    locs = [loc.strip().lower() for loc in raw.split(",") if loc.strip()]
    text = text.lower()
    return any(loc in text for loc in locs)

def scrape_remotive():
    print("[SCRAPE] Remotive...")
    url = "https://remotive.io/remote-jobs/software-dev"
    jobs = []
    try:
        r = requests.get(url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        for tile in soup.select("div.job-tile")[:MAX_RESULTS]:
            t = tile.select_one(".job-tile-title")
            l = tile.select_one("a")
            c = tile.select_one(".job-tile-company")
            if not (t and l): continue
            title = t.get_text(strip=True)
            company = c.get_text(strip=True) if c else "Unknown"
            href = l["href"]
            full = href if href.startswith("http") else f"https://remotive.io{href}"
            text = (title + " " + company + " " + full).lower()
            if any(kw in text for kw in KEYWORDS) and location_allowed(text):
                jobs.append({"url": full, "title": title, "company": company})
    except Exception as e:
        print(f"[ERROR] Remotive: {e}")
    return jobs

def scrape_remoteok():
    print("[SCRAPE] RemoteOK...")
    url = "https://remoteok.io/remote-dev-jobs"
    jobs = []
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        for row in soup.select("tr.job")[:MAX_RESULTS]:
            l = row.select_one("a.preventLink")
            if not l: continue
            full_url = "https://remoteok.io" + l["href"]
            title = row.get("data-position", "Remote Job")
            company = row.get("data-company", "Unknown")
            text = (title + " " + company + " " + full_url).lower()
            if any(kw in text for kw in KEYWORDS) and location_allowed(text):
                jobs.append({"url": full_url, "title": title, "company": company})
    except Exception as e:
        print(f"[ERROR] RemoteOK: {e}")
    return jobs

def scrape_weworkremotely():
    print("[SCRAPE] WeWorkRemotely...")
    url = "https://weworkremotely.com/categories/remote-programming-jobs"
    jobs = []
    try:
        r = requests.get(url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        for sec in soup.select("section.jobs li.feature")[:MAX_RESULTS]:
            l = sec.select_one("a")
            if not l: continue
            href = l["href"]
            full_url = "https://weworkremotely.com" + href
            title = sec.get_text(strip=True)
            text = (title + " " + full_url).lower()
            if any(kw in title.lower() for kw in KEYWORDS) and location_allowed(text):
                jobs.append({"url": full_url, "title": title, "company": "Unknown"})
    except Exception as e:
        print(f"[ERROR] WWR: {e}")
    return jobs

def scrape_jobspresso():
    print("[SCRAPE] Jobspresso...")
    url = "https://jobspresso.co/remote-developer-jobs/"
    jobs = []
    try:
        r = requests.get(url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        for li in soup.select("ul.jobs li.job_listing")[:MAX_RESULTS]:
            a = li.select_one("a")
            if not a: continue
            href = a["href"]
            title = a.get("title", "Remote Job")
            company = li.select_one(".company")
            company_name = company.get_text(strip=True) if company else "Unknown"
            text = (title + " " + company_name + " " + href).lower()
            if any(kw in title.lower() for kw in KEYWORDS) and location_allowed(text):
                jobs.append({"url": href, "title": title, "company": company_name})
    except Exception as e:
        print(f"[ERROR] Jobspresso: {e}")
    return jobs

def scrape_remoteco():
    print("[SCRAPE] Remote.co...")
    url = "https://remote.co/remote-jobs/developer/"
    jobs = []
    try:
        r = requests.get(url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        for row in soup.select("li.job_listing")[:MAX_RESULTS]:
            a = row.select_one("a")
            if not a: continue
            href = a["href"]
            title = a.get("title", "Remote Job")
            company = row.select_one(".company")
            company_name = company.get_text(strip=True) if company else "Unknown"
            text = (title + " " + company_name + " " + href).lower()
            if any(kw in title.lower() for kw in KEYWORDS) and location_allowed(text):
                jobs.append({"url": href, "title": title, "company": company_name})
    except Exception as e:
        print(f"[ERROR] Remote.co: {e}")
    return jobs

def get_jobs():
    all_jobs = []
    for fn in (scrape_remotive, scrape_remoteok, scrape_weworkremotely, scrape_jobspresso, scrape_remoteco):
        try:
            jobs = fn()
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[SCRAPE ERROR] {fn.__name__}: {e}")
        time.sleep(2)

    seen, unique = set(), []
    for j in all_jobs:
        if j["url"] not in seen:
            seen.add(j["url"])
            unique.append(j)
        if len(unique) >= MAX_RESULTS:
            break

    print(f"[SCRAPE] {len(unique)} unique jobs found")
    return unique
