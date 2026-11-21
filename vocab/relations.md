# Alignment relations

When an essay is aligned, each essay claim gets one or more relations to foundation claims in its **Foundation** field:

```
- **Foundation:** AD-V-014 (extends); AD-XI-031 (tension)
```

If the claim has no foundation counterpart, write `none (novel)`.

`tools/distill.py validate` reads the backticked values in the first column of this table.

| Relation | Meaning | Ledger entry |
|----------|---------|--------------|
| `agrees` | Says the same thing as the foundation claim, possibly in different words. | No |
| `extends` | Adds detail, examples or consequences the foundation does not state but that are compatible with it. | No |
| `refines` | Narrows, qualifies or sharpens the foundation claim without contradicting it. | No |
| `tension` | Compatible only under a strained reading, or differs in emphasis, scope or epistemic type in a way a reader could take as inconsistent. | **Required** |
| `contradicts` | Cannot both be true as written, or the essay gives the claim a different claim type (e.g. `Empirical` versus `Postulated`). | **Required** |
| `terminology-drift` | Same idea, but a key term is used with a different meaning, or a different term is used for a defined concept. | **Required** |
| `novel` | No foundation counterpart. Use only with `none (novel)`. | Optional. Open one if the claim may belong in the foundation. |

## Rules

- A relation that needs a ledger entry requires a **Ledger** field on the essay claim that references an entry in
  `alignment/ledger.md`.
- Pick the most severe relation that honestly applies. Don't soften a contradiction to `tension` to avoid a ledger entry.
- A type mismatch is a finding in itself: if the essay types the claim differently from the foundation, record at least `tension`.
- Internal tensions *within* the foundation (for example Section XI typing a claim differently from its originating chapter)
  are recorded as ledger entries with `Kind: foundation-internal`.

## Ruling options (used in the ledger)

| Option | Name | Effect on the distillations |
|--------|------|-----------------------------|
| `A` | Foundation holds | The essay claim gets `- **Canonical:** no (L-xxxx)`. The essay source is untouched. |
| `B` | Update foundation | The foundation claim is reworded (same ID) or a new `AD-…` claim is added, with `- **Amended:** L-xxxx`. The previous wording is kept only in the ledger entry's *Foundation before* field. The chapter's front matter gets `amended: true`. |
| `C` | Not a conflict | The essay claim's relation is changed to `agrees`/`extends`/`refines` and the reason is recorded in the ledger. |
