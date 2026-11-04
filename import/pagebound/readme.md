# import/pagebound — reading history

**medium:** books
**route:** unknown, to verify
**status:** `blocked` on facts, same as repov

## what it is

a reading tracker the owner named alongside fable and storygraph. its
interface has not been verified, so nothing here is assumed.

## what must be established first

1. export or api for a person's own library, or neither.
2. the row shape: isbn, title, author, dates, shelves.
3. whether ratings or reviews are part of the export.

## what it becomes

books rows: isbn first (the only hard identity), then title + author
resolution against open library. unmatched stays unmatched, reported.

## the rule

no scraping. a tracker that will not hand over your own data is a
tracker you use, not a tracker evie reads.
