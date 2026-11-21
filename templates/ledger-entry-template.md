<!--
Ledger entry template. Copy everything below the line into alignment/ledger.md (under "## Entries"), in ID order.
Get the next free ID with `python tools/distill.py next-id ledger`.
Field lines are parsed by tools/distill.py. Keep the "- **Field:** value" format and use "—" for empty values.
-->
---

### L-NNNN — Short title of the conflict

- **Kind:** essay-vs-foundation
- **Essay claim:** BCDP-003
- **Foundation claims:** AD-V-014, AD-XI-031
- **Relation:** contradicts
- **Status:** open
- **Ruling:** pending
- **Ruled by:** —
- **Proposed ruling:** —

**Nature of conflict:** One or two sentences that state exactly what cannot both be true, or how the claim types differ.

**Essay says:** "verbatim quote" (§ section)

**Foundation says:** "verbatim quote" (Chapter V §3)

**Options:**

- **A — Foundation holds:** what the foundation keeps saying; the essay claim is marked non-canonical.
- **B — Update foundation:** the exact proposed new foundation wording (or the new claim to add).
- **C — Not a conflict:** the reading under which both stand, and the relation it should be reclassified as.

**Analysis:** Neutral notes on what each option would cost or protect, such as load-bearing arguments affected, other essays
relying on the foundation claim (`python tools/distill.py ledger --impact L-NNNN`) and consistency with Book XI typing.
Do not recommend an option here.

**Proposal:** — *(filled only when the user asks the agent to resolve this entry: option, reasoning, and the exact edits.
Set "Proposed ruling" to the option letter. Nothing is applied until the user confirms.)*

**Rationale:** — *(the user's reasoning, or the confirmed proposal's reasoning)*

**Foundation before:** — *(ruling B only: verbatim previous Claim text for each amended claim, with its ID)*

**Foundation after:** — *(ruling B only: new Claim text for each amended or added claim, with its ID)*

<!--
Field values:
- Kind: essay-vs-foundation | foundation-internal (Essay claim is "—" for foundation-internal)
- Relation: tension | contradicts | terminology-drift | novel
- Status: open | applied
- Ruling: pending | A — foundation holds | B — update foundation | C — not a conflict
- Ruled by: — | user | agent (confirmed by user)
- Proposed ruling: — | A | B | C
-->
