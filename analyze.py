from collections import namedtuple
import json
import sys


Record = namedtuple("Record", ("status", "id", "config", "log_link"))


class ParseError(ValueError):
    pass


def robotest_filter(logs):
    """
    Yields all log lines prefixed with '[robotest]'.

    This prefix comes from Jenkins' pipeline plugin configuration, for the
    robotest step.
    """
    marker = "[robotest] "
    for line in logs:
        if line.startswith(marker):
            yield line[len(marker):]


def status_block_filter(logs):
    """
    Yields all lines after the summary and before the go test output.

    This is faster than regexing all lines in the file for the log pattern.
    """
    summary_marker = "******** TEST SUITE COMPLETED **********\n"
    go_test_marker = "--- FAIL: TestMain"
    after_summary = False
    for line in logs:
        if after_summary:
            if line.startswith(go_test_marker):
                break
            else:
                yield line
        if line == summary_marker:
            after_summary = True


def recordize(logs):
    for line in logs:
        try:
            record = parse_result(line)
            yield record
        except ParseError as e:
            print(e, file=sys.stderr)  # TODO: stash for future analysis


STATUSES = ["FAILED", "CANCELED", "PASSED"]


def parse_result(line):
    """
    Turn a result log line into structured data.

    Example result line:
        [robotest] FAILED f161ebf-upgrade3lts4-1 {"role":"node","cluster":"","flavor":"three","remote_support":false,"state_dir":"/var/lib/gravity","os":{"Vendor":"debian","Version":"9"},"storage_driver":"overlay2","nodes":3,"script":null,"from":"/telekube_6.3.6.tar"} https://console.cloud.google.com/logs/viewer?advancedFilter=resource.type%3D%22project%22%0Alabels.__uuid__%3D%22c6f8336c-2bb0-4732-a9ed-af382dcea1bc%22%0Alabels.__suite__%3D%22b304ff00-5d82-47e6-8ad4-ca83243b4165%22%0Aseverity%3E%3DINFO&authuser=1&expandAll=false&project=kubeadm-167321

    Fields:
        status, tid, config_json, log_link
    """ # Noqa
    line = line.rstrip()  # remove trailing newline

    try:
        status, remainder = line.split(" ", 1)
    except ValueError as e:
        raise ParseError(line) from e
    if status not in STATUSES:
        e = ParseError("%s is not a valid status" % status)
        raise ParseError(line) from e

    try:
        tid, remainder = remainder.split(" ", 1)
    except ValueError as e:
        raise ParseError(line) from e
    # is there anything to assert about the test id?

    try:
        config, remainder = split_json_config(remainder)
    except ValueError as e:
        raise ParseError(line) from e

    url = remainder.strip()
    # is there anything to assert about the url?

    return Record(status, tid, config, url)


def split_json_config(line):
    """
    Expects the first element in line to be a json object.

    Returns the json object (as a string) and the remainder of the line.
    """
    # this is broken, as there can be whitespace in json, but it
    # is good enough for a first pass -- walt 2020-04
    config, remainder = line.split(" ", 1)
    json.loads(config)  # using this for validation, result not needed
    return config, remainder


if __name__ == "__main__":
    filepaths = sys.argv[1:]
    if not filepaths:
        print("usage: %s [file ...]" % sys.argv[0], file=sys.stderr)
        sys.exit(2)
    all_records = []
    for filepath in filepaths:
        with open(filepath) as f:
            records = recordize(status_block_filter(robotest_filter(f)))
            records = list(records)  # force processing before the filehandle closes
        all_records.extend(records)

    # everything from here down is ad-hoc example analysis - feel free to edit
    successes = {}
    failures = {}
    for record in all_records:
        config = json.loads(record.config)
        if "from" not in config:  # only consider upgrade failures
            continue
        version = config["from"][len("/telekube_"):-len(".tar")]
        if record.status == "FAILED":
            failures[version] = failures.get(version, 0) + 1
        if record.status == "PASSED":
            successes[version] = successes.get(version, 0) + 1

    for version in sorted(list(set(failures.keys()) | set(successes.keys()))):
        fails = failures.get(version, 0)
        passes = successes.get(version, 0)
        total = passes + fails
        print("{:10} {:3}/{:3} passed ({:.2}%)".format(version, passes, total, passes/total))
