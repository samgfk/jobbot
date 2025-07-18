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
        for row in soup.select("div.job")[:MAX_RESULTS]:
            link_elem = row.select_one("a.preventLink")
            title_elem = row.select_one("h2")
            company_elem = row.select_one("h3")
            if not link_elem or not title_elem:
                continue

            full_url = "https://remoteok.io" + link_elem["href"]
            title = title_elem.text.strip()
            company = company_elem.text.strip() if company_elem else "Unknown"
            text = f"{title} {company}".lower()

            if location_allowed(text):
                jobs.append({
                    "title": title,
                    "company": company,
                    "link": full_url
                })
    except Exception as e:
        print(f"[ERROR] RemoteOK: {e}", flush=True)
    return jobs

