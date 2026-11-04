"""cli: build, check, check-context, dump, tags, recommend.

usage (from repo root):
  python3 -m src.cli build [--works dir] [--vocab dir] [--db path]
  python3 -m src.cli import --source letterboxd --path export/ [--out path]
  python3 -m src.cli import --source trakt [--out path]
  python3 -m src.cli affinity [--works dir] [--config path] [--out path]
  python3 -m src.cli affinity-check [--table path]
  python3 -m src.cli check [--works dir] [--vocab dir]
  python3 -m src.cli check-context context.yaml [--works dir] [--vocab dir]
  python3 -m src.cli dump work-id [--db path]
  python3 -m src.cli tags work-id [--db path] [--config path]
  python3 -m src.cli recommend context.yaml [--db path] [--config path]
"""

import argparse
import sys
from pathlib import Path

import yaml

from .build.affinity import (
    build_table,
    check_table,
    dump_table,
    harvest_terms,
    load_affinity_config,
    with_hashes,
)
from .build.compiler import compile_db, load_works, read_work
from .ingest import letterboxd, trakt
from .ingest.rows import dump_candidates
from .build.vocab import catalog_error, load_vocab
from .build.works import dump
from .query.context import load_context, validate_context
from .query.engine import engine

default_config = "config/scoring.v0.yaml"
default_vocab = "data/vocab"
default_works = "data/works"
default_db = "build/latent.db"
default_affinity_config = "config/affinity.v1.yaml"
default_affinity_table = "build/affinity-table.json"


def _fail(messages):
    for m in messages:
        print(f"error: {m}", file=sys.stderr)
    sys.exit(1)


def cmd_build(args):
    vocab = load_vocab(args.vocab)
    works = load_works(args.works, vocab)
    compile_db(works, vocab, args.db)
    reviewed = sum(1 for w in works.values() if w.get("status") == "reviewed")
    print(f"built {len(works)} works ({reviewed} reviewed, {len(works) - reviewed} draft) into {args.db}")


def cmd_check(args):
    vocab = load_vocab(args.vocab)
    works = load_works(args.works, vocab)
    print(f"ok: {len(works)} valid works, {len(vocab)} vocab axes")


def cmd_check_context(args):
    vocab = load_vocab(args.vocab)
    works = load_works(args.works, vocab)
    doc = load_context(args.context)
    errors = validate_context(doc, set(works), vocab, filename=str(args.context))
    if errors:
        _fail(errors)
    print(f"ok: valid taste context ({len(doc.get('liked') or [])} liked works)")


def cmd_import(args):
    """turn one source's data into a candidate file. never a taste context."""
    if args.source == "letterboxd":
        doc = letterboxd.collect(args.path)
    elif args.source == "trakt":
        doc, message = trakt.collect()
        if doc is None:
            print(f"error: {message}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"error: no adapter for source {args.source!r}", file=sys.stderr)
        sys.exit(1)
    out = Path(args.out) if args.out else Path(f"build/candidates-{args.source}.yaml")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dump_candidates(doc))
    print(
        f"import: {doc['summary']['rows']} candidates from {args.source} -> {out}"
    )
    print("candidates are not taste: confirm likes in a taste context before any scoring.")


def cmd_affinity(args):
    vocab = load_vocab(args.vocab)
    works = load_works(args.works, vocab)
    config = load_affinity_config(args.config)
    harvest = None
    harvest_meta = config["layers"].get("harvest") or {}
    if harvest_meta.get("weight"):
        harvest = harvest_terms(
            harvest_meta.get("source"), harvest_meta.get("routing"), vocab, config
        )
        harvest = {wid: terms for wid, terms in harvest.items() if terms}
    table = with_hashes(build_table(works, config, harvest), works, config)
    errors = check_table(table)
    if errors:
        _fail(errors)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(dump_table(table))
    summary = table["summary"]
    print(
        f"affinity table: {summary['terms']} terms, {summary['pairs_published']} pairs, "
        f"{summary['lonely_terms']} lonely -> {args.out}"
    )
    print(f"input_hash {table['input_hash'][:12]} output_hash {table['output_hash'][:12]}")


def cmd_affinity_check(args):
    import json

    table = json.loads(Path(args.table).read_text())
    errors = check_table(table)
    if errors:
        _fail(errors)
    print(
        f"ok: {table['summary']['terms']} terms, every neighbour recomputable from "
        f"its explanation, output_hash verified"
    )


def cmd_dump(args):
    doc = read_work(args.db, args.work_id)
    sys.stdout.write(dump(doc))


def cmd_tags(args):
    eng = engine(args.db, args.config)
    sys.stdout.write(eng.tags(args.work_id))


def cmd_recommend(args):
    eng = engine(args.db, args.config)
    result = eng.recommend(args.context)
    sys.stdout.write(yaml.safe_dump(result, sort_keys=False, default_flow_style=False, width=1000))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="latent", description="deterministic taste decomposition engine (phase 0)")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_source(p):
        p.add_argument("--vocab", default=default_vocab)
        p.add_argument("--works", default=default_works)

    p = sub.add_parser("build", help="validate works and compile the sqlite catalog")
    add_source(p)
    p.add_argument("--db", default=default_db)
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("check", help="validate works without writing anything")
    add_source(p)
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("check-context", help="validate a taste context file")
    add_source(p)
    p.add_argument("context")
    p.set_defaults(fn=cmd_check_context)

    p = sub.add_parser("import", help="turn one source's export into candidates (never taste)")
    p.add_argument("--source", required=True, help="letterboxd | trakt")
    p.add_argument("--path", default="", help="export directory, for file-export sources")
    p.add_argument("--out", default="")
    p.set_defaults(fn=cmd_import)

    p = sub.add_parser("affinity", help="build the structural affinity table (cold-start prior)")
    add_source(p)
    p.add_argument("--config", default=default_affinity_config)
    p.add_argument("--out", default=default_affinity_table)
    p.set_defaults(fn=cmd_affinity)

    p = sub.add_parser("affinity-check", help="re-verify a published affinity table")
    p.add_argument("--table", default=default_affinity_table)
    p.set_defaults(fn=cmd_affinity_check)

    p = sub.add_parser("dump", help="print one work from the database in canonical yaml")
    p.add_argument("work_id")
    p.add_argument("--db", default=default_db)
    p.set_defaults(fn=cmd_dump)

    p = sub.add_parser("tags", help="the decomposed tags with evidence, as the engine sees them")
    p.add_argument("work_id")
    p.add_argument("--db", default=default_db)
    p.add_argument("--config", default=default_config)
    p.set_defaults(fn=cmd_tags)

    p = sub.add_parser("recommend", help="recommend from a taste context (deterministic)")
    p.add_argument("context")
    p.add_argument("--db", default=default_db)
    p.add_argument("--config", default=default_config)
    p.set_defaults(fn=cmd_recommend)

    args = parser.parse_args(argv)
    try:
        args.fn(args)
    except catalog_error as err:
        _fail(err.messages)


if __name__ == "__main__":
    main()
