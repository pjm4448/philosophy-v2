---
name: check-distillations
description: Report the health and progress of the distillation project — validation errors, which foundation chapters and essays are distilled or aligned, and which ledger entries await a ruling or application. Use for "status", "where are we", "what's left", "validate", or before and after a work session.
---

# Check distillations

## Steps

1. Run `python tools/distill.py validate`. If `import yaml` fails, first run `python -m pip install -r tools/requirements.txt`.
   If it says the source documents are missing, run `git clone https://github.com/pjm4448/philosophy ../philosophy`.
2. Run `python tools/distill.py index` to refresh `distillations/INDEX.md`, `distillations/foundation/README.md` and the
   ledger summary.
3. Run `python tools/distill.py ledger --pending`.
4. Read `distillations/foundation/README.md` and the *Essays* table in `distillations/INDEX.md`.

## Report

- **Validation:** error and warning counts. Quote every error, and group the warnings (e.g. "12 drafts with no claims yet").
- **Foundation:** chapters not started / draft / reviewed, with claim counts and the number of amended claims.
- **Essays:** not started / draft / reviewed / aligned.
- **Ledger:** entries awaiting a ruling (list the IDs and titles, and flag any with a proposal), and entries ruled but not
  yet applied.
- **Suggested next step:** follow the workflow order (foundation chapters → essays → alignment → rulings). Suggest the next
  unit of work, but don't start it unless asked.

Fix validation errors only if the user asks, or if they come from your own edits in this session.
