# evie — entertainment vocabulary indexing engine

the decoupled home of evie: a deterministic decomposition engine that
breaks works into explicit, human-readable parts, stores them as a
queryable graph, and finds connections by shared parts. the user
decides which connections actually mean their taste.

this repository holds evie itself. moira (tinkrland/moira, branch
`evie`) keeps the persona-side mapping that builds against it. engine
work lands here first.

## branches, and why they are branches

each vertical shares the engine core and shares none of the others'
axes, so each is its own branch with its own readme, vocabulary and
rubrics:

| branch | what it covers | why it is separate |
|---|---|---|
| `evie` | books, film, tv: the narrative engine | the mainline. a narrative work answers the same questions whatever the medium, so one axis vocabulary holds all three. |
| `music` | songs, albums, artists | music carries two separable similarity spaces at once: the verbal (lyrics) and the sonic (texture, harmony, rhythm, production). averaging them is wrong twice, once for the lyric listener and once for the sound listener. |
| `activities` | things a person does | the catalogue is verbs, not titles. the question is "will i keep doing this", not "will i enjoy experiencing this", and enjoyment must stay separate from friction. |

## why books, film and tv share axes at all

they are all expressions of storytelling. what a work wants you to feel
(fantasy), where the lead stands against power (authority_stance), how
much of the story is family (family_role), what shape the structure
promises: those questions describe what the story does to the person
experiencing it, and they transfer across media because stories
transfer. that transferability is the whole reason the `evie` branch
can hold three media in one vocabulary, and it is exactly what music
breaks: a song's lyrics and a song's sound can each be loved while the
other is rejected, so music gets two channels and the listener gets the
blend.

## rules every branch inherits

1. deterministic at query time. same catalogue, same context, same
   config, same answer, always.
2. stateless. no user data is stored by the engine. a taste context
   travels with each request.
3. never trained on user data. no embeddings, no inference at query
   time.
4. usage is not liking. a watch or listen history is exposure; the
   owner confirms what they actually like.
5. evidence is tagged untrusted until the owner confirms it.
6. axes stay separate. keywords harvested from outside catalogues are
   proposals, never canonical values, until triaged and reviewed.
7. everything is versioned: data, rubrics, scoring config.
8. cross-vertical bridges are declared, typed and refusable. never an
   implicit average.

## reading this repository

start with the readme of the branch you care about. each carries its
own scope, contract notes, plan and docs list. `docs/agreement/` on the
`evie` branch holds the rubric agreement test that gates seed corpora.
