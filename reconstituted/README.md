# Reconstituted documents

This folder holds the **final stage** of the workflow: the foundation book and each essay rewritten from their
canonical distillations, after the alignment rulings have been applied.

```
reconstituted/
  book/agnostic-deism.md        # rebuilt from distillations/foundation/*.md (chapters P, I–XIII)
  article/<same paths as source> # rebuilt from distillations/essays/<slug>.md
```

The layout mirrors the source repository (`pjm4448/philosophy`). A reconstituted file has the same relative path as
its original. For example, `article/the-architecture-of-reality/the-architecture-of-reality.md`.

## Inputs

- **Foundation:** each chapter distillation. Where a claim carries `Amended: L-xxxx`, its text is canonical and replaces
  the original book wording. The ledger entry's *Foundation after* field gives the agreed text.
- **Essays:** each essay distillation. A claim marked `Canonical: no (L-xxxx)` must be revised in the reconstituted
  essay to agree with the foundation claim named in that ledger entry. Reclassified claims (ruling C) need no change.
- **Source text:** the original documents in `pjm4448/philosophy`, which supply voice, structure and prose.

## Rules

- Reconstitution is expected to be largely **manual**. The Distiller agent does not write here unless explicitly asked.
- Before reconstituting, run `python tools/distill.py validate` and `python tools/distill.py ledger --pending`. Every entry
  should be ruled and applied.
- Update the edition/version line (for example *Thirteenth Update*) and the book's revision history to list the ledger
  entries applied.
