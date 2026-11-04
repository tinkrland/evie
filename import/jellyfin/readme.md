# import/jellyfin — self-hosted watch state

**medium:** tv, film
**route:** api against the owner's own server (open source, documented,
no vendor gate)
**status:** the same shape as plex, without the vendor

## what it gives

user-scoped played items with timestamps and progress, per library.

## what it becomes

the same rows as plex: episode and film level, progress kept as
metadata, availability never treated as preference.

## the trap

jellyfin is the one source where the *user* is explicit and first-class,
so do not inherit plex's household assumption. still refuse to merge
profiles: a shared server with two users is two people with two taste
contexts.

## refusal rules

no library contents as taste. no file paths in any output. no server
admin endpoints at all: an import is not an audit.
