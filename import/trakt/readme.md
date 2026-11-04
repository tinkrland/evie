# import/trakt — tv and film watch history

**medium:** tv, film
**route:** api (oauth), documented and current
**status:** the friendliest real api in this space

## what it gives

`/sync/history` for watched items (episodes and films, with timestamps),
`/sync/watchlist`, `/sync/ratings`, and the user's lists. episodes carry
season and number, so "watched the show" can be derived honestly instead
of inferred.

## what it becomes

normalized rows at the **episode** level first, then rolled up to shows
for the candidate set. a show is a candidate only when the history backs
it: a single episode is a sample, not a series commitment, and the row
keeps the watched-episode count so that stays visible.

## auth

oauth with a client id and secret held per deployment. tokens are the
owner's, stored as secrets, never in the repo and never in a taste
context.

## the trap

scrobbles are noisy: background plays, test plays, and abandoned
premieres all land in history. the candidate set keeps them, because
that is what the source says. the owner's likes are what actually get
counted, and nothing here may promote a scrobble into a preference.
