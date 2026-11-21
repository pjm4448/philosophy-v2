---
# Front matter reference. `tools/distill.py scaffold` writes the real front matter. This block only documents the keys.
doc_id: "AD-VI | <essay-slug>"        # foundation: AD-<chapter id>; essay: the slug from distill.config.yaml
title: "<chapter heading or essay title>"
kind: "foundation-chapter | essay"
source_path: "book/agnostic-deism.md | article/<file>.md"   # relative to source_root
source_repo: "https://github.com/pjm4448/philosophy"
source_commit: "<commit distilled from; provenance only>"
framework_version_cited: "<e.g. Twelfth Update; none>"
distilled_on: "YYYY-MM-DD"
status: "draft | reviewed | aligned"      # aligned = essays only, every claim has a Foundation field
# foundation-chapter only:
chapter: "P | I … XIII"
chapter_heading: "<exact level-2 heading without '## '>"
amended: false                             # true once any claim in this chapter carries an Amended marker
---

# {{title}}

<!--
HOW TO FILL THIS IN (delete nothing structural; HTML comments are ignored by the validator)
- Paraphrase faithfully. Never add ideas the source does not contain; never "fix" the source.
- One claim = one assertion of one claim type (see vocab/claim-types.md). Split compound sentences.
- Claim IDs: {{id_pattern}}. Get the next free ID with `python tools/distill.py next-id {{doc_id}}`.
  IDs are never reused or renumbered, even if a claim is deleted.
- Concepts: tags from vocab/concepts.yaml, comma-separated.
- Source: the section heading (and line range if useful) in the source document.
- Quote: optional, one line, ≤40 words, verbatim, in double quotes.
- Run `python tools/distill.py validate` after every edit session.
-->

## 1. Thesis

<!-- ≤3 plain sentences: what this document asserts and why it matters to the framework. -->

## 2. Claims

<!--
Group claims under the domain headings below; delete unused domain headings.
Claim block format (field order fixed; omit optional fields that do not apply):

#### {{example_id}} — Short descriptive title
- **Claim:** One sentence, paraphrased.
- **Type:** Interpretation
- **Concepts:** infinite-pool, borrowed-current
- **Source:** § Heading in source (L120–L134)
- **Quote:** "Optional verbatim supporting quote."
- **Restates:** AD-V-014                      (foundation only: this claim repeats a claim made in another chapter)
- **Foundation:** AD-V-014 (extends); AD-XI-031 (tension)   (essays only, added during alignment; or `none (novel)`)
- **Ledger:** L-0007                          (required if any relation is tension / contradicts / terminology-drift)
- **Canonical:** no (L-0007)                  (essays only; added ONLY when ruling A is applied)
- **Amended:** L-0007                         (foundation only; added ONLY when ruling B is applied)
-->

### Epistemology

### Architect and metaphysics

### Time and quantum

### Agency

### Consciousness

### Mortality and the Infinite Pool

### Ethics

### AI and authorship

### Genetic engineering

### Religion and revelation

## 3. Explicit denials

<!--
Claims the document explicitly rejects or marks as not established, in the same claim-block format
(usually Type: Not established). Example: personal survival after death; a conscious Pool.
-->

## 4. Key terms

<!-- Required for essays; optional for foundation chapters (Chapter XII is mostly this section). -->

| Term | Definition as used here | Matches foundation glossary? |
|------|-------------------------|------------------------------|

<!-- Last column: yes | variant (explain) | new -->

## 5. Metaphors and imagery

<!-- Imagery is NOT a claim. Record it here so it is not mistaken for a literal assertion. -->

| Metaphor | Stands for | Literalisation risk |
|----------|------------|---------------------|

<!-- Literalisation risk: low | medium | high, with a few words on how it could be misread as physics or doctrine. -->

## 6. Load-bearing arguments

<!--
The argument chains the document depends on, using claim IDs. A contradiction in a premise threatens the conclusion.
Format: - AD-VI-001 + AD-VI-002 → AD-VI-005 — short label
-->

## 7. Objections addressed

<!-- Required for essays; optional for foundation chapters (Chapter X is mostly this section). -->

| Objection | Response (claim IDs) | Foundation cross-ref |
|-----------|----------------------|----------------------|

<!-- Foundation cross-ref: the matching Chapter X category/claim (e.g. AD-X-042), or "none". -->

## 8. Alignment summary

<!--
Essays only, filled in during alignment (align-with-foundation skill). Foundation chapters: write "Not applicable."
- Foundation chapters touched: VI, XI
- agrees: n · extends: n · refines: n · tension: n · contradicts: n · terminology-drift: n · novel: n
- Ledger entries: L-0007, L-0009
-->

## 9. Drift and open questions

<!--
- Framework version cited vs. current foundation edition.
- Terminology that differs from the glossary.
- Gaps, ambiguities, or points the distiller was unsure how to type (say why).
-->
