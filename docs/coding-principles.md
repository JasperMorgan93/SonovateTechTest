# Coding principles

Standing brief for humans and agents writing code in this repo.

## Less code is the best code
- Delete as much as you add
- No code for imagined futures — write an ADR instead
- Three similar lines beat a premature abstraction
- No dead code, no commented-out code

## Readability & maintainability
- Optimise for the reader, not the writer
- Explicit over implicit — no hidden state, no magic
- Names over comments
- Comments explain *why*, never *what*
- One function, one purpose
- Match existing patterns over local creativity

## SOLID — practically, not ceremonially
- One responsibility per module
- New behaviour = new class on an existing contract, not edited core logic
- Depend on abstractions, not concrete detail
- Skip interfaces/factories where a plain function will do

## Correctness
- Fail loudly on our own bugs
- Tolerate the outside world's surprises
- No handling for scenarios that can't happen
- Tests read as documentation, not just assertions

## Dependencies
- Every dependency is a liability — justify it
- Don't hand-roll what a proven library already solves

## For agents
- Read the ADRs before introducing a new pattern
- Extend existing abstractions before creating new ones
- Structural decision? Write an ADR, don't bury it in a comment
- Show test output before claiming success

## Before a PR
- [ ] Could this be smaller?
- [ ] Would a stranger understand it unaided?
- [ ] Does it match existing patterns?
- [ ] Is every abstraction earning its place today?
