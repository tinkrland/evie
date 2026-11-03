# moira — activities branch

the participatory vertical. evie decomposes works a person experiences;
this branch decomposes things a person does.

## why this needs its own branch

a work is authored: someone made it, and its traits describe what it
does to you when you meet it. an activity is not authored: it is a
practice you perform, and its "catalogue" is a list of verbs, not
titles. a session is not a work you can re-watch, and a hobby is not a
genre.

so evie's vocabulary cannot be reused, and not because the values are
wrong: because nothing in it answers the question an activity
recommendation must answer. "will I actually do this, and keep doing
it" is a different question from "will I enjoy experiencing this", and
the difference is the whole design.

## the axis families this branch proposes

- **company.** solo, pair, small group, crowd. who you do it with
  changes what the activity is.
- **skill curve.** entry cost, mastery ceiling, plateau behaviour.
  some things are fun in ten minutes and miserable at the top; some
  are the reverse.
- **physical load.** intensity, injury risk, recovery cost.
- **setting.** indoor or outdoor, seasonal, weather-dependent.
- **gear and logistics.** what must be bought, booked, traveled,
  reserved. friction is part of the experience, not a nuisance around
  it.
- **structure.** freeform vs rule-bound, competitive vs expressive,
  improvised vs choreographed.
- **commitment shape.** one session, one season, one lifetime. the
  same activity offered at different commitment shapes is a different
  recommendation.
- **enjoyment vs friction.** kept separate on purpose: a person can
  love an activity and never do it again because the friction wins.
  the engine must be able to say that out loud.

## the only honest bridge to evie

one's media taste very weakly predicts activity taste, and the bridge
that does exist runs through the typology axis, never the subject: same
teleology ("make the invisible visible": microscopy and documentary
film, per substrate's canvas research) or same way of knowing. the
bridge is declared, typed, and refusable. an implicit average between
"likes crime dramas" and "will enjoy bouldering" is a fabrication.

## what this branch shares with the others

the engine core (authored catalogue, deterministic build, stateless
contexts, provenance maps, versioned config) and the contract rules
(never train on user data, no embeddings, no inference at query time,
vocabulary and rubrics versioned together).

it shares no axes and no values with evie or music. an activity
appearing in a media profile would be axis leakage.

## limits

where this stops holding: activity taste is dominated by circumstances
this engine deliberately refuses to model: location, budget, access,
time of life, injuries, care duties. v0 should therefore restrict
itself to activities whose friction is mostly interior (reading,
walking, cooking, sketching) and say plainly that outdoor and
gear-heavy activities need the circumstance layer this branch does not
have. claiming otherwise would be the exact overreach the library
exists to avoid.

## status

pre-alpha. branch scaffolded, nothing built. vocabulary and rubrics to
be authored from scratch, in the same order as evie: rubrics before
tagging, evidence per claim, determinism proven by tests.

## planned docs

- `schema.md`: the axis families above, as formal axes with values
- `docs/rubrics/`: one file per axis, boundaries and counterexamples
- `docs/sources.md`: where activity metadata could come from
  (openstreetmap tags, federation taxonomies, sports bodies) and what
  each may not be used for
- `buildplan.md`: phased, same acceptance style as evie's
