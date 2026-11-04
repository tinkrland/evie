# import/goodreads — reading history

**medium:** books
**route:** file export (csv). the public api was retired in 2020 and is
not coming back.
**status:** the legacy format every other book tracker copies

## what it gives

title, author, isbn, shelf, rating, dates read, and review text. the
isbn field is the one piece of hard identity in the whole file, so use
it wherever it exists.

## what it becomes

rows where isbn present goes straight to a work id; the rest resolve by
title and author against open library, with the usual honest failures.

## the trap

goodreads shelves are behavioural, not editorial: "currently-reading",
"to-read", and abandoned books all live beside read ones. the candidate
set distinguishes them and never treats a to-read shelf as interest in a
work's traits.

## refusal rules

no shelf reading as taste. no rating interpretation. no scraping the
site, which is now the only way left to get anything, and therefore not
a way we take.
