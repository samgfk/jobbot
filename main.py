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

# Ensure usage.csv exists with header if it's new (added for robustness from earlier suggestions)
def initialize_usage_file():
    if not os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['email', 'last_scrape_timestamp'])
initialize_usage_file() # Call on app startup

@app.route('/')
def form():
    # Optional UI Tip: Add helper text for job titles in the form.
    # This would require modifying form.html to accept and display this.
    # For now, I'll just include the existing render.
    return render_template('form.html')

@app.route('/apply', methods=['POST'])
def apply():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        job_titles_raw = request.form.get('job_titles', '')
        resume = request.files.get('resume')

        if not name or not email:
            return "Missing required fields. Please fill out all fields.", 400
        if not resume or not resume.filename.lower().endswith('.pdf'):
            return "Please upload a PDF file only.", 400

        # Rate Limit Check
        now = time.time()
        usage_data = []
        if os.path.exists(USAGE_FILE):
            try: # Robustness for reading usage.csv
                with open(USAGE_FILE, 'r', newline='') as f:
                    reader = csv.reader(f)
                    # Skip header if it exists
                    first_row = next(reader, None)
                    if first_row and first_row[0] != 'email': # Simple check for header
                        usage_data.append(first_row) # If it's not a header, add it back
                    usage_data.extend(list(reader))
            except Exception as e:
                print(f"[ERROR] Could not read usage.csv: {e}. Starting with empty usage.", flush=True)
                usage_data = [] # Reset if file is corrupted

            for row in usage_data:
                if row and row[0] == email:
                    try: # Robustness for float conversion
                        last_time = float(row[1])
                        if now - last_time < 3600:
                            remaining_time_seconds = 3600 - (now - last_time)
                            minutes_left = int(remaining_time_seconds // 60)
                            seconds_left = int(remaining_time_seconds % 60)
                            return (
                                f"⏳ You can only perform a job search once per hour. Please try again in {minutes_left} minutes and {seconds_left} seconds.",
                                429
                            )
                    except ValueError:
                        print(f"[WARNING] Invalid timestamp '{row[1]}' for email '{row[0]}' in usage.csv. Treating as non-existent.", flush=True)
                        # If timestamp is invalid, treat as if user hasn't scraped recently

        # Save resume
        filename = f"{uuid.uuid4().hex}_{resume.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        resume.save(filepath)

        # Parse job titles (this already correctly handles blank input by resulting in an empty list)
        job_title_list = [j.strip().lower() for j in job_titles_raw.split(',') if j.strip()]

        # Save config
        config_data = {
            "name": name,
            "email": email,
            "keywords": job_title_list, # This correctly passes the (potentially empty) list
            "resume_path": filepath,
            "location_filter": "",
            "max_results": 50
        }

        with open("config.json", "w") as f:
            json.dump(config_data, f, indent=4)

        # Scrape jobs
        scraped_jobs = get_jobs()

        print("[DEBUG] Scraped jobs count:", len(scraped_jobs), flush=True)
        for job in scraped_jobs:
            print("[DEBUG] Job:", job, flush=True)

        # ✨ NEW: Check if no jobs found and redirect
        if not scraped_jobs:
            print("[WARNING] No jobs found for the provided keywords after scraping and filtering. Redirecting to no_jobs page.", flush=True)
            message = "No jobs were found matching your keywords. Please try broader terms like 'assistant', 'manager', or leave the field blank to see all jobs."
            return render_template('no_jobs.html', message=message)
        # ✨ END NEW

        # If jobs are found, proceed as usual
        with open('applied_jobs.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["title", "company", "url"])
            writer.writeheader()
            for job in scraped_jobs:
                writer.writerow(job)

        # Update rate limit log
        updated = False
        for i, row in enumerate(usage_data): # Iterate with index to modify in place
            if row and row[0] == email:
                usage_data[i][1] = str(now) # Update the timestamp in the list
                updated = True
                break
        if not updated:
            usage_data.append([email, str(now)])

        try: # Robustness for writing usage.csv
            with open(USAGE_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                # Re-write header if it was skipped or if file was new/empty
                if not os.path.exists(USAGE_FILE) or (not usage_data and os.path.getsize(USAGE_FILE) == 0):
                    writer.writerow(['email', 'last_scrape_timestamp'])
                writer.writerows(usage_data)
        except Exception as e:
            print(f"[ERROR] Could not write to usage.csv: {e}", flush=True)


        return render_template('success.html', name=name)

    except Exception as e:
        print(f"[ERROR] Exception occurred in /apply: {str(e)}", flush=True)
        return f"An internal server error occurred: {str(e)}", 500

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
        # Added check for file existence
        if not os.path.exists('applied_jobs.csv') or os.path.getsize('applied_jobs.csv') == 0:
            return render_template('log.html', jobs=[], message="No jobs have been applied to yet.") # Render with empty list
        with open('applied_jobs.csv', 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            jobs = list(reader)
        return render_template("log.html", jobs=jobs)
    except Exception as e:
        print(f"[ERROR] Error reading applied_jobs.csv: {str(e)}", flush=True)
        return f"Error reading log: {str(e)}", 500

@app.route("/download")
def download_log():
    try:
        file_path = os.path.join(os.getcwd(), "applied_jobs.csv")
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return "No log file to download.", 404
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        print(f"[ERROR] Error downloading log: {str(e)}", flush=True)
        return f"Error downloading log: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
