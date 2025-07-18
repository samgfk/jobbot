import requests
from bs4 import BeautifulSoup

MAX_RESULTS = 20

def scrape_jobicy(keyword):
    print(f"[SCRAPE] Jobicy for: {keyword}...", flush=True)
    jobs = []
    try:
        url = f"https://jobicy.com/jobs/?q={keyword}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        listings = soup.select('div.job-list-item')

        for listing in listings[:MAX_RESULTS]:
            title_elem = listing.select_one('h2 a')
            company_elem = listing.select_one('.job-company')
            link = title_elem['href'] if title_elem else None
            title = title_elem.text.strip() if title_elem else "Untitled"
            company = company_elem.text.strip() if company_elem else "Unknown"

            if link:
                jobs.append({
                    "title": title,
                    "company": company,
                    "link": link
                })

    except Exception as e:
        print(f"[ERROR] Jobicy: {e}", flush=True)
    return jobs
