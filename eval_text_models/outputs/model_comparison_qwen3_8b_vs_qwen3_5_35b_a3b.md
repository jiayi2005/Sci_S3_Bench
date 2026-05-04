# Qwen3-8B vs Qwen3.5-35B-A3B MCQA Text Baseline Comparison

## Summary
- Evaluation set: final selected MCQA subset, 3,573 questions.
- Qwen3-8B accuracy: 64.93% (2,320 / 3,573).
- Qwen3.5-35B-A3B accuracy: 73.30% (2,619 / 3,573).
- Absolute improvement: +8.37 percentage points.
- Invalid/API errors: 0 for both models.
- Parsing: all predictions were parsed successfully.

## Overall Comparison
| Model | Count | Correct | Accuracy |
|---|---:|---:|---:|
| Qwen3-8B | 3,573 | 2,320 | 64.93% |
| Qwen3.5-35B-A3B | 3,573 | 2,619 | 73.30% |

## Domain Comparison
| Domain | Count | Qwen3-8B | Qwen3.5-35B-A3B | Delta |
|---|---:|---:|---:|---:|
| Clinical Medicine | 675 | 54.81% | 73.04% | +18.22 |
| Genomics | 250 | 59.60% | 72.40% | +12.80 |
| Chemistry | 527 | 62.05% | 70.21% | +8.16 |
| Computer Science | 426 | 70.66% | 77.23% | +6.57 |
| Climate Science | 242 | 75.62% | 80.99% | +5.37 |
| Physics | 415 | 86.02% | 91.33% | +5.30 |
| Materials Science | 567 | 63.49% | 67.72% | +4.23 |
| Earth Science | 124 | 80.65% | 84.68% | +4.03 |
| Astronomy | 119 | 56.30% | 59.66% | +3.36 |
| Life Sciences | 228 | 46.49% | 48.68% | +2.19 |

## Dataset Comparison
| Dataset | Count | Qwen3-8B | Qwen3.5-35B-A3B | Delta |
|---|---:|---:|---:|---:|
| MedQA_USMLE | 129 | 50.39% | 75.97% | +25.58 |
| MedMCQA | 398 | 62.31% | 82.91% | +20.60 |
| MaScQA | 58 | 63.79% | 82.76% | +18.97 |
| Genome-Bench | 250 | 59.60% | 72.40% | +12.80 |
| MedXpertQA | 82 | 10.98% | 19.51% | +8.54 |
| EarthSE_Earth-Iron | 154 | 85.71% | 93.51% | +7.79 |
| ChemBench | 192 | 61.46% | 68.75% | +7.29 |
| CSBench_MCQ | 426 | 70.66% | 77.23% | +6.57 |
| ClimaQA_silver | 126 | 77.78% | 84.13% | +6.35 |
| SciKnowEval | 1,336 | 69.99% | 75.00% | +5.02 |
| Astro-QA | 119 | 56.30% | 59.66% | +3.36 |
| EarthSE_Earth-Silver | 78 | 57.69% | 60.26% | +2.56 |
| PubMedQA | 66 | 72.73% | 74.24% | +1.52 |
| ClimaQA_gold | 41 | 75.61% | 75.61% | +0.00 |
| Lab-Bench | 118 | 31.36% | 29.66% | -1.69 |

## Speech Feature Comparison
| Feature | Count | Qwen3-8B | Qwen3.5-35B-A3B | Delta |
|---|---:|---:|---:|---:|
| gene_or_sequence | 510 | 53.92% | 64.51% | +10.59 |
| formula_or_expression | 1,920 | 57.97% | 67.81% | +9.84 |
| exact_text_expression | 2,606 | 59.90% | 69.30% | +9.40 |
| strong_oov_min1 | 3,061 | 64.06% | 73.02% | +8.95 |
| weak_oov_min10 | 3,128 | 64.39% | 73.11% | +8.73 |
| abbreviation | 3,411 | 65.05% | 73.70% | +8.65 |
| spoken_written_mismatch | 3,570 | 64.96% | 73.33% | +8.38 |
| unit | 1,275 | 60.71% | 68.71% | +8.00 |
| computer_science_term | 416 | 71.15% | 77.64% | +6.49 |
| code_expression | 11 | 90.91% | 72.73% | -18.18 |

## Error Overlap
| Pattern | Count | Share |
|---|---:|---:|
| Both correct | 2,108 | 59.00% |
| Both wrong | 742 | 20.77% |
| 8B wrong, 35B correct | 511 | 14.30% |
| 8B correct, 35B wrong | 212 | 5.93% |

## Main Findings
1. Qwen3.5-35B-A3B improves the text baseline substantially: +8.37 points overall.
2. The largest gains are in Clinical Medicine (+18.22), Genomics (+12.80), and Chemistry (+8.16), which are exactly the domains where specialist terminology and exact scientific expressions matter most.
3. Dataset-level gains are strongest for MedQA_USMLE (+25.58), MedMCQA (+20.60), MaScQA (+18.97), and Genome-Bench (+12.80). The larger model is much better on exam-style medical reasoning and genomics MCQA.
4. Lab-Bench remains hard and slightly drops with the larger model, suggesting these lab MCQA items may require more specialized biomedical lab knowledge or have answer conventions not captured by scale alone.
5. Feature-level gains are strongest on gene_or_sequence (+10.59), formula_or_expression (+9.84), and exact_text_expression (+9.40). This supports the benchmark design: exact scientific expressions are meaningful stress points for text models and likely even more important for speech input.
6. There are still 742 questions both models miss, which are useful candidates for deeper error analysis and potential human review.

## Output Files
- Qwen3-8B predictions: `eval_text_models/outputs/qwen3_8b_api/predictions_full.jsonl`
- Qwen3.5-35B-A3B predictions: `eval_text_models/outputs/qwen3_5_35b_a3b_api/predictions_full.jsonl`
- Qwen3-8B metrics: `eval_text_models/outputs/qwen3_8b_api/full_metrics/`
- Qwen3.5-35B-A3B metrics: `eval_text_models/outputs/qwen3_5_35b_a3b_api/full_metrics/`
