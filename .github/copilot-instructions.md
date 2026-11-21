# Copilot instructions — philosophy-v2

This repository distils the *Agnostic Deism* foundation book and its essays (source: `pjm4448/philosophy`, cloned to
`../philosophy`) into structured claim files. It aligns each essay with the foundation and records the user's rulings on
contradictions. Use the **Philosophy Distiller** agent (`.github/agents/distiller.agent.md`) and its skills in
`.github/skills/`.

Key conventions:

- **Source documents are read-only.** Never edit `../philosophy`. All outputs go in this repository.
- The **distilled foundation chapters** (`distillations/foundation/`) are canonical.
- **Only the user rules on conflicts.** The agent proposes a ruling only when asked, and applies one only after the user
  confirms it.
- Claim IDs (`AD-<chapter>-NNN`, `<PREFIX>-NNN`, ledger `L-NNNN`) are stable. Never renumber or reuse them. Get them with
  `python tools/distill.py next-id`.
- Claim types come from `vocab/claim-types.md`, relations from `vocab/relations.md` and concept tags from `vocab/concepts.yaml`.
- After editing anything under `distillations/` or `alignment/`, run `python tools/distill.py validate` and then
  `python tools/distill.py index`.
- Tool tests: `python -m pytest tools/tests -q`.
- `reconstituted/` holds the later, mostly manual, rewrite of the documents. Don't write there unless explicitly asked.
