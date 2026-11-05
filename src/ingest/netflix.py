"""netflix import: the viewing activity download.

netflix hands over `NetflixViewingActivity.csv` from account settings. two
columns only: a title and a date. everything else about netflix rows is a
trap worth naming:

- the title is the show with the episode baked in ("the office: season 1:
  episode 1"), so a series is not a title and a film has no episode part.
  the adapter keeps the source's own words in `detail.netflix_title` and
  does not try to be clever about where the series ends.
- there is no year, no id, and no medium, so `source_id` and `year` stay
  null and `medium` stays null rather than being guessed from an
  episode-shaped string.
- profile rows can appear for several people on one account: the file
  names the profile in the title column when it is a shared account.
  those rows import as candidates like any other, because sorting out who
  is who is the owner's call, not a title-matching guess.

usage is not liking: this is viewing, including whatever was left running.
"""

import csv
from pathlib import Path

from src.ingest.rows import candidate_doc, row

source = "netflix"


def _looks_like_viewing_activity(handle):
    """identify by columns, never by filename. netflix renames its own file."""
    first = handle.readline().strip().lower()
    return "title" in first and "date" in first


def _download(path):
    """the viewing activity csv, found by its columns when given a folder."""
    if path.is_file():
        return path
    if not path.is_dir():
        return None
    matches = []
    for candidate in sorted(path.glob("*.csv")):
        with candidate.open(encoding="utf-8-sig", errors="replace") as handle:
            if _looks_like_viewing_activity(handle):
                matches.append(candidate)
    return matches[0] if matches else None


def rows_from_export(export_path):
    """rows from the viewing activity csv. missing file is an empty import."""
    path = _download(Path(export_path))
    if path is None:
        return []
    out = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for entry in csv.DictReader(handle):
            clean = {(key or "").strip().lower(): (value or "").strip() for key, value in entry.items()}
            title = clean.get("title") or ""
            if not title:
                continue
            detail = {"netflix_title": title}
            if clean.get("date"):
                detail["netflix_row_date"] = clean["date"]
            out.append(
                row(
                    title,
                    None,
                    medium=None,
                    source=source,
                    source_id=None,
                    watched_at=clean.get("date") or None,
                    detail=detail,
                )
            )
    return out


def collect(export_path):
    """candidate doc for a netflix download. deterministic."""
    return candidate_doc(rows_from_export(export_path), source)
