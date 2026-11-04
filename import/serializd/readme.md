# import/serializd — tv and film watch history

**medium:** tv (film secondary)
**route:** verify before building
**status:** the owner named it among the trackers they use; no public
api has been confirmed, and an export has not been confirmed either.

## what it is

a social tracking app for tv shows, closer in spirit to letterboxd than
to trakt: diary-like logging, ratings, reviews, and lists per show and
per episode.

## what it must become

the same normalized row as every other import: title, year, medium,
source, source id when one exists, watched timestamp when one exists.
episode-level rows roll up to shows with the episode count kept visible.

## what to verify first

1. does the app expose a data export from account settings? if yes, that
   is the route, and this becomes a file-export import like letterboxd.
2. if a private web api exists, is it documented and permitted for
   reading a user's own data? an undocumented endpoint is not a route,
   it is a scrape with extra steps.
3. if neither exists, the folder stays `blocked` and says so. no
   scraping, ever.

## the trap

diary-style logging is per-viewing, like letterboxd. the same episode
logged twice is one candidate, not a stronger signal.
