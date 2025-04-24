import csv
import os
import json
import requests
from datetime import datetime, timedelta
from croniter import croniter

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_ORG = os.getenv("GITHUB_ORG", "your-org")  # Replace this with your GitHub username or org

CSV_FILE = "trigger_bot/triggers.csv"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Store the last run times of workflows in memory (no need for file)
last_trigger_times = {}

def should_trigger_by_cron(cron_expr, now, repo):
    if not cron_expr.strip():
        return False

    # Get the previous cron time from the croniter
    cron_iter = croniter(cron_expr.strip(), now)
    previous_time = cron_iter.get_prev(datetime)

    # Calculate the time difference between now and the last cron time
    time_diff = now - previous_time
    if time_diff <= timedelta(minutes=10):
        last_trigger_times[repo] = now  # Update last trigger time for the repo
        return True
    return False

def trigger_workflow(repo, workflow_file, branch, environment, inputs_json):
    url = f"https://api.github.com/repos/{GITHUB_ORG}/{repo}/actions/workflows/{workflow_file}/dispatches"
    try:
        inputs = json.loads(inputs_json) if inputs_json else {}
    except json.JSONDecodeError as e:
        print(f"[❌] Invalid JSON for inputs in repo {repo}: {e}")
        return

    if environment:
        inputs["environment"] = environment

    payload = {
        "ref": branch,
        "inputs": inputs
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 204:
        print(f"[{datetime.now()}] ✅ Triggered {repo}/{workflow_file} with inputs {inputs}")
    else:
        print(f"[{datetime.now()}] ❌ Failed: {response.status_code} - {response.text}")

def main():
    now = datetime.now().replace(second=0, microsecond=0)
    print(f"[🔍] Checking for trigger match at {now.strftime('%H:%M')}")

    with open(CSV_FILE, newline='') as csvfile:
        rows = csv.DictReader(csvfile)
        for row in rows:
            repo = row["repo"]
            cron_expr = row["cron"]

            # Check if the repo is already triggered in the last 10 minutes
            if repo in last_trigger_times:
                last_trigger_time = last_trigger_times[repo]
                if now - last_trigger_time < timedelta(minutes=10):
                    print(f"[ℹ️] Skipping {repo}, already triggered within the last 10 minutes.")
                    continue

            # Check cron condition
            if should_trigger_by_cron(cron_expr, now, repo):
                trigger_workflow(
                    repo=row["repo"],
                    workflow_file=row["workflow_file"],
                    branch=row["branch"],
                    environment=row["environment"],
                    inputs_json=row.get("inputs", "")
                )

if __name__ == "__main__":
    main()
