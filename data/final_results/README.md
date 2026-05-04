# Final Results

This folder collects the quality-checked final Sci S3 Bench selected dataset and main summary files in one place.

## Final Dataset

- File: `selected_filtered.jsonl`
- Total samples: 5,681
- Computer Science samples: 438
- CSBench_MCQ samples: 426
- Cybersecurity_QA samples: 0
- Code generation samples: 0

Canonical source file:

```text
/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/selected_filtered.jsonl
```

## Quality Audit

- Full records checked: 5,681
- Strict audit flags: 0
- Removed by quality audit: 28 records
- Removed reasons: 26 duplicate questions, 2 weak-metadata CS items
- Audit report: `quality_audit/quality_audit_report.md`
- Cleaning report: `quality_audit/quality_checked_report.md`

## Domain Distribution

| Domain | Count |
|---|---:|
| Chemistry | 782 |
| Clinical Medicine | 675 |
| Genomics | 663 |
| Climate Science | 645 |
| Life Sciences | 610 |
| Materials Science | 609 |
| Physics | 573 |
| Earth Science | 562 |
| Computer Science | 438 |
| Astronomy | 124 |

## Question Type Distribution

| Question Type | Count |
|---|---:|
| MCQA | 3,573 |
| Open-ended | 1,195 |
| Open generation/extraction | 402 |
| Open-ended dialogue | 145 |
| Open numeric/short answer | 142 |
| Fill-in-the-blank | 113 |
| True/False | 111 |

## Included Files

- `selected_filtered.jsonl`: quality-checked final selected samples with normalized schema and speech metadata.
- `final_counts_summary.csv`: compact final counts.
- `final_result_manifest.csv`: file list and original source paths.
- `domain_distribution.csv`, `question_type_distribution.csv`, `dataset_distribution.csv`: final distributions.
- `domain_subdomain_distribution.csv`: final Primary/Secondary category distribution.
- `selection_filtered_analysis.md`: final selection analysis report.
- `computer_science_addition_report.md`: updated CSBench_MCQ integration report.
- `quality_audit/`: full-record audit outputs.
- `merged_dataset_summary.csv`, `merged_domain_subdomain_counts.csv`, `domain_taxonomy_v2.md`: source domain analysis references.

## Notes

Raw downloaded source datasets and intermediate rejected/candidate JSONL files are intentionally not included here. Use `selected_filtered.jsonl` for benchmark construction.
