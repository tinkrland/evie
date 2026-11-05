"""storygraph import: file export, csv.

storygraph sends the export as a file, and the download is not always one
file: the library and its tags arrive as separate csvs in a folder. this
adapter finds the library csv by its columns instead of its filename,
because storygraph names it differently across export revisions.

the read status rules mirror goodreads, because the shelves mean the same
thing:

- `read` is a candidate.
- `currently-reading` is unfinished, not a judgement.
- `to-read` is intentions, not interest.
- `did-not-finish` is a real negative signal, but it is a *statement of
  dislike*, and this import only collects candidates. it is excluded and
  named in the row report, never silently dropped.

identity: the export carries isbn, or a storygraph uid for books without
one. an isbn is a hard identity and becomes `source_id`; a plain uid is
not, so it goes to detail and source_id stays null.

moods and tags are the user's own in-app vocabulary, not evie's axes.
they go to detail untouched as future wrangling candidates, and never
into a taste context: importing them as axis values would smuggle a
foreign taxonomy in through the side door.
"""

import csv
from pathlib import Path

from src.ingest.goodreads import clean_isbn
from src.ingest.rows import candidate_doc, row

source = "storygraph"

read_statuses = {"read", "read "}
excluded_statuses = {"to-read", "currently-reading", "did-not-finish"}

# column names this adapter depends on, used to identify the library csv.
required_columns = {"title", "read status"}


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [
            {(key or "").strip().lower(): (value or "").strip() for key, value in entry.items()}
            for entry in reader
        ]


def library_files(export_path):
    """csv files in the export that look like the library, sorted by name."""
    export_path = Path(export_path)
    candidates = [export_path] if export_path.is_file() else sorted(export_path.glob("*.csv"))
    found = []
    for path in candidates:
        try:
            with path.open(encoding="utf-8-sig") as handle:
                header = next(csv.reader(handle), [])
        except (OSError, StopIteration):
            continue
        columns = {(name or "").strip().lower() for name in header}
        if required_columns <= columns:
            found.append(path)
    return found


def _year(entry):
    for key in ("original publication year", "year published", "publication year"):
        raw = entry.get(key) or ""
        if raw.isdigit():
            return int(raw)
    return None


def _detail(entry):
    detail = {}
    if entry.get("star rating"):
        detail["rating"] = entry["star rating"]
    if entry.get("read count") and entry["read count"].isdigit():
        detail["views"] = int(entry["read count"]) or 1
    if entry.get("review"):
        detail["has_review"] = True
    if entry.get("tags"):
        # the user's own shelf words. wrangling candidates later, never axes.
        detail["tags"] = entry["tags"]
    uid = entry.get("isbn/uid") or ""
    if uid and not clean_isbn(uid):
        detail["storygraph_uid"] = uid
    return detail


def rows_from_export(export_path):
    """candidate rows from a storygraph export file or folder."""
    out = []
    for path in library_files(export_path):
        for entry in _read_csv(path):
            status = (entry.get("read status") or "").strip().lower()
            if status not in read_statuses:
                continue
            title = entry.get("title") or ""
            if not title:
                continue
            uid = entry.get("isbn/uid") or ""
            isbn = clean_isbn(uid)
            out.append(
                row(
                    title,
                    _year(entry),
                    medium="book",
                    source=source,
                    source_id=isbn,
                    watched_at=entry.get("last date read") or None,
                    detail=_detail(entry),
                )
            )
    return out


def status_counts(export_path):
    """how many rows each read status contributed, including exclusions.

    did-not-finish is a real negative signal, so it is counted and
    reported even though it never becomes a candidate.
    """
    counts = {}
    for path in library_files(export_path):
        for entry in _read_csv(path):
            status = (entry.get("read status") or "").strip().lower() or "unknown"
            counts[status] = counts.get(status, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def collect(export_path):
    """candidate doc for a storygraph export. deterministic."""
    doc = candidate_doc(rows_from_export(export_path), source)
    counts = status_counts(export_path)
    excluded = {k: v for k, v in counts.items() if k not in read_statuses}
    if excluded:
        doc["summary"]["excluded_by_status"] = excluded
    return doc
