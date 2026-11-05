"""resolution: candidate row -> evie work id, with evidence for the match.

imports hand over what a source says a person read or watched. this module
answers the only question left: which evie work is that?

three rules, in order, and nothing else:

1. **hard id.** a row carrying an isbn is matched against works whose
   `external_ids.isbn` equals it. same input, same answer, no scoring.
2. **exact title plus year.** normalized title equality AND the same year
   (or a work with no year recorded). never a fuzzy or partial match.
3. **nothing.** unmatched rows stay unmatched and are reported with the
   count. an unresolved row is not an error; it is work the catalogue has
   not done yet.

two works matching the same row is an ambiguity, not a toss-up: the row
is reported `ambiguous` with every candidate id, and no work id is
chosen. the owner resolves it by tagging, not by the importer guessing.
"""

import yaml

from src.ingest.rows import normalize_title


def catalogue_index(works):
    """index the catalogue by isbn and by (normalized title, year)."""
    by_isbn = {}
    by_title = {}
    for work_id, doc in sorted(works.items()):
        external = doc.get("external_ids") or {}
        isbn = (external.get("isbn") or "").replace("-", "").strip()
        if isbn:
            by_isbn.setdefault(isbn, []).append(work_id)
        key = normalize_title(doc.get("title") or "")
        if key:
            by_title.setdefault(key, []).append(work_id)
    return {"by_isbn": by_isbn, "by_title": by_title}


def resolve_row(entry, index, works):
    """resolve one row. returns a resolution dict, never raises."""
    isbn = (entry.get("source_id") or "").replace("-", "").strip()
    if isbn and isbn in index["by_isbn"]:
        hits = index["by_isbn"][isbn]
        if len(hits) == 1:
            return {"status": "resolved", "method": "isbn", "work_ids": hits}
        return {"status": "ambiguous", "method": "isbn", "work_ids": hits}

    key = normalize_title(entry.get("title") or "")
    hits = list(index["by_title"].get(key) or [])
    year = entry.get("year")
    if hits and year:
        same_year = [w for w in hits if (works[w].get("first_release") or None) in (year, None)]
        if same_year:
            hits = same_year
    if len(hits) == 1:
        return {"status": "resolved", "method": "title-year", "work_ids": hits}
    if len(hits) > 1:
        return {"status": "ambiguous", "method": "title-year", "work_ids": hits}
    return {"status": "unmatched", "method": "none", "work_ids": []}


def resolve_doc(candidate_doc, works):
    """attach a resolution to every row of a candidate doc. deterministic."""
    index = catalogue_index(works)
    rows = []
    counts = {"resolved": 0, "unmatched": 0, "ambiguous": 0}
    for entry in candidate_doc.get("rows") or []:
        resolution = resolve_row(entry, index, works)
        counts[resolution["status"]] += 1
        merged = dict(entry)
        merged["resolution"] = resolution
        rows.append(merged)
    out = {
        "version": 1,
        "kind": "resolved-candidates",
        "source": candidate_doc.get("source"),
        "rows": rows,
        "summary": {
            "rows": len(rows),
            "resolved": counts["resolved"],
            "unmatched": counts["unmatched"],
            "ambiguous": counts["ambiguous"],
        },
    }
    return out


def dump(doc):
    """the resolved file, stable across identical inputs."""
    head = (
        "# candidates with a resolution attached. resolved rows name an evie\n"
        "# work id and the method that produced it. unmatched and ambiguous\n"
        "# rows name nothing: guessing a work id is how a catalogue rots.\n"
    )
    return head + yaml.safe_dump(doc, sort_keys=False, default_flow_style=False, width=1000)
