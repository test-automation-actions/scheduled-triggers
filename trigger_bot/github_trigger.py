import csv
import os
import json
import requests
from datetime import datetime, timedelta
from croniter import croniter

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_ORG = os.getenv("GITHUB_ORG", "your-org")
CSV_FILE = "trigger_bot/triggers.csv"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

last_trigger_times = {}

def should_trigger_by_cron(cron_expr, now, repo):
    try:
        cron_iter = croniter(cron_expr.strip(), now)
        previous_time = cron_iter.get_prev(datetime)
        time_diff = now - previous_time
        if time_diff <= timedelta(minutes=10):
            last_trigger_times[repo] = now
            return True
    except Exception as e:
        print(f"Error parsing cron for {repo}: {e}")
    return False

def trigger_workflow(repo, workflow_file, branch, inputs_json):
    url = f"https://api.github.com/repos/{GITHUB_ORG}/{repo}/actions/workflows/{workflow_file}/dispatches"
    inputs = json.loads(inputs_json) if inputs_json.strip() else {}

    payload = {"ref": branch}
    if inputs:
        payload["inputs"] = inputs

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 204:
        print(f"✅ Triggered workflow '{workflow_file}' for '{repo}' on branch '{branch}'")
    else:
        print(f"❌ Failed to trigger '{workflow_file}' for '{repo}': {response.status_code} {response.text}")

def main():
    now = datetime.now().replace(second=0, microsecond=0)

    with open(CSV_FILE, newline='') as csvfile:
        rows = csv.DictReader(csvfile)
        for row in rows:
            repo = row["repo"]
            cron_expr = row["cron"]
            enabled = row.get("enabled", "false").strip().lower()
            workflow_file = row["workflow_file"]

            # Skip if workflow is disabled
            if enabled != "true":
                print(f"⏭ {workflow_file} Workflow for repo '{repo}' is disabled. Skipping.")
                continue

            if repo in last_trigger_times:
                if now - last_trigger_times[repo] < timedelta(minutes=10):
                    continue

            if should_trigger_by_cron(cron_expr, now, repo):
                trigger_workflow(
                    repo=row["repo"],
                    workflow_file=row["workflow_file"],
                    branch=row["branch"],
                    inputs_json=row.get("inputs", "")
                )

if __name__ == "__main__":
    main()
