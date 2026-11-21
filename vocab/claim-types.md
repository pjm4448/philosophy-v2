# Claim types

Every distilled claim has exactly one **Type**. The types come from the foundation book's own epistemic taxonomy
(Section XI, *Epistemic Transparency*). Record the type the **document itself** gives the claim, not the type you think it
should have. If an essay gives a claim a different type from the foundation, that is an alignment finding
(usually `tension` or `contradicts`). Don't quietly correct it.

`tools/distill.py validate` reads the backticked values in the first column of this table. Only add a row here if the
book's taxonomy really needs it.

| Type | Use when the document… | Book XI source | Standard applied |
|------|------------------------|----------------|------------------|
| `Empirical` | adopts an established scientific finding | XI.1 Empirical Foundations | Falsifiable |
| `First-person` | asserts something directly apprehended (e.g. one's own experience occurs) | XI.8, XI.9 | Direct access |
| `Inference` | infers something from evidence or analogy (other minds, animal suffering, the Architect from fine-tuning) | XI.2, XI.8 | Converging evidence / coherence |
| `Interpretation` | reads established facts within a larger frame without new predictions (fine-tuning as calibration, the Pool as shared participation) | XI.2 Metaphysical Interpretations | Coherence, interpretive power |
| `Postulated` | offers an explicitly speculative or functional model (Data Cube, lazy loading, functional indifference) | XI.3 Postulated Models | Coherence only |
| `Uncertainty` | marks a matter as scientifically or philosophically unknown or unresolved | XI.4 Scientific Uncertainties | Awaiting discovery |
| `Methodological` | states a commitment that guides inquiry rather than describing reality (is-ought gap, Substrate Humility) | XI.5 Methodological Commitments | Not falsifiable; reflective |
| `Chosen foundation` | states a foundational value chosen, not discovered (suffering should be minimised, solidarity) | XI.6 Foundational Values | Reflective endorsement |
| `Entailed conclusion` | derives a position from chosen foundations (abortion opposed, universal access to enhancements) | XI.6 Entailed Conclusions | Follows from foundations |
| `Not established` | denies a claim or marks it as not established (personal survival, a conscious Pool) | XI.8, XI.9 "Not established" | Burden unmet |

## Guidance

- A **metaphor is not a claim**. Record evocative imagery in *Metaphors and imagery*. Only make it a claim if the document
  asserts something literal through it, and then type the literal assertion.
- If one sentence makes two kinds of claim (for example an empirical fact and an interpretation of it), split it into two claims.
- Use `Entailed conclusion` only when the document presents the claim as following from chosen foundations. Otherwise use
  `Chosen foundation` or `Inference`.
- Put the confidence a document expresses ("strongly inferred", "highly speculative") in the claim wording. It is not part of the type.
