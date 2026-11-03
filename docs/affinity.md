# affinity: the cold-start prior

`src/build/affinity.py` answers the question a recommender faces before
anyone has clicked anything: **which axis values travel together?**

it is computed from the governed catalogue alone. no signals, no user
data, no embeddings, no clock. same catalogue plus same config gives the
same table, and the table carries the hashes that prove it.

## what it computes

terms are `(axis, value)` pairs from every work in the catalogue: layer 2
tags, genre tradition, setting scale, and the crime module. `unknown` is
excluded, because unknown means "unobserved" and must never be summed as
if it were a measurement.

for terms a and b, with work incidence lists:

```
support(a)  = number of works carrying a
shared(a,b) = number of works carrying both
score(a,b)  = shared / sqrt(support(a) * support(b))
```

that is cosine similarity over work-incidence vectors: 1.0 means the two
values always appear together, 0 means they never do. in the current
catalogue, `lens/consulting-detective` travels with
`authority-stance/outsider-underestimated`, `gift-kind/hyper-observation`,
`lead-manner/eccentric` and `protagonist-gift/puzzle-intellect`. that is
the civilian-detective cluster appearing as structure rather than as a
genre label.

## why the union and not per-axis

scoring runs across every axis at once. a value scored only inside its
own axis family looks lonely even when its real neighbours live next
door: `consulting-detective` has no useful neighbour inside `lens`, and
plenty outside it. the union is the honest surface.

lonely values are allowed to exist and are reported by name, never
padded with weak matches. nothing invents coverage.

## the invariants

1. **deterministic.** input hash over the catalogue terms and config,
   output hash over the table body, both recorded inside the artifact.
2. **explainable.** every neighbour carries `shared_works`,
   `support_this`, `support_other` and the formula, so its score is
   recomputable from the explanation alone.
3. **checkable.** `python3 -m src.cli affinity-check` re-verifies every
   published neighbour and the output hash without rebuilding anything.
   the test suite includes a tampering test: a score that cannot be
   recomputed must fail the check.

## knobs (config/affinity.v1.yaml)

- `min_pair_works`: how many works a pair must share to be published.
  1 is honest at this catalogue size; raise it as the catalogue grows and
  report what drops out rather than silently truncating.
- `min_score`: floor for a published pair.
- `top_k`: neighbours kept per term.
- `score_rounding_decimals`: rounding before hashing, so float noise
  cannot make two identical runs disagree.
- `exclude_values`: sentinels that are never evidence.
- `layers.*.weight`: how much each evidence layer counts (see above).
  setting the harvest weight to 0 disables the layer without deleting
  the code path.

changing any knob is a config version bump and changes the output hash,
by construction.

## what this is not

- not a taste model. it knows nothing about any person.
- not a recommender. it seeds the candidate graph that the persona's
  taste context then scores; the policy layer decides what surfaces.
- not learned. the numbers come from authored tags, and the moment the
  tags change, the table rebuilds and the hashes change.
- not coverage-pretending. sparse means sparse.

## commands

```
python3 -m src.cli affinity --works tests/fixtures/works
python3 -m src.cli affinity-check
```

the table is written to `build/affinity-table.json`. it is a build
artifact, regenerated from source, never edited by hand.

## the harvest layer (config/affinity.v1.yaml)

the prior now blends two evidence layers:

- **catalog** (weight 1.0): the authored tags, as described above.
- **harvest** (weight 0.5): co-occurrence of tmdb keywords, admitted
  only through `routing.yaml` alias routes that name an *existing* axis
  value. a motif proposal is not a value yet, and metadata or discarded
  keywords are not taste evidence at all, so none of them enter the
  graph.

score = sum(weight x layer_score) / sum(weight) over the layers that
actually have shared works for that pair. an absent layer is **absent**,
never a zero dragging the number down, and every published pair carries
its layers in `explain.layers`, each with its own `shared_works`,
supports, weight and score. the check script re-verifies both the layer
scores and the blend.

what it looks like today: 4 of 436 pairs carry harvest evidence, e.g.
`authority_stance/criminal-protagonist <-> lens/criminal-consultant`
(shared: psych, white collar, from tmdb's "criminal consultant"
keyword). that is small on purpose, and it is also a warning the layer
makes visible: tmdb's keyword is loose about psych, and the provenance
says so in plain sight rather than hiding inside an aggregate.

the harvest layer grows as `routing.yaml` grows. it is wired now so it
accumulates evidence from every future harvest instead of being a
rewrite later. no user signal enters it: this is catalogue-adjacent
metadata, still nobody's taste.
