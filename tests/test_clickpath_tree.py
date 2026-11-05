"""the click path tree must stay honest as it grows."""

import importlib
from pathlib import Path

import pytest

from src.ingest import clickpath

paths_dir = Path(__file__).resolve().parents[1] / "data" / "clickpaths"


def _sources():
    return sorted(path.stem for path in paths_dir.glob("*.yaml"))


def test_every_click_path_validates():
    for source in _sources():
        assert clickpath.check(clickpath.load(source), source=source) == []


def test_every_click_path_states_its_purpose():
    for source in _sources():
        doc = clickpath.load(source)
        assert doc.get("purpose") in ("export", "credential"), source


def test_every_export_path_has_a_real_parser_or_a_reason():
    for source in _sources():
        doc = clickpath.load(source)
        if doc.get("purpose") != "export":
            continue
        parse = doc.get("parse")
        if parse:
            module = importlib.import_module(f"src.ingest.{parse}")
            assert hasattr(module, "collect"), f"{source}: {parse} exposes no collect()"
        else:
            assert len(str(doc.get("why_unparsed") or "").strip()) > 30, source


def test_an_export_path_without_parser_or_reason_is_refused():
    doc = {
        "source": "nowhere",
        "purpose": "export",
        "steps": [{"do": "click", "target": "a", "expect": "b"}],
        "artifact": {"pattern": "*.csv"},
    }
    errors = clickpath.check(doc, source="nowhere")
    assert any("why_unparsed" in error for error in errors)


def test_a_bad_purpose_is_refused():
    doc = {
        "source": "nowhere",
        "purpose": "scrape",
        "steps": [{"do": "click", "target": "a", "expect": "b"}],
        "artifact": {"pattern": "*.csv"},
    }
    assert any("purpose" in error for error in clickpath.check(doc, source="nowhere"))


def test_credential_paths_need_no_parser():
    doc = clickpath.load("plex")
    assert doc["purpose"] == "credential"
    assert "parse" not in doc


def test_credential_paths_never_name_a_file_artifact():
    for source in _sources():
        doc = clickpath.load(source)
        if doc.get("purpose") != "credential":
            continue
        assert (doc.get("artifact") or {}).get("kind") == "secret", source


def test_all_click_paths_are_unverified_until_executed():
    """a path is not verified by being written. only a real run flips this."""
    unverified = [source for source in _sources() if not clickpath.load(source).get("verified")]
    assert set(unverified) == set(_sources())


def test_plan_prints_the_purpose():
    text = clickpath.plan("netflix")
    assert "[export]" in text.splitlines()[0]
    assert "Viewing activity" in text


@pytest.mark.parametrize("source", ["netflix", "repov"])
def test_capture_needs_a_driver(source):
    with pytest.raises(TypeError):
        clickpath.capture(source, object(), None)
