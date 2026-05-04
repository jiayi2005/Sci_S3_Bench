# Filtered Selection Analysis

- Selected file: `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/selected_filtered.jsonl`
- Rejected file: `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/rejected_by_quality_filter.jsonl`
- Raw before quality filter: 6,492
- Kept after quality filter: 5,681
- Rejected by quality filter: 811
- Requires exact text: 4,329 (76.20%)
- Avg critical spans/sample: 8.16
- Avg manual pronunciation items/sample: 2.81

## Domain Distribution

| Domain | Count | Share |
|---|---:|---:|
| Chemistry | 782 | 13.77% |
| Clinical Medicine | 675 | 11.88% |
| Genomics | 663 | 11.67% |
| Climate Science | 645 | 11.35% |
| Life Sciences | 610 | 10.74% |
| Materials Science | 609 | 10.72% |
| Physics | 573 | 10.09% |
| Earth Science | 562 | 9.89% |
| Computer Science | 438 | 7.71% |
| Astronomy | 124 | 2.18% |

## Question Type Distribution

| Question Type | Count | Share |
|---|---:|---:|
| MCQA | 3,573 | 62.89% |
| Open-ended | 1,195 | 21.04% |
| Open generation/extraction | 402 | 7.08% |
| Open-ended dialogue | 145 | 2.55% |
| Open numeric/short answer | 142 | 2.50% |
| Fill-in-the-blank | 113 | 1.99% |
| True/False | 111 | 1.95% |

## Dataset Distribution

| Dataset | Count | Share |
|---|---:|---:|
| SciKnowEval | 1,336 | 23.52% |
| EarthSE_Earth-Iron | 654 | 11.51% |
| CSBench_MCQ | 426 | 7.50% |
| GeneTuring | 402 | 7.08% |
| MedMCQA | 398 | 7.01% |
| BioASQ | 276 | 4.86% |
| ChemBench | 270 | 4.75% |
| EarthSE_Earth-Silver | 254 | 4.47% |
| Genome-Bench | 250 | 4.40% |
| ClimaQA_silver | 206 | 3.63% |
| ATLAS | 179 | 3.15% |
| EarthSE_Earth-Gold | 145 | 2.55% |
| QCBench | 142 | 2.50% |
| MedQA_USMLE | 129 | 2.27% |
| Astro-QA | 124 | 2.18% |
| Lab-Bench | 118 | 2.08% |
| PHYBench | 94 | 1.65% |
| MedXpertQA | 82 | 1.44% |
| ClimaQA_gold | 69 | 1.21% |
| PubMedQA | 66 | 1.16% |
| MaScQA | 58 | 1.02% |
| UGPhysics | 3 | 0.05% |

## Feature Coverage

| Feature | Count | Share |
|---|---:|---:|
| spoken_written_mismatch | 5,678 | 99.95% |
| abbreviation | 5,295 | 93.21% |
| weak_oov_min10 | 4,867 | 85.67% |
| strong_oov_min1 | 4,751 | 83.63% |
| formula_or_expression | 2,885 | 50.78% |
| unit | 1,702 | 29.96% |
| gene_or_sequence | 1,212 | 21.33% |
| computer_science_term | 416 | 7.32% |
| code_expression | 19 | 0.33% |

## Quality Filter Rejections

| Reason | Count | Share of Raw |
|---|---:|---:|
| missing_or_empty_answer | 275 | 4.24% |
| low_score_too_few_critical_spans | 232 | 3.57% |
| image_or_figure_dependent | 169 | 2.60% |
| score_below_45 | 126 | 1.94% |
| code_related | 89 | 1.37% |
| very_long_sequence | 49 | 0.75% |
| low_score_without_exact_speech_feature | 26 | 0.40% |
| ocr_or_format_noise | 23 | 0.35% |

## Output CSVs

- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/domain_distribution.csv`
- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/dataset_distribution.csv`
- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/question_type_distribution.csv`
- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/domain_dataset_distribution.csv`
- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/domain_question_type_distribution.csv`
- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/dataset_question_type_distribution.csv`
- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/domain_subdomain_distribution.csv`
- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/feature_coverage.csv`
- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/domain_feature_coverage.csv`
- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/score_distribution.csv`
- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/level_distribution.csv`
- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/rejection_reason_counts.csv`
- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/rejected_domain_distribution.csv`
- `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/rejected_dataset_distribution.csv`
