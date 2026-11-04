# import/storygraph — reading history and moods

**medium:** books
**route:** file export (csv, goodreads-compatible format)
**api:** none. roadmap requests have been open since 2021 with no date.

## what it gives

books read, dates, star ratings, shelves, and review text where the
user wrote any.

## what it becomes

rows keyed by title and author, resolved to isbn or an open library work
id, never to a guessed edition. ratings stay metadata.

## the trap

storygraph's own value is its *mood* tagging, and that data is authored
by users about books. it is tempting and it is off limits for taste
inference: importing someone else's mood tags as if they were the
owner's opinions would launder a third party's judgment into a taste
context.

## refusal rules

no moods, no community tags, no ratings-as-preference. titles, authors,
dates, and the owner's own shelves.
