"""the motif proposal queue: deterministic merges, proposal-only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingest.tmdb_keywords import dump_queue, load_queue, main, merge_proposals

root = Path(__file__).resolve().parents[1]
queue_path = root / "data" / "motifs" / "queue.yaml"


def test_seed_queue_is_well_formed():
    doc = load_queue(queue_path)
    assert doc["version"] == 1
    assert len(doc["proposals"]) >= 3
    names = [p["proposal"] for p in doc["proposals"]]
    assert names == sorted(names)
    for proposal in doc["proposals"]:
        assert proposal["proposal"] == proposal["proposal"].lower().strip()
        assert proposal["sources"], proposal["proposal"]
        for source in proposal["sources"]:
            assert source["kind"]
            assert source["ref"]
            assert isinstance(source["uses"], int)


def test_seed_queue_has_verified_tmdb_ids():
    doc = load_queue(queue_path)
    refs = {}
    for proposal in doc["proposals"]:
        for source in proposal["sources"]:
            refs[proposal["proposal"]] = source["ref"]
    assert refs.get("whodunit") == "tmdb:12570"
    assert refs.get("buddy cop") == "tmdb:167316"
    assert refs.get("small town") == "tmdb:1415"


def test_merge_dedupes_and_replaces_uses():
    existing = [{"proposal": "whodunit", "sources": [{"kind": "tmdb-keyword", "ref": "tmdb:12570", "uses": 2}]}]
    incoming = [
        {"proposal": "whodunit", "sources": [{"kind": "tmdb-keyword", "ref": "tmdb:12570", "uses": 3}]},
        {"proposal": "Amnesia", "sources": [{"kind": "tmdb-keyword", "ref": "tmdb-work:mare", "uses": 1}]},
    ]
    merged = merge_proposals(existing, incoming)
    assert [p["proposal"] for p in merged] == ["Amnesia", "whodunit"]
    whodunit = next(p for p in merged if p["proposal"] == "whodunit")
    assert len(whodunit["sources"]) == 1
    # same ref reporting again replaces, never adds: reruns stay identical
    assert whodunit["sources"][0]["uses"] == 3


def test_merge_is_order_independent_and_canonical():
    a = [{"proposal": "small town", "sources": [{"kind": "tmdb-keyword", "ref": "tmdb:1415", "uses": 1}]}]
    b = [{"proposal": "buddy cop", "sources": [{"kind": "tmdb-keyword", "ref": "tmdb:167316", "uses": 1}]}]
    first = dump_queue({"version": 1, "proposals": merge_proposals(a, b)})
    second = dump_queue({"version": 1, "proposals": merge_proposals(b, a)})
    assert first == second


def test_harvest_refuses_without_key(monkeypatch):
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    assert main([]) == 2


def test_queue_never_touches_canonical_vocab():
    # proposals stay proposals: the vocab file must not contain queue names
    # until a human reviews them.
    vocab = (root / "data" / "vocab" / "motifs.yaml").read_text()
    assert "buddy cop" not in vocab
