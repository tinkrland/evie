"""click paths: the export route for sources that have no api.

some sources only hand over data through their own interface: an export
button buried in settings, a "request my archive" form, a download link
that arrives by email. there is no file to parse until somebody clicks.

a click path is that route written down as data (`data/clickpaths/`):
ordered steps with the label to click, the expected outcome of each step,
and the artifact the run must produce. nothing here scrapes page content;
the steps only ever drive an *export flow*, and the driver is handed an
allowlist of labels from the file. a step that is not in the file cannot
be performed.

a path has a purpose: `export` fetches the data file, `credential`
fetches the token an api adapter needs (the clicks to make an app, mint
a key, copy a plex token). two ways to use it:

- `plan(source)` prints the click path for a human. this is the whole
  feature for sources where the click needs a logged-in browser the owner
  is already holding.
- `capture(source, driver, downloads)` runs the steps through an injected
  driver and then waits for the artifact. the driver is anything that
  answers `click(label)` and `wait_for_file(pattern)`; tests use a fake,
  production uses whatever the owner has wired. no driver ships here,
  because a browser dependency in the engine would make the build
  non-deterministic for everybody who only ever imports a csv.
"""

from pathlib import Path

import yaml

default_paths_dir = Path(__file__).resolve().parents[2] / "data" / "clickpaths"

step_keys = ("do", "target", "expect")


def load(source, paths_dir=None):
    """read one click path file and validate it. raises on a bad file."""
    base = Path(paths_dir) if paths_dir else default_paths_dir
    path = base / f"{source}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"no click path for source: {source} ({path})")
    doc = yaml.safe_load(path.read_text()) or {}
    errors = check(doc, source=source)
    if errors:
        raise ValueError("; ".join(errors))
    return doc


def check(doc, source=None):
    """validate a click path. returns a list of problems, empty when fine."""
    errors = []
    if source and doc.get("source") != source:
        errors.append(f"source field does not match file name: {doc.get('source')}")
    steps = doc.get("steps") or []
    if not steps:
        errors.append("a click path needs at least one step")
    for index, step in enumerate(steps):
        for key in step_keys:
            if not str(step.get(key) or "").strip():
                errors.append(f"step {index} is missing '{key}'")
    artifact = doc.get("artifact") or {}
    if not artifact.get("pattern"):
        errors.append("a click path must name the artifact pattern it produces")
    purpose = doc.get("purpose", "export")
    if purpose not in ("export", "credential"):
        errors.append(f"purpose must be export or credential, not {purpose!r}")
    if purpose == "export":
        # an export path is only worth writing if something can read the
        # artifact. refuse silence: name a parser, or say why there is none.
        parse = doc.get("parse")
        if not parse and not str(doc.get("why_unparsed") or "").strip():
            errors.append(
                "an export path needs `parse:` naming its adapter, or "
                "`why_unparsed:` saying why none exists"
            )
    if not doc.get("verified"):
        # not an error: an unverified path is honest, it just has to say so
        pass
    return errors


def plan(source, paths_dir=None):
    """human-readable click path. the text a person can follow."""
    doc = load(source, paths_dir)
    header = doc.get("purpose", "export")
    lines = [f"click path: {doc['source']} ({doc.get('app', 'unknown app')}) [{header}]", ""]
    if doc.get("notes"):
        lines += [f"note: {doc['notes']}", ""]
    for index, step in enumerate(doc.get("steps") or [], start=1):
        lines.append(f"{index}. {step['do']}: {step['target']}")
        lines.append(f"   expect: {step['expect']}")
    artifact = doc.get("artifact") or {}
    lines += ["", f"artifact: {artifact.get('kind', 'file')} matching {artifact['pattern']}"]
    if artifact.get("unpack"):
        lines.append(f"unpack: {artifact['unpack']}")
    lines += [f"verified: {bool(doc.get('verified'))}"]
    return "\n".join(lines)


def allowed_labels(source, paths_dir=None):
    """the only interactions a driver may perform for this source."""
    doc = load(source, paths_dir)
    return [step["target"] for step in doc["steps"] if step["do"] == "click"]


def capture(source, driver, downloads, paths_dir=None):
    """drive the export flow, then hand back the artifact path.

    the driver is injected: `click(label)` per click step, and
    `wait_for_file(pattern)` for the artifact. a driver that offers no
    such method is refused by name rather than silently skipped.
    """
    doc = load(source, paths_dir)
    for method in ("click", "wait_for_file"):
        if not hasattr(driver, method):
            raise TypeError(f"driver has no {method}(); refusing to pretend it does")
    allowed = set(allowed_labels(source, paths_dir))
    for step in doc["steps"]:
        if step["do"] == "click":
            if step["target"] not in allowed:
                raise ValueError(f"step outside the file's allowlist: {step['target']}")
            driver.click(step["target"])
        elif step["do"] == "wait":
            driver.wait_for_file(step["target"])
        else:
            raise ValueError(f"unknown step kind: {step['do']}")
    found = driver.wait_for_file((doc.get("artifact") or {})["pattern"])
    if not found:
        raise TimeoutError(f"{source}: no artifact matched {doc['artifact']['pattern']}")
    path = Path(downloads) / Path(str(found)).name if downloads else Path(str(found))
    return {"source": source, "artifact": str(path), "verified": bool(doc.get("verified"))}
