import requests
from bs4 import BeautifulSoup

def scrape_jobicy(keyword):
    print(f"[SCRAPE] Jobicy for: {keyword}...", flush=True)
    url = f"https://jobicy.com/jobs/?q={keyword.lower().replace(' ', '+')}"
    jobs = []
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        listings = soup.select("article.job-list-item")
        for job in listings[:20]:
            title_elem = job.select_one("h2")
            company_elem = job.select_one("div.company")
            link_elem = job.select_one("a")

            if not title_elem or not link_elem:
                continue

            jobs.append({
                "title": title_elem.text.strip(),
                "company": company_elem.text.strip() if company_elem else "Unknown",
                "link": link_elem["href"]
            })

    except Exception as e:
        print(f"[ERROR] Jobicy: {e}", flush=True)

    return jobs

