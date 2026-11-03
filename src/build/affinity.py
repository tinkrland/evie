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
    layers = doc.get("layers") or {"catalog": {"weight": 1.0, "source": "authored tags"}}
    harvest = layers.get("harvest") or {}
    return {
        "version": doc.get("version", "affinity.v0"),
        "score": scoring.get("score", "cosine_incidence"),
        "min_score": float(scoring.get("min_score", 0.0)),
        "min_pair_works": int(scoring.get("min_pair_works", 1)),
        "top_k": int(scoring.get("top_k", 8)),
        "decimals": int(scoring.get("score_rounding_decimals", 6)),
        "exclude_values": set(doc.get("exclude_values") or ["unknown"]),
        "layers": {
            "catalog": {
                "weight": float((layers.get("catalog") or {}).get("weight", 1.0)),
                "source": (layers.get("catalog") or {}).get("source", "authored tags"),
            },
            "harvest": {
                "weight": float(harvest.get("weight", 0.0)),
                "source": harvest.get("source"),
                "routing": harvest.get("routing"),
            },
        },
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


def harvest_terms(queue_path, routing_path, vocab, config):
    """work id -> terms implied by the harvest queue's alias routes.

    only keywords that route to an EXISTING axis value count. a motif
    proposal is not a value yet, and metadata or discarded keywords are
    not taste evidence at all, so none of them enter the graph.
    """
    from src.ingest.routing import load_routing, route_keyword

    queue_path = Path(queue_path)
    if not queue_path.exists():
        return {}
    routing = load_routing(routing_path)
    doc = yaml.safe_load(queue_path.read_text()) or {}
    excluded = config["exclude_values"]
    out = {}
    for proposal in doc.get("proposals") or []:
        route = route_keyword(proposal["proposal"], routing, vocab)
        if route.get("kind") != "alias":
            continue
        term = (route["axis"], route["value"])
        if str(route["value"]).lower() in excluded:
            continue
        for source in proposal.get("sources") or []:
            ref = str(source.get("ref") or "")
            if not ref.startswith("tmdb-work:"):
                continue
            work_id = ref.split(":", 1)[1]
            out.setdefault(work_id, set()).add(term)
    return {work_id: sorted(terms) for work_id, terms in sorted(out.items())}


def layer_maps(term_source, config):
    """(incidence, pair->works) for one evidence layer."""
    support = {}
    for work_id, terms in sorted(term_source.items()):
        clean = [
            tuple(t) if not isinstance(t, tuple) else t
            for t in terms
            if str(t[1]).lower() not in config["exclude_values"]
        ]
        for term in clean:
            support.setdefault(term, set()).add(work_id)
    pairs = {}
    for work_id, terms in sorted(term_source.items()):
        clean = [
            tuple(t) if not isinstance(t, tuple) else t
            for t in terms
            if str(t[1]).lower() not in config["exclude_values"]
        ]
        for i, left in enumerate(clean):
            for right in clean[i + 1:]:
                pairs.setdefault((left, right), set()).add(work_id)
    return support, {pair: sorted(ids) for pair, ids in pairs.items()}


def score_pair(shared, support_a, support_b):
    """cosine over work incidence. returns 0.0 when either side is empty."""
    if not support_a or not support_b:
        return 0.0
    return shared / math.sqrt(support_a * support_b)


def build_table(works, config, harvest=None):
    """build the structural affinity table. deterministic and total.

    layers: `catalog` is authored tags. `harvest` is keyword co-occurrence
    from the harvest queue, admitted only through alias routes that name an
    existing axis value. a pair's score is the weighted mean of the layers
    that actually carry shared works for it, so an absent layer is absent,
    never a zero dragging the number down.
    """
    decimals = config["decimals"]
    catalog_terms = {work_id: work_terms(work, config) for work_id, work in works.items()}
    supports = {}
    pairmaps = {}
    supports["catalog"], pairmaps["catalog"] = layer_maps(catalog_terms, config)
    if harvest:
        supports["harvest"], pairmaps["harvest"] = layer_maps(harvest, config)

    all_terms = sorted({term for layer in supports.values() for term in layer})
    neighbours = {term: [] for term in all_terms}
    pair_keys = {pair for layer in pairmaps.values() for pair in layer}

    harvested_pairs = 0
    for pair in sorted(pair_keys):
        layers = []
        for name in ("catalog", "harvest"):
            pair_map = pairmaps.get(name) or {}
            if pair not in pair_map:
                continue
            shared_ids = pair_map[pair]
            if len(shared_ids) < config["min_pair_works"]:
                continue
            layer_support = supports[name]
            left, right = pair
            layer_score = score_pair(
                len(shared_ids), len(layer_support[left]), len(layer_support[right])
            )
            layers.append(
                {
                    "name": name,
                    "weight": config["layers"][name]["weight"],
                    "shared": len(shared_ids),
                    "shared_works": shared_ids,
                    "support_this": len(layer_support[left]),
                    "support_other": len(layer_support[right]),
                    "score": round(layer_score, decimals),
                }
            )
        if not layers:
            continue
        total_weight = sum(layer["weight"] for layer in layers) or 1.0
        blended = sum(layer["weight"] * layer["score"] for layer in layers) / total_weight
        if blended < config["min_score"]:
            continue
        if any(layer["name"] == "harvest" for layer in layers):
            harvested_pairs += 1
        shared_union = sorted({work for layer in layers for work in layer["shared_works"]})
        for this, other in ((pair[0], pair[1]), (pair[1], pair[0])):
            rows = []
            for layer in layers:
                row = dict(layer)
                if this == pair[1]:
                    row["support_this"], row["support_other"] = (
                        layer["support_other"],
                        layer["support_this"],
                    )
                rows.append(row)
            neighbours[this].append(
                {
                    "term": list(other),
                    "score": round(blended, decimals),
                    "shared": len(shared_union),
                    "explain": {
                        "formula": "sum(weight * score) / sum(weight)",
                        "layers": rows,
                    },
                }
            )

    terms = []
    for term in sorted(neighbours):
        layer_supports = [
            len(supports[name][term]) for name in ("catalog", "harvest") if term in supports.get(name, {})
        ]
        rows = sorted(neighbours[term], key=lambda r: (-r["score"], r["term"]))
        rows = rows[: config["top_k"]]
        terms.append(
            {
                "term": list(term),
                "support": max(layer_supports) if layer_supports else 0,
                "support_layers": {
                    name: len(supports[name][term])
                    for name in ("catalog", "harvest")
                    if term in supports.get(name, {})
                },
                "neighbours": rows,
            }
        )

    lonely = [t["term"] for t in terms if not t["neighbours"]]
    table = {
        "schema": "evie-affinity-table-v2",
        "config_version": config["version"],
        "scoring": {
            "score": config["score"],
            "min_score": config["min_score"],
            "min_pair_works": config["min_pair_works"],
            "top_k": config["top_k"],
            "score_rounding_decimals": decimals,
            "exclude_values": sorted(config["exclude_values"]),
            "layers": {
                name: {"weight": meta["weight"], "source": meta.get("source")}
                for name, meta in config["layers"].items()
                if name == "catalog" or meta.get("weight")
            },
        },
        "terms": terms,
        "summary": {
            "terms": len(terms),
            "pairs_published": sum(len(t["neighbours"]) for t in terms) // 2,
            "pairs_with_harvest_evidence": harvested_pairs,
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

    for each neighbour: every layer's score must recompute from that
    layer's own shared/support numbers, and the blended score must equal
    the weighted mean of the present layers. returns a list of
    human-readable errors; empty means the artifact is self-consistent.
    """
    errors = []
    decimals = (table.get("scoring") or {}).get("score_rounding_decimals", 6)
    if tolerance is None:
        tolerance = 0.5 * 10 ** (-decimals)
    for row in table.get("terms") or []:
        for neighbour in row.get("neighbours") or []:
            explain = neighbour.get("explain") or {}
            layers = explain.get("layers") or []
            if not layers:
                errors.append(f"{row['term']} -> {neighbour['term']}: no evidence layers")
                continue
            total_weight = sum(float(layer.get("weight") or 0.0) for layer in layers)
            if total_weight <= 0:
                errors.append(f"{row['term']} -> {neighbour['term']}: no layer weights")
                continue
            expected = 0.0
            for layer in layers:
                declared_shared = int(layer.get("shared") or 0)
                actual_shared = len(layer.get("shared_works") or [])
                if declared_shared != actual_shared:
                    errors.append(
                        f"{row['term']} -> {neighbour['term']}: {layer.get('name')} "
                        f"shared count disagrees with its work list"
                    )
                    continue
                layer_score = score_pair(
                    declared_shared,
                    int(layer.get("support_this") or 0),
                    int(layer.get("support_other") or 0),
                )
                if abs(layer_score - float(layer.get("score") or 0.0)) > tolerance:
                    errors.append(
                        f"{row['term']} -> {neighbour['term']}: {layer.get('name')} score "
                        f"not recomputable from its own numbers"
                    )
                    continue
                expected += float(layer.get("weight") or 0.0) * float(layer.get("score") or 0.0)
            expected /= total_weight
            if abs(expected - float(neighbour.get("score") or 0.0)) > tolerance:
                errors.append(
                    f"{row['term']} -> {neighbour['term']}: blended score "
                    f"{neighbour.get('score')} not recomputable from its layers "
                    f"(expected {round(expected, decimals)})"
                )
    if "output_hash" in table and table["output_hash"] != output_hash(table):
        errors.append("output_hash does not match the table body")
    return errors


def dump_table(table):
    """sorted, stable json. json rather than yaml: it is machine artifact."""
    return json.dumps(table, sort_keys=True, indent=2) + "\n"
