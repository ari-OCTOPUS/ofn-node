"""Contact-enrichment agent for painting_b2b_accounts.

Finds legitimate, publicly-published business contact numbers for leads that
have none (or only a switchboard), records where every single one came from,
and remembers which research paths actually work so later runs spend their
effort better.

Design stance, learned the hard way on this data (see LESSONS in
`lessons.py` and the notes in `strategy.py`): the binding constraint on this
task is NOT search cleverness. Two manual research rounds over ~40 Sydney
strata/property companies yielded 5 mobiles, because mid-size firms in this
segment deliberately route everything through a 1300/switchboard line and
publish no personal numbers at all. So this package is built to be equally
good at producing *reliable negative knowledge* — "this lead has no public
mobile, here is the evidence space that was searched, do not pay to search
it again" — as it is at producing numbers. A run that truthfully closes out
30 hopeless leads is worth more than one that invents 3 questionable ones.

Everything here is collection-only: HTTP GETs and writes to the painting
store. No outreach, no email, no form submission.
"""
