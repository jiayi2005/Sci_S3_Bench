# Four-Model MCQA Text Baseline Comparison

## Summary
- Evaluation set: final selected MCQA subset, 3,573 questions.
- All models used text-only input and the same JSON-answer prompt.
- Qwen-Max had 4 invalid/API-error records; all other models had 0 invalid records.

| Model | Type | Correct / Total | Accuracy |
|---|---|---:|---:|
| Qwen3-8B | small text baseline | 2320 / 3573 | 64.93% |
| Qwen3-VL-30B-A3B-Instruct | VL MoE, text-only | 2529 / 3573 | 70.78% |
| Qwen-Max | commercial Qwen baseline | 2554 / 3573 | 71.48% |
| Qwen3.5-35B-A3B | strong text MoE | 2619 / 3573 | 73.30% |

## Domain Comparison
| Domain | Qwen3-8B | Qwen3-VL-30B | Qwen-Max | Qwen3.5-35B |
|---|---:|---:|---:|---:|
| Physics | 86.02% | 88.92% | 88.67% | 91.33% |
| Earth Science | 80.65% | 81.45% | 81.45% | 84.68% |
| Climate Science | 75.62% | 80.17% | 83.06% | 80.99% |
| Computer Science | 70.66% | 77.93% | 79.34% | 77.23% |
| Chemistry | 62.05% | 71.16% | 68.50% | 70.21% |
| Materials Science | 63.49% | 66.31% | 68.25% | 67.72% |
| Genomics | 59.60% | 62.80% | 66.00% | 72.40% |
| Astronomy | 56.30% | 67.23% | 67.23% | 59.66% |
| Clinical Medicine | 54.81% | 64.15% | 63.85% | 73.04% |
| Life Sciences | 46.49% | 49.12% | 53.51% | 48.68% |

## Dataset Highlights
| Dataset | Qwen3-8B | Qwen3-VL-30B | Qwen-Max | Qwen3.5-35B |
|---|---:|---:|---:|---:|
| EarthSE_Earth-Iron | 85.71% | 89.61% | 92.21% | 93.51% |
| ClimaQA_silver | 77.78% | 80.95% | 86.51% | 84.13% |
| CSBench_MCQ | 70.66% | 77.93% | 79.34% | 77.23% |
| SciKnowEval | 69.98% | 74.85% | 75.90% | 75.00% |
| MedMCQA | 62.31% | 74.37% | 75.38% | 82.91% |
| Genome-Bench | 59.60% | 62.80% | 66.00% | 72.40% |
| MedQA_USMLE | 50.39% | 58.91% | 57.36% | 75.97% |
| Lab-Bench | 31.36% | 28.81% | 32.20% | 29.66% |
| MedXpertQA | 10.98% | 14.63% | 10.98% | 19.51% |

## Speech Feature Comparison
| Feature | Qwen3-8B | Qwen3-VL-30B | Qwen-Max | Qwen3.5-35B |
|---|---:|---:|---:|---:|
| abbreviation | 65.05% | 71.03% | 71.47% | 73.70% |
| strong_oov_min1 | 64.06% | 69.91% | 70.24% | 73.02% |
| weak_oov_min10 | 64.39% | 70.11% | 70.62% | 73.11% |
| unit | 60.71% | 68.16% | 68.47% | 68.71% |
| exact_text_expression | 59.90% | 66.12% | 67.23% | 69.30% |
| formula_or_expression | 57.97% | 64.27% | 65.05% | 67.81% |
| gene_or_sequence | 53.92% | 59.02% | 62.35% | 64.51% |
| computer_science_term | 71.15% | 78.85% | 79.81% | 77.64% |

## Interpretation
1. Overall ranking is Qwen3.5-35B-A3B > Qwen-Max > Qwen3-VL-30B-A3B-Instruct > Qwen3-8B.
2. Qwen-Max is not the overall winner, but it is competitive and beats Qwen3.5-35B in several domains: Climate Science, Computer Science, Materials Science, Astronomy, and Life Sciences.
3. Qwen3.5-35B remains much stronger on Clinical Medicine and Genomics, which are the most specialist biomedical parts of this benchmark.
4. Qwen-Max improves exact scientific expression handling over Qwen3-VL-30B, but still trails Qwen3.5-35B on formula/expression and gene/sequence samples.
5. The hard tail remains: Lab-Bench and MedXpertQA stay low across all models, so these are useful hard subsets for later analysis.

## Files
- Qwen3-8B: `eval_text_models/outputs/qwen3_8b_api/`
- Qwen3-VL-30B-A3B-Instruct: `eval_text_models/outputs/qwen3_vl_30b_a3b_instruct_api/`
- Qwen-Max: `eval_text_models/outputs/qwen_max_api/`
- Qwen3.5-35B-A3B: `eval_text_models/outputs/qwen3_5_35b_a3b_api/`
