import requests

def scrape_jobs(keyword):
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        print("[ERROR] RemoteOK API failed")
        return []

    data = res.json()
    jobs = []

    for job in data[1:]:  # first item is metadata
        if keyword.lower() in job.get("position", "").lower():
            jobs.append({
                "title": job.get("position", "N/A"),
                "company": job.get("company", "N/A"),
                "link": job.get("url", "#")
            })

    print(f"[DEBUG] Found {len(jobs)} RemoteOK API jobs.")
    return jobs

