# Reviewer Evidence Map - Crypto Signal AI

Updated: 2026-05-29

This document is the short path for a recruiter, hiring manager, technical reviewer, or buyer who wants to understand what this repository proves without wandering through every file.

## One-Line Proof

**B2C/B2B research automation.** Auditable signal research with indicators, sentiment hooks, and backtesting, without return promises.

## Audience and Commercial Angle

| Lens | Answer |
|---|---|
| Primary reviewer | Quant learners, research communities, analytics teams, and automation builders. |
| Hiring signal | Can the project be explained, verified, bounded, and extended like a real product surface? |
| Buyer signal | Is there a narrow operational pain, a runnable proof path, and a risk-aware pilot shape? |
| Stack signal | Python |

## Seven-Minute Review Route

1. Read the README `Product and Review Surface` and `Reviewer Fast Path` sections.
2. Open `docs/monetization-playbook.md` to understand the buyer, offer ladder, and GTM hypothesis.
3. Run or inspect the strongest local quality gate below.
4. Inspect CI workflow definitions and test fixtures before deeper implementation review.
5. Check the risk boundaries so claims stay credible and not overextended.

## Verification Commands

| Purpose | Command |
|---|---|
| Test suite | `python -m pytest` |

## CI and Automation Surface

- .github/workflows/architecture-blueprint.yml
- .github/workflows/ci.yml
- .github/workflows/dependency-review.yml
- .github/workflows/repository-health.yml
- .github/workflows/repository-surface.yml
- .github/workflows/secret-scan.yml

## Evidence Inventory

- pytest/ruff-style local verification path
- Tests pass
- Backtest assumptions visible
- Financial-advice boundary is explicit

## Commercialization Snapshot

| Offer | Pricing hypothesis |
|---|---|
| Paid research dashboard | $9-$29/month research access |
| Private strategy-lab template | $1k-$5k setup |
| Automation/report workflow setup | $500-$3k/month private reporting |

## Risk Boundaries

- No investment advice
- No guaranteed returns
- Live trading requires risk controls

## Metrics That Matter

- Report retention
- Backtest reproducibility
- Automation adoption

## Review Verdict

This repository should be evaluated as part of the broader KIM3310 portfolio: it is strongest when the reviewer sees the link between a concrete implementation, a documented verification path, and a monetizable or employable operating story.
