# import subprocess
import requests
import os
import json
import sys

# Get metrics diff
# --------------------------------------------------------------------------------------------------
payload = json.dumps(
    {
        "user": {
            "public_key": "6546b543a35b7d5af8c93a7b",
            "private_key": int(os.environ["PRIVATE_KEY"]),
        },
        "from": os.environ["FROM"],
        "to": os.environ["TO"],
    }
)
print(f"payload: {payload}")
response = requests.get(
    url="http://3.10.39.149:3000/diff",
    data=payload,
    headers={"Content-Type": "application/json"},
)
print(f"response: {response}")
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

# Post/Update comment
# --------------------------------------------------------------------------------------------------
repo = os.environ["REPO"]
issue = os.environ["ISSUE_NUMBER"]
token = os.environ["TOKEN"]

# Get list of comments
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
    "X-GitHub-Api-Version": "2022-11-28",
}
response = requests.get(
    url=f"https://api.github.com/repos/{repo}/issues/{issue}/comments", headers=headers
)
print(f"response: {response}")
print(f"response.json(): {response.json()}")
comments = response.json()
CI_METRICS_HEADER = "### CI Metrics"
id = None
for comment in comments:
    if comment["body"].startswith(CI_METRICS_HEADER):
        id = comment["id"]
print(f"id: {id}")

payload = json.dumps({"body": f"{CI_METRICS_HEADER}\n{table}"})

# If CI metrics comment is not present, post it.
if id == None:
    response = requests.post(
        url=f"https://api.github.com/repos/{repo}/issues/{issue}/comments",
        data=payload,
        headers=headers,
    )
    print(f"response: {response}")
# Else if CI metrics comment present, update it.
else:
    response = requests.patch(
        url=f"https://api.github.com/repos/{repo}/issues/comments/{id}",
        data=payload,
        headers=headers,
    )
    print(f"response: {response}")
