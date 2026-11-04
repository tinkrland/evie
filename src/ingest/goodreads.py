"""goodreads import: file export, csv.

goodreads exports `goodreads_library_export.csv` from import/export in
account settings. the api was retired in 2020, so the file is the route.

the shelf rules are the point of this adapter:

- `exclusive shelf` = read is a candidate. currently-reading is not (an
  unfinished book is not a judgement). to-read is not (a shelf of
  intentions, not interest).
- isbn13 then isbn10 is the only hard identity in the file, so a row
  carries it as `source_id` and leaves title matching to the resolution
  step.
- my rating is carried as detail and never interpreted as taste.

isbn values arrive wrapped in excel's ""=""..."" armour, so they are
unwrapped before anything else touches them.
"""

import csv
from pathlib import Path

from src.ingest.rows import candidate_doc, row

source = "goodreads"

export_file = "goodreads_library_export.csv"


def _read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [
            {(key or "").strip().lower(): (value or "").strip() for key, value in entry.items()}
            for entry in reader
        ]


def clean_isbn(raw):
    """unwrap excel armour and keep only a real isbn. absent stays absent."""
    if not raw:
        return None
    value = str(raw).strip().strip('="').strip('"').strip()
    value = value.replace("-", "").replace(" ", "")
    if value.lower().endswith("x"):
        digits = value[:-1]
        if digits.isdigit() and len(digits) == 9:
            return value.upper()
        return None
    if value.isdigit() and len(value) in {10, 13}:
        return value
    return None


def _original_year(entry):
    for key in ("original publication year", "year published"):
        raw = entry.get(key) or ""
        if raw.isdigit():
            return int(raw)
    return None


def _book_path(export_path):
    export_path = Path(export_path)
    if export_path.is_dir():
        return export_path / export_file
    return export_path


def rows_from_export(export_path):
    """candidate rows from a goodreads library export."""
    out = []
    for entry in _read_csv(_book_path(export_path)):
        shelf = (entry.get("exclusive shelf") or "").lower()
        if shelf != "read":
            continue
        title = entry.get("title") or ""
        if not title:
            continue
        isbn13 = clean_isbn(entry.get("isbn13"))
        isbn10 = clean_isbn(entry.get("isbn"))
        detail = {}
        if entry.get("my rating"):
            detail["rating"] = entry["my rating"]
        if entry.get("number of pages"):
            detail["pages"] = entry["number of pages"]
        if entry.get("read count") and entry["read count"].isdigit():
            detail["views"] = int(entry["read count"]) or 1
        if isbn10 and isbn13:
            detail["isbn10"] = isbn10
        out.append(
            row(
                title,
                _original_year(entry),
                medium="book",
                source=source,
                source_id=isbn13 or isbn10,
                watched_at=entry.get("date read") or None,
                detail=detail,
            )
        )
    return out


def collect(export_path):
    """candidate doc for a goodreads export. deterministic."""
    return candidate_doc(rows_from_export(export_path), source)
