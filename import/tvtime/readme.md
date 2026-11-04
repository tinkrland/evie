# import/tvtime — episode watch history (sunset)

**medium:** tv
**route:** file export, via community extractors (the service is
shutting down and has never had a public api)
**status:** migration source only. treat the format as dead already.

## what it gives

per-episode watch history with dates, and follows/favourites. it was one
of the best episode-level trackers and its shutdown is exactly why file
exports beat integrations.

## what it becomes

rows at episode level, rolled up to shows, with the episode count kept.

## the trap

community extractors are unmaintained software handling someone's whole
viewing history. run them locally, treat the output as untrusted, and
never send the file anywhere but the owner's own evie instance.

## refusal rules

no live integration. no scraping the app's endpoints. this folder exists
so people who kept their export are not stranded, not to resurrect a
dead service.
