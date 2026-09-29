"""Tests for notify_upstream_failures.py.

    python3 -m unittest discover -s .github/scripts

Offline by design: every probe and every GitHub call is stubbed, so the suite
is fast and cannot fail because an upstream happens to be down. To exercise the
real probes, run the notifier itself with DRY_RUN=1, which reports what it
would do without touching anything.

Stdlib only, for the same reason the notifier is: the thing that tells you
something broke should not depend on something that can break.
"""

import importlib
import json
import os
import re
import sys
import unittest
import unittest.mock as mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The module reads its configuration at import time. These are set rather than
# defaulted: on a runner the real GITHUB_RUN_ID is already present, and with
# setdefault the suite silently tested against it -- every run then looked
# superseded by a newer one, which passed locally and failed in CI.
os.environ["GITHUB_REPOSITORY"] = "owner/repo"
os.environ["GITHUB_RUN_ID"] = "100"
os.environ["GITHUB_TOKEN"] = "x"
os.environ["GITHUB_SERVER_URL"] = "https://github.com"
os.environ.pop("DRY_RUN", None)
# Never append to the runner's real job summary.
os.environ.pop("GITHUB_STEP_SUMMARY", None)

import notify_upstream_failures as notifier  # noqa: E402

WORKFLOW = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "workflows", "import.yaml"
)


class Base(unittest.TestCase):
    def setUp(self):
        # Reload so module state, notably the cached issue list, is clean.
        importlib.reload(notifier)
        notifier.DRY_RUN = False
        self.calls = []

    def stub_api(self, gets=None, raises=None):
        """Record every API call. `gets` maps a path regex to a GET response.

        Matching is per method on purpose: POST /issues and GET /issues share a
        path, and an earlier version of this stub answered the create call with
        the list response.
        """
        gets = gets or {}

        def api(method, path, payload=None):
            self.calls.append((method, path, payload))
            if raises and re.search(raises, path):
                raise RuntimeError("GitHub said no")
            if method != "GET":
                return {"number": 1}
            for pattern, value in gets.items():
                if re.search(pattern, path):
                    return value
            return []

        notifier.api = api

    def run_main(self, results):
        os.environ["JOB_RESULTS"] = json.dumps(
            {job: {"result": r} for job, r in results.items()}
        )
        self.rows = None
        notifier.write_summary = lambda rows: setattr(self, "rows", rows)
        try:
            notifier.main()
            return 0
        except SystemExit as exc:
            return 0 if exc.code in (0, None) else 1

    def writes(self):
        return [(m, p) for m, p, _ in self.calls if m in ("POST", "PATCH")]


class Probe(Base):
    """A status line means the host is serving; 5xx and 52x mean it is not."""

    def check(self, status, expected):
        import urllib.error

        if status == "unreachable":
            err = urllib.error.URLError("no route")
            with mock.patch("urllib.request.urlopen", side_effect=err):
                self.assertEqual(notifier.probe("https://x")[0], expected)
            return
        if status >= 400:
            err = urllib.error.HTTPError("https://x", status, "", {}, None)
            with mock.patch("urllib.request.urlopen", side_effect=err):
                self.assertEqual(notifier.probe("https://x")[0], expected)
            return
        resp = mock.MagicMock()
        resp.status = status
        resp.__enter__.return_value = resp
        with mock.patch("urllib.request.urlopen", return_value=resp):
            self.assertEqual(notifier.probe("https://x")[0], expected)

    def test_serving_states_are_reachable(self):
        for status in (200, 301, 403, 404):
            with self.subTest(status=status):
                self.check(status, True)

    def test_not_serving_states_are_unreachable(self):
        for status in (500, 502, 521, 522, 524, "unreachable"):
            with self.subTest(status=status):
                self.check(status, False)

    def test_tcp_probe_reports_connect_failure(self):
        import socket

        with mock.patch("socket.create_connection", side_effect=OSError("refused")):
            ok, detail = notifier.probe("tcp://host:5432")
        self.assertFalse(ok)
        self.assertIn("TCP connect failed", detail)
        with mock.patch("socket.create_connection", return_value=mock.MagicMock()):
            self.assertTrue(notifier.probe("tcp://host:5432")[0])
        del socket


class Verdict(Base):
    """An importer reading two resources fails if either is down."""

    def verdict_for(self, probes):
        notifier.SOURCES = {"x": ("X", list(probes))}
        notifier.probe = lambda target: probes[target]
        self.stub_api()
        self.run_main({"x": "failure"})
        return self.rows[0][3]

    def test_all_targets_must_answer(self):
        up, down = (True, "HTTP 200"), (False, "HTTP 521")
        self.assertEqual(self.verdict_for({"a": up, "b": up}), "needs-attention")
        self.assertEqual(self.verdict_for({"a": up, "b": down}), "upstream-unavailable")
        self.assertEqual(self.verdict_for({"a": down, "b": down}), "upstream-unavailable")


class FindIssue(Base):
    """The issues endpoint also returns pull requests."""

    PR = {"number": 5, "title": "import failure: X", "pull_request": {}, "body": ""}
    ISSUE = {"number": 9, "title": "import failure: X", "body": ""}

    def test_pull_request_is_never_selected(self):
        self.stub_api(gets={"issues": [self.PR, self.ISSUE]})
        self.assertEqual(notifier.find_issue("import failure: X")["number"], 9)

    def test_pull_request_alone_is_no_match(self):
        self.stub_api(gets={"issues": [self.PR]})
        self.assertIsNone(notifier.find_issue("import failure: X"))

    def test_issue_list_is_fetched_once(self):
        self.stub_api(gets={"issues": [self.ISSUE]})
        for _ in range(3):
            notifier.find_issue("import failure: X")
        self.assertEqual(len([c for c in self.calls if c[0] == "GET"]), 1)


class Lifecycle(Base):
    """One open issue per resource: open, stay quiet, update, close."""

    def setUp(self):
        super().setUp()
        notifier.SOURCES = {"x": ("X", ["u"])}
        notifier.probe = lambda target: (False, "HTTP 521")

    def open_issue(self, verdict="upstream-unavailable"):
        return {
            "number": 42,
            "title": "import failure: X",
            "body": f"{notifier.MARKER}{verdict} -->",
        }

    def test_first_failure_opens_an_issue(self):
        self.stub_api(gets={"issues": []})
        self.run_main({"x": "failure"})
        self.assertIn(("POST", f"/repos/{notifier.REPO}/issues"), self.writes())

    def test_unchanged_verdict_stays_quiet(self):
        self.stub_api(gets={r"issues\?": [self.open_issue()]})
        self.run_main({"x": "failure"})
        self.assertEqual(self.writes(), [])

    def test_changed_verdict_comments_and_refreshes(self):
        self.stub_api(gets={r"issues\?": [self.open_issue("needs-attention")]})
        self.run_main({"x": "failure"})
        methods = [m for m, _ in self.writes()]
        self.assertIn("POST", methods)
        self.assertIn("PATCH", methods)

    def test_recovery_comments_and_closes(self):
        self.stub_api(gets={r"issues\?": [self.open_issue()]})
        self.run_main({"x": "success"})
        self.assertTrue(any("comments" in p for _, p in self.writes()))
        self.assertTrue(
            any(m == "PATCH" for m, _ in self.writes()), "issue should be closed"
        )

    def test_success_with_nothing_open_does_nothing(self):
        self.stub_api(gets={"issues": []})
        self.run_main({"x": "success"})
        self.assertEqual(self.writes(), [])

    def test_skipped_job_is_not_evaluated(self):
        self.stub_api(gets={"issues": []})
        self.run_main({"x": "skipped"})
        self.assertEqual(self.writes(), [])
        self.assertEqual(self.rows[0][4], "not evaluated")


class Resilience(Base):
    """Reporting is the job; it must not be the most brittle part of the run."""

    def test_one_failure_does_not_hide_the_others(self):
        notifier.SOURCES = {k: (k.upper(), ["u"]) for k in ("a", "b", "c")}
        notifier.probe = lambda target: (False, "HTTP 521")
        self.stub_api(gets={"issues": []}, raises=r"issues$")
        code = self.run_main({k: "failure" for k in notifier.SOURCES})
        self.assertEqual([r[0] for r in self.rows], ["a", "b", "c"])
        self.assertEqual(code, 1, "the run must still go red")

    def test_label_failure_still_writes_the_summary(self):
        notifier.SOURCES = {"x": ("X", ["u"])}
        notifier.probe = lambda target: (False, "HTTP 521")
        self.stub_api(gets={"workflows": {"workflow_runs": [{"id": 100}]}}, raises=r"/labels")
        code = self.run_main({"x": "failure"})
        self.assertIsNotNone(self.rows, "summary must be written anyway")
        self.assertEqual(code, 1)

    def test_a_superseded_run_changes_nothing(self):
        notifier.SOURCES = {"x": ("X", ["u"])}
        notifier.probe = lambda target: (False, "HTTP 521")
        self.stub_api(gets={"workflows": {"workflow_runs": [{"id": 999}]}})
        self.run_main({"x": "failure"})
        self.assertEqual(self.writes(), [])
        self.assertIn("newer run", self.rows[0][4])

    def test_the_newest_run_does_act(self):
        notifier.SOURCES = {"x": ("X", ["u"])}
        notifier.probe = lambda target: (False, "HTTP 521")
        self.stub_api(gets={"workflows": {"workflow_runs": [{"id": 100}]}, "issues": []})
        self.run_main({"x": "failure"})
        self.assertNotEqual(self.writes(), [])


class Wiring(unittest.TestCase):
    """The probe table and the workflow must not drift apart."""

    def setUp(self):
        # Other classes mutate SOURCES on the module object; reload to see the
        # real table rather than whatever ran last.
        importlib.reload(notifier)

    @staticmethod
    def read_workflow():
        with open(WORKFLOW) as handle:
            return handle.read()

    def workflow_jobs(self):
        text = self.read_workflow()
        body = text.split("\njobs:\n", 1)[1]
        return {m.group(1) for m in re.finditer(r"^  ([a-z0-9][a-z0-9-]*):$", body, re.M)}

    def notify_needs(self):
        text = self.read_workflow()
        block = text.split("\n  notify:\n", 1)[1].split("\n    if:", 1)[0]
        return {m.group(1) for m in re.finditer(r"^      - ([a-z0-9-]+)$", block, re.M)}

    def test_every_probed_source_is_a_job(self):
        self.assertEqual(set(notifier.SOURCES) - self.workflow_jobs(), set())

    def test_notify_waits_for_every_probed_source(self):
        self.assertEqual(set(notifier.SOURCES), self.notify_needs())

    def notify_permissions(self):
        text = self.read_workflow()
        block = text.split("\n  notify:\n", 1)[1].split("\n    concurrency:", 1)[0]
        return dict(re.findall(r"^      (\w+): (read|write)$", block, re.M))

    def test_notify_job_grants_every_scope_the_script_needs(self):
        """A job-level permissions map denies everything it does not name.

        Each of these is reachable from the script, and a missing one fails at
        runtime in a way that is easy to miss: the stale-run check catches its
        own 403 and carries on, so losing `actions` degrades the guard silently
        rather than failing the job.
        """
        needed = {
            "contents": "actions/checkout",
            "issues": "read, open, comment, close, and label the tracking issue",
            "actions": "list this workflow's runs for the stale-run guard",
        }
        granted = self.notify_permissions()
        for scope, why in needed.items():
            with self.subTest(scope=scope):
                self.assertIn(scope, granted, f"{scope} is needed to {why}")

    def test_every_source_has_at_least_one_target(self):
        for name, (_, targets) in notifier.SOURCES.items():
            with self.subTest(source=name):
                self.assertTrue(targets)


if __name__ == "__main__":
    unittest.main(verbosity=2)
