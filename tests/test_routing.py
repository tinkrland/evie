"""keyword routing: harvested keywords triage onto the axis they describe."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.build.vocab import load_vocab
from src.ingest.routing import load_routing, route_keyword, route_proposals, summarise

root = Path(__file__).resolve().parents[1]
vocab = load_vocab(root / "data" / "vocab")
routing = load_routing(root / "data" / "motifs" / "routing.yaml")


def test_small_town_is_a_locale_axis_not_a_motif():
    # the owner's correction: locale belongs to setting_scale, never motifs
    route = route_keyword("small town", routing, vocab)
    assert route == {"kind": "alias", "axis": "setting_scale", "value": "small-town"}


def test_whodunit_routes_to_mechanism():
    route = route_keyword("whodunit", routing, vocab)
    assert route["kind"] == "alias"
    assert route["axis"] == "mystery_mechanism"
    assert route["value"] == "whodunit"


def test_buddy_cop_routes_to_ensemble():
    route = route_keyword("buddy cop", routing, vocab)
    assert route["kind"] == "alias"
    assert route["axis"] == "ensemble_shape"
    assert route["value"] == "odd-couple"


def test_criminal_consultant_routes_to_lens():
    route = route_keyword("criminal consultant", routing, vocab)
    assert route == {"kind": "alias", "axis": "lens", "value": "criminal-consultant"}


def test_place_names_are_metadata_not_taste():
    for keyword in ("california", "london, england", "new york city"):
        route = route_keyword(keyword, routing, vocab)
        assert route["kind"] == "metadata"
        assert route["field"] == "setting_geo"


def test_provenance_keywords_are_discarded():
    assert route_keyword("based on novel or book", routing, vocab)["kind"] == "discard"
    assert route_keyword("adoring", routing, vocab)["kind"] == "discard"


def test_unrouted_keywords_default_to_motif_never_to_a_value():
    route = route_keyword("dysfunctional family", routing, vocab)
    assert route == {"kind": "motif"}


def test_new_value_when_routing_names_a_missing_value():
    route = route_keyword("arms dealer", routing, vocab)
    assert route["kind"] == "new-value"
    assert route["axis"] == "protagonist_gift"
    assert route["value"] is None


def test_routing_is_deterministic_and_order_stable():
    proposals = [
        {"proposal": "small town", "sources": [{"kind": "tmdb-keyword", "ref": "x", "uses": 1}]},
        {"proposal": "whodunit", "sources": [{"kind": "tmdb-keyword", "ref": "y", "uses": 1}]},
    ]
    first = route_proposals(proposals, routing, vocab)
    second = route_proposals(list(reversed(proposals)), routing, vocab)
    assert first == list(reversed(second))
    assert summarise(first)["kinds"]["alias"] == 2


def test_every_proposal_has_a_route():
    from src.ingest.tmdb_keywords import load_queue

    doc = load_queue(root / "data" / "motifs" / "queue.yaml")
    for proposal in doc["proposals"]:
        assert "route" in proposal, proposal["proposal"]
        assert proposal["route"]["kind"] in {"alias", "new-value", "motif", "metadata", "discard"}
