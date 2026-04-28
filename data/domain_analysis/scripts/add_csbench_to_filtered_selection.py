#!/usr/bin/env python3
import csv
import hashlib
import importlib.util
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

DATA_ROOT = Path('/DB/rhome/heyangliu/sci_s2s_bench/data')
SCRIPT_DIR = DATA_ROOT / 'domain_analysis/scripts'
OUT_DIR = DATA_ROOT / 'speech_sensitive_selection_v3_no_codegen_filtered'
SELECTED = OUT_DIR / 'selected_filtered.jsonl'
BACKUP = OUT_DIR / 'selected_filtered.before_csbench_addition.jsonl'
CSBENCH_PARQUET = DATA_ROOT / 'CSBench_MCQ/data/mcq-00000-of-00001.parquet'
CSBENCH_SCORED = OUT_DIR / 'csbench_candidates_scored.jsonl'
CSBENCH_SELECTED = OUT_DIR / 'csbench_selected.jsonl'
CSBENCH_REJECTED = OUT_DIR / 'csbench_rejected.jsonl'
REPORT = OUT_DIR / 'csbench_addition_report.md'
TARGET_CS_TOTAL = 400
MAX_ADD = 450

spec = importlib.util.spec_from_file_location('build_speech_sensitive_v3', SCRIPT_DIR / 'build_speech_sensitive_v3.py')
v3 = importlib.util.module_from_spec(spec)
sys.modules['build_speech_sensitive_v3'] = v3
spec.loader.exec_module(v3)

SPACE_RE = re.compile(r'\s+')
IMAGE_DEP_RE = re.compile(r'\b(figure|image|diagram|shown below|shown above|following graph|following table|screenshot)\b', re.I)
CODE_HEAVY_RE = re.compile(r'```|<code>|</code>|\b(write|implement|complete|generate)\s+(?:a\s+)?(?:function|program|code|script)\b', re.I)
OCR_NOISE_RE = re.compile(r'<[^>]+>|&[a-z]+;|\ufffd')
COMPLEXITY_RE = re.compile(r'\b(?:O|Θ|Omega|Ω)\s*\([^) ]{1,40}\)')
BOGUS_CODE_CALL_WORDS = {
    'is', 'are', 'include', 'includes', 'included', 'incorrect', 'correct',
    'following', 'below', 'requires', 'means', 'refers', 'called', 'uses',
    'using', 'adopts', 'contains', 'consists', 'becomes', 'belongs',
}

CS_DOMAIN_TERMS = re.compile(
    r'\b(?:algorithm|algorithms|array|arrays|stack|queue|tree|graph|heap|hash|hashing|search|searching|sort|sorting|'
    r'complexity|recursion|recursive|iteration|iterative|pointer|pointers|linked list|binary tree|b-tree|red-black|'
    r'cpu|cache|register|interrupt|pipeline|instruction|addressing|memory|virtual memory|bus|i/o|input/output|'
    r'process|thread|threads|scheduling|scheduler|deadlock|semaphore|mutex|paging|segmentation|file system|'
    r'tcp|udp|ip|http|dns|osi|router|routing|subnet|ethernet|packet|frame|datagram|congestion|'
    r'data structure|operating system|computer network|computer organization)\b',
    re.I,
)


def norm_text(text):
    return SPACE_RE.sub(' ', str(text or '').strip())


def norm_question(text):
    return SPACE_RE.sub(' ', str(text or '').lower()).strip()


def make_id(row):
    raw = f"CSBench_MCQ::{row.get('ID')}::{row.get('Question')}"
    return hashlib.md5(raw.encode('utf-8', errors='ignore')).hexdigest()[:16]


def load_jsonl(path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    with path.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def reject_reason(rec):
    q = norm_text(rec.get('question'))
    opts = [norm_text(x) for x in rec.get('options') or []]
    ans = norm_text(rec.get('answer'))
    text = ' '.join([q, ans] + opts)
    if not q or not ans:
        return 'empty_question_or_answer'
    if len(opts) != 4 or any(not x for x in opts):
        return 'bad_mcqa_options'
    if len(set(x.lower() for x in opts)) < 4:
        return 'duplicate_options'
    if IMAGE_DEP_RE.search(text):
        return 'image_or_diagram_dependent'
    if CODE_HEAVY_RE.search(text):
        return 'code_generation_or_code_heavy'
    if OCR_NOISE_RE.search(text):
        return 'ocr_or_html_noise'
    if len(q.split()) > 220:
        return 'long_context_dominant'
    meta = rec.get('speech_metadata', {})
    score = meta.get('speech_sensitive_score_v3', 0)
    core = set(meta.get('core_features') or [])
    critical = meta.get('critical_spans') or []
    has_cs_term = bool(CS_DOMAIN_TERMS.search(text))
    if score < 45 and len(core) < 2 and not has_cs_term:
        return 'weak_speech_sensitive_evidence'
    if score < 35:
        return 'score_too_low'
    return ''



def clean_csbench_metadata(meta, text):
    features = meta.get('speech_sensitive_features', {})
    code_spans = features.get('code_spans') or []
    cleaned_code = []
    removed = set()
    for span in code_spans:
        s = norm_text(span)
        head = s[:-1].strip().lower() if s.endswith('(') else s.lower()
        looks_like_plain_fill_blank = s.endswith('(') and re.fullmatch(r'[A-Za-z ]{1,30}\(', s)
        # The generic v3 code regex sees English cloze text like 'is (' as a
        # function call. In CSBench MCQA these are option blanks, not code.
        if low := s.lower():
            pass
        if low.startswith('from '):
            removed.add(span)
            continue
        if s.endswith('(') and (looks_like_plain_fill_blank or head in BOGUS_CODE_CALL_WORDS):
            removed.add(span)
            continue
        cleaned_code.append(span)
    features['code_spans'] = v3.unique_keep_order(cleaned_code)
    if removed:
        meta['critical_spans'] = [x for x in (meta.get('critical_spans') or []) if x not in removed]
        features['spoken_written_mismatches'] = [
            x for x in (features.get('spoken_written_mismatches') or []) if x not in removed
        ]
    complexity = v3.unique_keep_order(COMPLEXITY_RE.findall(text))
    if complexity:
        existing = {x.lower() for x in features.get('formulas', [])}
        for expr in complexity:
            if expr.lower() not in existing:
                features.setdefault('formulas', []).append(expr)
                meta.setdefault('critical_spans', []).append(expr)
                features.setdefault('spoken_written_mismatches', []).append(expr)
    core = set(meta.get('core_features') or [])
    if not features.get('code_spans'):
        core.discard('code_expression')
    if features.get('formulas') or features.get('special_expressions'):
        core.add('formula_or_expression')
    if features.get('spoken_written_mismatches') or complexity:
        core.add('spoken_written_mismatch')
    meta['core_features'] = sorted(core)
    meta['critical_spans'] = v3.unique_keep_order(meta.get('critical_spans') or [])[:40]
    return meta


def clean_critical_spans(meta):
    clean = []
    for span in meta.get('critical_spans') or []:
        s = norm_text(span)
        low = s.lower()
        if not s:
            continue
        if s.endswith('('):
            continue
        if low in {'from the', 'of the', 'in the', 'the', 'it', 'where', 'parentheses'}:
            continue
        if low.startswith('from '):
            continue
        if re.fullmatch(r'[a-z ]{1,16}', low) and not CS_DOMAIN_TERMS.search(s):
            continue
        clean.append(s)
    meta['critical_spans'] = v3.unique_keep_order(clean)[:40]
    return meta


def recompute_score(meta, question):
    core = set(meta.get('core_features') or [])
    proxy = meta.get('text_easy_proxy') or {'is_likely_text_easy': False}
    score = 0
    reasons = []
    if 'strong_oov_min1' in core:
        score += 30
        reasons.append('strong_oov_min1')
    elif 'weak_oov_min10' in core:
        score += 15
        reasons.append('weak_oov_min10')
    if 'abbreviation' in core:
        score += 20
        reasons.append('abbreviation')
    if {'formula_or_expression', 'unit', 'gene_or_sequence', 'code_expression'} & core:
        score += 25
        reasons.append('exact_text_expression')
    if 'computer_science_term' in core:
        score += 20
        reasons.append('computer_science_domain_term')
    if 'spoken_written_mismatch' in core:
        score += 10
        reasons.append('spoken_written_mismatch')
    if proxy.get('is_likely_text_easy'):
        score += 10
        reasons.append('text_easy_proxy')
    if len(core) == 0 and len(norm_text(question)) < 220:
        score -= 20
        reasons.append('ordinary_short_text_no_professional_expression')
    score = max(0, min(100, score))
    meta['speech_sensitive_score_v3'] = score
    meta['speech_sensitive_reasons'] = reasons
    meta['speech_sensitive_level'] = 'high' if score >= 75 else 'medium' if score >= 60 else 'low' if score >= 45 else 'very_low'
    return meta

def cs_score_key(rec):
    meta = rec.get('speech_metadata', {})
    source = rec.get('source', {})
    text = ' '.join([rec.get('question', ''), ' '.join(rec.get('options') or []), rec.get('answer', '')])
    has_cs_term = 1 if CS_DOMAIN_TERMS.search(text) else 0
    return (
        -meta.get('speech_sensitive_score_v3', 0),
        -len(meta.get('core_features') or []),
        -has_cs_term,
        source.get('csbench_domain', ''),
        source.get('csbench_id', 0),
    )


def normalize_rows(df, existing_questions):
    vocab1 = v3.load_vocab(v3.VOCAB_MIN1)
    vocab10 = v3.load_vocab(v3.VOCAB_MIN10)
    rules = v3.load_abbreviation_rules(v3.ABBR_RULE_FILE)
    denylist = v3.load_denylist(v3.ABBR_DENYLIST_FILE)
    scored, rejected = [], []
    for _, row in df.iterrows():
        if norm_text(row.get('Language')) != 'English':
            continue
        ans_letter = norm_text(row.get('Answer')).upper()
        if ans_letter not in {'A', 'B', 'C', 'D'}:
            rejected.append({'source_id': int(row.get('ID')), 'reason': 'bad_answer_letter'})
            continue
        option_map = {k: norm_text(row.get(k)) for k in ['A', 'B', 'C', 'D']}
        question = norm_text(row.get('Question'))
        if norm_question(question) in existing_questions:
            rejected.append({'source_id': int(row.get('ID')), 'reason': 'duplicate_with_existing_question'})
            continue
        rec = {
            'id': make_id(row),
            'dataset': 'CSBench_MCQ',
            'domain': 'Computer Science',
            'subdomain': f"{norm_text(row.get('Domain'))}: {norm_text(row.get('SubDomain'))}",
            'question_type': 'MCQA',
            'question': question,
            'options': [option_map['A'], option_map['B'], option_map['C'], option_map['D']],
            'answer': option_map[ans_letter],
            'source': {
                'split': norm_text(row.get('Split')).lower(),
                'csbench_id': int(row.get('ID')),
                'answer_letter': ans_letter,
                'csbench_domain': norm_text(row.get('Domain')),
                'csbench_subdomain': norm_text(row.get('SubDomain')),
                'tag': norm_text(row.get('Tag')),
                'format': norm_text(row.get('Format')),
            },
        }
        meta, _ = v3.build_v3_metadata(rec, vocab1, vocab10, rules, denylist)
        text = ' '.join([rec['question'], rec['answer'], ' '.join(rec['options'])])
        meta = clean_csbench_metadata(meta, text)
        # CSBench is concept-heavy. If a question has clear CS terminology but the
        # generic scientific OOV rules under-score it, keep that evidence explicit.
        cs_terms = []
        for m in CS_DOMAIN_TERMS.finditer(text):
            term = norm_text(m.group(0))
            if term and term.lower() not in {x.lower() for x in cs_terms}:
                cs_terms.append(term)
        if cs_terms:
            feats = meta['speech_sensitive_features']
            existing_terms = {x.lower() for x in feats.get('domain_advanced_terms', [])}
            for term in cs_terms[:12]:
                if term.lower() not in existing_terms:
                    feats['domain_advanced_terms'].append(term)
                    meta['critical_spans'].append(term)
            meta['critical_spans'] = v3.unique_keep_order(meta['critical_spans'])[:40]
            core = set(meta.get('core_features') or [])
            core.add('computer_science_term')
            if 'spoken_written_mismatch' not in core and any(t.upper() == t and len(t) >= 2 for t in cs_terms):
                core.add('spoken_written_mismatch')
            meta['core_features'] = sorted(core)
        meta = clean_critical_spans(meta)
        meta = recompute_score(meta, rec['question'])
        rec['speech_metadata'] = meta
        reason = reject_reason(rec)
        if reason:
            rec['csbench_reject_reason'] = reason
            rejected.append(rec)
        else:
            scored.append(rec)
    return scored, rejected


def balanced_select(candidates, need):
    if need <= 0:
        return []
    by_domain = {}
    for rec in sorted(candidates, key=cs_score_key):
        by_domain.setdefault(rec['source']['csbench_domain'], []).append(rec)
    selected, seen_ids = [], set()
    # First pass: take an even floor from each CSBench sub-area.
    areas = sorted(by_domain)
    floor = max(1, min(need // max(1, len(areas)), 110))
    for area in areas:
        for rec in by_domain[area][:floor]:
            if rec['id'] not in seen_ids and len(selected) < need:
                selected.append(rec)
                seen_ids.add(rec['id'])
    # Fill the rest by score.
    for rec in sorted(candidates, key=cs_score_key):
        if len(selected) >= need:
            break
        if rec['id'] not in seen_ids:
            selected.append(rec)
            seen_ids.add(rec['id'])
    return selected


def write_csv(path, rows):
    fields = ['bucket', 'name', 'count']
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    if not SELECTED.exists():
        raise FileNotFoundError(SELECTED)
    if not CSBENCH_PARQUET.exists():
        raise FileNotFoundError(CSBENCH_PARQUET)
    if not BACKUP.exists():
        shutil.copy2(SELECTED, BACKUP)

    current = load_jsonl(SELECTED)
    base = [r for r in current if r.get('dataset') != 'CSBench_MCQ']
    existing_questions = {norm_question(r.get('question')) for r in base}
    existing_cs = sum(1 for r in base if r.get('domain') == 'Computer Science')
    need = min(MAX_ADD, max(0, TARGET_CS_TOTAL - existing_cs))

    df = pd.read_parquet(CSBENCH_PARQUET)
    candidates, rejected = normalize_rows(df, existing_questions)
    selected_add = balanced_select(candidates, need)
    final_rows = base + selected_add

    write_jsonl(CSBENCH_SCORED, sorted(candidates, key=cs_score_key))
    write_jsonl(CSBENCH_SELECTED, selected_add)
    write_jsonl(CSBENCH_REJECTED, rejected)
    write_jsonl(SELECTED, final_rows)

    final_domain = Counter(r.get('domain') for r in final_rows)
    final_dataset = Counter(r.get('dataset') for r in final_rows)
    cs_area = Counter(r['source']['csbench_domain'] for r in selected_add)
    reject_reasons = Counter(r.get('csbench_reject_reason') or r.get('reason') for r in rejected)
    qtypes = Counter(r.get('question_type') for r in final_rows)

    dist_rows = []
    for k, v in final_domain.most_common():
        dist_rows.append({'bucket': 'final_domain', 'name': k, 'count': v})
    for k, v in final_dataset.most_common():
        dist_rows.append({'bucket': 'final_dataset', 'name': k, 'count': v})
    for k, v in cs_area.most_common():
        dist_rows.append({'bucket': 'csbench_area_selected', 'name': k, 'count': v})
    for k, v in qtypes.most_common():
        dist_rows.append({'bucket': 'final_question_type', 'name': k, 'count': v})
    write_csv(OUT_DIR / 'csbench_addition_distribution.csv', dist_rows)

    lines = []
    lines.append('# CSBench_MCQ Addition Report')
    lines.append('')
    lines.append(f'- Source parquet: `{CSBENCH_PARQUET}`')
    lines.append(f'- Previous selected backup: `{BACKUP}`')
    lines.append(f'- Existing non-CSBench final rows: {len(base):,}')
    lines.append(f'- Existing Computer Science rows before add: {existing_cs:,}')
    lines.append(f'- CSBench raw rows: {len(df):,}')
    lines.append(f'- CSBench accepted candidates: {len(candidates):,}')
    lines.append(f'- CSBench rejected rows: {len(rejected):,}')
    lines.append(f'- CSBench selected and appended: {len(selected_add):,}')
    lines.append(f'- Final selected rows: {len(final_rows):,}')
    lines.append(f'- Final Computer Science rows: {final_domain.get("Computer Science", 0):,}')
    lines.append('')
    lines.append('## Selected CSBench Areas')
    lines.append('')
    lines.append('| Area | Count |')
    lines.append('|---|---:|')
    for k, v in cs_area.most_common():
        lines.append(f'| {k} | {v:,} |')
    lines.append('')
    lines.append('## CSBench Rejection Reasons')
    lines.append('')
    lines.append('| Reason | Count |')
    lines.append('|---|---:|')
    for k, v in reject_reasons.most_common():
        lines.append(f'| {k} | {v:,} |')
    lines.append('')
    lines.append('## Final Domain Distribution')
    lines.append('')
    lines.append('| Domain | Count |')
    lines.append('|---|---:|')
    for k, v in final_domain.most_common():
        lines.append(f'| {k} | {v:,} |')
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print('csbench_candidates', len(candidates))
    print('csbench_rejected', len(rejected))
    print('csbench_selected', len(selected_add))
    print('final_total', len(final_rows))
    print('final_computer_science', final_domain.get('Computer Science', 0))
    print('report', REPORT)


if __name__ == '__main__':
    main()
