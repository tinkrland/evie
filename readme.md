# moira — music branch

the music vertical. sibling of evie, which handles books, film and tv. a
separate branch because it needs a separate contract, not a separate mood.

## why music cannot reuse evie's axes

books, film and tv shows can share one axis vocabulary because they are
all expressions of storytelling. a narrative work answers the same
questions whatever its medium: what does this want me to feel (fantasy),
where does the lead stand against power (authority_stance), what shape
does the structure promise (structure, resolution), how much of it is
family (family_role). those properties describe what the story does to
the person experiencing it, and they transfer across media because
stories transfer. someone who loves a heist film and a con-artist show
is telling you one thing that one vocabulary can carry.

music is not that, or not only that. a song carries two largely
separable spaces of similarity at once:

1. **the verbal.** what the lyrics say, from what stance, in what
   register. this is the storytelling half, and it does connect to
   narrative taste.
2. **the sonic.** texture, harmony, rhythm, production, timbre, energy.
   this has nothing to do with what the song says.

people routinely love a lyric and cannot stand how it sounds, or love
how a song sounds and could not repeat a line of it. so the fatal move
is averaging the two channels into one similarity score: it is wrong
twice at once, once for the lyric listener and once for the sound
listener, and every recommendation drawn from it is half right for the
wrong person.

## design consequences

- two channel families, matched separately, never fused silently: a
  lyric channel and a sonic channel. this is evie's orthogonality rule
  applied inside a single medium.
- the listener's own weighting decides the blend, explicitly, and the
  provenance map names the channel behind every match.
- instrumental and non-lyric tracks are first-class: where the verbal
  channel is absent it is absent, not empty.
- units stay separate: track, album, artist and playlist carry
  different promises, and an artist match is not a track match.
- usage is not liking, same as evie. a listening history is exposure,
  never taste.

## what this branch shares with evie

the engine core (authored catalogue, deterministic build, stateless
taste contexts, provenance maps, versioned config) and the contract
rules (never train on user data, no embeddings, no inference at query
time, vocabulary and rubrics versioned together).

what it does not share is any axis or value. music authoring starts
from an empty vocab on purpose. an evie value appearing here would be
axis leakage, and axis leakage is how the whole thing rots back into
genre labels.

## the cross-vertical rule

the verticals may talk only through a declared bridge: a named axis, a
written reason, a refusable recommendation. "this song will land
because you like slow-burn crime dramas" is not a bridge, it is a
guess. "you like tight puzzle structures on screen and dense wordplay
in lyrics, same teleology: make the surface work reveal a hidden
structure" is a bridge: typed, explainable, and the listener can say no.

the typology for such bridges comes from substrate's canvas research
(five axes: same formalism, same craft, same subject, same purpose,
same way of knowing), not from adjacency in a genre tree.

## limits

where this stops holding: for music whose primary content is sonic
texture (ambient, instrumental), the verbal channel is absent and
lyric-weighted profiles collapse to the sonic channel alone; the model
does not claim to explain live performance, listening context, or
cultural scenes, which are circumstances of consumption, not traits of
the work. v0 keeps unit scope narrow (tracks and albums) and says so
rather than pretending the coverage is complete.

## status

pre-alpha. branch scaffolded, nothing built. the vocabulary will be
authored the way evie's was: values frozen, evidence per tag, rubrics
before tagging, determinism verified by tests.

## import/

`import/` holds one folder per source spec, same contract as the evie
vertical: what the source gives, how it is reached, what it becomes, and
where the import must refuse. the music-specific twist is the `channel`
field: every imported row declares whether its evidence is sonic,
verbal, or both, so the two similarity channels this vertical exists to
keep separate can never be merged by an import.

first folder: `import/superfan/`, the one source that carries both
channels (listens plus written album reviews).

## planned docs

- `schema.md`: the two channel families and their axes
- `docs/rubrics/`: lyric channel rubrics, sonic channel rubrics
- `docs/sources.md`: music catalogues (musicbrainz, discogs,
  listenbrainz, acoustic descriptor sets) and their terms
- `buildplan.md`: phased, same acceptance style as evie's
