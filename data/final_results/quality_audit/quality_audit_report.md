# Final Selection Quality Audit

- Input: `/DB/rhome/heyangliu/sci_s2s_bench/data/final_results/selected_filtered.jsonl`
- Total records checked: 5,681
- Passed strict rule audit: 5,681
- Flagged records: 0
- Warning-only records: 9

## Strict Issues

| Issue | Count |
|---|---:|

## Warnings

| Warning | Count |
|---|---:|
| long_question_review | 9 |
| text_easy_proxy_not_true | 1 |

## Outputs

- `flagged_records.jsonl`: records that fail at least one strict rule.
- `warning_records.jsonl`: records that pass strict rules but need optional review.
- `issue_counts.csv`, `warning_counts.csv`, `issue_by_domain.csv`, `issue_by_dataset.csv`.

## Strict Rule Meaning

A strict pass means the record has valid required fields, valid answer/options shape, allowed dataset/question type, no obvious image dependency, no code-generation prompt, no overlong biological sequence, score >= 45, and non-empty speech-sensitive evidence.
