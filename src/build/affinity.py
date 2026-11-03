"""structural affinity table: the cold-start prior.

answers "which axis values travel together" from the governed catalogue
alone, before any user signal exists. deterministic, explainable, and
free of learned components: same catalogue and same config produce the
same table, proven by input and output hashes recorded in the table.

score: cosine over work incidence. for terms a and b,
    score = shared_works / sqrt(support_a * support_b)
every published neighbour carries the numbers needed to recompute its
score, and `check_table` re-verifies that recomputation, so "why this
surfaced" is a citable artifact rather than a claim.

scoring runs over the union of all axes at once, never per axis family:
a value whose real neighbours live in another axis would otherwise look
lonely, and a lonely value is allowed to exist. nothing pads it.
"""

import hashlib
import json
import math
from pathlib import Path

import yaml

root = Path(__file__).resolve().parents[2]
default_config = root / "config" / "affinity.v0.yaml"

# layer 1 fields that behave like tags for the graph. crime module
# fields are listed flat; setting_scale and genre_tradition sit on the
# work root.
crime_list_fields = (
    "mystery_mechanism",
    "lens",
    "detecting_subject",
    "legal_role",
)


def load_affinity_config(path=default_config):
    """read the affinity config. versioned file, never code constants."""
    doc = yaml.safe_load(Path(path).read_text()) or {}
    scoring = doc.get("scoring") or {}
    return {
        "version": doc.get("version", "affinity.v0"),
        "score": scoring.get("score", "cosine_incidence"),
        "min_score": float(scoring.get("min_score", 0.0)),
        "min_pair_works": int(scoring.get("min_pair_works", 1)),
        "top_k": int(scoring.get("top_k", 8)),
        "decimals": int(scoring.get("score_rounding_decimals", 6)),
        "exclude_values": set(doc.get("exclude_values") or ["unknown"]),
    }


def work_terms(work, config):
    """every (axis, value) a work carries. sorted, sentinels removed.

    unknown is not evidence: it says "unobserved", never "this much".
    """
    excluded = config["exclude_values"]
    terms = set()

    def add(axis, value):
        if value is None:
            return
        if str(value).lower() in excluded:
            return
        terms.add((axis, str(value)))

    for axis, entries in (work.get("tags") or {}).items():
        for entry in entries or []:
            add(axis, entry.get("value"))

    for genre in work.get("genre_tradition") or []:
        add("genre_tradition", genre)
    add("setting_scale", work.get("setting_scale"))

    crime = work.get("crime_module") or {}
    add("crime_relation", crime.get("crime_relation"))
    for field in crime_list_fields:
        for value in crime.get(field) or []:
            add(field, value)

    return sorted(terms)


def incidence(works, config):
    """term -> set of work ids carrying it."""
    support = {}
    for work_id, work in works.items():
        for term in work_terms(work, config):
            support.setdefault(term, set()).add(work_id)
    return support


def pair_works(works, config):
    """unorddered term pairs -> sorted work ids where both appear."""
    pairs = {}
    for work_id, work in works.items():
        terms = work_terms(work, config)
        for i, left in enumerate(terms):
            for right in terms[i + 1:]:
                pairs.setdefault((left, right), []).append(work_id)
    return {pair: sorted(ids) for pair, ids in pairs.items()}


def score_pair(shared, support_a, support_b):
    """cosine over work incidence. returns 0.0 when either side is empty."""
    if not support_a or not support_b:
        return 0.0
    return shared / math.sqrt(support_a * support_b)


def build_table(works, config):
    """build the structural affinity table. deterministic and total."""
    support = incidence(works, config)
    pairs = pair_works(works, config)
    decimals = config["decimals"]

    neighbours = {term: [] for term in support}
    for (left, right), shared_ids in pair_works_sorted(pairs):
        shared = len(shared_ids)
        if shared < config["min_pair_works"]:
            continue
        raw = score_pair(shared, len(support[left]), len(support[right]))
        if raw < config["min_score"]:
            continue
        score = round(raw, decimals)
        for this, other in ((left, right), (right, left)):
            neighbours[this].append(
                {
                    "term": list(other),
                    "score": score,
                    "shared": shared,
                    # explanation: everything needed to recompute `score`
                    "explain": {
                        "shared_works": shared_ids,
                        "support_this": len(support[this]),
                        "support_other": len(support[other]),
                        "formula": "shared / sqrt(support_this * support_other)",
                    },
                }
            )

    terms = []
    for term in sorted(neighbours):
        rows = sorted(neighbours[term], key=lambda r: (-r["score"], r["term"]))
        rows = rows[: config["top_k"]]
        terms.append(
            {
                "term": list(term),
                "support": len(support[term]),
                "neighbours": rows,
            }
        )

    lonely = [t["term"] for t in terms if not t["neighbours"]]
    table = {
        "schema": "evie-affinity-table-v1",
        "config_version": config["version"],
        "scoring": {
            "score": config["score"],
            "min_score": config["min_score"],
            "min_pair_works": config["min_pair_works"],
            "top_k": config["top_k"],
            "score_rounding_decimals": decimals,
            "exclude_values": sorted(config["exclude_values"]),
        },
        "terms": terms,
        "summary": {
            "terms": len(terms),
            "pairs_published": sum(len(t["neighbours"]) for t in terms) // 2,
            "lonely_terms": len(lonely),
            "lonely": lonely,
        },
    }
    return table


def pair_works_sorted(pairs):
    """deterministic iteration order for pairs."""
    for pair in sorted(pairs):
        yield pair, pairs[pair]


def canonical_json(value):
    """sorted-key json for hashing. the only serialisation that matters."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def input_hash(works, config_doc):
    """hash of everything that can change the table's content."""
    payload = {
        "config": config_doc,
        "works": {
            work_id: work_terms(work, config_doc) for work_id, work in works.items()
        },
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def output_hash(table):
    """hash of the table body, excluding the hash fields themselves."""
    body = {k: v for k, v in table.items() if k not in {"input_hash", "output_hash"}}
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def with_hashes(table, works, config):
    """attach determinism evidence. hashes are inside the artifact."""
    table = dict(table)
    table["input_hash"] = input_hash(works, config)
    table["output_hash"] = output_hash(table)
    return table


def check_table(table, tolerance=None):
    """re-verify every published neighbour from its own explanation.

    returns a list of human-readable errors; empty means the artifact is
    self-consistent. this is the invariant that makes the table citable.
    """
    errors = []
    decimals = (table.get("scoring") or {}).get("score_rounding_decimals", 6)
    if tolerance is None:
        tolerance = 0.5 * 10 ** (-decimals)
    for row in table.get("terms") or []:
        for neighbour in row.get("neighbours") or []:
            explain = neighbour.get("explain") or {}
            shared = int(explain.get("shared_works") and len(explain["shared_works"]) or 0)
            support_this = int(explain.get("support_this") or 0)
            support_other = int(explain.get("support_other") or 0)
            if shared != int(neighbour.get("shared") or 0):
                errors.append(
                    f"{row['term']} -> {neighbour['term']}: shared works disagree with explanation"
                )
                continue
            expected = score_pair(shared, support_this, support_other)
            if abs(expected - float(neighbour.get("score") or 0.0)) > tolerance:
                errors.append(
                    f"{row['term']} -> {neighbour['term']}: score {neighbour.get('score')} "
                    f"not recomputable from explanation (expected {round(expected, decimals)})"
                )
    if "output_hash" in table and table["output_hash"] != output_hash(table):
        errors.append("output_hash does not match the table body")
    return errors


def dump_table(table):
    """sorted, stable json. json rather than yaml: it is machine artifact."""
    return json.dumps(table, sort_keys=True, indent=2) + "\n"
