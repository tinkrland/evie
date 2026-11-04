"""letterboxd import: file export, csv.

the export is a folder of csv files from account settings. `watched.csv`
is the spine; `diary.csv` adds per-viewing dates and rewatching; ratings
and reviews are carried as detail, never interpreted as taste.

diary rows are per-viewing, not per-film, so the same film arrives many
times: dedupe to one candidate per film and keep the view count visible.
"""

import csv
from pathlib import Path

from src.ingest.rows import row

source = "letterboxd"

# the export's column names are stable but not guaranteed across years;
# match on lowercase names and tolerate missing files entirely.
watched_file = "watched.csv"
diary_file = "diary.csv"
ratings_file = "ratings.csv"


def _read_csv(path):
    """rows of a csv as dicts with lowercase, stripped keys."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [
            {(key or "").strip().lower(): (value or "").strip() for key, value in entry.items()}
            for entry in reader
        ]


def _title_from(entry):
    return entry.get("name") or entry.get("title") or ""


def _year_from(entry):
    raw = entry.get("year") or ""
    return int(raw) if raw.isdigit() else None


def rows_from_export(export_dir):
    """all candidate rows from a letterboxd export directory."""
    export_dir = Path(export_dir)
    out = []

    for entry in _read_csv(export_dir / watched_file):
        out.append(
            row(
                _title_from(entry),
                _year_from(entry),
                medium="film",
                source=source,
                source_id=entry.get("letterboxd uri"),
                watched_at=entry.get("date"),
            )
        )

    diary_entries = _read_csv(export_dir / diary_file)
    for entry in diary_entries:
        detail = {"views": 1}
        if entry.get("rewatch", "").lower() in {"yes", "true"}:
            detail["rewatch"] = True
        if entry.get("rating"):
            detail["rating"] = entry["rating"]
        out.append(
            row(
                _title_from(entry),
                _year_from(entry),
                medium="film",
                source=source,
                source_id=entry.get("letterboxd uri"),
                watched_at=entry.get("watched date") or entry.get("date"),
                detail=detail,
            )
        )

    for entry in _read_csv(export_dir / ratings_file):
        out.append(
            row(
                _title_from(entry),
                _year_from(entry),
                medium="film",
                source=source,
                source_id=entry.get("letterboxd uri"),
                watched_at=entry.get("date"),
                detail={"rating": entry["rating"]} if entry.get("rating") else {},
            )
        )

    return [entry for entry in out if entry["title"]]


def collect(export_dir):
    """candidate doc for a letterboxd export. deterministic."""
    from src.ingest.rows import candidate_doc

    return candidate_doc(rows_from_export(export_dir), source)
