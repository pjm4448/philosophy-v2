---
name: record-ruling
description: Apply a ruling the user has made (or confirmed) on an alignment ledger entry — A foundation holds (mark essay claim non-canonical), B update foundation (amend or add the canonical foundation claim, keeping the old wording only in the ledger), or C not a conflict (reclassify the relation). Use when the user says "rule L-0007 A", "the essay is right, update the foundation", "confirm your proposal", etc.
---

# Record and apply a ruling

Use this skill only when the user has stated a ruling or explicitly confirmed a proposal. If their intent is ambiguous
(e.g. "hmm, maybe the essay is right"), ask before applying anything.

## Steps

1. In `alignment/ledger.md`, update the entry:
   - `- **Ruling:** A — foundation holds` / `B — update foundation` / `C — not a conflict`
   - `- **Ruled by:** user`, or `agent (confirmed by user)` if the user confirmed your proposal
   - `**Rationale:**` the user's reasoning, in their words where possible (or the confirmed proposal's reasoning)
2. Apply the ruling to the distillations:
   - **A — foundation holds:** add `- **Canonical:** no (L-NNNN)` to the essay claim, as the last field. Don't touch the claim text.
     Don't touch the essay source.
   - **B — update foundation:**
     - Copy each affected foundation claim's current `Claim` text, verbatim and with its ID, into
       `**Foundation before:**`, e.g. `AD-V-014: <old text>`.
     - Edit the claim in its chapter file: new `Claim` text (keep the ID). Update `Type`, `Concepts`, `Quote` and `Source` if
       they change. A quote from the book that no longer matches the amended claim must be removed. Add
       `- **Amended:** L-NNNN` (comma-append if the claim is already amended).
     - If the ruling adds a new claim instead, get the ID with `next-id AD-<chapter>`, set `Source: ledger L-NNNN`, and add
       `Amended: L-NNNN`.
     - Write `**Foundation after:**` with the new text of every amended or added claim, with IDs.
     - Set `amended: true` in that chapter file's front matter.
     - Change the essay claim's relation to the amended claim to `agrees` (or whatever honestly applies now), and keep its
       `Ledger` reference.
   - **C — not a conflict:** change the essay claim's relation(s) to the listed foundation claims to `agrees`/`extends`/`refines`.
     Keep the `Ledger` reference for history.
3. Set `- **Status:** applied`.
4. Run `python tools/distill.py ledger --impact L-NNNN`. For ruling B, every other essay claim listed must be re-checked
   against the amended text. Re-run the relevant part of `align-with-foundation` for each, which may open new pending entries.
5. Run `python tools/distill.py validate` (0 errors) and `python tools/distill.py index`.
6. Report: the ruling applied, the files changed, the impacted claims re-checked, and any new pending entries.

## Never

- Never edit the source book or essays. `reconstituted/` is where the user rewrites documents later.
- Never delete the superseded foundation wording from the ledger.
- Never apply a ruling the user has not made or confirmed.
