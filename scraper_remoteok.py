import requests
from bs4 import BeautifulSoup

def scrape_jobs(keyword):
    url = "https://weworkremotely.com/categories/remote-programming-jobs"
    jobs = []
    try:
        r = requests.get(url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        for sec in soup.select("section.jobs li.feature"):
            l = sec.select_one("a")
            if not l:
                continue
            href = l["href"]
            full_url = "https://weworkremotely.com" + href
            title = sec.get_text(strip=True)

            if keyword.lower() in title.lower():
                jobs.append({
                    "title": title,
                    "company": "Unknown",
                    "link": full_url
                })

    except Exception as e:
        print(f"[ERROR] WWR: {e}")
    print(f"[DEBUG] Found {len(jobs)} jobs from WeWorkRemotely.")
    return jobs
