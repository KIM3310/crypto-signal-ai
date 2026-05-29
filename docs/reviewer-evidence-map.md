# Review Guide - Crypto Signal AI

Updated: 2026-05-30

Use this page as the short path through the repository. It keeps the review grounded in the code, docs, commands, and boundaries that are already present.

## Summary

| Field | Notes |
|---|---|
| Lane | B2C/B2B research automation |
| Core idea | Auditable signal research with indicators, sentiment hooks, and backtesting, without return promises. |
| Primary reader | Quant learners, research communities, analytics teams, and automation builders. |
| Stack | Python |

## Open First

1. Start with the README fast path and architecture section.
2. Open `docs/monetization-playbook.md` only when reviewing the product or service angle.
3. Check the commands below before making claims about quality.
4. Skim the CI workflows and fixture data before deeper implementation review.
5. Read the boundaries section before presenting the project externally.

## Checks

| Purpose | Command |
|---|---|
| Test suite | `python -m pytest` |

## CI

- .github/workflows/architecture-blueprint.yml
- .github/workflows/ci.yml
- .github/workflows/dependency-review.yml
- .github/workflows/repository-health.yml
- .github/workflows/repository-surface.yml
- .github/workflows/secret-scan.yml

## Evidence

- pytest/ruff-style local verification path
- Tests pass
- Backtest assumptions visible
- Financial-advice boundary is explicit

## Commercial Notes

| Possible offer | Working price assumption |
|---|---|
| Paid research dashboard | $9-$29/month research access |
| Private strategy-lab template | $1k-$5k setup |
| Automation/report workflow setup | $500-$3k/month private reporting |

## Boundaries

- No investment advice
- No guaranteed returns
- Live trading requires risk controls

## Useful Metrics

- Report retention
- Backtest reproducibility
- Automation adoption
