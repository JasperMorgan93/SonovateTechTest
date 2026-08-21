# Engineering principles

Standing brief for how we work, distinct from [coding-principles.md](coding-principles.md)'s brief for how we write code.

## Complexity kills codebases
- Software entropy always increases unless someone actively pushes back on it

## Make the change easy, then make the easy change
- Improve the code first, then make the change you actually came for

## You build it, you run it
- Ownership doesn't end at merge

## Reliability is a feature
- Uptime and correctness are prioritised alongside new functionality, not sacrificed for it

## Leave it better than you found it
- Every change should nudge the code it touches toward a better state, not just add to it

## Default to transparency
- Share context, decisions and progress openly rather than on request

## Make it work, make it right, make it fast
- In that order — don't optimise before it's correct, don't polish before it works

## Security and privacy is everyone's job
- Not just a review gate owned by someone else

## Delete more than you add
- The cheapest, fastest and safest code is the code that doesn't exist. Prefer to remove/improve functions and code that no longer hold real value. Less surface area means less bugs, and better coding principles.
