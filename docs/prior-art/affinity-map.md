# prior art: jewelfinity's affinity-map (reviewed 2026-11-03)

jewelfinity's `platform/discoverability/affinity-map/` is a deterministic
taste-intelligence engine for jewelry and objects. it is the same
architecture family as evie (governed vocabulary in, versioned config,
pure compute, explanation objects out, no learned components) applied
to a different vertical. that makes it unusually good prior art: the
structure is comparable, so the differences are informative.

## what transfers

### 1. the structural affinity prior

the affinity table answers "people who like x also like y" *before any
signal volume exists*, computed from the governed vocabulary alone, and
later blended deterministically with measured co-occurrence.

evie has no vocabulary-level prior today. it scores a work against a
taste context at query time, but nothing says which axis values tend to
travel together ("consulting-detective tends to arrive with
hyper-observation"; "island rarely arrives with metropolis"). a
structural table is the cold-start answer, and our own harvest is
already the co-occurrence half of it.

### 2. the union lesson

they score over the union of all three vocabularies, not one file at a
time, because a term whose real neighbors live in another vocabulary
looks lonely inside its own. celestial mode found metal_silver, cancer
and leo through the symbol layer, and would have been stranded by a
style-only pass.

evie's version of the mistake is scoring within one axis family. the
honest surface is the union of axes, and a value that meets nothing
anywhere is allowed to have an empty neighborhood: they state it
plainly, "that is honest, not a bug: nothing pads them."

### 3. explanations that recompute the score

every neighbor in their table carries the shared facets, each side's
intensity, class weights and contributions and both norms, such that
the score can be recomputed from the explanation object alone, and a
check script re-verifies that recomputation on every published row.

evie's provenance map carries attribution shares. it does not yet
guarantee that the score is reconstructible from the explanation. that
is a stronger and better contract, and it is testable, which is the
only kind of contract worth writing.

### 4. determinism as a recorded artifact

their table records an input hash and an output hash; a config version
bump changes the hash; knobs live in versioned config, never in code
constants, and there is no clock anywhere in the path.

evie already keeps its knobs in `config/scoring.v0.yaml` and proves
byte-identical rebuilds. adopting input and output hashes inside the
compiled database would make determinism *checkable by a consumer*, not
just by our own test suite.

### 5. sparse is the honest baseline

their corpus study found only 1.2% of 3,050 titles carry two or more
vocabulary terms, and they call that a finding, not a failure:
"sparse co-occurrence is the honest baseline."

our first harvest says the same thing in our own numbers: 12 of 141
tmdb keywords (8.5%) recur across works. recurrence is rare. a
threshold policy that treats sparsity as incompleteness will invent
connections that do not exist.

### 6. the confusable cross-check

they run a standing check that surfaces terms which look like each other
so they cannot be silently merged. evie has written boundary rules for
exactly this class of error (gift_cover is not the world axis;
family_role is not ensemble_shape; island is not coastal-town) but no
executable check that the boundaries still hold across the vocabulary.
theirs is the pattern to copy.

## what does not transfer

- the jewelry vocabularies and the object character records. different
  vertical, different axes.
- the marketplace policy layer (price, geography, creator affinity).
  evie stays availability-blind and business-blind on purpose.
- their graph storage choice (falkordb). evie's compiled catalogue is
  sqlite and the query path is byte-deterministic; the graph is a
  rendering and query-surface question, not a modelling one.
- solimet-gated corpus acquisition. we have no equivalent gate and do
  not need one yet.

## adjacent find in the same repo

`prior-art-qloo.md` reviews qloo's cultural graph and lands on the same
line evie drew for itself: privacy as a system boundary rather than a
policy layer, inference from entities and relationships, no identity
graph, stateless per-request inference. worth citing whenever the
"you need user data to be good" argument comes up.

## resulting open questions

30. (2026-11-03) adopt a structural affinity table: compute
    axis-value affinity from the governed vocabulary alone, version it,
    and blend our measured keyword co-occurrence into it
    deterministically? this is the cold-start half evie lacks.

31. (2026-11-03) make the confusable cross-check executable: a test
    that asserts the declared boundary pairs (gift_cover/world,
    family_role/ensemble_shape, island/coastal-town) are still distinct
    in the vocab and routes.
