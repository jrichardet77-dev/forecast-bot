"""Writes DASHBOARD.md (readable in the GitHub iPhone app) and data/report.json (feeds the dashboard page)."""
import json

from . import ledger


def write(summary):
    (ledger.DATA / "report.json").write_text(json.dumps(summary, indent=1, default=str))
