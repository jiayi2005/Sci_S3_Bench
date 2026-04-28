# Sci S3 Bench

Sci S3 Bench is a curated scientific speech-to-speech benchmark selection. The current release contains speech-sensitive scientific QA samples selected from normalized STEM and biomedical datasets.

## Current Selected Set

Final selected file:

```text
data/speech_sensitive_selection_v3_no_codegen_filtered/selected_filtered.jsonl
```

Current version summary:

| Metric | Count |
|---|---:|
| Total samples | 5,709 |
| Chemistry | 782 |
| Clinical Medicine | 691 |
| Genomics | 663 |
| Climate Science | 645 |
| Materials Science | 613 |
| Life Sciences | 610 |
| Physics | 573 |
| Earth Science | 562 |
| Computer Science | 446 |
| Astronomy | 124 |

Computer Science was expanded with high-quality `CSBench_MCQ` samples only:

| Dataset | Count |
|---|---:|
| CSBench_MCQ | 434 |
| ATLAS Computer Science subset | 12 |
| Cybersecurity_QA | 0 |
| Code generation | 0 |

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

`speech_metadata` contains v3 speech-sensitivity features, including:

- GigaSpeech OOV technical terms
- abbreviations and pronunciation hints
- formulas, units, gene/sequence spans, and special expressions
- critical spans that make the item speech-sensitive
- rule-based text-easy proxy and final score

## Included Reports

Key analysis files are under:

```text
data/speech_sensitive_selection_v3_no_codegen_filtered/
data/domain_analysis/
```

Important files:

- `domain_distribution.csv`
- `question_type_distribution.csv`
- `dataset_distribution.csv`
- `domain_subdomain_distribution.csv`
- `selection_filtered_analysis.md`
- `computer_science_addition_report.md`
- `merged_dataset_summary.csv`
- `merged_domain_subdomain_counts.csv`
- `domain_taxonomy_v2.md`

## Reproduction Scripts

Core scripts are in:

```text
data/domain_analysis/scripts/
```

The scripts cover domain analysis, v3 speech-sensitive scoring, no-codegen filtering, option recovery, final cleanup, and Computer Science source integration.

## Data Policy

This repository intentionally excludes large raw source datasets and intermediate JSONL artifacts. Only the curated final selection, summary reports, and processing scripts are tracked. Raw datasets should be downloaded separately from their original sources if full reproduction is needed.
