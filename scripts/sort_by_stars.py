#!/usr/bin/env python3
"""Sort skill tables in README files by GitHub star count."""

import re
import sys
import time
import urllib.request
import urllib.error
import json

GITHUB_TOKEN = None  # Set via environment variable GITHUB_TOKEN


def fetch_stars(owner: str, repo: str) -> int:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "awesome-human-distillation")
    req.add_header("Accept", "application/vnd.github+json")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("stargazers_count", 0)
    except Exception as e:
        print(f"Warning: failed to fetch stars for {owner}/{repo}: {e}", file=sys.stderr)
        return 0


def extract_repo(row: str):
    """Extract owner/repo from a table row's skill link."""
    match = re.search(r"https://github\.com/([^/]+)/([^/)\s]+)", row)
    if match:
        return match.group(1), match.group(2)
    return None, None


def sort_table_section(lines: list[str]) -> list[str]:
    """Given lines of a markdown table (including header), sort data rows by stars desc."""
    if len(lines) < 3:
        return lines

    header = lines[0]
    separator = lines[1]
    data_rows = lines[2:]

    # Fetch stars for each row
    rows_with_stars = []
    for row in data_rows:
        if not row.strip() or not row.startswith("|"):
            rows_with_stars.append((row, -1))
            continue
        owner, repo = extract_repo(row)
        if owner and repo:
            stars = fetch_stars(owner, repo)
            time.sleep(0.1)  # be polite to the API
        else:
            stars = 0
        rows_with_stars.append((row, stars))

    rows_with_stars.sort(key=lambda x: x[1], reverse=True)
    return [header, separator] + [r for r, _ in rows_with_stars]


def process_readme(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines(keepends=True)
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        # Detect table header row (contains | Name | or | Skill |)
        if re.match(r"\|\s*(Name|名字)\s*\|", line):
            # Collect the full table
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i].rstrip("\n"))
                i += 1
            sorted_table = sort_table_section(table_lines)
            for tl in sorted_table:
                result.append(tl + "\n")
        else:
            result.append(line)
            i += 1

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(result)

    print(f"Updated: {filepath}")


if __name__ == "__main__":
    import os
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

    files = sys.argv[1:] if len(sys.argv) > 1 else ["README.md", "README_EN.md"]
    for filepath in files:
        process_readme(filepath)
