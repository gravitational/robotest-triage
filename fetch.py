import json
from os.path import exists
import requests

DATA_DIR = "data"


def fetch(url, auth, filepath):
    with requests.get(url, auth=auth) as r:
        r.raise_for_status()
        with open(local_file, 'wb') as f:
            for chunk in r.iter_content():
                if chunk:
                    f.write(chunk)


def get_latest_job(job_url, auth):
    api_url = job_url + "/api/json"
    with requests.get(api_url, auth=auth) as r:
        r.raise_for_status()
        json = r.json()
    latest = json["builds"][0]["number"]
    return latest


if __name__ == "__main__":
    with open("config.json", 'r') as cf:
        config = json.load(cf)

    credentials_path = config["credentials"]
    with open(credentials_path, 'r') as cf:
        creds = json.load(cf)
        auth = (creds["user"], creds["token"])

    datadir = DATA_DIR  # const for now, consider making configurable -- walt 2020-04
    server = config["url"]
    job = config["job"]
    job_url = server + "/job/" + job

    jid_start = config.get("jid_start", 1)
    if not jid_start > 0:
        raise ValueError("jid_start (%i) must be > 0" % jid_start)
    jid_end = config.get("jid_end", "latest")
    if jid_end == "latest":
        jid_end = get_latest_job(job_url, auth)
    if not jid_start < jid_end:
        raise ValueError("jid_start (%s) must be < jid_end (%s)" % (jid_start, jid_end))

    console_url_template = job_url + "/{jid}/consoleText"

    for jid in range(jid_start, jid_end + 1):
        console_url = console_url_template.format(jid=jid)
        local_file = datadir + "/" + (job + "-" + str(jid) + ".txt").lower()
        if exists(local_file):
            print("%s exists. Skipping." % local_file)
        else:
            print("Downloading %s to %s... " % (console_url, local_file), end="", flush=True)
            fetch(console_url, auth, local_file)
            print("done.")
