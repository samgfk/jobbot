import requests
from bs4 import BeautifulSoup

def scrape_jobs(job_title):
    url = f"https://remoteok.com/remote-{job_title.replace(' ', '-')}-jobs"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    job_rows = soup.select("tr.job")

    jobs = []
    for job in job_rows:
        title_tag = job.select_one("h2")
        company_tag = job.select_one(".companyLink span")
        link_tag = job.select_one("a.preventLink")

        if title_tag and company_tag and link_tag:
            jobs.append({
                "title": title_tag.text.strip(),
                "company": company_tag.text.strip(),
                "link": f"https://remoteok.com{link_tag['href']}"
            })

    print(f"[DEBUG] Found {len(jobs)} RemoteOK jobs.")
    return jobs


