# import — where a listener's history comes from (music vertical)

one folder per source, same contract as the evie vertical's `import/`,
with one difference that shapes every spec here: **music splits into two
channels.**

a source that records *what played* gives sonic exposure. a source that
records *what was written about it* (reviews, ratings with a caption,
notes) can also touch the verbal channel. no source gets to merge them:
the import produces rows, and each row says which channel its evidence
belongs to.

and the standing rule still holds: **usage is not liking.** a listen is
exposure, a scrobble is a play, and the owner confirms what they
actually love.

## the normalized row (music)

```
title        track, album, or artist as the source wrote it
artist       the artist as the source wrote it
medium       track | album | artist
source       superfan, lastfm, statsfm, ...
source_id    the source's own id, when it has one
played_at    the timestamp, when the source has one
channel      sonic | verbal | both
```

`channel` is the music-specific field: a scrobble is sonic only. an
album review with a written opinion is verbal plus sonic evidence.

## the sources

| folder | route | channel | status |
|---|---|---|---|
| `superfan/` | mobile app, export to verify | sonic + verbal | designed |

more sources are named by the owner (last.fm, stats.fm, musicboard) and
each gets a folder when its spec is written. last.fm and stats.fm are
scrobble-first (sonic only); musicboard is review-first (verbal heavy).
