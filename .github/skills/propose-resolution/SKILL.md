---
name: propose-resolution
description: When — and only when — the user asks the agent to resolve, recommend or decide a ledger entry, analyse the conflict and write a proposed ruling (A foundation holds, B update foundation, C not a conflict) with reasoning and exact edits, without applying it. Use for "resolve L-0007", "what would you rule", "propose a fix for this contradiction".
---

# Propose a resolution

The user has asked you to resolve one or more ledger entries. You **propose**; the user **confirms**. Nothing in
`distillations/` changes in this skill.

## Steps

1. Read the entry in `alignment/ledger.md`, both claims in full (the essay claim and the foundation claim(s)), and the
   surrounding claims in their files.
2. Gather context:
   - `python tools/distill.py ledger --impact L-NNNN` shows other essays relying on the foundation claim, restatements and
     load-bearing arguments.
   - Read the originating source passages (both documents) for nuance the distillation may have lost. If the conflict
     disappears once the source is read properly, the right proposal is probably C, or a correction to the distillation itself.
3. Weigh the options against the framework's own standards (Book XI.7): **internal coherence**, **external consistency** with
   established science, **epistemic honesty** (correct claim typing) and **utility**. Also consider how far the change reaches:
   a B ruling on a load-bearing foundation claim touches every essay that links to it.
4. Write in the entry:
   - `- **Proposed ruling:** A` (or B or C)
   - `**Proposal:**` the option, 3–6 sentences of reasoning, and the **exact** edits that would be made:
     - A: the `Canonical: no (L-NNNN)` marker on the essay claim;
     - B: the new wording for each amended or added `AD-…` claim (by ID);
     - C: the essay claim's new relation and why both claims stand.
   - Leave `Ruling: pending`, `Ruled by: —` and `Status: open` unchanged.
5. Run `python tools/distill.py index` and `python tools/distill.py validate`.
6. Present the proposal to the user and ask them to confirm, amend or reject it. Do not apply it in the same turn unless the
   user's request already said explicitly to apply it ("resolve and apply").

When the user confirms, continue with the `record-ruling` skill using `Ruled by: agent (confirmed by user)`.
