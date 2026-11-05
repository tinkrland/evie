"""manual capture: the landing zone for exports a human had to click.

sources without an api deliver a file into a downloads folder. this module
is the deterministic half of that: point it at a folder and it says what
each file is, or refuses to guess.

detection is by **column signature**, never by filename, for the same
reason the storygraph adapter does it: providers rename their exports
between revisions, and a file called `data.csv` can be anything. a file
whose columns match no known source is reported `unknown` with the header
it actually had, so the next person can add a signature instead of
guessing.
"""

import csv
from pathlib import Path

from src.ingest import goodreads, letterboxd, storygraph

# required columns per source. lowercase, order-insensitive.
signatures = {
    "goodreads": ("title", "author", "exclusive shelf"),
    "letterboxd": ("name", "year", "letterboxd uri"),
    "storygraph": ("title", "authors", "read status"),
}

archive_suffixes = (".zip",)


def header_of(path):
    """the first csv row of a file, lowercased. empty when it cannot read one."""
    try:
        with Path(path).open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            return [column.strip().lower() for column in next(reader, [])]
    except (OSError, UnicodeDecodeError, csv.Error):
        return []


def identify(path):
    """which source a file is, by its columns. `unknown` when nothing fits."""
    if Path(path).suffix.lower() in archive_suffixes:
        return {"source": "archive", "reason": "zip: unpack it and re-run on the folder"}
    columns = header_of(path)
    if not columns:
        return {"source": "unknown", "reason": "no readable csv header", "columns": []}
    for source, needed in signatures.items():
        if all(column in columns for column in needed):
            return {"source": source, "reason": "column signature", "columns": columns}
    return {"source": "unknown", "reason": "columns match no known source", "columns": columns}


def scan(folder):
    """report every file in a landing zone, sorted. writes nothing."""
    folder = Path(folder)
    if not folder.exists():
        raise FileNotFoundError(f"no such folder: {folder}")
    files = sorted(p for p in folder.rglob("*") if p.is_file() and not p.name.startswith("."))
    rows = []
    for path in files:
        found = identify(path)
        rows.append({"file": str(path.relative_to(folder)), **found})
    counts = {}
    for entry in rows:
        counts[entry["source"]] = counts.get(entry["source"], 0) + 1
    return {"version": 1, "kind": "landing-zone", "files": rows, "summary": {"files": len(rows), "by_source": counts}}


def collect(folder):
    """parse every recognisable file in a landing zone into one candidate doc."""
    folder = Path(folder)
    report = scan(folder)
    rows = []
    used = []
    for entry in report["files"]:
        source = entry["source"]
        if source == "goodreads":
            rows += goodreads.rows_from_export(folder / entry["file"])
            used.append(entry["file"])
        elif source == "letterboxd":
            rows += letterboxd.rows_from_export(folder / entry["file"])
            used.append(entry["file"])
        elif source == "storygraph":
            rows += storygraph.rows_from_export(folder / entry["file"])
            used.append(entry["file"])
    doc = {
        "version": 1,
        "kind": "import-candidates",
        "source": "manual-capture",
        "rows": rows,
        "summary": {
            "rows": len(rows),
            "files_used": used,
            "unknown": [e["file"] for e in report["files"] if e["source"] == "unknown"],
            "archives": [e["file"] for e in report["files"] if e["source"] == "archive"],
        },
    }
    return doc
