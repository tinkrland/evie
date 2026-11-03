"""triage harvested keyword proposals onto the axis they describe.

pure and deterministic: same queue + same routing + same vocab gives the
same routed queue, byte for byte. no network, no guesses beyond the
routing table.

kinds:
    alias      keyword names an existing axis value (joins its alias table)
    new-value  keyword names a value that axis does not have yet
    motif      freeform narrative texture, no axis fits
    metadata   identity metadata (locales -> setting_geo), not taste
    discard    not a taste signal
"""

import sys
from pathlib import Path

import yaml

root = Path(__file__).resolve().parents[2]
default_routing = root / "data" / "motifs" / "routing.yaml"


def load_routing(path=default_routing):
    """read the routing table. absent file means everything stays a motif."""
    path = Path(path)
    if not path.exists():
        return {"routes": {}, "discard": [], "locale_keywords": []}
    doc = yaml.safe_load(path.read_text()) or {}
    return {
        "routes": doc.get("routes") or {},
        "discard": doc.get("discard") or [],
        "locale_keywords": doc.get("locale_keywords") or [],
    }


def route_keyword(keyword, routing, vocab):
    """route one keyword. returns a route mapping, deterministic."""
    keyword = str(keyword).lower().strip()
    routes = routing.get("routes") or {}
    if keyword in routes:
        entry = routes[keyword]
        axis = entry.get("axis")
        value = entry.get("value")
        if not axis:
            return {"kind": "discard", "reason": "listed as non-taste in routing"}
        if value is None:
            return {"kind": "new-value", "axis": axis, "value": None}
        known = (vocab.get(axis) or {}).get("values") or []
        if value in known:
            return {"kind": "alias", "axis": axis, "value": value}
        return {"kind": "new-value", "axis": axis, "value": value}
    if keyword in (routing.get("discard") or []):
        return {"kind": "discard", "reason": "listed as non-taste in routing"}
    if keyword in (routing.get("locale_keywords") or []):
        return {"kind": "metadata", "field": "setting_geo"}
    return {"kind": "motif"}


def route_proposals(proposals, routing, vocab):
    """attach a route to every proposal. preserves order and sources."""
    routed = []
    for proposal in proposals:
        entry = {"proposal": proposal["proposal"]}
        entry["route"] = route_keyword(proposal["proposal"], routing, vocab)
        entry["sources"] = proposal.get("sources") or []
        routed.append(entry)
    return routed


def summarise(routed):
    """counts by kind, then by axis, for a human to read."""
    kinds = {}
    axes = {}
    for entry in routed:
        kind = entry["route"]["kind"]
        kinds[kind] = kinds.get(kind, 0) + 1
        axis = entry["route"].get("axis")
        if axis:
            axes[axis] = axes.get(axis, 0) + 1
    return {"kinds": dict(sorted(kinds.items())), "axes": dict(sorted(axes.items()))}


def main(argv=None):
    """route the queue in place and print a summary."""
    sys.path.insert(0, str(root))
    from src.build.vocab import load_vocab
    from src.ingest.tmdb_keywords import default_queue, dump_queue, load_queue

    vocab = load_vocab(root / "data" / "vocab")
    doc = load_queue(default_queue)
    routed = route_proposals(doc["proposals"], load_routing(), vocab)
    out = {"version": doc.get("version", 1), "proposals": routed}
    default_queue.write_text(dump_queue(out))
    summary = summarise(routed)
    print(f"routed {len(routed)} proposals: {summary['kinds']}")
    print(f"by axis: {summary['axes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
