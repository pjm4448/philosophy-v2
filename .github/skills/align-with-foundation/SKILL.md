---
name: align-with-foundation
description: Compare a distilled essay claim-by-claim with the distilled foundation chapters, set the relation for each claim (agrees, extends, refines, tension, contradicts, terminology-drift, novel), and open pending ledger entries for every conflict. Use when asked to align, compare, check consistency or find contradictions between an essay and the foundation.
---

# Align an essay with the foundation

The distilled foundation is canonical. Your job is to **find and describe** each difference between it and the essay. Ruling
on a difference is the user's job.

## Before starting

- The essay distillation must exist (`distill-document`).
- Run `python tools/distill.py validate`. Fix any errors before aligning.
- Find the foundation chapters the essay touches, using `distillations/INDEX.md` (claims grouped by concept) and the essay's
  concept tags. Each of those chapters must be distilled. If one isn't, stop and tell the user which chapter is missing.
- Read `vocab/relations.md`.

## Steps

1. For each essay claim (sections 2 and 3), find candidate foundation claims:
   - first by shared concept tags in `distillations/INDEX.md`;
   - then by searching the foundation files for key terms (`search` tool);
   - always check Chapter XI for the claim's canonical **type**, and Chapter X if the essay rebuts an objection.
2. Compare **content** and **type**, then choose the relation(s):
   - same content and same type → `agrees`
   - compatible additions → `extends`; compatible narrowing or qualification → `refines`
   - strained compatibility or a different emphasis → `tension`
   - can't both be true, or a different claim type → `contradicts` (a type mismatch is at least `tension`)
   - a key term used differently → `terminology-drift`
   - no counterpart → `none (novel)`
   Pick the most severe relation that honestly applies. Never soften one to avoid a ledger entry.
3. Write the **Foundation** field on the essay claim, e.g. `- **Foundation:** AD-V-014 (extends); AD-XI-031 (tension)`.
4. For every `tension` / `contradicts` / `terminology-drift` relation, and for `novel` claims that might belong in the
   foundation, open a ledger entry:
   - Get the ID with `python tools/distill.py next-id ledger`.
   - Copy `templates/ledger-entry-template.md` into `alignment/ledger.md` under `## Entries`.
   - Fill it in: `Kind: essay-vs-foundation`, `Essay claim`, `Foundation claims`, `Relation`, `Status: open`,
     `Ruling: pending`, `Ruled by: —`, `Proposed ruling: —`; *Nature of conflict*; verbatim quotes from **both** sources;
     options A/B/C stated concretely (option B with the exact proposed foundation wording); and a neutral *Analysis*
     (run `python tools/distill.py ledger --impact L-NNNN` to see what else depends on the foundation claim).
     Do **not** fill *Proposal* or *Rationale*.
   - Add `- **Ledger:** L-NNNN` to the essay claim (comma-separate multiple entries).
   - One entry per distinct conflict. If several essay claims share the same conflict, open one entry per essay claim and
     cross-reference them in *Analysis*.
5. Fill section *8. Alignment summary*: the chapters touched, a count per relation, and the ledger IDs.
6. Record terminology drift in section 9. Version references (e.g. "Eleventh Update") are not alignment findings; don't
   open ledger entries for them.
7. Set the essay's front matter `status: aligned` once every claim has a `Foundation` field.
8. Run `python tools/distill.py validate` (0 errors) and then `python tools/distill.py index`.

## Report

List the relation counts and every new ledger entry (`L-NNNN — essay claim ↔ foundation claim: one-line nature`). End with:
"These N entries are pending your ruling."
