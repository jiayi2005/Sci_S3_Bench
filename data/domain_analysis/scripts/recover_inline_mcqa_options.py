#!/usr/bin/env python3
import csv
import json
import re
import shutil
from collections import Counter
from pathlib import Path

OUT_DIR = Path('/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered')
INOUT = OUT_DIR / 'selected_filtered.jsonl'
BACKUP = OUT_DIR / 'selected_filtered.before_option_recovery.jsonl'
TMP = OUT_DIR / 'selected_filtered.option_recovery.tmp.jsonl'
REPORT = OUT_DIR / 'option_recovery_report.md'
UNPARSED = OUT_DIR / 'option_recovery_unparsed.csv'

LABEL_RE = re.compile(r'(?<![A-Za-z0-9])([A-H])[\).:]\s*')
LETTERS = 'ABCDEFGH'


def parse_inline_options(question):
    matches = list(LABEL_RE.finditer(question or ''))
    if len(matches) < 2:
        return None, None
    best = None
    for start_idx, m in enumerate(matches):
        if m.group(1).upper() != 'A':
            continue
        seq = [m]
        expected = 1
        for nxt in matches[start_idx + 1:]:
            label = nxt.group(1).upper()
            # Ignore false positives such as the trailing F. in IMERG-F.
            if expected < len(LETTERS) and label == LETTERS[expected]:
                seq.append(nxt)
                expected += 1
        if len(seq) >= 2 and (best is None or len(seq) > len(best)):
            best = seq
    if not best:
        return None, None
    # Prefer normal MCQA with at least A-D when available, but allow A/B true-false variants.
    if len(best) < 4 and len(matches) >= 4:
        return None, None
    stem = question[:best[0].start()].strip()
    options = []
    for i, m in enumerate(best):
        end = best[i + 1].start() if i + 1 < len(best) else len(question)
        opt = question[m.end():end].strip()
        opt = re.sub(r'\s+', ' ', opt).strip(' ;')
        if not opt:
            return None, None
        options.append(opt)
    if not stem or len(options) < 2:
        return None, None
    return stem, options


def main():
    if not BACKUP.exists():
        shutil.copy2(INOUT, BACKUP)
    records = []
    stats = Counter()
    unparsed_rows = []
    for line in INOUT.open(encoding='utf-8'):
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get('question_type') == 'MCQA' and len(rec.get('options') or []) < 2:
            stats['mcqa_missing_options_before'] += 1
            stem, options = parse_inline_options(str(rec.get('question') or ''))
            if options:
                rec['question'] = stem
                rec['options'] = options
                source = rec.get('source')
                if not isinstance(source, dict):
                    source = {'original_source': source}
                source['options_recovered_from_inline_question'] = True
                rec['source'] = source
                stats['recovered'] += 1
            else:
                stats['unparsed'] += 1
                unparsed_rows.append({
                    'id': rec.get('id'),
                    'dataset': rec.get('dataset'),
                    'domain': rec.get('domain'),
                    'answer': rec.get('answer'),
                    'question_prefix': str(rec.get('question') or '')[:500],
                })
        records.append(rec)

    with TMP.open('w', encoding='utf-8') as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    shutil.move(TMP, INOUT)

    after_missing = 0
    for rec in records:
        if rec.get('question_type') == 'MCQA' and len(rec.get('options') or []) < 2:
            after_missing += 1
    stats['mcqa_missing_options_after'] = after_missing

    with UNPARSED.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'dataset', 'domain', 'answer', 'question_prefix'])
        writer.writeheader()
        writer.writerows(unparsed_rows)

    lines = []
    lines.append('# Inline MCQA Option Recovery Report')
    lines.append('')
    lines.append(f'- Updated file: {INOUT}')
    lines.append(f'- Backup before recovery: {BACKUP}')
    lines.append(f'- MCQA missing options before: {stats["mcqa_missing_options_before"]}')
    lines.append(f'- Recovered from inline A/B/C/D labels: {stats["recovered"]}')
    lines.append(f'- Still missing options after: {stats["mcqa_missing_options_after"]}')
    lines.append(f'- Unparsed CSV: {UNPARSED}')
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print(dict(stats))
    print('report', REPORT)
    print('backup', BACKUP)

if __name__ == '__main__':
    main()
