# Five-Model MCQA Text Baseline Comparison

## Summary
- Evaluation set: final selected MCQA subset, 3,573 questions.
- All models used text-only input and the same JSON-answer prompt.
- Qwen-Max-Latest is the best overall model among all runs.

| Model | Correct / Total | Accuracy | Invalid/API Error |
|---|---:|---:|---:|
| Qwen3-8B | 2320 / 3573 | 64.93% | 0 |
| Qwen3-VL-30B-A3B-Instruct | 2529 / 3573 | 70.78% | 0 |
| Qwen-Max | 2554 / 3573 | 71.48% | 4 |
| Qwen3.5-35B-A3B | 2619 / 3573 | 73.30% | 0 |
| Qwen-Max-Latest | 2685 / 3573 | 75.15% | 0 |

## Domain Comparison
| Domain | Qwen3-8B | Qwen3-VL-30B | Qwen-Max | Qwen3.5-35B | Qwen-Max-Latest |
|---|---:|---:|---:|---:|---:|
| Physics | 86.02% | 88.92% | 88.67% | 91.33% | 90.36% |
| Computer Science | 70.66% | 77.93% | 79.34% | 77.23% | 83.33% |
| Climate Science | 75.62% | 80.17% | 83.06% | 80.99% | 80.17% |
| Earth Science | 80.65% | 81.45% | 81.45% | 84.68% | 79.84% |
| Chemistry | 62.05% | 71.16% | 68.50% | 70.21% | 78.18% |
| Astronomy | 56.30% | 67.23% | 67.23% | 59.66% | 73.95% |
| Materials Science | 63.49% | 66.31% | 68.25% | 67.72% | 69.49% |
| Clinical Medicine | 54.81% | 64.15% | 63.85% | 73.04% | 68.59% |
| Genomics | 59.60% | 62.80% | 66.00% | 72.40% | 68.40% |
| Life Sciences | 46.49% | 49.12% | 53.51% | 48.68% | 58.77% |

## Dataset Highlights
| Dataset | Qwen3-8B | Qwen3-VL-30B | Qwen-Max | Qwen3.5-35B | Qwen-Max-Latest |
|---|---:|---:|---:|---:|---:|
| EarthSE_Earth-Iron | 85.71% | 89.61% | 92.21% | 93.51% | 90.26% |
| MaScQA | 63.79% | 74.14% | 74.14% | 82.76% | 89.66% |
| ClimaQA_gold | 75.61% | 85.37% | 82.93% | 75.61% | 87.80% |
| CSBench_MCQ | 70.66% | 77.93% | 79.34% | 77.23% | 83.33% |
| SciKnowEval | 69.98% | 74.85% | 75.90% | 75.00% | 79.49% |
| MedMCQA | 62.31% | 74.37% | 75.38% | 82.91% | 79.15% |
| Astro-QA | 56.30% | 67.23% | 67.23% | 59.66% | 73.95% |
| Genome-Bench | 59.60% | 62.80% | 66.00% | 72.40% | 68.40% |
| MedQA_USMLE | 50.39% | 58.91% | 57.36% | 75.97% | 65.12% |
| Lab-Bench | 31.36% | 28.81% | 32.20% | 29.66% | 37.29% |
| MedXpertQA | 10.98% | 14.63% | 10.98% | 19.51% | 19.51% |

## Speech Feature Comparison
| Feature | Qwen3-8B | Qwen3-VL-30B | Qwen-Max | Qwen3.5-35B | Qwen-Max-Latest |
|---|---:|---:|---:|---:|---:|
| abbreviation | 65.05% | 71.03% | 71.47% | 73.70% | 75.17% |
| strong_oov_min1 | 64.06% | 69.91% | 70.24% | 73.02% | 73.83% |
| weak_oov_min10 | 64.39% | 70.11% | 70.62% | 73.11% | 74.14% |
| unit | 60.71% | 68.16% | 68.47% | 68.71% | 74.67% |
| exact_text_expression | 59.90% | 66.12% | 67.23% | 69.30% | 71.34% |
| formula_or_expression | 57.97% | 64.27% | 65.05% | 67.81% | 69.27% |
| gene_or_sequence | 53.92% | 59.02% | 62.35% | 64.51% | 64.71% |
| computer_science_term | 71.15% | 78.85% | 79.81% | 77.64% | 83.89% |

## Main Findings
1. Qwen-Max-Latest is the strongest overall text baseline: 75.15%, +10.22 points over Qwen3-8B and +1.85 points over Qwen3.5-35B-A3B.
2. Qwen3.5-35B-A3B remains stronger on Clinical Medicine and Genomics, especially MedQA_USMLE and Genome-Bench.
3. Qwen-Max-Latest is much stronger on Chemistry, Computer Science, Astronomy, Life Sciences, and unit/exact-expression samples.
4. The hard tail remains: MedXpertQA and Lab-Bench are still weak across all models, though Qwen-Max-Latest improves Lab-Bench to 37.29%.
5. The benchmark continues to separate model capability well: accuracy ranges from 64.93% to 75.15% under the same MCQA prompt.

## Files
- Qwen3-8B: `eval_text_models/outputs/qwen3_8b_api/`
- Qwen3-VL-30B-A3B-Instruct: `eval_text_models/outputs/qwen3_vl_30b_a3b_instruct_api/`
- Qwen-Max: `eval_text_models/outputs/qwen_max_api/`
- Qwen3.5-35B-A3B: `eval_text_models/outputs/qwen3_5_35b_a3b_api/`
- Qwen-Max-Latest: `eval_text_models/outputs/qwen_max_latest_api/`
