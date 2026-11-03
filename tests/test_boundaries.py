"""boundary pairs, executable (open question 31).

the rubrics declare boundaries in prose: gift_cover is not world,
family_role is not ensemble_shape, island is not coastal-town. prose
drifts. these tests are the drift alarm: if someone adds a value to an
axis that belongs to a neighbouring axis, the boundary check fails
before the ambiguity reaches a tagger.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.build.vocab import load_vocab

root = Path(__file__).resolve().parents[1]
vocab = load_vocab(root / "data" / "vocab")


def values(axis):
    return set(vocab[axis]["values"])


def test_gift_cover_is_not_world():
    assert values("gift_cover") & values("world") == set()


def test_family_role_is_not_ensemble_shape():
    assert values("family_role") & values("ensemble_shape") == set()


def test_lens_is_not_authority_stance():
    # the lens is the job; the stance is the relationship to power. a
    # value in both axes is the classic collapsing mistake.
    assert values("lens") & values("authority_stance") == set()


def test_mystery_mechanism_is_not_detecting_subject():
    # how the puzzle works versus what is being investigated.
    assert values("mystery_mechanism") & values("detecting_subject") == set()


def test_island_is_not_coastal_town():
    scale = values("setting_scale")
    assert "island" in scale and "coastal-town" in scale
    assert "island" != "coastal-town"
    rubric = (root / "docs" / "rubrics" / "setting_scale.md").read_text()
    assert "a coastal town is connected by road" in rubric


def test_routing_keeps_locales_out_of_taste_axes():
    from src.ingest.routing import load_routing, route_keyword

    routing = load_routing(root / "data" / "motifs" / "routing.yaml")
    for locale in ("california", "london, england", "new york city"):
        route = route_keyword(locale, routing, vocab)
        assert route["kind"] == "metadata"
        assert route.get("field") == "setting_geo"
        assert "axis" not in route


def test_axis_values_are_normalised():
    # the vocab is load-bearing: no stray casing or whitespace.
    for axis, meta in vocab.items():
        for value in meta["values"]:
            assert value == value.strip().lower(), f"{axis}: {value!r}"
