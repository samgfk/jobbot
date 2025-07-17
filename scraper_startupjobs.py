import requests
from bs4 import BeautifulSoup

def scrape_startup_jobs(job_title):
    query = job_title.replace(" ", "+")
    url = f"https://startup.jobs/search?query={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    job_rows = soup.select("div.job-info")

    jobs = []
    for job in job_rows:
        title_tag = job.select_one("h3")
        company_tag = job.select_one("h4")
        link_tag = job.find_parent("a")

        if title_tag and company_tag and link_tag:
            jobs.append({
                "title": title_tag.text.strip(),
                "company": company_tag.text.strip(),
                "link": "https://startup.jobs" + link_tag['href']
            })

    print(f"[DEBUG] Found {len(jobs)} startup jobs")
    return jobs
