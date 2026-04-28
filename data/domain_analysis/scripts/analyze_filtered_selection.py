#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path

OUT_DIR = Path('/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen_filtered')
SELECTED = OUT_DIR / 'selected_filtered.jsonl'
REJECTED = OUT_DIR / 'rejected_by_quality_filter.jsonl'
REPORT = OUT_DIR / 'selection_filtered_analysis.md'


def load_jsonl(path):
    with path.open(encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def write_csv(path, fieldnames, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def pct(n, total):
    return f'{n / total:.2%}' if total else '0.00%'


def main():
    selected = list(load_jsonl(SELECTED))
    rejected = list(load_jsonl(REJECTED)) if REJECTED.exists() else []
    total = len(selected)
    raw_total = total + len(rejected)

    domain_counts = Counter(r.get('domain') for r in selected)
    dataset_counts = Counter(r.get('dataset') for r in selected)
    qtype_counts = Counter(r.get('question_type') for r in selected)
    domain_dataset = Counter((r.get('domain'), r.get('dataset')) for r in selected)
    domain_qtype = Counter((r.get('domain'), r.get('question_type')) for r in selected)
    dataset_qtype = Counter((r.get('dataset'), r.get('question_type')) for r in selected)
    subdomain_counts = Counter((r.get('domain'), r.get('subdomain') or 'General') for r in selected)
    feature_counts = Counter()
    score_counts = Counter()
    level_counts = Counter()
    review_count = 0
    critical_span_count = 0
    requires_exact_count = 0
    domain_feature = Counter()
    for r in selected:
        meta = r.get('speech_metadata', {})
        features = meta.get('core_features', []) or []
        feature_counts.update(features)
        for feat in features:
            domain_feature[(r.get('domain'), feat)] += 1
        score_counts[meta.get('speech_sensitive_score_v3', 0)] += 1
        level_counts[meta.get('speech_sensitive_level', 'unknown')] += 1
        review_count += len(meta.get('pronunciation', {}).get('needs_manual_pronunciation_check', []) or [])
        critical_span_count += len(meta.get('critical_spans', []) or [])
        if meta.get('requires_exact_text'):
            requires_exact_count += 1

    rejection_reasons = Counter()
    rejected_domain = Counter()
    rejected_dataset = Counter()
    for r in rejected:
        rejection_reasons.update(r.get('quality_filter_reasons', []) or [])
        rejected_domain[r.get('domain')] += 1
        rejected_dataset[r.get('dataset')] += 1

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
        for (d, ds), n in sorted(domain_dataset.items(), key=lambda x: (x[0][0] or '', -x[1], x[0][1] or ''))
    ])
    write_csv(OUT_DIR / 'domain_question_type_distribution.csv', ['domain', 'question_type', 'selected_count', 'share_within_domain', 'share_total'], [
        {'domain': d, 'question_type': qt, 'selected_count': n, 'share_within_domain': round(n / domain_counts[d], 4), 'share_total': round(n / total, 4)}
        for (d, qt), n in sorted(domain_qtype.items(), key=lambda x: (x[0][0] or '', -x[1], x[0][1] or ''))
    ])
    write_csv(OUT_DIR / 'dataset_question_type_distribution.csv', ['dataset', 'question_type', 'selected_count', 'share_within_dataset', 'share_total'], [
        {'dataset': ds, 'question_type': qt, 'selected_count': n, 'share_within_dataset': round(n / dataset_counts[ds], 4), 'share_total': round(n / total, 4)}
        for (ds, qt), n in sorted(dataset_qtype.items(), key=lambda x: (x[0][0] or '', -x[1], x[0][1] or ''))
    ])
    write_csv(OUT_DIR / 'domain_subdomain_distribution.csv', ['domain', 'subdomain', 'selected_count', 'share_within_domain', 'share_total'], [
        {'domain': d, 'subdomain': sd, 'selected_count': n, 'share_within_domain': round(n / domain_counts[d], 4), 'share_total': round(n / total, 4)}
        for (d, sd), n in sorted(subdomain_counts.items(), key=lambda x: (x[0][0] or '', -x[1], x[0][1] or ''))
    ])
    write_csv(OUT_DIR / 'feature_coverage.csv', ['feature', 'selected_count', 'share'], [
        {'feature': k, 'selected_count': v, 'share': round(v / total, 4)} for k, v in feature_counts.most_common()
    ])
    write_csv(OUT_DIR / 'domain_feature_coverage.csv', ['domain', 'feature', 'selected_count', 'share_within_domain', 'share_total'], [
        {'domain': d, 'feature': feat, 'selected_count': n, 'share_within_domain': round(n / domain_counts[d], 4), 'share_total': round(n / total, 4)}
        for (d, feat), n in sorted(domain_feature.items(), key=lambda x: (x[0][0] or '', -x[1], x[0][1] or ''))
    ])
    write_csv(OUT_DIR / 'score_distribution.csv', ['score_v3', 'selected_count', 'share'], [
        {'score_v3': k, 'selected_count': v, 'share': round(v / total, 4)} for k, v in sorted(score_counts.items())
    ])
    write_csv(OUT_DIR / 'level_distribution.csv', ['level', 'selected_count', 'share'], [
        {'level': k, 'selected_count': v, 'share': round(v / total, 4)} for k, v in level_counts.most_common()
    ])
    write_csv(OUT_DIR / 'rejection_reason_counts.csv', ['reason', 'rejected_count', 'share_of_raw'], [
        {'reason': k, 'rejected_count': v, 'share_of_raw': round(v / raw_total, 4)} for k, v in rejection_reasons.most_common()
    ])
    write_csv(OUT_DIR / 'rejected_domain_distribution.csv', ['domain', 'rejected_count', 'share_of_rejected'], [
        {'domain': k, 'rejected_count': v, 'share_of_rejected': round(v / len(rejected), 4)} for k, v in rejected_domain.most_common()
    ] if rejected else [])
    write_csv(OUT_DIR / 'rejected_dataset_distribution.csv', ['dataset', 'rejected_count', 'share_of_rejected'], [
        {'dataset': k, 'rejected_count': v, 'share_of_rejected': round(v / len(rejected), 4)} for k, v in rejected_dataset.most_common()
    ] if rejected else [])

    lines = []
    lines.append('# Filtered Selection Analysis')
    lines.append('')
    lines.append(f'- Selected file: `{SELECTED}`')
    lines.append(f'- Rejected file: `{REJECTED}`')
    lines.append(f'- Raw before quality filter: {raw_total:,}')
    lines.append(f'- Kept after quality filter: {total:,}')
    lines.append(f'- Rejected by quality filter: {len(rejected):,}')
    lines.append(f'- Requires exact text: {requires_exact_count:,} ({pct(requires_exact_count, total)})')
    lines.append(f'- Avg critical spans/sample: {critical_span_count / total:.2f}')
    lines.append(f'- Avg manual pronunciation items/sample: {review_count / total:.2f}')
    lines.append('')
    lines.append('## Domain Distribution')
    lines.append('')
    lines.append('| Domain | Count | Share |')
    lines.append('|---|---:|---:|')
    for k, v in domain_counts.most_common():
        lines.append(f'| {k} | {v:,} | {pct(v, total)} |')
    lines.append('')
    lines.append('## Question Type Distribution')
    lines.append('')
    lines.append('| Question Type | Count | Share |')
    lines.append('|---|---:|---:|')
    for k, v in qtype_counts.most_common():
        lines.append(f'| {k} | {v:,} | {pct(v, total)} |')
    lines.append('')
    lines.append('## Dataset Distribution')
    lines.append('')
    lines.append('| Dataset | Count | Share |')
    lines.append('|---|---:|---:|')
    for k, v in dataset_counts.most_common():
        lines.append(f'| {k} | {v:,} | {pct(v, total)} |')
    lines.append('')
    lines.append('## Feature Coverage')
    lines.append('')
    lines.append('| Feature | Count | Share |')
    lines.append('|---|---:|---:|')
    for k, v in feature_counts.most_common():
        lines.append(f'| {k} | {v:,} | {pct(v, total)} |')
    lines.append('')
    lines.append('## Quality Filter Rejections')
    lines.append('')
    lines.append('| Reason | Count | Share of Raw |')
    lines.append('|---|---:|---:|')
    for k, v in rejection_reasons.most_common():
        lines.append(f'| {k} | {v:,} | {pct(v, raw_total)} |')
    lines.append('')
    lines.append('## Output CSVs')
    lines.append('')
    for name in [
        'domain_distribution.csv', 'dataset_distribution.csv', 'question_type_distribution.csv',
        'domain_dataset_distribution.csv', 'domain_question_type_distribution.csv',
        'dataset_question_type_distribution.csv', 'domain_subdomain_distribution.csv',
        'feature_coverage.csv', 'domain_feature_coverage.csv', 'score_distribution.csv',
        'level_distribution.csv', 'rejection_reason_counts.csv', 'rejected_domain_distribution.csv',
        'rejected_dataset_distribution.csv'
    ]:
        lines.append(f'- `{OUT_DIR / name}`')
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('selected', total)
    print('rejected', len(rejected))
    print('report', REPORT)
    print('csv_count', 14)

if __name__ == '__main__':
    main()
