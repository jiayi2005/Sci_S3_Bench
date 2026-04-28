#!/usr/bin/env python3
import csv
import json
import re
import shutil
from collections import Counter
from pathlib import Path

OUT_DIR = Path('/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered')
SELECTED = OUT_DIR / 'selected_filtered.jsonl'
BACKUP = OUT_DIR / 'selected_filtered.before_edge_cleanup.jsonl'
REJECTED = OUT_DIR / 'rejected_by_edge_cleanup.jsonl'
REPORT = OUT_DIR / 'edge_cleanup_report.md'
TMP = OUT_DIR / 'selected_filtered.edge_cleanup.tmp.jsonl'

EDGE_NOISE_PAT = re.compile(
    r'<img\b|\b(?:kgAoa|minWhat|Aoa oxygen|SP02|AFBpositive|shoness|uncomfoable|veebral|aerial pH|'
    r'hypeensive|hypeension|aoic|aery|\bhea\b|\brepo\b|paicularly|impoant)\b',
    re.I,
)


def duplicate_mcqa_options(rec):
    if rec.get('question_type') != 'MCQA':
        return False
    opts = [str(o).strip().lower() for o in (rec.get('options') or [])]
    return len(opts) >= 2 and len(set(opts)) < len(opts)


def text_blob(rec):
    return ' '.join([str(rec.get('question') or ''), ' '.join(map(str, rec.get('options') or [])), str(rec.get('answer') or '')])


def reasons(rec):
    out = []
    if duplicate_mcqa_options(rec):
        out.append('duplicate_mcqa_options')
    if EDGE_NOISE_PAT.search(text_blob(rec)):
        out.append('edge_ocr_or_html_noise')
    return out


def main():
    if not BACKUP.exists():
        shutil.copy2(SELECTED, BACKUP)
    kept = []
    rejected = []
    counts = Counter()
    for line in SELECTED.open(encoding='utf-8'):
        if not line.strip():
            continue
        rec = json.loads(line)
        rs = reasons(rec)
        if rs:
            rec = dict(rec)
            rec['edge_cleanup_reasons'] = rs
            rejected.append(rec)
            counts.update(rs)
        else:
            kept.append(rec)
    with TMP.open('w', encoding='utf-8') as f:
        for rec in kept:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    shutil.move(TMP, SELECTED)
    with REJECTED.open('w', encoding='utf-8') as f:
        for rec in rejected:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    lines = []
    lines.append('# Edge Cleanup Report')
    lines.append('')
    lines.append(f'- Input backup: {BACKUP}')
    lines.append(f'- Updated selected: {SELECTED}')
    lines.append(f'- Kept: {len(kept)}')
    lines.append(f'- Rejected edge cases: {len(rejected)}')
    lines.append('')
    lines.append('| Reason | Count |')
    lines.append('|---|---:|')
    for k, v in counts.most_common():
        lines.append(f'| {k} | {v} |')
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('kept', len(kept))
    print('rejected', len(rejected))
    print('reasons', dict(counts))
    print('report', REPORT)

if __name__ == '__main__':
    main()
