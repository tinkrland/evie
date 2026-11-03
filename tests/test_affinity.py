"""structural affinity: the cold-start prior is deterministic, explainable
and honest about what it does not know."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.build.affinity import (
    build_table,
    check_table,
    dump_table,
    load_affinity_config,
    score_pair,
    with_hashes,
    work_terms,
)
from src.build.compiler import load_works
from src.build.vocab import load_vocab

root = Path(__file__).resolve().parents[1]
vocab = load_vocab(root / "data" / "vocab")
works = load_works(root / "tests" / "fixtures" / "works", vocab)
config = load_affinity_config(root / "config" / "affinity.v0.yaml")


def table():
    return with_hashes(build_table(works, config), works, config)


def test_build_is_deterministic():
    first = table()
    second = table()
    assert first["output_hash"] == second["output_hash"]
    assert first["input_hash"] == second["input_hash"]
    assert dump_table(first) == dump_table(second)


def test_every_neighbour_is_recomputable_from_its_explanation():
    assert check_table(table()) == []


def test_a_tampered_score_is_caught():
    broken = table()
    neighbour = next(
        n
        for row in broken["terms"]
        for n in row["neighbours"]
        if n["explain"]["shared_works"]
    )
    neighbour["score"] = 0.999999
    errors = check_table(broken)
    assert errors, "the check must not trust a score it cannot recompute"


def test_scoring_runs_over_the_union_not_per_axis():
    # consulting-detective's neighbours must come from other axes: the
    # label alone predicts nothing, which is the whole point of the graph.
    row = next(
        r for r in table()["terms"] if r["term"] == ["lens", "consulting-detective"]
    )
    axes = {n["term"][0] for n in row["neighbours"]}
    assert "lens" not in axes
    assert axes & {"gift_kind", "protagonist_gift", "lead_manner"}


def test_unknown_is_not_evidence():
    synthetic = {
        "w1": {
            "tags": {
                "lead_manner": [{"value": "unknown", "role": "primary"}],
                "tone": [{"value": "earnest", "role": "primary"}],
            }
        }
    }
    terms = work_terms(synthetic["w1"], config)
    assert ("lead_manner", "unknown") not in terms
    assert ("tone", "earnest") in terms


def test_lonely_terms_are_published_empty_not_padded():
    synthetic = {
        "a": {"tags": {"tone": [{"value": "earnest", "role": "primary"}]}},
        "b": {"tags": {"stakes": [{"value": "high", "role": "primary"}]}},
    }
    lonely_config = dict(config)
    lonely_config["min_pair_works"] = 2
    built = build_table(synthetic, lonely_config)
    assert built["summary"]["lonely_terms"] == 2
    for row in built["terms"]:
        assert row["neighbours"] == []


def test_min_pair_works_filters_thin_pairs():
    synthetic = {
        "a": {"tags": {"tone": [{"value": "earnest", "role": "primary"}],
                       "stakes": [{"value": "high", "role": "primary"}]}},
        "b": {"tags": {"tone": [{"value": "earnest", "role": "primary"}],
                       "stakes": [{"value": "high", "role": "primary"}]}},
    }
    strict = dict(config)
    strict["min_pair_works"] = 2
    built = build_table(synthetic, strict)
    pair_rows = [r for r in built["terms"] if r["term"] == ["tone", "earnest"]]
    assert pair_rows and pair_rows[0]["neighbours"]
    loose = dict(config)
    loose["min_pair_works"] = 3
    assert build_table(synthetic, loose)["summary"]["pairs_published"] == 0


def test_config_change_changes_the_hash():
    louder = dict(config)
    louder["top_k"] = 1
    assert (
        with_hashes(build_table(works, louder), works, louder)["output_hash"]
        != table()["output_hash"]
    )


def test_published_table_on_disk_is_self_consistent():
    path = root / "build" / "affinity-table.json"
    if not path.exists():
        return
    published = json.loads(path.read_text())
    assert check_table(published) == []


def test_score_is_cosine_over_incidence():
    assert score_pair(2, 4, 4) == 0.5
    assert score_pair(0, 0, 4) == 0.0
