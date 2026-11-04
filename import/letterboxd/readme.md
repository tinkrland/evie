# import/letterboxd — film watch history

**medium:** film
**route:** file export (csv), from account settings
**api:** none public. their api has been "coming soon" for years; do not
build against a promise.

## what it gives

every film logged, with rating, watched date, rewatch flag, and usually
the year. favourite lists and watchlists come along in separate files.

## what it becomes

normalized rows (`title`, `year`, `film`, `letterboxd`, no source id,
`watched_at` from the logged date). ratings are carried as metadata only
and never interpreted as taste.

## the trap

diary rows are per-viewing, not per-film. the same film appears many
times and a rewatch is not a stronger signal. dedupe to one candidate
per film, keep the earliest and latest dates, and let the owner decide.

## refusal rules

- no scraping the public profile, even though it is trivially readable.
  the export exists precisely so we do not have to.
- no inventing a `tmdb_id` from a title match inside the import. that
  resolution belongs to the catalogue step, with its own evidence.
