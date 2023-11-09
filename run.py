# import subprocess
import requests
import os
import json
import sys

ADDR = "http://3.10.39.149:3000/"
CI_METRICS_HEADER = "### CI Metrics"
GITHUB_REPO_API = "https://api.github.com/repos/"


# Uploads metrics
def upload(sha, public_key, private_key, data):
    print(f"Running upload.")
    payload = json.dumps(
        {
            "user": {
                "public_key": public_key,
                "private_key": private_key,
            },
            "sha": sha,
            "metrics": data,
        }
    )
    print(f"payload: {payload}")
    response = requests.post(
        url=f"{ADDR}metrics",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200


# Gets metrics difference
def diff(base, head, public_key, private_key):
    print(f"Running diff.")
    payload = json.dumps(
        {
            "user": {
                "public_key": public_key,
                "private_key": private_key,
            },
            "from": base,
            "to": head,
        }
    )
    print(f"payload: {payload}")
    response = requests.get(
        url=f"{ADDR}diff",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    print(f"response: {response}")
    assert response.status_code == 200
    print(f"response.json(): {response.json()}")
    diff = response.json()
    table = "Metric|∆%|∆|Old|New\n--:|--:|--:|--:|--:\n"

    table_set = []
    for key, value in diff.items():
        x = value["from"]
        y = value["to"]
        if x != None and y != None:
            d = y - x
            pd = 100 * float(d) / float(x)
            table_set.append(
                (
                    key,
                    f"{pd:+.2f}",
                    f"{d:+}",
                    str(x),
                    str(y),
                )
            )
        else:
            table_set.append(
                (
                    key,
                    "NaN",
                    "NaN",
                    str(x),
                    str(y),
                )
            )
    print(f"table_set: {table_set}")

    # Sort diff by %
    def get_sort_key(x):
        if x[1] == "NaN":
            return float(-1)
        else:
            return abs(float(x[1]))

    table_set.sort(reverse=True, key=get_sort_key)

    print(f"table_set: {table_set}")
    for components in table_set:
        table += "|".join(components)
        table += "\n"

    return table


# Posts metrics difference on PRs
def post(repo, issue, token, table):
    print(f"Running post.")

    # Get list of comments
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    response = requests.get(
        url=f"{GITHUB_REPO_API}{repo}/issues/{issue}/comments",
        headers=headers,
    )
    print(f"response: {response}")
    print(f"response.json(): {response.json()}")
    comments = response.json()
    id = None
    for comment in comments:
        if comment["body"].startswith(CI_METRICS_HEADER):
            id = comment["id"]
    print(f"id: {id}")

    payload = json.dumps({"body": f"{CI_METRICS_HEADER}\n{table}"})

    # If CI metrics comment is not present, post it.
    if id == None:
        response = requests.post(
            url=f"{GITHUB_REPO_API}{repo}/issues/{issue}/comments",
            data=payload,
            headers=headers,
        )
        print(f"response: {response}")
    # Else if CI metrics comment present, update it.
    else:
        response = requests.patch(
            url=f"{GITHUB_REPO_API}{repo}/issues/comments/{id}",
            data=payload,
            headers=headers,
        )
        print(f"response: {response}")


public_key = os.environ["PUBLIC_KEY"]
private_key = int(os.environ["PRIVATE_KEY"])
head = os.environ["HEAD"]

DATA_TEXT = "DATA_TEXT"
DATA_FILE = "DATA_FILE"

data_text = os.environ.get(DATA_TEXT)
data_file = os.environ.get(DATA_FILE)

if data_text is None and data_file is not None:
    print(f"data_text: {data_file}")
    data_str = open(data_file, "r").read()
    print(f"data_str: {data_str}")
    upload(head, public_key, private_key, json.loads(data_str))
elif data_text is not None and data_file is None:
    print(f"data_text: {data_text}")
    upload(head, public_key, private_key, json.loads(data_text))
else:
    print(f"Neither `{DATA_TEXT}` or `{DATA_FILE}` set, skipping upload.")

BASE = "BASE"
ISSUE = "ISSUE"
TOKEN = "TOKEN"
REPO = "REPO"

base = os.environ.get(BASE)
issue = os.environ.get(ISSUE)
token = os.environ.get(TOKEN)
repo = os.environ.get(REPO)

if head is not None and issue is not None and token is not None and repo is not None:
    table = diff(base, head, public_key, private_key)
    post(repo, issue, token, table)
elif head is None and issue is None and token is None and repo is None:
    print(f"None of `{BASE}`, `{ISSUE}`, `{TOKEN}` or `{REPO}` set, skipping diff.")
else:
    raise Exception(
        f"`{BASE}` ({base}), `{ISSUE}` ({issue}), `{TOKEN}` ({token}) and `{REPO}` ({repo}) must all be set when any are set."
    )
