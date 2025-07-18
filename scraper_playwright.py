import asyncio
from playwright.async_api import async_playwright

async def scrape_jobs(keyword):
    jobs = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = f"https://remoteok.com/remote-{keyword.replace(' ', '-')}-jobs"
        await page.goto(url)
        await page.wait_for_timeout(3000)  # wait for JS to load

        job_elements = await page.query_selector_all("tr.job")
        for job in job_elements:
            try:
                title = await job.query_selector("h2")
                company = await job.query_selector(".companyLink span")
                link = await job.query_selector("a.preventLink")
                if title and company and link:
                    jobs.append({
                        "title": await title.inner_text(),
                        "company": await company.inner_text(),
                        "link": "https://remoteok.com" + await link.get_attribute("href")
                    })
            except:
                continue
        await browser.close()
    return jobs
