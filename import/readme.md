# import — where a person's history comes from

one folder per source. each folder carries the spec for that import: what
it gives, how it is reached, what it becomes, and where it must stop.

these are specifications, not adapters. the code that implements them
lives on the `evie` branch under `src/ingest/`, one adapter per folder
here, so a spec and its implementation always share a name.

## the one rule that shapes everything

**usage is not liking.** an import produces *candidates*: things this
person has watched, read, or listened to. it never produces taste. the
owner confirms what they actually like from that candidate set, and only
confirmed likes enter a taste context. a history file is evidence of
exposure, nothing more.

the second rule: **no scraping.** if a source has no public interface
and no export of your own data, it is not importable, and we say so
rather than inventing a route.

## the normalized row

every import, whatever its source, produces the same narrow shape:

```
title       the title as the source wrote it
year        release or first-air year, when the source has one
medium      film | tv | book
source      letterboxd, trakt, storygraph, ...
source_id   the source's own id, when it has one (never invented)
watched_at  the timestamp from the source, when it has one
```

resolution to an evie work id happens **after** import, against the
reference catalogues (wikidata, tmdb, open library), and never by
guessing: unmatched rows stay unmatched and are reported.

## the two access families

1. **file export.** the person downloads their own data and uploads it.
   this is the majority of sources, including every book tracker.
2. **api.** a real interface with real auth. this is the minority, and
   it skews toward self-hosting hobbyists.

file exports are the robust path: they are just another input to a taste
context, and they survive services shutting down, which they keep doing
(tv time is in the middle of exactly that).

## the sources

| folder | medium | route | status |
|---|---|---|---|
| `letterboxd/` | film | file export (csv) | designed |
| `trakt/` | tv + film | api (oauth) | designed |
| `simkl/` | tv + film | api | designed |
| `plex/` | tv + film | api (server) | designed |
| `jellyfin/` | tv + film | api (open source) | designed |
| `netflix/` | tv + film | file export (viewing activity) | designed |
| `tvtime/` | tv | file export (community extractors; service shutting down) | designed |
| `storygraph/` | books | file export (csv) | designed |
| `goodreads/` | books | file export (csv; api retired 2020) | designed |

status means: `designed` (spec written, no code), `verified` (adapter
exists and passes its tests), `blocked` (needs something we do not
have). nothing here is verified yet.

## what an adapter must refuse

- rows it cannot read, rather than best-guessing fields
- media outside the vertical's scope (music rows in a books import)
- duplicate candidates that the source itself would not distinguish
- any behaviour that writes a taste context directly
