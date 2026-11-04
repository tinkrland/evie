# import/repov — cross-vertical personal log

**medium:** tv, books, games, places, music (cross-vertical)
**route:** mobile app (ios, android). export and api unverified.
**status:** designed pending route confirmation. the data model is known
and it is unusually useful.

## what it is (verified 2026-11-04, from the app's own billing)

a mini blog for recording favourite things in one place: shows, books,
games, places, and more, with a social layer for following friends.
its screens name the model directly: **records**, a **taste room**, and
an **archive** split by category (all, tv, books, game, travel, track),
plus collections, social, and my space.

## why this one matters more than another tracker

almost every other source is single-vertical: letterboxd knows films,
goodreads knows books. repov holds *one person's judgement across
verticals in one place*, which is exactly the shape a cross-vertical
bridge needs and the shape evie otherwise has to infer badly.

that also makes it the easiest source to over-read, so: a repov entry is
the person *recording that they love a thing*. it is a strong candidate,
not a confirmed like, and it still passes the owner gate like everything
else. no import may promote a record straight into a taste context.

## what evie imports from it

only the rows inside evie's vertical: tv and books (and film where
present). game, travel and track rows are noted in the report and left
for their own verticals, because importing them here would be axis
leakage between verticals.

## what to verify

1. whether the app offers an export or an api for the owner's own
   records.
2. the row shape per category: is a tv entry a show or an episode? a
   book entry an edition or a work?
3. whether "taste room" is a curated shelf or the whole archive
   re-rendered. the import takes records, never a rendered view.
