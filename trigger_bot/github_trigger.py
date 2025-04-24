import csv
import os
import json
import requests
from datetime import datetime, timedelta
from croniter import croniter

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_ORG = os.getenv("GITHUB_ORG", "your-org")  # Replace with your GitHub org/user

CSV_FILE = "trigger_bot/triggers.csv"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Memory-only last trigger tracking
last_trigger_times = {}

def should_trigger_by_cron(cron_expr, now, repo):
    if not cron_expr.strip():
        return False

    cron_iter = croniter(cron_expr.strip(), now)
    previous_time = cron_iter.get_prev(datetime)
    time_diff = now - previous_time

    if time_diff <= timedelta(minutes=10):
        last_trigger_times[repo] = now
        return True
    return False

def trigger_workflow(repo, workflow_file, branch, environment, inputs_json):
    url = f"https://api.github.com/repos/{GITHUB_ORG}/{repo}/actions/workflows/{workflow_file}/dispatches"

    try:
        inputs = json.loads(inputs_json) if inputs_json.strip() else {}
    except json.JSONDecodeError as e:
        print(f"[❌] Invalid JSON in repo {repo}: {e}")
        return

    # Optional: inject environment if present
    if environment:
        inputs["environment"] = environment

    payload = {
        "ref": branch
    }

    if inputs:
        payload["inputs"] = inputs

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 204:
        print(f"[{datetime.now()}] ✅ Triggered {repo}/{workflow_file} on '{branch}' with inputs: {inputs}")
    else:
        print(f"[{datetime.now()}] ❌ Failed to trigger {repo}: {response.status_code} - {response.text}")

def main():
    now = datetime.now().replace(second=0, microsecond=0)
    print(f"[🔍] Checking for trigger matches at {now.strftime('%H:%M')}")

    with open(CSV_FILE, newline='') as csvfile:
        rows = csv.DictReader(csvfile)
        for row in rows:
            repo = row["repo"]
            cron_expr = row["cron"]

            if repo in last_trigger_times:
                if now - last_trigger_times[repo] < timedelta(minutes=10):
                    continue

            if should_trigger_by_cron(cron_expr, now, repo):
                trigger_workflow(
                    repo=row["repo"],
                    workflow_file=row["workflow_file"],
                    branch=row["branch"],
                    environment=row.get("environment", ""),
                    inputs_json=row.get("inputs", "")
                )

if __name__ == "__main__":
    main()
