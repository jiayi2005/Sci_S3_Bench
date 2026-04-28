# Quality Filter Report

- Input: /DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen/selected_around6k_no_codegen.jsonl
- Output: /DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/selected_filtered.jsonl
- Raw selected: 6128
- Kept: 5317
- Rejected: 811

## Rejection Reasons

| Reason | Count |
|---|---:|
| missing_or_empty_answer | 275 |
| low_score_too_few_critical_spans | 232 |
| image_or_figure_dependent | 169 |
| score_below_45 | 126 |
| code_related | 89 |
| very_long_sequence | 49 |
| low_score_without_exact_speech_feature | 26 |
| ocr_or_format_noise | 23 |

## Kept Domain Distribution

| Domain | Count | Share |
|---|---:|---:|
| Chemistry | 782 | 14.71% |
| Clinical Medicine | 732 | 13.77% |
| Genomics | 663 | 12.47% |
| Climate Science | 646 | 12.15% |
| Materials Science | 613 | 11.53% |
| Life Sciences | 610 | 11.47% |
| Physics | 573 | 10.78% |
| Earth Science | 562 | 10.57% |
| Astronomy | 124 | 2.33% |
| Computer Science | 12 | 0.23% |

## Notes

- Low-score formula/unit-heavy samples are retained if they still have exact speech-sensitive spans.
- Very long contiguous DNA/protein sequences are removed because they are impractical as S2S prompts, while shorter sequence/gene samples remain.
- Image/figure-dependent and empty-answer samples are removed because they cannot be evaluated from speech-only input.
