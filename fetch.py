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
    jid_start = config["jid_start"]
    jid_end = config["jid_end"]
    job_url = server + "/job/" + job
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
