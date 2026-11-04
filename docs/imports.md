# imports: turning a source into candidates

`src/ingest/` holds the adapters. each one is named after its folder in
the repository's `import/` tree, so spec and code never drift apart.

## the shape

```
src/ingest/rows.py        the normalized row, dedupe, candidate file
src/ingest/letterboxd.py  file export (csv) -> candidates
src/ingest/trakt.py       api (oauth) -> candidates
```

an import produces **candidates**: things a person watched or read,
according to one source. a candidate is not taste, an import never writes
a taste context, and nothing here assigns an evie work id. resolution
against the reference catalogues is a later step with its own evidence.

## the row

```
title       the title as the source wrote it
year        release or first-air year, when the source has one
medium      film | tv | book
source      letterboxd, trakt, ...
source_id   the source's own id, never invented
watched_at  the source's timestamp, when it has one
detail      source-specific extras, kept visible, never interpreted
```

`detail` is where the honesty lives. letterboxd's diary gives `views`
(actual viewings, not file appearances) and `rewatch`; trakt gives
`episodes`, `seasons` and `last_watched_at`. ratings ride along as text
and are never read as preference.

## commands

```
python3 -m src.cli import --source letterboxd --path export/
python3 -m src.cli import --source trakt
```

`letterboxd` reads a folder of the export's csv files and tolerates any
of them missing. `trakt` needs `TRAKT_CLIENT_ID` and `TRAKT_ACCESS_TOKEN`
in the environment and refuses with a plain message when they are absent;
its shaping function is pure and its http call is injectable, so the
adapter is tested without a token and without the network.

both write `build/candidates-<source>.yaml`, sorted, deterministic, and
both print the same reminder: candidates are not taste.

## what an adapter must refuse

- rows it cannot read, rather than best-guessing fields
- promoting a rating, a streak, or a recap screen into a preference
- writing a taste context
- inventing a work id from a title match

## status

| adapter | route | status |
|---|---|---|
| letterboxd | file export (csv) | implemented, tested offline |
| trakt | api (oauth) | implemented, tested with an injected payload; live call untested until a token is present |

## next

the remaining file-export adapters in the `import/` tree (goodreads,
storygraph, netflix, tvtime, fable, serializd, pagebound, repov, pifyi)
follow the letterboxd pattern: read the export, normalize, dedupe,
report. the remaining api adapters (simkl, plex, jellyfin) follow the
trakt pattern: pure shaping plus an injectable fetch.
