# import/fable — reading history

**medium:** books
**route:** file export, to verify (fable imports from goodreads; whether
it exports is the question that decides this folder)
**status:** designed pending route confirmation

## what it is

a social reading app built around book clubs and reading progress. it is
where a lot of people who left goodreads actually read now, which is why
it earned a folder.

## what it must become

rows keyed by title and author, resolved to isbn or an open library work
id. shelves and progress stay metadata. ratings stay metadata.

## the trap

fable is social first: club shelves, buddy reads, and shared lists mix
other people's activity into what looks like the user's own. only rows
the person themselves marked as read count as candidates.

## what to verify first

whether account settings offer a data export. if fable only accepts
imports and never gives them, this folder is blocked with the reason
written down, not quietly dropped.
