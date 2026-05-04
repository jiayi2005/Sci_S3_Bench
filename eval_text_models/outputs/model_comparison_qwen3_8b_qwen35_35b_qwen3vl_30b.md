# Three-Model MCQA Text Baseline Comparison

## Summary
- Evaluation set: final selected MCQA subset, 3,573 questions.
- All models used text-only input and the same JSON-answer prompt.
- All three runs completed with 0 invalid/API errors.

| Model | Type | Count | Correct | Accuracy |
|---|---|---:|---:|---:|
| Qwen3-8B | text dense/API | 3,573 | 2,320 | 64.93% |
| Qwen3-VL-30B-A3B-Instruct | VL MoE/API, text-only | 3,573 | 2,529 | 70.78% |
| Qwen3.5-35B-A3B | text MoE/API | 3,573 | 2,619 | 73.30% |

## Main Takeaways
1. Qwen3-VL-30B-A3B-Instruct is clearly stronger than Qwen3-8B: +5.85 points overall.
2. Qwen3.5-35B-A3B remains the strongest overall: +8.37 over Qwen3-8B and +2.52 over Qwen3-VL-30B.
3. VL-30B is not always weaker than Qwen3.5-35B: it beats Qwen3.5-35B on Astronomy, Chemistry, Computer Science, and slightly on Life Sciences.
4. Qwen3.5-35B is much stronger on Clinical Medicine and Genomics, which are the most specialist biomedical domains.
5. There are 626 questions all three models miss, useful for later hard-case analysis.

## Domain Comparison
| Domain | Count | Qwen3-8B | Qwen3.5-35B | Qwen3-VL-30B | VL-8B | VL-35B |
|---|---:|---:|---:|---:|---:|---:|
| Astronomy | 119 | 56.30% | 59.66% | 67.23% | +10.92 | +7.56 |
| Clinical Medicine | 675 | 54.81% | 73.04% | 64.15% | +9.33 | -8.89 |
| Chemistry | 527 | 62.05% | 70.21% | 71.16% | +9.11 | +0.95 |
| Computer Science | 426 | 70.66% | 77.23% | 77.93% | +7.28 | +0.70 |
| Climate Science | 242 | 75.62% | 80.99% | 80.17% | +4.55 | -0.83 |
| Genomics | 250 | 59.60% | 72.40% | 62.80% | +3.20 | -9.60 |
| Physics | 415 | 86.02% | 91.33% | 88.92% | +2.89 | -2.41 |
| Materials Science | 567 | 63.49% | 67.72% | 66.31% | +2.82 | -1.41 |
| Life Sciences | 228 | 46.49% | 48.68% | 49.12% | +2.63 | +0.44 |
| Earth Science | 124 | 80.65% | 84.68% | 81.45% | +0.81 | -3.23 |

## Dataset Highlights
| Dataset | Count | Qwen3-8B | Qwen3.5-35B | Qwen3-VL-30B | Note |
|---|---:|---:|---:|---:|---|
| MedMCQA | 398 | 62.31% | 82.91% | 74.37% | 35B strongest |
| MedQA_USMLE | 129 | 50.39% | 75.97% | 58.91% | 35B much stronger |
| Genome-Bench | 250 | 59.60% | 72.40% | 62.80% | 35B stronger on genomics |
| Astro-QA | 119 | 56.30% | 59.66% | 67.23% | VL strongest |
| ClimaQA_gold | 41 | 75.61% | 75.61% | 85.37% | VL strongest |
| CSBench_MCQ | 426 | 70.66% | 77.23% | 77.93% | VL slightly strongest |
| Lab-Bench | 118 | 31.36% | 29.66% | 28.81% | All weak |
| MedXpertQA | 82 | 10.98% | 19.51% | 14.63% | All weak, 35B best |

## Speech Feature Comparison
| Feature | Count | Qwen3-8B | Qwen3.5-35B | Qwen3-VL-30B |
|---|---:|---:|---:|---:|
| abbreviation | 3,411 | 65.05% | 73.70% | 71.03% |
| strong_oov_min1 | 3,061 | 64.06% | 73.02% | 69.91% |
| unit | 1,275 | 60.71% | 68.71% | 68.16% |
| exact_text_expression | 2,606 | 59.90% | 69.30% | 66.12% |
| formula_or_expression | 1,920 | 57.97% | 67.81% | 64.27% |
| gene_or_sequence | 510 | 53.92% | 64.51% | 59.02% |
| computer_science_term | 416 | 71.15% | 77.64% | 78.85% |

## Error Overlap
| Pattern | Count | Share |
|---|---:|---:|
| All three correct | 1,986 | 55.58% |
| All three wrong | 626 | 17.52% |
| 35B and VL correct, 8B wrong | 318 | 8.90% |
| Only 35B correct | 193 | 5.40% |
| 8B and 35B correct, VL wrong | 122 | 3.41% |
| Only VL correct | 116 | 3.25% |
| 8B and VL correct, 35B wrong | 109 | 3.05% |
| Only 8B correct | 103 | 2.88% |

## Interpretation
- Qwen3-VL-30B-A3B-Instruct is a useful intermediate baseline: stronger than 8B, but below Qwen3.5-35B overall.
- Its strength is more visible in Astronomy, Chemistry, Computer Science, and Climate-style data, while it lags Qwen3.5-35B in Clinical Medicine and Genomics.
- The strongest benchmark conclusion is robust: specialist biomedical and exact-expression samples remain difficult, and larger text/MoE models improve substantially but do not solve the benchmark.

## Files
- Qwen3-8B: `eval_text_models/outputs/qwen3_8b_api/`
- Qwen3.5-35B-A3B: `eval_text_models/outputs/qwen3_5_35b_a3b_api/`
- Qwen3-VL-30B-A3B-Instruct: `eval_text_models/outputs/qwen3_vl_30b_a3b_instruct_api/`
