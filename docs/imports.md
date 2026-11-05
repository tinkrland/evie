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

## goodreads: the shelf rules are the adapter

the export's `exclusive shelf` column decides everything, and only
`read` becomes a candidate:

- `to-read` is a shelf of intentions, not interest. excluded.
- `currently-reading` is unfinished, so it is not a judgement yet.
  excluded.
- `read` is a candidate, and `read count` becomes views.

isbn13 then isbn10 is the only hard identity in the file, so it becomes
`source_id`, and dedupe keys on a hard id before falling back to title:
two shelf rows carrying one isbn are one book however many editions
they were logged as, and their read counts add up. excel wraps isbns in
armour quotes, which the adapter unwraps first, and a row with no isbn
keeps `source_id` null rather than inventing one. title resolution stays
in the catalogue step, as ever.

## what an adapter must refuse

- rows it cannot read, rather than best-guessing fields
- promoting a rating, a streak, or a recap screen into a preference
- writing a taste context
- inventing a work id from a title match

## storygraph: the status rules, and one negative signal

same shelf logic as goodreads, with one addition worth naming:

- `read` is a candidate.
- `currently-reading` and `to-read` are excluded for the same reasons.
- `did-not-finish` is excluded from candidates but **counted and
  reported** as `excluded_by_status`. it is the only source that tells
  us a book was rejected, and a rejection is real evidence. it is not a
  candidate, and it is not dropped either.

identity: storygraph exports `isbn` or a `uid` for books without one. an
isbn becomes `source_id`; a uid is not an identity, so it goes to detail
and `source_id` stays null.

the export is sometimes a folder: the library csv plus a tags csv. the
adapter finds the library by its columns (`title`, `read status`), not
by filename, because the filename changes across export revisions.

the user's own tags go to detail untouched. they are shelf words, the
raw material of a future wrangling pass, and importing them as axis
values would let a foreign taxonomy in through the side door.

## status

| adapter | route | status |
|---|---|---|
| letterboxd | file export (csv) | implemented, tested offline |
| trakt | api (oauth) | implemented, tested with an injected payload; live call untested until a token is present |
| goodreads | file export (csv) | implemented, tested offline; shelf rules pinned by test |
| storygraph | file export (csv, file or folder) | implemented, tested offline; did-not-finish counted, not promoted |

## next

the remaining file-export adapters in the `import/` tree (netflix,
tvtime) follow the letterboxd pattern: read the export, normalize,
dedupe, report. the mobile-app sources (fable, serializd, pagebound,
repov, pifyi) take the click-path route instead: a written route plus a
landing-zone parse, because none of them offers a file we can fetch. the remaining api adapters (simkl, plex, jellyfin) follow the
trakt pattern: pure shaping plus an injectable fetch.
