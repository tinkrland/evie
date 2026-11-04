# import/simkl — tv, film and anime watch history

**medium:** tv, film (anime titles exist in the source; v0 scope for
evie is not anime, so those rows import as candidates and stay unmatched)
**route:** api with app registration, open docs
**status:** second-best api surface after trakt

## what it gives

watched history per episode and film, watchlist, ratings, and lists, in
a shape close enough to trakt's that one normalized row serves both.

## the trap

simkl aggregates duplicates: the same film can arrive from several
playback sources within one day. dedupe on (title, year, day) and keep
the earliest timestamp, then let the catalogue step do identity work.

## refusal rules

no rating interpretation, same as every other import. a 10 in simkl is
a claim about a viewing, not evidence about a person's taste until the
owner says so.
