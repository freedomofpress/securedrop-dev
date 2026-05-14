#!/usr/bin/env python3
"""Sync product versions in eol.yaml from upstream sources."""

import re
from pathlib import Path

import requests
import yaml

PNPM_LOCK_URL = (
    "https://raw.githubusercontent.com/freedomofpress/securedrop-client"
    "/refs/heads/main/app/pnpm-lock.yaml"
)
EOL_YAML = Path(__file__).parent / "eol.yaml"


def fetch_electron_major() -> str:
    resp = requests.get(PNPM_LOCK_URL)
    resp.raise_for_status()
    lock = yaml.safe_load(resp.text)
    version = lock["importers"]["."]["devDependencies"]["electron"]["version"]
    return version.split(".")[0]


def set_version(text: str, product: str, new_version: str) -> tuple[str, str]:
    """Replace the version field in the named product block, preserving formatting.

    Returns (updated_text, old_version) or (text, None) if the product was not found.
    """
    # Match a product entry block and capture the version line within it.
    pattern = re.compile(
        r"(- product: " + re.escape(product) + r"\n"
        r"(?:[ \t]+\S[^\n]*\n)*?)"   # preceding fields (non-greedy)
        r"([ \t]+version: )([^\n]+)",  # the version line
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        raise RuntimeError(f"Unable to find {product} block in yaml")

    old_raw = m.group(3)
    # Preserve quoting style of the original value
    if old_raw.startswith('"'):
        replacement_value = f'"{new_version}"'
    elif old_raw.startswith("'"):
        replacement_value = f"'{new_version}'"
    else:
        replacement_value = new_version

    old_version = old_raw.strip('"\'')
    updated = text[: m.start(3)] + replacement_value + text[m.end(3) :]
    return updated, old_version


def main():
    text = EOL_YAML.read_text()

    major = fetch_electron_major()
    updated, old_version = set_version(text, "electron", major)

    if old_version == major:
        print(f"electron version already at {major}, no change needed")
        return

    print(f"Updating electron version: {old_version} -> {major}")
    EOL_YAML.write_text(updated)
    print("eol.yaml updated")


if __name__ == "__main__":
    main()
