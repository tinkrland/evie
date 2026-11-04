# import/repov — tv tracking (owner-named, unverified)

**medium:** tv
**route:** unknown
**status:** `blocked` on facts. the owner named repov as one of their tv
trackers, and nothing about its interface has been verified yet.

## what must be established before this folder gets a spec

1. what repov actually is: a mainstream tracking app, a regional one, a
   niche or self-hosted tool. the answer decides everything below it.
2. how a person's own data leaves it: export, api, or neither.
3. what the rows look like: film-level, show-level, episode-level.

## what it will become regardless

the normalized row (`title`, `year`, `medium`, `source`, `source_id`,
`watched_at`). show and episode level rows roll up the same way as every
other tv source, keeping the episode count visible.

## the rule that does not bend

no scraping, no guessing. if repov cannot hand over a user's own
history through an interface they are meant to use, it is not an import,
and the honest entry in this repo is "blocked" rather than a clever
workaround.

## open

if this is a self-hosted or open-source tool, prefer the option to read
its own database file locally over any network route at all: it is the
owner's machine and the owner's server, the same reasoning as plex and
jellyfin.
