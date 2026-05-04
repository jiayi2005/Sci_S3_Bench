# Qwen3-8B MCQA Text Baseline Report

## Summary
- Model: `qwen3-8b` via Alibaba Bailian / DashScope OpenAI-compatible API
- Input: `data/final_results/selected_filtered.jsonl` filtered to `question_type == MCQA`
- Evaluated samples: 3,573
- Correct: 2,320
- Accuracy: 64.93%
- Invalid/API error: 0
- Parse status: all `json_answer`

## Domain Accuracy
| Domain | Count | Correct | Accuracy |
|---|---:|---:|---:|
| Physics | 415 | 357 | 86.02% |
| Earth Science | 124 | 100 | 80.65% |
| Climate Science | 242 | 183 | 75.62% |
| Computer Science | 426 | 301 | 70.66% |
| Materials Science | 567 | 360 | 63.49% |
| Chemistry | 527 | 327 | 62.05% |
| Genomics | 250 | 149 | 59.60% |
| Astronomy | 119 | 67 | 56.30% |
| Clinical Medicine | 675 | 370 | 54.81% |
| Life Sciences | 228 | 106 | 46.49% |

## Dataset Accuracy
| Dataset | Count | Correct | Accuracy |
|---|---:|---:|---:|
| EarthSE_Earth-Iron | 154 | 132 | 85.71% |
| ClimaQA_silver | 126 | 98 | 77.78% |
| ClimaQA_gold | 41 | 31 | 75.61% |
| PubMedQA | 66 | 48 | 72.73% |
| CSBench_MCQ | 426 | 301 | 70.66% |
| SciKnowEval | 1,336 | 935 | 69.99% |
| MaScQA | 58 | 37 | 63.79% |
| MedMCQA | 398 | 248 | 62.31% |
| ChemBench | 192 | 118 | 61.46% |
| Genome-Bench | 250 | 149 | 59.60% |
| EarthSE_Earth-Silver | 78 | 45 | 57.69% |
| Astro-QA | 119 | 67 | 56.30% |
| MedQA_USMLE | 129 | 65 | 50.39% |
| Lab-Bench | 118 | 37 | 31.36% |
| MedXpertQA | 82 | 9 | 10.98% |

## Speech Feature Accuracy
| Feature | Count | Correct | Accuracy |
|---|---:|---:|---:|
| code_expression | 11 | 10 | 90.91% |
| computer_science_domain_term | 416 | 296 | 71.15% |
| computer_science_term | 416 | 296 | 71.15% |
| abbreviation | 3,411 | 2,219 | 65.05% |
| spoken_written_mismatch | 3,570 | 2,319 | 64.96% |
| text_easy_proxy | 3,573 | 2,320 | 64.93% |
| weak_oov_min10 | 3,128 | 2,014 | 64.39% |
| strong_oov_min1 | 3,061 | 1,961 | 64.06% |
| unit | 1,275 | 774 | 60.71% |
| exact_text_expression | 2,606 | 1,561 | 59.90% |
| formula_or_expression | 1,920 | 1,113 | 57.97% |
| gene_or_sequence | 510 | 275 | 53.92% |

## Main Findings
1. Qwen3-8B text baseline reaches 64.93% on the final MCQA subset. This is a valid text-only baseline because all 3,573 responses were parsed successfully as JSON answer letters.
2. Performance varies strongly by domain. Physics, Earth Science, and Climate Science are highest, while Life Sciences, Clinical Medicine, Astronomy, and Genomics are lower.
3. Dataset difficulty is highly uneven. MedXpertQA and Lab-Bench are much harder than MedMCQA/PubMedQA, which suggests the model struggles with specialist biomedical/lab reasoning more than general medical MCQA.
4. Formula/exact-expression/gene-or-sequence samples are harder than general abbreviation samples. This supports the benchmark design: samples with formulas, units, sequences, and exact text expressions remain challenging even for text models.
5. The option-count distribution matters. 4-option questions have 66.78% accuracy, while 10-option questions have 10.98% accuracy, matching the low MedXpertQA result.

## Important Caveats
- This is text-only evaluation, not speech or S2S evaluation. It measures the base text model ability on selected samples.
- Only MCQA is evaluated. Open-ended, dialogue, fill-blank, and generation/extraction samples are excluded.
- The current prompt forces direct JSON answer output and disables thinking, so the result is a clean non-reasoning answer-only baseline.
- The API key used for this run was provided in chat; it should be rotated before further experiments.

## Output Files
- Predictions: `eval_text_models/outputs/qwen3_8b_api/predictions_full.jsonl`
- Invalid/API errors: `eval_text_models/outputs/qwen3_8b_api/invalid_full.jsonl`
- Metrics directory: `eval_text_models/outputs/qwen3_8b_api/full_metrics/`
- Log: `eval_text_models/outputs/qwen3_8b_api/full_run.log`
