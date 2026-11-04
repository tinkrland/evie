# import/netflix — streaming viewing activity

**medium:** tv, film
**route:** file export (download viewing activity, csv) or the account
page; there is no api
**status:** fragile by nature: region-dependent, profile-dependent,
often title-truncated

## what it gives

title, date, and little else. no year, no ids, no episode structure.
netflix writes titles its own way and truncates long ones.

## what it becomes

rows that must survive being vague: `title` as written, `year` absent,
`medium` unknown until resolution. resolution against the reference
catalogues decides, and unmatched rows stay unmatched and are reported.

## the trap

netflix activity includes whatever played, including things left
running by accident and things another person in the household watched
on the same profile. a netflix profile is frequently not one person.

## refusal rules

no title guessing when the export truncates. no assuming a series
commitment from one episode row. no merging profiles.
