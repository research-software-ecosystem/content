"""Tell maintainers why an importer failed, and whether it is our problem.

Runs after the import jobs. For every importer that failed, it re-checks that
importer's upstream resource and says which of two things happened:

  upstream-unavailable  the resource is down. Nothing to fix here; the import
                        will resume by itself. data/ was left untouched.
  needs-attention       the resource answers normally, so the failure is most
                        likely in the importer.

The verdict is carried in one open issue per resource, labelled
`upstream-outage`. A new failure opens it, a change of verdict comments on it,
an unchanged verdict stays silent so that a long outage does not produce a
weekly alert, and a recovery comments and closes it.

Deliberately stdlib-only: no pip install step, and no dependency that can break
the thing whose job is to tell you something broke.
"""

import json
import os
import socket
import sys
import urllib.error
import urllib.request

# Each importer's own upstream, taken from what the importer actually fetches.
# A tcp:// probe is for a resource that is not HTTP at all.
SOURCES = {
    "biotools": ("bio.tools", ["https://bio.tools/api/tool/?page=1"]),
    "openebench": ("OpenEBench", ["https://openebench.bsc.es/monitor/metrics/"]),
    "bioconda": (
        "Bioconda",
        ["https://codeload.github.com/bioconda/bioconda-recipes/zip/master"],
    ),
    "biii": ("BIII", ["http://biii.eu/"]),
    "biocontainers": (
        "BioContainers",
        [
            "https://raw.githubusercontent.com/BioContainers/tools-metadata/"
            "master/annotations.yaml"
        ],
    ),
    "galaxytool": (
        "Galaxy Codex",
        [
            "https://raw.githubusercontent.com/galaxyproject/galaxy_codex/"
            "refs/heads/main/communities/all/resources/tools.json"
        ],
    ),
    "debian-med": ("Debian Med (UDD)", ["tcp://udd-mirror.debian.net:5432"]),
    "bioconductor": ("Bioconductor", ["https://bioconductor.org/config.yaml"]),
    "workflowhub": ("WorkflowHub", ["https://workflowhub.eu/workflows.json?page=1"]),
}

LABEL = "upstream-outage"
NOTIFY_TEAM = "@research-software-ecosystem/rsec-ops"
MARKER = "<!-- rsec-notify verdict="
TIMEOUT = 20

API = "https://api.github.com"
REPO = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
SERVER = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
RUN_ID = os.environ.get("GITHUB_RUN_ID", "")
RUN_URL = f"{SERVER}/{REPO}/actions/runs/{RUN_ID}" if RUN_ID else "(no run url)"
DRY_RUN = os.environ.get("DRY_RUN") == "1" or not TOKEN


def probe(target):
    """Return (reachable, detail) for one upstream target."""
    if target.startswith("tcp://"):
        host, _, port = target[len("tcp://") :].partition(":")
        try:
            with socket.create_connection((host, int(port or 0)), timeout=TIMEOUT):
                return True, "TCP connect OK"
        except OSError as exc:
            return False, f"TCP connect failed: {exc}"
    # HEAD first: one of these targets is a multi-megabyte archive, and we only
    # ever want the status line. Some servers refuse HEAD, hence the fallback.
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(
            target,
            method=method,
            headers={"Accept": "*/*", "User-Agent": "rsec-notify"},
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return True, f"HTTP {response.status}"
        except urllib.error.HTTPError as exc:
            if method == "HEAD" and exc.code in (403, 405, 501):
                continue
            # A status line is an answer: the host is up even if the path is
            # unhappy. 5xx, and Cloudflare's 52x, mean it is not serving.
            return (exc.code < 500), f"HTTP {exc.code}"
        except (urllib.error.URLError, socket.timeout, OSError) as exc:
            return False, f"unreachable: {getattr(exc, 'reason', exc)}"
    return False, "no response to HEAD or GET"


def api(method, path, payload=None):
    if DRY_RUN:
        print(f"    [dry-run] {method} {path} {json.dumps(payload)[:120] if payload else ''}")
        return {} if method != "GET" else []
    request = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "rsec-notify",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
    return json.loads(body) if body else {}


def ensure_label():
    """Create the tracking label if the repository does not have it yet.

    find_issue() filters on this label, so an issue created before the label
    exists could be invisible on the next run, and a duplicate would be opened
    for an outage already being tracked.
    """
    if DRY_RUN:
        print(f"    [dry-run] ensure label {LABEL} exists")
        return
    try:
        api("GET", f"/repos/{REPO}/labels/{LABEL}")
        return
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
    api(
        "POST",
        f"/repos/{REPO}/labels",
        {
            "name": LABEL,
            "color": "d93f0b",
            "description": "An upstream resource an importer depends on is unavailable",
        },
    )
    print(f"created the {LABEL} label")


_OPEN_ISSUES = None


def find_issue(title):
    """Look up our open tracking issues, fetching the list at most once."""
    global _OPEN_ISSUES
    if _OPEN_ISSUES is None:
        _OPEN_ISSUES = api(
            "GET", f"/repos/{REPO}/issues?state=open&labels={LABEL}&per_page=100"
        )
    for issue in _OPEN_ISSUES:
        if issue.get("title") == title:
            return issue
    return None


def previous_verdict(issue):
    body = (issue or {}).get("body") or ""
    if MARKER in body:
        return body.split(MARKER, 1)[1].split("-->", 1)[0].strip()
    return None


def body_for(resource, verdict, probe_lines):
    headline = {
        "upstream-unavailable": (
            f"**{resource} is not answering.** The importer stopped before writing "
            "anything, so `data/` still holds the previous import. Nothing needs "
            "fixing here: the next scheduled run will pick up where it left off "
            "once the resource is back."
        ),
        "needs-attention": (
            f"**{resource} answers normally, so this is probably not an outage.** "
            "The failure is more likely in the importer or in a change to the "
            f"resource's API. Someone should look at the run."
        ),
    }[verdict]
    probes = "\n".join(f"- `{url}` -> {detail}" for url, detail in probe_lines)
    return (
        f"{MARKER}{verdict} -->\n"
        f"{headline}\n\n"
        f"Checked just now, from the notifier job:\n{probes}\n\n"
        f"Failing run: {RUN_URL}\n\n"
        f"{NOTIFY_TEAM}\n\n"
        "<sub>Opened automatically. It will be closed when the importer next "
        "succeeds.</sub>"
    )


def main():
    needs = json.loads(os.environ.get("JOB_RESULTS") or "{}")
    if not needs:
        sys.exit("JOB_RESULTS is empty; nothing to report")

    if any((needs.get(job) or {}).get("result") == "failure" for job in SOURCES):
        ensure_label()

    rows = []
    for job, (resource, targets) in SOURCES.items():
        result = (needs.get(job) or {}).get("result", "missing")
        title = f"import failure: {resource}"

        if result == "success":
            issue = find_issue(title)
            if issue:
                api(
                    "POST",
                    f"/repos/{REPO}/issues/{issue['number']}/comments",
                    {"body": f"Recovered: the importer succeeded in {RUN_URL}."},
                )
                api("PATCH", f"/repos/{REPO}/issues/{issue['number']}", {"state": "closed"})
                rows.append((job, result, "-", "recovered", f"closed #{issue['number']}"))
            else:
                rows.append((job, result, "-", "-", "nothing to do"))
            continue

        if result in ("skipped", "cancelled", "missing"):
            rows.append((job, result, "-", "-", "not evaluated"))
            continue

        # Probe each target once; both the verdict and the report come from it.
        checked = [(target, *probe(target)) for target in targets]
        probe_lines = [(target, detail) for target, _, detail in checked]
        verdict = (
            "needs-attention"
            if any(ok for _, ok, _ in checked)
            else "upstream-unavailable"
        )
        summary = "; ".join(detail for _, detail in probe_lines)

        issue = find_issue(title)
        if issue is None:
            created = api(
                "POST",
                f"/repos/{REPO}/issues",
                {
                    "title": title,
                    "body": body_for(resource, verdict, probe_lines),
                    "labels": [LABEL],
                },
            )
            action = f"opened #{created.get('number', '?')}"
        elif previous_verdict(issue) != verdict:
            api(
                "POST",
                f"/repos/{REPO}/issues/{issue['number']}/comments",
                {
                    "body": f"Still failing, but the picture changed "
                    f"(`{previous_verdict(issue)}` -> `{verdict}`).\n\n"
                    f"{body_for(resource, verdict, probe_lines)}"
                },
            )
            api(
                "PATCH",
                f"/repos/{REPO}/issues/{issue['number']}",
                {"body": body_for(resource, verdict, probe_lines)},
            )
            action = f"updated #{issue['number']}"
        else:
            action = f"#{issue['number']} already open, staying quiet"
        rows.append((job, result, summary, verdict, action))

    write_summary(rows)


def write_summary(rows):
    lines = [
        "## Importer outcomes",
        "",
        "| importer | job | upstream check | verdict | action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for job, result, summary, verdict, action in rows:
        lines.append(f"| {job} | {result} | {summary} | {verdict} | {action} |")
    text = "\n".join(lines) + "\n"
    print(text)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as handle:
            handle.write(text)


if __name__ == "__main__":
    main()
