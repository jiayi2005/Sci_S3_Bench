import csv
import importlib.util
import json
import shutil
from collections import Counter
from pathlib import Path

script_path = Path('/DB/rhome/heyangliu/sci_s2s_bench/data/domain_analysis/scripts/build_speech_sensitive_v3.py')
out_dir = Path('/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection_v3_no_codegen')
selected_path = out_dir / 'selected_around6k_no_codegen.jsonl'
backup_path = out_dir / 'selected_around6k_no_codegen.before_lab_normalization.jsonl'
tmp_path = out_dir / 'selected_around6k_no_codegen.tmp.jsonl'
report_path = out_dir / 'lab_normalization_fix_report.md'

spec = importlib.util.spec_from_file_location('build_speech_sensitive_v3', script_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

for path in [mod.VOCAB_MIN1, mod.VOCAB_MIN10, mod.ABBR_RULE_FILE, mod.ABBR_DENYLIST_FILE, selected_path]:
    mod.die_if_missing(path)

if not backup_path.exists():
    shutil.copy2(selected_path, backup_path)

vocab1 = mod.load_vocab(mod.VOCAB_MIN1)
vocab10 = mod.load_vocab(mod.VOCAB_MIN10)
abbr_rules = mod.load_abbreviation_rules(mod.ABBR_RULE_FILE)
denylist = mod.load_denylist(mod.ABBR_DENYLIST_FILE)

bad_terms = ['HgPCO2', 'Hgcalculated', 'LHCO3', 'LBUN', 'dLglucose', 'LK', 'gases']
before_bad = Counter()
after_bad = Counter()
feature_counts = Counter()

def metadata_spans(meta):
    features = meta.get('speech_sensitive_features', {})
    for key in ['gigaspeech_oov_min1_terms', 'gigaspeech_oov_min10_terms', 'domain_advanced_terms', 'units', 'formulas', 'gene_or_sequence_spans', 'code_spans', 'special_expressions']:
        for value in features.get(key, []) or []:
            yield str(value)
    for hit in features.get('abbreviations', []) or []:
        yield str(hit.get('surface', ''))
    for value in meta.get('critical_spans', []) or []:
        yield str(value)
score_counts = Counter()
review_counts = Counter()
records = []
with selected_path.open(encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        rec = json.loads(line)
        old_spans = set(metadata_spans(rec.get('speech_metadata', {})))
        for term in bad_terms:
            if term in old_spans:
                before_bad[term] += 1
        meta, core = mod.build_v3_metadata(rec, vocab1, vocab10, abbr_rules, denylist)
        rec['speech_metadata'] = meta
        new_spans = set(metadata_spans(meta))
        for term in bad_terms:
            if term in new_spans:
                after_bad[term] += 1
        feature_counts.update(meta.get('core_features', []))
        score_counts[meta['speech_sensitive_score_v3']] += 1
        for item in meta.get('pronunciation', {}).get('needs_manual_pronunciation_check', []):
            review_counts[item.get('surface', '')] += 1
        records.append(rec)

with tmp_path.open('w', encoding='utf-8') as f:
    for rec in records:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
shutil.move(tmp_path, selected_path)

def write_csv(path, fieldnames, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

total = len(records)
write_csv(out_dir / 'feature_coverage.csv', ['feature', 'selected_count', 'share'], [
    {'feature': k, 'selected_count': v, 'share': round(v / total, 4)} for k, v in feature_counts.most_common()
])
write_csv(out_dir / 'score_distribution.csv', ['score_v3', 'selected_count', 'share'], [
    {'score_v3': k, 'selected_count': v, 'share': round(v / total, 4)} for k, v in sorted(score_counts.items())
])

first = records[0]
meta = first['speech_metadata']
features = meta['speech_sensitive_features']
report = []
report.append('# Lab Normalization Fix Report')
report.append('')
report.append(f'- Rescored selected samples: {total}')
report.append(f'- Backup: {backup_path}')
report.append(f'- Updated: {selected_path}')
report.append('')
report.append('## Known fused-token cleanup')
report.append('')
report.append('| Token | Before records | After records |')
report.append('|---|---:|---:|')
for term in bad_terms:
    report.append(f'| {term} | {before_bad[term]} | {after_bad[term]} |')
report.append('')
report.append('## First Sample After Fix')
report.append('')
report.append(f'- id: {first.get("id")}')
report.append(f'- score: {meta.get("speech_sensitive_score_v3")}')
report.append(f'- core_features: {", ".join(meta.get("core_features", []))}')
report.append(f'- OOV min1 terms: {", ".join(features.get("gigaspeech_oov_min1_terms", [])[:20])}')
report.append(f'- units: {", ".join(features.get("units", [])[:30])}')
report.append(f'- formulas: {", ".join(features.get("formulas", [])[:30])}')
report.append(f'- gene_or_sequence_spans: {", ".join(features.get("gene_or_sequence_spans", [])[:30])}')
report.append(f'- manual pronunciation first 20: {", ".join([x[0] for x in review_counts.most_common(20)])}')
report_path.write_text('\n'.join(report) + '\n', encoding='utf-8')

print('rescored', total)
print('backup', backup_path)
print('selected', selected_path)
print('before_bad', dict(before_bad))
print('after_bad', dict(after_bad))
print('first_units', features['units'])
print('first_gene_spans', features['gene_or_sequence_spans'])
print('first_manual_review', [x['surface'] for x in meta['pronunciation']['needs_manual_pronunciation_check']])
