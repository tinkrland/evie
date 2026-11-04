"""normalized import rows: the narrow shape every adapter must produce.

one row is one candidate: something a person watched or read according to
a source. a candidate is not taste. the owner confirms likes from the
candidate set, and only confirmed likes enter a taste context.

nothing in this module writes a taste context, and nothing here assigns an
evie work id: resolution against the reference catalogues is a separate,
later step with its own evidence.
"""

import yaml

row_fields = ("title", "year", "medium", "source", "source_id", "watched_at", "detail")


def row(title, year=None, medium=None, source=None, source_id=None, watched_at=None, detail=None):
    """build one normalized candidate row. absent values stay absent."""
    return {
        "title": str(title).strip(),
        "year": int(year) if year not in (None, "") else None,
        "medium": medium,
        "source": source,
        "source_id": str(source_id) if source_id not in (None, "") else None,
        "watched_at": str(watched_at) if watched_at not in (None, "") else None,
        "detail": detail or {},
    }


def dedupe(rows):
    """one candidate per hard id, else per (title, year, medium).

    merges duplicates from sources that log per-viewing (letterboxd diary,
    trakt scrobbles): views count up, the earliest and latest watched dates
    are kept, and nothing else is invented.
    """
    merged = {}
    for entry in rows:
        hard = entry.get("source_id") if str(entry.get("source_id") or "")[:3] in {"978", "979"} else None
        key = hard or (
            str(entry["title"]).strip().lower(),
            entry["year"],
            entry["medium"],
        )
        slot = merged.get(key)
        if slot is None:
            merged[key] = {
                **entry,
                "detail": {**entry.get("detail", {}), "views": int(entry.get("detail", {}).get("views") or 0)},
            }
            continue
        slot["detail"]["views"] = int(slot["detail"].get("views") or 0) + int(
            entry.get("detail", {}).get("views") or 0
        )
        earlier = [d for d in (slot.get("watched_at"), entry.get("watched_at")) if d]
        if earlier:
            slot["watched_at"] = min(earlier)
            slot["detail"]["last_watched_at"] = max(earlier)
        extra = entry.get("detail") or {}
        for name, value in extra.items():
            if name in {"views", "last_watched_at"}:
                continue
            slot["detail"].setdefault(name, value)
    for slot in merged.values():
        # a candidate the source lists at all has been seen once, even when
        # the source never states a view count
        slot["detail"]["views"] = max(1, int(slot["detail"].get("views") or 0))
    return sorted(
        merged.values(),
        key=lambda r: (r["title"].lower(), r["year"] or 0, r["medium"] or ""),
    )


def candidate_doc(rows, source):
    """the candidate file: deterministic, sorted, honest about counts."""
    clean = dedupe(rows)
    return {
        "version": 1,
        "kind": "import-candidates",
        "source": source,
        "rows": clean,
        "summary": {"rows": len(clean), "sources_seen": sorted({r["source"] for r in clean if r["source"]})},
    }


def dump_candidates(doc):
    """stable yaml for a candidate file."""
    head = (
        "# import candidates: things this person watched or read per one source.\n"
        "# candidates are not taste. the owner confirms likes from this set;\n"
        "# nothing here may be written into a taste context automatically.\n"
    )
    return head + yaml.safe_dump(doc, sort_keys=False, default_flow_style=False, width=1000)
