# Sci S3 Bench

Sci S3 Bench is a curated scientific speech-sensitive benchmark for scientific speech-to-speech and text-model evaluation. The current release contains quality-checked scientific QA samples selected from normalized STEM, biomedical, clinical, genomics, materials, earth/climate, astronomy, and computer science datasets.

## Final Selected Set

Canonical final file:

```text
data/final_results/selected_filtered.jsonl
```

The legacy mirrored copy is also kept at:

```text
data/speech_sensitive_selection_v3_no_codegen_filtered/selected_filtered.jsonl
```

Current final version summary:

| Metric | Count |
|---|---:|
| Total samples | 5,681 |
| MCQA samples | 3,573 |
| Open-ended samples | 1,195 |
| Open generation/extraction | 402 |
| Open-ended dialogue | 145 |
| Open numeric/short answer | 142 |
| Fill-in-the-blank | 113 |
| True/False | 111 |
| Cybersecurity_QA | 0 |
| Code generation | 0 |

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

## Schema

Each row in `selected_filtered.jsonl` is a JSON object with normalized fields:

```json
{
  "id": "...",
  "dataset": "...",
  "domain": "...",
  "subdomain": "...",
  "question_type": "MCQA",
  "question": "...",
  "options": [],
  "answer": "...",
  "source": {},
  "speech_metadata": {}
}
```

`speech_metadata` contains v3 speech-sensitivity features, including GigaSpeech OOV technical terms, abbreviations and pronunciation hints, formulas, units, gene/sequence spans, critical spans, and rule-based text-easy proxy scores.

## Text Model Baselines

MCQA text-only evaluation was run on the 3,573 MCQA samples. These scores are text upper-bound baselines, not speech/S2S scores.

| Model | Accuracy |
|---|---:|
| Qwen3-8B | 64.93% |
| Qwen3-VL-30B-A3B-Instruct | 70.78% |
| Qwen-Max | 71.48% |
| Qwen3.5-35B-A3B | 73.30% |
| Qwen-Max-Latest | 75.15% |

Evaluation reports are under:

```text
eval_text_models/outputs/
```

The main comparison report is:

```text
eval_text_models/outputs/model_comparison_5_qwen_models.md
```

## Included Reports

Key final dataset reports are under:

```text
data/final_results/
data/domain_analysis/
```

Important files:

- `data/final_results/selected_filtered.jsonl`
- `data/final_results/domain_distribution.csv`
- `data/final_results/question_type_distribution.csv`
- `data/final_results/domain_subdomain_distribution.csv`
- `data/final_results/quality_audit/quality_checked_report.md`
- `data/domain_analysis/merged_dataset_summary.csv`
- `data/domain_analysis/merged_domain_subdomain_counts.csv`
- `data/domain_analysis/domain_taxonomy_v2.md`

## Reproduction Scripts

Core data scripts are in:

```text
data/domain_analysis/scripts/
```

Text model evaluation scripts are in:

```text
eval_text_models/scripts/
```

## Data Policy

This repository intentionally excludes large raw source datasets, downloaded model files, temporary API logs, and intermediate candidate/rejected JSONL artifacts. It tracks the curated final selection, summary reports, evaluation scripts, and compact evaluation metrics/reports.
