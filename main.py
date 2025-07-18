import csv
import json
import os
import uuid
from flask import Flask, render_template, request
import asyncio
from scraper_playwright import scrape_jobs
from flask import send_file

app = Flask(__name__)
UPLOAD_FOLDER = 'resumes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/apply', methods=['POST'])
def apply():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        job_titles = request.form.get('job_titles')
        resume = request.files.get('resume')

        # Validate required fields
        if not name or not email or not job_titles:
            return "Missing required fields. Please fill out all fields.", 400

        if not resume or not resume.filename:
            return "Resume upload failed. Please select a PDF file.", 400

        if not resume.filename.lower().endswith('.pdf'):
            return "Please upload a PDF file only.", 400

        # Save uploaded resume
        filename = f"{uuid.uuid4().hex}_{resume.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        resume.save(filepath)

        # Save config JSON
        job_title_list = [j.strip() for j in job_titles.split(',') if j.strip()]
        config_data = {
            "name": name,
            "email": email,
            "job_titles": job_title_list,
            "resume_path": filepath,
            "location": "Los Angeles"  # Can change to user input later
        }

        with open("config.json", "w") as f:
            json.dump(config_data, f, indent=4)

        # Now scrape jobs and write to CSV
        scraped_jobs = []

        for title in job_title_list:
            jobs = asyncio.run(scrape_jobs(title))
            print(f"[DEBUG] Scraped {len(jobs)} jobs for title: {title}")
            print(f"[DEBUG] Raw scrape_jobs() result for '{title}': {jobs}")
            for job in jobs:
                print(f"[DEBUG] Job Found → Title: {job.get('title')} | Company: {job.get('company')} | Link: {job.get('link')}")
            scraped_jobs.extend(jobs)


        print(f"[DEBUG] Total jobs to write: {len(scraped_jobs)}")



        # Write results to CSV
        with open('applied_jobs.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["title", "company", "link"])
            writer.writeheader()
            for job in scraped_jobs:
                writer.writerow(job)

        return render_template('success.html', name=name)

    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route('/dashboard')
def dashboard():
    return view_log()


@app.errorhandler(404)
def not_found(error):
    return "Page not found", 404

@app.errorhandler(500)
def internal_error(error):
    return "Internal server error", 500

@app.route("/log")
def view_log():
    try:
        with open('applied_jobs.csv', 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)

        table_html = "<table class='table table-striped table-bordered'>"
        table_html += "<thead><tr>" + "".join([f"<th>{header}</th>" for header in headers]) + "</tr></thead><tbody>"

        for row in rows:
            table_html += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"

        table_html += "</tbody></table>"

        return render_template("log.html", table=table_html)
    except Exception as e:
        return f"Error reading log: {str(e)}"

@app.route("/download")
def download_log():
    try:
        file_path = os.path.join(os.getcwd(), "applied_jobs.csv")
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"Error downloading log: {str(e)}"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)

