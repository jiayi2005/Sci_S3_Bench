# CSBench_MCQ Addition Report

- Source parquet: `/DB/rhome/heyangliu/sci_s2s_bench/data/CSBench_MCQ/data/mcq-00000-of-00001.parquet`
- Previous selected backup: `/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered/selected_filtered.before_csbench_addition.jsonl`
- Existing non-CSBench final rows: 5,275
- Existing Computer Science rows before add: 12
- CSBench raw rows: 1,336
- CSBench accepted candidates: 885
- CSBench rejected rows: 451
- CSBench selected and appended: 388
- Final selected rows: 5,663
- Final Computer Science rows: 400

## Selected CSBench Areas

| Area | Count |
|---|---:|
| Computer Network | 97 |
| Computer Organization | 97 |
| Data Structure and Algorithm | 97 |
| Operating System | 97 |

## CSBench Rejection Reasons

| Reason | Count |
|---|---:|
| weak_speech_sensitive_evidence | 222 |
| score_too_low | 214 |
| image_or_diagram_dependent | 6 |
| duplicate_options | 4 |
| ocr_or_html_noise | 3 |
| code_generation_or_code_heavy | 2 |

## Final Domain Distribution

| Domain | Count |
|---|---:|
| Chemistry | 782 |
| Clinical Medicine | 691 |
| Genomics | 663 |
| Climate Science | 645 |
| Materials Science | 613 |
| Life Sciences | 610 |
| Physics | 573 |
| Earth Science | 562 |
| Computer Science | 400 |
| Astronomy | 124 |
