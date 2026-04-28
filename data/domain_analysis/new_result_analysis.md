# New 10-Domain Result Analysis

## 1. Overall Pool

The v2 taxonomy contains exactly 10 domains:

| Domain | Raw question-like count |
|---|---:|
| Clinical Medicine | 209,328 |
| Life Sciences | 11,684 |
| Chemistry | 11,137 |
| Materials Science | 6,190 |
| Climate Science | 4,569 |
| Physics | 4,098 |
| Genomics | 4,022 |
| Earth Science | 2,861 |
| Astronomy | 2,016 |
| Computer Science | 1,281 |

Key split results:

- `Clinical Medicine` is now separated from Life Sciences and is dominated by MedMCQA.
- `Genomics` is separated from Life Sciences and mainly comes from GeneTuring plus Genome-Bench.
- `Climate Science` is separated from Earth Science and includes ClimaQA plus climate/atmosphere/cryosphere/polar parts of EarthSE.
- `Earth Science` now mostly contains oceanography, hydrology, geology, geophysics, geography, and non-climate EarthSE records.
- `MMLU` and `ScienceQA` remain excluded.
- `SciKnowEval` is split into Chemistry, Life Sciences, Materials Science, and Physics by internal `Appendix.domain`.

## 2. Final Speech-Sensitive Selection

The selected set contains 5,500 samples:

| Domain | Selected | Share |
|---|---:|---:|
| Clinical Medicine | 700 | 12.73% |
| Chemistry | 700 | 12.73% |
| Materials Science | 600 | 10.91% |
| Physics | 600 | 10.91% |
| Life Sciences | 550 | 10.00% |
| Genomics | 550 | 10.00% |
| Climate Science | 550 | 10.00% |
| Earth Science | 450 | 8.18% |
| Astronomy | 400 | 7.27% |
| Computer Science | 400 | 7.27% |

All domains meet the target quota. The largest domain share is 12.73%, below the 18% cap.

## 3. Selected Dataset Composition

Dominant selected sources:

| Domain | Main selected source(s) |
|---|---|
| Clinical Medicine | MedMCQA: 700 |
| Chemistry | ChemBench: 631; QCBench: 40; ATLAS: 29 |
| Materials Science | SciKnowEval: 534; MaScQA: 46; ATLAS: 20 |
| Physics | SciKnowEval: 505; PHYBench: 76; ATLAS: 19 |
| Life Sciences | BioASQ: 544; ATLAS: 6 |
| Genomics | GeneTuring: 543; ATLAS: 7 |
| Climate Science | EarthSE_Earth-Iron: 272; ClimaQA_silver: 186; ClimaQA_gold: 46; EarthSE_Earth-Gold: 45 |
| Earth Science | EarthSE_Earth-Iron: 331; EarthSE_Earth-Gold: 116; ATLAS: 3 |
| Astronomy | Astro-QA: 400 |
| Computer Science | BigCodeBench: 367; ATLAS: 33 |

Important bias:

- Within several domains, one dataset fills almost the entire quota.
- Clinical Medicine uses only MedMCQA, despite MedQA_USMLE and PubMedQA being available.
- Life Sciences is almost entirely BioASQ.
- Genomics is almost entirely GeneTuring.
- Computer Science is mostly BigCodeBench.

This is acceptable for a first balanced domain-level selection, but not ideal if dataset diversity is also required.

## 4. Question Type Composition

Notable selected question forms:

- Clinical Medicine: 700 MCQA.
- Chemistry: 460 MCQA, 200 open-ended, 40 open numeric/short answer.
- Climate Science: mixed open-ended, MCQA, fill-in-the-blank, dialogue, true/false.
- Earth Science: mixed open-ended, dialogue, MCQA, fill-in-the-blank, true/false.
- Genomics: mostly open generation/extraction.
- Computer Science: mostly code generation.
- Life Sciences: mostly open-ended.
- Astronomy: mostly MCQA with some true/false.

This means the final benchmark is domain-balanced, but not question-type-balanced.

## 5. Speech-Sensitive Signal

All selected 5,500 samples satisfy `requires_exact_text`.

Top detected reasons:

| Reason | Count |
|---|---:|
| requires_exact_text | 5,500 |
| spoken_form_differs | 5,368 |
| contains_abbreviation | 4,658 |
| high_terminology_density | 4,335 |
| contains_special_symbol | 2,378 |

The current rule set is effective as a coarse filter: it strongly favors formulas, symbols, abbreviations, units, gene/protein names, code, and technical terminology.

However, score saturation is visible:

- Most selected domains have average score 5.0.
- Astronomy average is 4.251.

This means the current score is good for selecting candidates, but not very informative for ranking high-quality candidates inside the selected pool.

## 6. Main Issues

1. Dataset diversity is weaker than domain diversity.
   The sampler balances domains, but inside each domain it simply takes the highest-scoring candidates. Large or alphabetically earlier datasets can dominate.

2. Score saturation reduces ranking quality.
   Many samples hit the max score 5.0, so the system cannot distinguish "very speech-sensitive" from "moderately speech-sensitive but has symbols".

3. Some domains are structurally narrow.
   Astronomy only has Astro-QA. Computer Science is mostly BigCodeBench. Clinical Medicine is dominated by MedMCQA.

4. Life Sciences vs Clinical Medicine is now cleaner, but BioASQ still contains biomedical/clinical-flavored questions.
   If a strict separation is needed, BioASQ should be further split into biomedical literature, genetics, clinical, and general biology.

## 7. Recommended Next Step

For the next version, keep the 10-domain taxonomy but add dataset-level caps inside each domain:

- No single dataset should exceed 60-70% of a domain quota when alternatives exist.
- Clinical Medicine should mix MedMCQA, MedQA_USMLE, PubMedQA, and MedXpertQA.
- Life Sciences should mix BioASQ, Lab-Bench, SciKnowEval biology, and EarthSE biosphere/ecology records.
- Genomics should mix GeneTuring, Genome-Bench, and ATLAS genetics/bioinformatics.
- Computer Science should mix BigCodeBench, SciCode, and ATLAS CS.

Also adjust scoring:

- Keep exact-text detection as a hard candidate gate.
- Replace the current additive 0-5 score with separate feature counters:
  - notation/formula/code score
  - abbreviation score
  - terminology score
  - oral-text mismatch score
  - long-context penalty
- Use these features for ranking after domain and dataset balancing.

