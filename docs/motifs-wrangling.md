# motifs wrangling (ao3-style, deterministic)

governance for the motifs axis: controlled free-ish tags, wrangled
like archive of our own canonical tags, but deterministic. concepts
adapted from the owner's memorium/substrate tag-wrangling research.

## where proposals come from

the queue lives at `data/motifs/queue.yaml`. proposals arrive from:

- **tmdb keywords** via `src/ingest/tmdb_keywords.py` (needs
  TMDB_API_KEY). verified seeds so far: whodunit (tmdb:12570),
  buddy cop (tmdb:167316), small town (tmdb:1415).
- **open library subjects** (book side, same pipeline later).
- **owner and tagger notes**: anything a reviewer wants to propose.

first live harvest (2026-11-03): 13 works resolved to tmdb ids (13/13,
exact title plus year), 141 proposals in the queue. repeated runs are
byte-identical. what the harvest shows: tmdb already carries lens-like
keywords ("criminal consultant" on three works) but the long tail is
noise ("adoring", "amused" from one work each). that settles the shape
of open question 28: a keyword enters the queue as a candidate only
when it recurs; uses counts are the filter.

## triage: keywords route to the axis they describe

a harvested keyword is not automatically a motif. before anything is
queued, `src/ingest/routing.py` triages each keyword against
`data/motifs/routing.yaml` into one of:

- **alias**: the keyword names an existing axis value ("small town" is
  setting_scale/small-town, "whodunit" is mystery_mechanism/whodunit,
  "buddy cop" is ensemble_shape/odd-couple, "criminal consultant" is
  lens/criminal-consultant). on review it joins that value's alias
  table; no new value is created.
- **new-value**: the keyword names a value an axis lacks. a proposal
  for that single axis only.
- **metadata**: a place name is setting_geo geography, not a taste
  value and not a motif.
- **discard**: provenance tags ("based on novel or book"), generic
  nouns, single-use adjectives.
- **motif**: genuine freeform texture, the only bucket where a new
  motif can emerge.

first full triage (2026-11-03): 141 proposals -> 8 aliases, 3 metadata,
10 discards, 120 still motifs. the ratio is the point: most harvested
keywords were never motifs at all.

rules: nothing auto-adopts. a proposal is a normalized lowercase
string with sources and a uses count. merging is deterministic: dedupe
by name, sources by ref, uses summed, output sorted. a proposal
crosses into canonical only by reviewed edit of
`data/vocab/motifs.yaml` with an alias table (see the model below).

## the model

ao3 wrangles by hand: volunteers map messy human tags onto canonical
tags with aliases. evie does the same, but the resolution is a rule,
not a judgment call:

1. canonical motifs live in the vocab (`data/vocab/motifs.yaml`),
   added by reviewed proposal only. a canonical value never appears
   without an owner review.
2. each canonical motif carries an explicit alias table (a list of
   phrasings that resolve to it). example:
   `will-they-wont-they-marathon` aliases: "eight seasons of will
   they wont they", "excruciating slow burn", "dragged out romance".
3. resolution at build time is exact match on a normalized alias
   (lowercase, trimmed, punctuation-folded). same input, same output,
   always. no fuzzy scoring in v0.
4. alias provenance is preserved: the authored phrasing is stored as
   written, and the resolution to the canonical motif is recorded.
   the alias is preserved as provenance; the canonical tag is the
   resolution, not a replacement.
5. an unresolved phrasing never becomes a tag. it enters the proposal
   queue for review. nothing auto-applies, ever.

## where the model is allowed to touch this

per the determinism contract, no model output ever enters the catalog
unreviewed. an assistant model (adaptionlabs credits are available if
useful) may pre-suggest canonical resolutions for queued proposals
with a confidence score, exactly the "ambiguous tail" split from the
substrate research: rules handle everything the alias table covers,
the model only drafts suggestions for what it does not, and a human
approves or rejects. the suggestion is never the resolution.

this keeps the contract intact: same catalog, same context, same
answers, because the alias table and canonical vocab are the only
inputs to resolution, and both change only by review.

## degree nuance lives here

axes carry shape, motifs carry degree and flavor. "slow-burn" is a
romantic_arc value; "eight seasons of shawn/jules-grade pining" is the
motif `will-they-wont-they-marathon`. rubrics (docs/rubrics/) define
axes; wrangling defines motifs; neither bleeds into the other.
