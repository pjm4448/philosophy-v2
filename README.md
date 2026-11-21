# philosophy-v2

Distillation and alignment workspace for **Agnostic Deism**. The foundation book and each essay from
[pjm4448/philosophy](https://github.com/pjm4448/philosophy) are distilled into typed, atomic claims with stable IDs. Every
essay is then compared with the distilled foundation. Where they conflict, **you decide what is true**, and the result is
written into the distilled foundation. Finally, the documents are reconstituted from the canonical distillations.

The source repository is read-only input. Nothing here ever edits it.

## Workflow

```
1. Distil foundation   book chapter  ──►  distillations/foundation/NN-*.md   (Preamble, I–XIII; canonical)
2. Distil essays       essay         ──►  distillations/essays/<slug>.md
3. Align               essay claims  ──►  relations to AD-… claims + pending entries in alignment/ledger.md
4. Rule                you decide each entry: A foundation holds | B update foundation | C not a conflict
5. Apply               ruling        ──►  essay claim marked non-canonical, or foundation claim amended
6. Reconstitute        (later, mostly manual) ──►  reconstituted/book, reconstituted/article
```

Ask the agent to resolve an entry and it writes a **proposal** with its reasoning. Nothing is applied until you confirm.

## Layout

| Path | Purpose |
|------|---------|
| [distill.config.yaml](distill.config.yaml) | Source location, chapter registry (heading → file), essay registry (slug → ID prefix) |
| [templates/distillation-template.md](templates/distillation-template.md) | The shared template for foundation chapters and essays |
| [templates/ledger-entry-template.md](templates/ledger-entry-template.md) | Format of one ledger entry |
| [vocab/](vocab/) | Claim types (from Book XI), alignment relations and ruling options, concept tags (from the Book XII glossary) |
| [distillations/](distillations/) | Distilled foundation chapters and essays. [INDEX.md](distillations/INDEX.md) is generated |
| [alignment/ledger.md](alignment/ledger.md) | Every conflict and its ruling, including superseded foundation wording |
| [reconstituted/](reconstituted/) | Rewritten documents, produced after the rulings |
| [tools/distill.py](tools/distill.py) | Helper CLI (below) |
| [.github/agents/distiller.agent.md](.github/agents/distiller.agent.md) | The **Philosophy Distiller** custom agent |
| [.github/skills/](.github/skills/) | Skills: `distill-document`, `align-with-foundation`, `propose-resolution`, `record-ruling`, `check-distillations` |

### Claim IDs

- Foundation: `AD-<chapter>-NNN`, e.g. `AD-VI-007` or `AD-P-003`. The chapter tells you which file holds the claim.
- Essays: `<PREFIX>-NNN`, e.g. `BCDP-003`. Prefixes are set in `distill.config.yaml`.
- Ledger: `L-NNNN`.

IDs are never renumbered or reused.

## Setup

Clone the source repository next to this one (the default `source_root` is `../philosophy`) and install the tool's
dependencies:

```powershell
git clone https://github.com/pjm4448/philosophy ../philosophy   # skip if it already exists
python -m pip install -r tools/requirements.txt
```

To use a checkout somewhere else, set `PHILOSOPHY_SOURCE_ROOT` or pass `--source-root`. For the Copilot cloud agent,
[.github/workflows/copilot-setup-steps.yml](.github/workflows/copilot-setup-steps.yml) does this automatically.

## Using the agent

Choose **Philosophy Distiller** in Copilot Chat (VS Code), Copilot CLI or the GitHub.com agents panel. Example requests:

- "Distil chapter VI." / "Distil the Beanstalk Bible essay."
- "Align borrowed-current-dissolved-pattern with the foundation."
- "What's the status?"
- "Resolve L-0007." (proposal only) → "Confirmed." (applied)
- "Rule L-0012 B: the essay's wording is better." (applied directly)

## Tool reference

```
python tools/distill.py outline [--chapter X | --essay SLUG]   # headings with line numbers
python tools/distill.py chapter X                              # print one book chapter with line numbers
python tools/distill.py scaffold --foundation [--chapter X]    # create chapter distillation(s); never overwrites
python tools/distill.py scaffold --essay SLUG|all              # create essay distillation(s)
python tools/distill.py next-id AD-VI | <slug> | ledger        # next free ID
python tools/distill.py validate [--strict]                    # structure, vocab, IDs, links, ruling markers
python tools/distill.py index                                  # regenerate INDEX.md, foundation/README.md, ledger summary
python tools/distill.py ledger [--pending] [--impact L-NNNN]   # list entries / what a ruling affects
python -m pytest tools/tests -q                                # tool tests
```

## Known source observations

- The book is the *Twelfth Update*. Some essays cite the *Eleventh* (and one the *Tenth*) Update. This drift is recorded in
  each essay's distillation.
- The source README lists `cosmic-insignificance-is-not-the-end-of-meaning.md`, which does not exist. It is not registered
  in `distill.config.yaml`.
