from __future__ import annotations

import json
from pathlib import Path

import pytest


def pytest_sessionfinish(session, exitstatus):
    results = []
    for item in session.items:
        report = getattr(item, "rep_call", None)
        if report is None:
            outcome = "not_run"
        else:
            outcome = report.outcome
        results.append({"test": item.nodeid, "outcome": outcome})
    out = Path("data/model/model_unit_test_summary.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "phase": "M1",
                "exitstatus": int(exitstatus),
                "passed": sum(1 for item in results if item["outcome"] == "passed"),
                "failed": sum(1 for item in results if item["outcome"] == "failed"),
                "results": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        item.rep_call = report
