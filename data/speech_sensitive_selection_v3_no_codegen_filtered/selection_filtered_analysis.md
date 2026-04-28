# Filtered Selection Analysis

- Selected file: `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/selected_filtered.jsonl`
- Rejected file: `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/rejected_by_quality_filter.jsonl`
- Raw before quality filter: 6,520
- Kept after quality filter: 5,709
- Rejected by quality filter: 811
- Requires exact text: 4,356 (76.30%)
- Avg critical spans/sample: 8.14
- Avg manual pronunciation items/sample: 2.81

## Domain Distribution

| Domain | Count | Share |
|---|---:|---:|
| Chemistry | 782 | 13.70% |
| Clinical Medicine | 691 | 12.10% |
| Genomics | 663 | 11.61% |
| Climate Science | 645 | 11.30% |
| Materials Science | 613 | 10.74% |
| Life Sciences | 610 | 10.68% |
| Physics | 573 | 10.04% |
| Earth Science | 562 | 9.84% |
| Computer Science | 446 | 7.81% |
| Astronomy | 124 | 2.17% |

## Question Type Distribution

| Question Type | Count | Share |
|---|---:|---:|
| MCQA | 3,601 | 63.08% |
| Open-ended | 1,195 | 20.93% |
| Open generation/extraction | 402 | 7.04% |
| Open-ended dialogue | 145 | 2.54% |
| Open numeric/short answer | 142 | 2.49% |
| Fill-in-the-blank | 113 | 1.98% |
| True/False | 111 | 1.94% |

## Dataset Distribution

| Dataset | Count | Share |
|---|---:|---:|
| SciKnowEval | 1,340 | 23.47% |
| EarthSE_Earth-Iron | 654 | 11.46% |
| CSBench_MCQ | 434 | 7.60% |
| MedMCQA | 414 | 7.25% |
| GeneTuring | 402 | 7.04% |
| BioASQ | 276 | 4.83% |
| ChemBench | 270 | 4.73% |
| EarthSE_Earth-Silver | 254 | 4.45% |
| Genome-Bench | 250 | 4.38% |
| ClimaQA_silver | 206 | 3.61% |
| ATLAS | 179 | 3.14% |
| EarthSE_Earth-Gold | 145 | 2.54% |
| QCBench | 142 | 2.49% |
| MedQA_USMLE | 129 | 2.26% |
| Astro-QA | 124 | 2.17% |
| Lab-Bench | 118 | 2.07% |
| PHYBench | 94 | 1.65% |
| MedXpertQA | 82 | 1.44% |
| ClimaQA_gold | 69 | 1.21% |
| PubMedQA | 66 | 1.16% |
| MaScQA | 58 | 1.02% |
| UGPhysics | 3 | 0.05% |

## Feature Coverage

| Feature | Count | Share |
|---|---:|---:|
| spoken_written_mismatch | 5,706 | 99.95% |
| abbreviation | 5,319 | 93.17% |
| weak_oov_min10 | 4,889 | 85.64% |
| strong_oov_min1 | 4,773 | 83.60% |
| formula_or_expression | 2,904 | 50.87% |
| unit | 1,718 | 30.09% |
| gene_or_sequence | 1,212 | 21.23% |
| computer_science_term | 422 | 7.39% |
| code_expression | 22 | 0.39% |

## Quality Filter Rejections

| Reason | Count | Share of Raw |
|---|---:|---:|
| missing_or_empty_answer | 275 | 4.22% |
| low_score_too_few_critical_spans | 232 | 3.56% |
| image_or_figure_dependent | 169 | 2.59% |
| score_below_45 | 126 | 1.93% |
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
