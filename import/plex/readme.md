# import/plex — self-hosted watch state

**medium:** tv, film
**route:** api against the owner's own server (token per server)
**status:** self-hosters only, and perfectly fine for them

## what it gives

the library itself (what exists) and the watch state (what was watched,
when, how far). for evie only the watch state matters: library contents
are availability, not preference, and availability is deliberately not
modelled.

## what it becomes

rows at episode and film level, with a progress figure where the server
has one. progress is kept as metadata: a half-watched film is not a
rejection, and an abandoned series is not a dislike.

## the trap

household servers are shared. a plex account is not one person. the
import must ask whose profile it is reading and refuse to merge
profiles, even when they share a server and a token.

## refusal rules

never read libraries as taste. never expose the server's file paths,
which leak more about a person than their watch history does.
