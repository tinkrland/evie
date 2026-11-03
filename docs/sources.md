# sources: reference catalogues and ingest apps

evie needs two very different kinds of outside help, and they get
confused constantly. keep them apart:

- **reference catalogues** answer "what is this work and what is it
  called in other systems". they feed identity, metadata, and the
  language of our vocab. they never supply latent traits.
- **ingest apps** answer "what has this person actually watched".
  they feed the *candidate set* a taste context is built on. usage is
  not liking: a watch history is evidence of exposure, never of taste.

surveyed 2026-11-03. terms and availability change; re-check before
building an adapter.

## 1. reference catalogues

| source | what it gives | access | terms / caveat | our use |
|---|---|---|---|---|
| tmdb | titles, years, cast, genres, and a large community keyword vocabulary | free REST api, key required | attribution required; keywords are community-written and noisy | metadata, external ids, keyword harvest |
| thetvdb | series metadata, genres, season/episode structure | v4 api, project-specific keys; key model has tightened | per-project keys, not open | episode structure only; genres are coarse |
| imdb | very large title datasets (basics, crew, ratings), plus a keywords dataset | dataset dumps, no free live api | non-commercial license terms | bulk identity lookup, year/creator checks |
| wikidata | cross-medium identity spine: same work across book, film, tv; creators; ids | cc0, sparql | requires care with deprecated values | external_ids spine, cross-medium links |
| open library | book works, editions, isbn, and a huge free-form subject list | open api, no key | subjects are messy, unreconciled | book identity, subject harvest for wrangling |
| google books | volume metadata and coarse categories | api with quota | categories are b2c-ish and coarse | fallback book metadata |
| tv tropes | the richest written language for narrative patterns in existence | no api; scraping is contested | do not bulk-copy; honour their terms | vocabulary *inspiration* for rubrics and motifs, never data |

### how each maps into evie

- identity: wikidata first (stable, cross-medium), then tmdb/imdb for
  screen and open library/isbn for books. never invent an id.
- metadata: title, first_release, creators, lead_performers come from
  these catalogues. they are facts, so they must be verifiable.
- language: tmdb keywords and open library subjects are the raw feed
  for the motifs wrangling queue (docs/motifs-wrangling.md). they are
  proposals, never auto-adopted.
- latent traits: **none of these sources supply them.** fantasy,
  authority_stance, gift_* and friends stay rubric-tagged. no
  embedding, no inference.

## 2. ingest apps (what has this person watched)

| app / site | signal | access reality | note |
|---|---|---|---|
| trakt | watch history, watchlist, ratings, lists | documented rest api, OAuth (22 apis published) | the most integration-friendly tracker; also the hub many media center users export to |
| simkl | tv/movie/anime tracking | open api with app registration | second-best api surface |
| plex | library, watch state | own api, server token | self-hosted signal; no cloud account needed |
| jellyfin | library, watch state | open source api | self-hosted, fully documented |
| letterboxd | films watched, ratings, lists, reviews | **no public api** ("coming soon" since forever); CSV export from account settings | export-only for now; scraping is against terms |
| tv time | episode-level watch history | **no public api, and the service is shutting down**; community extractors exist (CSV/JSON) | treat as a migration source, not an integration |
| storygraph | books read, moods, ratings | **no public api**; roadmap requests open since 2021 with no timeline; CSV import/export of goodreads format | export-only |
| goodreads | books read, shelves, ratings | public api retired 2020 | dead for programmatic use; CSV export still exists |
| netflix / prime / disney | viewing history | account page csv (netflix) or nothing | messy, region-dependent |

### the pattern worth designing around

the trackers people actually use for books and film (letterboxd,
storygraph, tv time, goodreads) mostly **do not have public read
apis**, and one of them is shutting down. the ones with real apis
(trakt, simkl, plex, jellyfin) skew toward self-hosting hobbyists.

so ingest v1 should be: **user uploads an export file, or connects a
real api where one exists**. file-based ingest is stateless-friendly
(it is just another input to a taste context), and it survives
services dying, which they keep doing.

### the contract still applies

- usage is not liking. a watch history proposes candidates; the owner
  confirms the liked set. no rating-based taste inference, ever.
- evidence tagged untrusted. imported rows are claims by the source.
- determinism is safe: ingest feeds the *catalogue and context
  authoring* path, never query time.

## 3. what this implies for the build

1. `src/ingest/` gets **adapters**, not integrations: `trakt`,
   `simkl`, `plex`, `jellyfin` (api) and `letterboxd`, `storygraph`,
   `goodreads`, `tvtime`, `netflix` (file exports). one interface:
   file or token in, normalized rows out.
2. a normalized row is the narrowest possible shape: title, year,
   medium, source, source id if any, timestamp. resolution to an
   evie work id happens after, against wikidata/tmdb/open library.
3. nothing in ingest may write a taste context. it produces
   *candidates* for the owner to confirm.

## 4. candidate mappings (proposal, not approved)

tmdb movie genres: action, adventure, animation, comedy, crime,
documentary, drama, family, fantasy, history, horror, music, mystery,
romance, science fiction, thriller, war, western.
tmdb tv genres: action & adventure, animation, comedy, crime,
documentary, drama, family, kids, mystery, news, reality, sci-fi &
fantasy, soap, talk, war & politics, western.

our genre_tradition is deliberately smaller and more narrative-shaped
(crime, noir, cozy-mystery, legal, thriller, spy, fantasy, sci-fi,
romance, horror, drama, comedy). the mapping is many-to-few and
one-way: tmdb genre feeds genre_tradition, never the reverse, and a
keyword harvest feeds motifs candidates only after wrangling review.

## 5. open questions raised

27. which ingest source ships first? proposal: letterboxd csv (film
    half of the audience) and trakt api (the only friendly tv api
    left standing).
28. tmdb keyword harvest: do we adopt tmdb keywords as motif
    candidates wholesale into the wrangling queue, or only when a
    keyword appears often enough to matter?
29. tv time shutdown: do we offer a one-time migration path for its
    export files, given it will be a dead format soon but real users
    have real history in it?
