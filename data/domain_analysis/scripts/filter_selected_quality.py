#!/usr/bin/env python3
import csv
import json
import re
from collections import Counter
from pathlib import Path

DATA_ROOT = Path('/DB/rhome/heyangliu/sci_s2s_bench/data')
IN = DATA_ROOT / 'speech_sensitive_selection_v3_no_codegen/selected_around6k_no_codegen.jsonl'
OUT_DIR = DATA_ROOT / 'speech_sensitive_selection_v3_no_codegen_filtered'
OUT = OUT_DIR / 'selected_filtered.jsonl'
REJECTED = OUT_DIR / 'rejected_by_quality_filter.jsonl'
REPORT = OUT_DIR / 'quality_filter_report.md'

IMAGE_PAT = re.compile(r'\b(shown below|shown in|figure|fig\.|image|diagram|graph|table below|radiograph is shown|x-rays are shown|following image|shown\s*\.)\b', re.I)
CODE_PAT = re.compile(r'```|\b(def|class|import|return|raise)\s+\w+|\b(np|pd|torch|tf|sklearn)\.', re.I)
# Very long contiguous sequence is impractical as a speech benchmark prompt. Short gene/protein spans remain allowed.
LONG_SEQ_PAT = re.compile(r'\b[ACDEFGHIKLMNPQRSTVWY]{180,}\b|\b[ACGTUNacgtun]{180,}\b')
OCR_PAT = re.compile(r'\b(?:shoness|uncomfoable|veebral|AFBpositive|SP02|aerial pH)\b', re.I)
PLACEHOLDER_ANSWER_PAT = re.compile(r'^\s*(?:nan|none|null|n/?a|unknown|not provided)?\s*$', re.I)

# These are not automatic rejects; they are used to reject weak samples where the only evidence is noisy/generic.
GENERIC_SPANS = {
    'Numerous', 'numerous', 'Uncompensated', 'uncompensated', 'High-output', 'gases', 'Gases',
    'Following', 'Identify', 'Choose', 'Which', 'What', 'Determine'
}


def text_blob(rec):
    return ' '.join([
        str(rec.get('question') or ''),
        ' '.join(map(str, rec.get('options') or [])),
        str(rec.get('answer') or ''),
    ])


def has_missing_answer(rec):
    ans = rec.get('answer')
    if ans is None:
        return True
    if isinstance(ans, list):
        return len(ans) == 0 or all(PLACEHOLDER_ANSWER_PAT.match(str(x)) for x in ans)
    return bool(PLACEHOLDER_ANSWER_PAT.match(str(ans)))


def reject_reasons(rec):
    meta = rec.get('speech_metadata', {})
    features = meta.get('speech_sensitive_features', {})
    text = text_blob(rec)
    q = str(rec.get('question') or '')
    score = meta.get('speech_sensitive_score_v3', 0)
    core = set(meta.get('core_features', []))
    critical = [str(x) for x in meta.get('critical_spans', [])]
    reasons = []

    if rec.get('question_type') == 'Code generation' or CODE_PAT.search(text):
        reasons.append('code_related')
    if has_missing_answer(rec):
        reasons.append('missing_or_empty_answer')
    if IMAGE_PAT.search(text):
        reasons.append('image_or_figure_dependent')
    if LONG_SEQ_PAT.search(text):
        reasons.append('very_long_sequence')
    if OCR_PAT.search(text):
        reasons.append('ocr_or_format_noise')
    if not critical:
        reasons.append('no_critical_spans')
    if score < 45:
        reasons.append('score_below_45')

    # Borderline low-score samples are kept when they have real formula/unit/abbreviation evidence.
    has_exact = bool({'formula_or_expression', 'unit', 'abbreviation', 'gene_or_sequence'} & core)
    if score < 60 and not has_exact:
        reasons.append('low_score_without_exact_speech_feature')
    if score < 60 and len(critical) < 2:
        reasons.append('low_score_too_few_critical_spans')

    advanced = set(map(str, features.get('domain_advanced_terms', []) or []))
    non_generic_critical = [x for x in critical if x not in GENERIC_SPANS]
    if advanced and advanced <= GENERIC_SPANS and len(non_generic_critical) < 2:
        reasons.append('generic_span_only')

    # Long-context samples are acceptable only when speech-sensitive evidence is rich.
    if len(q.split()) > 520 and len(critical) < 4:
        reasons.append('long_context_low_speech_density')
    return reasons


def write_csv(path, fieldnames, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    kept = []
    rejected = []
    reason_counts = Counter()
    raw = 0
    for line in IN.open(encoding='utf-8'):
        if not line.strip():
            continue
        raw += 1
        rec = json.loads(line)
        reasons = reject_reasons(rec)
        if reasons:
            rec = dict(rec)
            rec['quality_filter_reasons'] = reasons
            rejected.append(rec)
            reason_counts.update(reasons)
        else:
            kept.append(rec)

    with OUT.open('w', encoding='utf-8') as f:
        for rec in kept:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    with REJECTED.open('w', encoding='utf-8') as f:
        for rec in rejected:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')

    total = len(kept)
    domain_counts = Counter(r['domain'] for r in kept)
    dataset_counts = Counter(r['dataset'] for r in kept)
    qtype_counts = Counter(r['question_type'] for r in kept)
    domain_dataset = Counter((r['domain'], r['dataset']) for r in kept)
    feature_counts = Counter()
    score_counts = Counter()
    for rec in kept:
        meta = rec['speech_metadata']
        feature_counts.update(meta.get('core_features', []))
        score_counts[meta.get('speech_sensitive_score_v3', 0)] += 1

    write_csv(OUT_DIR / 'domain_distribution.csv', ['domain', 'selected_count', 'share'], [
        {'domain': k, 'selected_count': v, 'share': round(v / total, 4)} for k, v in domain_counts.most_common()
    ])
    write_csv(OUT_DIR / 'dataset_distribution.csv', ['dataset', 'selected_count', 'share'], [
        {'dataset': k, 'selected_count': v, 'share': round(v / total, 4)} for k, v in dataset_counts.most_common()
    ])
    write_csv(OUT_DIR / 'question_type_distribution.csv', ['question_type', 'selected_count', 'share'], [
        {'question_type': k, 'selected_count': v, 'share': round(v / total, 4)} for k, v in qtype_counts.most_common()
    ])
    write_csv(OUT_DIR / 'domain_dataset_distribution.csv', ['domain', 'dataset', 'selected_count', 'share_within_domain', 'share_total'], [
        {'domain': d, 'dataset': ds, 'selected_count': n, 'share_within_domain': round(n / domain_counts[d], 4), 'share_total': round(n / total, 4)}
        for (d, ds), n in sorted(domain_dataset.items())
    ])
    write_csv(OUT_DIR / 'feature_coverage.csv', ['feature', 'selected_count', 'share'], [
        {'feature': k, 'selected_count': v, 'share': round(v / total, 4)} for k, v in feature_counts.most_common()
    ])
    write_csv(OUT_DIR / 'score_distribution.csv', ['score_v3', 'selected_count', 'share'], [
        {'score_v3': k, 'selected_count': v, 'share': round(v / total, 4)} for k, v in sorted(score_counts.items())
    ])
    write_csv(OUT_DIR / 'rejection_reason_counts.csv', ['reason', 'rejected_count'], [
        {'reason': k, 'rejected_count': v} for k, v in reason_counts.most_common()
    ])

    lines = []
    lines.append('# Quality Filter Report')
    lines.append('')
    lines.append(f'- Input: {IN}')
    lines.append(f'- Output: {OUT}')
    lines.append(f'- Raw selected: {raw}')
    lines.append(f'- Kept: {len(kept)}')
    lines.append(f'- Rejected: {len(rejected)}')
    lines.append('')
    lines.append('## Rejection Reasons')
    lines.append('')
    lines.append('| Reason | Count |')
    lines.append('|---|---:|')
    for k, v in reason_counts.most_common():
        lines.append(f'| {k} | {v} |')
    lines.append('')
    lines.append('## Kept Domain Distribution')
    lines.append('')
    lines.append('| Domain | Count | Share |')
    lines.append('|---|---:|---:|')
    for k, v in domain_counts.most_common():
        lines.append(f'| {k} | {v} | {v / total:.2%} |')
    lines.append('')
    lines.append('## Notes')
    lines.append('')
    lines.append('- Low-score formula/unit-heavy samples are retained if they still have exact speech-sensitive spans.')
    lines.append('- Very long contiguous DNA/protein sequences are removed because they are impractical as S2S prompts, while shorter sequence/gene samples remain.')
    lines.append('- Image/figure-dependent and empty-answer samples are removed because they cannot be evaluated from speech-only input.')
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print('raw', raw)
    print('kept', len(kept))
    print('rejected', len(rejected))
    print('reasons', dict(reason_counts))
    print('out', OUT)

if __name__ == '__main__':
    main()
