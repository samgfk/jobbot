import requests
from bs4 import BeautifulSoup

MAX_RESULTS = 20

def location_allowed(text):
    return "remote" in text.lower()

def scrape_remoteok(keyword):
    print(f"[SCRAPE] RemoteOK for: {keyword}...", flush=True)
    url = f"https://remoteok.io/remote-{keyword.lower().replace(' ', '-')}-jobs"
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
            if location_allowed(text):
                jobs.append({"title": title, "company": company, "link": full_url})
    except Exception as e:
        print(f"[ERROR] RemoteOK: {e}", flush=True)
    return jobs
