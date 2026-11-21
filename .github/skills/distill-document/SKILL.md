---
name: distill-document
description: Distil one foundation book chapter (Preamble, I–XIII) or one essay from the Agnostic Deism corpus into the shared distillation template — typed atomic claims with stable IDs, denials, key terms, metaphors, load-bearing arguments and objections. Use when asked to distil, summarise into claims, or extract the claims of a chapter or essay.
---

# Distil a document

The output is one file that follows `templates/distillation-template.md`:
`distillations/foundation/<NN-name>.md` for a book chapter, or `distillations/essays/<slug>.md` for an essay.

## Before starting

- Identify the target: a chapter ID (`P`, `I` … `XIII`) or an essay slug or prefix from `distill.config.yaml`.
- Read `vocab/claim-types.md` and skim `vocab/concepts.yaml`. You will use both throughout.
- When distilling an essay, read `distillations/INDEX.md` first. Reuse the foundation's concept tags so alignment is easy later.
- Distil only. Do **not** fill in `Foundation`/`Ledger` fields; alignment is a separate step (`align-with-foundation`).

## Steps

1. **Scaffold** (skipped if the file exists; never overwrites):
   - `python tools/distill.py scaffold --foundation --chapter VI`
   - `python tools/distill.py scaffold --essay the-beanstalk-bible`
2. **Map the source:** run `python tools/distill.py outline --chapter VI` (or `--essay <slug>`). For a long chapter (VIII, X),
   plan one pass per subsection.
3. **Read** with `python tools/distill.py chapter VI` or by viewing line ranges of the source file. Read the whole unit before
   writing its claims.
4. **Extract claims** into *2. Claims*, under the matching domain headings. For each assertion:
   - Get the ID: `python tools/distill.py next-id AD-VI` (or the essay slug). IDs increase in reading order.
   - Write the claim block exactly as shown in the template: `Claim`, `Type`, `Concepts`, `Source` and, where useful, `Quote`.
   - Split compound sentences. If one sentence holds a fact and an interpretation of it, that's two claims with two types.
   - Typing: use the type the document itself gives or implies. The book often labels claims explicitly ("Postulated",
     "Chosen foundation", "Interpretation"). Those labels are binding.
   - Skip pure rhetoric, transitions and repetitions. If a paragraph only restates an earlier claim of the same document,
     don't add a new claim.
5. **Explicit denials** go in *3.*, also as claim blocks (usually `Type: Not established`). Examples: "personal survival is
   not established" and "the Pool is not a consciousness field".
6. **Key terms (4.):** for every coined or technical term, give the definition as used here and whether it matches the Book XII
   glossary (`yes` / `variant: …` / `new`).
7. **Metaphors (5.):** record imagery (Data Cube, Infinite Pool, firmware/software, receiver/antenna, beanstalk …) with what
   it stands for and its literalisation risk. A metaphor is never a claim.
8. **Load-bearing arguments (6.):** chains of claim IDs, e.g. `- AD-VI-003 + AD-VI-004 → AD-VI-009 — case against abortion`.
9. **Objections (7.):** objection, then the response's claim IDs, then the cross-reference to the matching Chapter X claim (if X
   is distilled) or `none`.
10. **Thesis (1.)** last: at most 3 plain sentences.
11. **Drift and open questions (9.):** terms that differ from the glossary, and any claim you were unsure how to type, with
    the reason. Keep the scaffold's list of version references ("Eleventh Update" etc.): essays must not cite a foundation
    edition, so these are removed at reconstitution. They are not claims and not alignment findings.
12. Set `status: reviewed` only when the user has reviewed the file. Leave `draft` otherwise.
13. Run `python tools/distill.py validate`, fix every error, then run `python tools/distill.py index`.

## Chapter-specific notes

- **Preamble:** names and frames the core commitments. Distil them as claims and use `Restates` in later chapters where those
  chapters repeat them.
- **Chapter X (Criticisms):** mostly *Objections addressed*. Also distil each rebuttal's substantive claim in *2.*, because
  essays are aligned against these.
- **Chapter XI (Epistemic map):** most rows restate claims from other chapters. Distil each row as a claim with
  `Restates: AD-<chapter>-NNN` when the originating chapter is already distilled. If XI types a claim differently from its
  origin, validate warns. Record it as a `foundation-internal` ledger entry rather than "fixing" either side.
- **Chapter XII (Glossary):** mostly *Key terms*. Only definitions that make a substantive assertion become claims.
- **Chapter XIII (Manifesto):** short-form commitments. Use `Restates` heavily.

## Quality checklist

- [ ] Every claim is one assertion, paraphrased faithfully, with a type from `vocab/claim-types.md`.
- [ ] No metaphor is recorded as a literal claim.
- [ ] Concept tags come from `vocab/concepts.yaml`. Add a new tag only if none fits, and say so in your report.
- [ ] Quotes are verbatim, one line, ≤40 words.
- [ ] `validate` reports 0 errors.
