# import/pagebound — reading history

**medium:** books
**route:** mobile app (ios, android). export and api unverified.
**status:** designed pending route confirmation. the shape is known now;
how data leaves it is not.

## what it is (verified 2026-11-04, from the app's own billing)

a social book tracker. reading tracking and discovery, posting thoughts
and theories about the current read, badges, quests and points to keep a
habit going, and monthly wrap-ups of progress.

## what it must become

books rows: isbn first where the export has one, else title plus author
resolved against open library. unmatched stays unmatched and is
reported.

## the traps this app brings

1. **discussion is not taste.** thoughts and theories posted about a
   current read are the person thinking out loud mid-book, which is a
   different thing from liking the book. never read post volume as
   preference.
2. **gamification is not signal.** badges, quests, points and streak
   mechanics reward *logging*, and a streak is a fact about a habit, not
   about a book. the import takes read rows only.
3. **monthly wrap-ups are a display, not an export.** a recap screen is
   not a data export, and the folder stays unverified until settings
   actually offer one.

## to verify

does account settings offer a data export? if yes this becomes a
file-export import like goodreads. if the app only shows wrap-ups, the
folder stays blocked and says so. no scraping, ever.
