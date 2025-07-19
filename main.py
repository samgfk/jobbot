import csv
import json
import os
import time
import uuid
from flask import Flask, render_template, request, send_file
from scraper import get_jobs

app = Flask(__name__)
UPLOAD_FOLDER = 'resumes'
USAGE_FILE = 'usage.csv'
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
        job_titles_raw = request.form.get('job_titles', '')
        resume = request.files.get('resume')

        if not name or not email or not job_titles_raw:
            return "Missing required fields. Please fill out all fields.", 400
        if not resume or not resume.filename.lower().endswith('.pdf'):
            return "Please upload a PDF file only.", 400

        # ✅ Rate Limit Check
        now = time.time()
        usage_data = []
        if os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, 'r') as f:
                reader = csv.reader(f)
                usage_data = list(reader)

            for row in usage_data:
                if row and row[0] == email:
                    last_time = float(row[1])
                    if now - last_time < 3600:
                        return "⏳ You can only perform a job search once per hour. Please try again later.", 429

        # Save resume
        filename = f"{uuid.uuid4().hex}_{resume.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        resume.save(filepath)

        # Parse job titles
        job_title_list = [j.strip().lower() for j in job_titles_raw.split(',') if j.strip()]

        # Save config
        config_data = {
            "name": name,
            "email": email,
            "keywords": job_title_list,
            "resume_path": filepath,
            "location_filter": "",
            "max_results": 50
        }

        with open("config.json", "w") as f:
            json.dump(config_data, f, indent=4)

        # Scrape jobs (LIMIT RESULTS)
        scraped_jobs = get_jobs()
        

        print("[DEBUG] Scraped jobs count:", len(scraped_jobs))
        for job in scraped_jobs:
            print("[DEBUG] Job:", job)

        if not scraped_jobs:
            print("[WARNING] No jobs found. Check keyword match or site blocks.")

        with open('applied_jobs.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["title", "company", "url"])
            writer.writeheader()
            for job in scraped_jobs:
                writer.writerow(job)

        # ✅ Update rate limit log
        updated = False
        for row in usage_data:
            if row and row[0] == email:
                row[1] = str(now)
                updated = True
        if not updated:
            usage_data.append([email, str(now)])

        with open(USAGE_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(usage_data)

        return render_template('success.html', name=name)

    except Exception as e:
        print("[ERROR] Exception occurred:", str(e))
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
            reader = csv.DictReader(f)
            jobs = list(reader)
        return render_template("log.html", jobs=jobs)
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
