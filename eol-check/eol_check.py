#!/usr/bin/env python3
"""CLI utilities for EOL monitoring (gh‑powered).

Commands
--------
• generate-ics <yaml> <ics>
    Produce an iCalendar file listing each EOL date as an all‑day event.

• open-issues <yaml>
    For entries whose EOL is within `warn_days`, open a GitHub issue (via `gh`).
    Duplicate issues (open **or** closed) are avoided by searching titles.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests
import yaml
from ics import Calendar, Event

TITLE_TMPL = "{product} {version} reaches EOL on {eol_date}"
BODY_TMPL = (
    "⚠️ **End‑of‑life approaching**\n\n"
    "* **Product:** {product} {version}\n"
    "* **EOL date:** {eol_date}\n\n"
    "_Source: {source_ref}_\n"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _iso(d: str) -> dt.date:
    return dt.date.fromisoformat(d)


def _resolve_eol(entry: Dict[str, Any]) -> dt.date:
    """Return the EOL date for a product entry.

    Assumes **endoflife.date** schema ≥ v1.1.
    """

    # Manual overrides short‑circuit the API entirely
    if entry.get("source", "api") == "manual":
        return _iso(entry["eol_date"])

    ep = entry["api_endpoint"]
    rv = requests.get(ep, timeout=10)
    rv.raise_for_status()
    payload: Any = rv.json()

    try:
        releases = payload["result"]["releases"]
    except (KeyError, TypeError):
        raise ValueError(f"Unexpected schema from {ep}; expected result.releases")

    version = str(entry["version"])
    for rel in releases:
        if rel.get("name") == version:
            eol_str = rel.get("eolFrom")
            if not eol_str:
                raise ValueError(f"eolFrom missing for {entry['product']} {version}")
            return _iso(eol_str)

    raise ValueError(f"{entry['product']} {version} not found @ {ep}")



def _calendar(entries: List[Dict[str, Any]], dest: Path):
    cal = Calendar()
    for e in entries:
        print(e)
        eol = _resolve_eol(e)
        evt = Event()
        evt.name = f"{e['product']} {e['version']} EOL"
        evt.begin = eol
        evt.make_all_day()
        evt.uid = f"{e['product']}-{e['version']}@eol-checks"
        evt.description = TITLE_TMPL.format(
            product=e["product"], version=e["version"], eol_date=eol.isoformat()
        )
        cal.events.add(evt)

    dest.write_text(cal.serialize(), encoding="utf-8")


def _days_until(d: dt.date) -> int:
    return (d - dt.date.today()).days

# ---------------------------------------------------------------------------
# gh‑helpers
# ---------------------------------------------------------------------------

def _issue_exists(repo: str, title: str) -> bool:
    cmd = [
        "gh",
        "issue",
        "list",
        "--repo",
        repo,
        "--state",
        "all",
        "--json",
        "title",
        "--search",
        f'in:title "{title}"',
        "-L",
        "1",
    ]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    return len(json.loads(out)) > 0


def _create_issue(repo: str, title: str, body: str):
    subprocess.run(
        [
            "gh",
            "issue",
            "create",
            "--repo",
            repo,
            "--title",
            title,
            "--body",
            body,
        ],
        check=True,
    )

# ---------------------------------------------------------------------------
# High‑level flows
# ---------------------------------------------------------------------------

def _open_issues(entries: List[Dict[str, Any]]):
    if not os.getenv("GH_TOKEN"):
        print("ERROR: GH_TOKEN env var not set", file=sys.stderr)
        sys.exit(1)

    for e in entries:
        repo = e.get("issue_repo")
        if not repo:
            continue  # calendar‑only entry

        warn = int(e.get("warn_days", 30))
        eol = _resolve_eol(e)
        if _days_until(eol) > warn:
            continue

        title = TITLE_TMPL.format(
            product=e["product"], version=e["version"], eol_date=eol.isoformat()
        )
        if _issue_exists(repo, title):
            print(f"Issue already exists in {repo}: {title}")
            continue

        body = BODY_TMPL.format(
            product=e["product"],
            version=e["version"],
            eol_date=eol.isoformat(),
            source_ref=e.get("api_endpoint", "manual entry"),
        )
        _create_issue(repo, title, body)
        print(f"Created issue in {repo}: {title}")

# ---------------------------------------------------------------------------
# CLI entry‑point
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="EOL check utility")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_cal = sub.add_parser("generate-ics", help="Generate an iCalendar file")
    p_cal.add_argument("yaml", type=Path, help="Path to YAML config")
    p_cal.add_argument("ics", type=Path, help="Output .ics path")

    p_iss = sub.add_parser("open-issues", help="Open GitHub issues if EOL is near")
    p_iss.add_argument("yaml", type=Path, help="Path to YAML config")

    args = p.parse_args()
    entries = _load(args.yaml)

    match args.cmd:
        case "generate-ics":
            _calendar(entries, args.ics)
        case "open-issues":
            _open_issues(entries)


if __name__ == "__main__":
    main()