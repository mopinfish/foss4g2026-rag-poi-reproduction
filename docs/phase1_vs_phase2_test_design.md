# Phase 1 vs. Phase 2: how question difficulty was actually designed

Both phases label their test cases L1 (basic retrieval) through L5 (advanced
reasoning), but the two question sets were **not** built with the same level
of care at the harder levels. This note quantifies the difference so that
anyone reproducing both phases understands what "L4" and "L5" mean in each.

## Quantitative comparison (single-area cases only)

| Level | Phase 1 avg. prompt length | Phase 1 avg. keyword count | Phase 2 avg. prompt length | Phase 2 avg. keyword count |
|---|---|---|---|---|
| L1 | 14.3 chars | 3.2 | 16.9 chars | 2.4 |
| L2 | 32.0 chars | 4.1 | 22.0 chars | 3.1 |
| L3 | 33.4 chars | 3.7 | 23.2 chars | 2.8 |
| L4 | **57.8 chars** | 5.2 | **25.3 chars** | 3.6 |
| L5 | **62.4 chars** | 5.6 | **27.0 chars** | 4.2 |

(Phase 1: `eval/test_cases_v2.py`, 55 Shibuya-only cases. Phase 2:
`eval/test_cases_multi_area.py`, single-area subset of the 130 cases across 4
areas — cross-area and landmark-origin cases excluded for a like-for-like
comparison.)

Phase 1's prompts grow steadily longer and more elaborate from L1 to L5
(14 → 62 characters). Phase 2's prompts stay roughly flat (17 → 27
characters) — the level labels were reused, but the escalation in question
complexity that defines them in Phase 1 was not carried over.

## Qualitative comparison

**Phase 1 L4/L5** spell out multiple explicit constraints or a hypothesis to
test, in the question text itself:

- L4-01: "If opening a nursery school near Shibuya Station, where is the best
  location? **Consider proximity to parks and the presence of a police box.**"
- L5-01: "Does the conclusion 'there are many cafes near Shibuya Station'
  **still hold if you change the search radius from 500m to 300m**? Compare
  cafe counts in both ranges and judge."
- L5-08: "Looking for a cafe with a 'good atmosphere' near Shibuya Station.
  Recommend what you can from the data, **and explain the limits of that
  judgment**."

**Phase 2 L4/L5** reuse the same category names (`decision_support`,
`sensitivity`, `multi_hop`, `competitor`, `complementary`, ...) but are single
short clauses:

- L4-01: "List 3 cafes near Shibuya Station, nearest first."
- L4-04: "How does the cafe count change between a 500m and a 1km radius
  around Shibuya Station?"
- L5-01: "What's the nearest cafe to Shibuya Station, and how many other
  cafes are within 300m of it?"

## What this means for reproduction

- Both question sets were verified byte-identical to the original research
  repository's source files (`test_cases_v2.py`, `test_cases_graphrag.py`,
  `test_cases_multi_area.py`) — this is not a transcription error introduced
  while assembling this reproduction package.
- It reflects how the multi-area experiment (Phase 2) was actually designed:
  the L1-L5 category scaffolding from Phase 1 was reused, but the elaborate
  multi-constraint / hypothesis-testing / uncertainty-hedging prompt design
  that made Phase 1's L4/L5 harder was not re-applied when the question set
  was expanded to 4 areas.
- If you are comparing L4/L5 results across the two phases, keep in mind
  they are not testing an equivalent level of reasoning difficulty, despite
  sharing level numbers and category names.
