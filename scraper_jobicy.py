import requests
from bs4 import BeautifulSoup

def scrape_jobs(job_title):
    query = job_title.replace(" ", "-").lower()
    url = f"https://jobicy.com/search?q={query}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    job_cards = soup.select("div.job-list-item")

    jobs = []
    for job in job_cards:
        title_tag = job.select_one("h2.title")
        company_tag = job.select_one("span.company")
        link_tag = job.select_one("a")

        if title_tag and company_tag and link_tag:
            job_data = {
                "title": title_tag.text.strip(),
                "company": company_tag.text.strip(),
                "link": link_tag["href"]
            }
            jobs.append(job_data)

    print(f"[DEBUG] Found {len(jobs)} Jobicy jobs")
    return jobs
