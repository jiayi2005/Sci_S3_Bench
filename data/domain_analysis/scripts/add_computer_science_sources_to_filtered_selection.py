#!/usr/bin/env python3
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
BACKUP = OUT_DIR / 'selected_filtered.before_computer_science_sources.jsonl'
CSBENCH_PARQUET = DATA_ROOT / 'CSBench_MCQ/data/mcq-00000-of-00001.parquet'
CYBER_JSONL = DATA_ROOT / 'Cybersecurity_QA/cybersecurity_qa.jsonl'
USE_CYBERSECURITY_QA = False
REPORT = OUT_DIR / 'computer_science_addition_report.md'
CSBENCH_SELECTED = OUT_DIR / 'csbench_selected.jsonl'
CYBER_SCORED = OUT_DIR / 'cybersecurity_candidates_scored.jsonl'
CYBER_SELECTED = OUT_DIR / 'cybersecurity_selected.jsonl'
COMBINED_SELECTED = OUT_DIR / 'computer_science_selected_sources.jsonl'
TARGET_CS_TOTAL = 446
TARGET_CSBENCH = 434

spec_v3 = importlib.util.spec_from_file_location('build_speech_sensitive_v3', SCRIPT_DIR / 'build_speech_sensitive_v3.py')
v3 = importlib.util.module_from_spec(spec_v3)
sys.modules['build_speech_sensitive_v3'] = v3
spec_v3.loader.exec_module(v3)

spec_cs = importlib.util.spec_from_file_location('add_csbench', SCRIPT_DIR / 'add_csbench_to_filtered_selection.py')
csmod = importlib.util.module_from_spec(spec_cs)
sys.modules['add_csbench'] = csmod
spec_cs.loader.exec_module(csmod)

SPACE_RE = re.compile(r'\s+')
CYBER_TERM_RE = re.compile(
    r'\b(?:cybersecurity|malware|ransomware|phishing|spear phishing|vulnerability|vulnerabilities|exploit|exploitation|'
    r'firewall|botnet|rootkit|trojan|worm|spyware|adware|keylogger|backdoor|zero-day|zero day|'
    r'encryption|cryptography|authentication|authorization|multifactor|multi-factor|password|hashing|salt|'
    r'spoofing|sniffing|packet sniffing|sql injection|cross-site scripting|xss|csrf|ddos|dos|mitm|'
    r'tls|ssl|vpn|ids|ips|siem|cve|cwe|nist|owasp|aes|rsa|sha|md5|dns|dhcp|tcp|udp|ip|http|https|ssh|'
    r'access control|penetration testing|incident response|threat model|attack surface|privilege escalation)\b',
    re.I,
)
IMAGE_DEP_RE = re.compile(r'\b(figure|image|diagram|shown below|shown above|following graph|screenshot)\b', re.I)
HTML_RE = re.compile(r'<[^>]+>|&[a-z]+;|\ufffd')
CS_ACRONYM_RE = re.compile(r'\b[A-Z]{2,}[A-Z0-9]*(?:/[A-Z0-9]+)*(?:-[A-Z0-9]+)*(?:s)?\b|\b[A-Z][a-zA-Z]+(?:CI|CD|SQL|XSS|API|HTTP|TLS|SSL)\b')
ROMAN_RE = re.compile(r'^(?:I|II|III|IV|V|VI|VII|VIII|IX|X)$')


def norm_text(x):
    return SPACE_RE.sub(' ', str(x or '').strip())


def norm_question(x):
    return SPACE_RE.sub(' ', str(x or '').lower()).strip()


def load_jsonl(path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    with path.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def make_cyber_id(q, a, idx):
    return hashlib.md5(f'Cybersecurity_QA::{idx}::{q}::{a}'.encode('utf-8', errors='ignore')).hexdigest()[:16]


def score_key(rec):
    meta = rec.get('speech_metadata', {})
    return (
        -meta.get('speech_sensitive_score_v3', 0),
        -len(meta.get('core_features') or []),
        -len(meta.get('critical_spans') or []),
        rec.get('dataset', ''),
        rec.get('id', ''),
    )


def is_score40_acceptable(rec):
    meta = rec.get('speech_metadata', {})
    if meta.get('speech_sensitive_score_v3', 0) != 40:
        return False
    core = set(meta.get('core_features') or [])
    spans = meta.get('critical_spans') or []
    if 'computer_science_term' not in core or not spans:
        return False
    q = (rec.get('question') or '').lower()
    if any(x in q for x in ['shown below', 'shown above', 'see figure', 'see image', 'as shown']):
        return False
    # Prefer score-40 items whose difficulty still comes from CS exact terms,
    # symbols, acronyms, or canonical technical concepts rather than pure English.
    joined = ' '.join(spans)
    if re.search(r'[A-Z]{2,}|\d|/|_|-|\[|\]|\(|\)|≤|≥|→', joined):
        return True
    technical = re.compile(r'\b(binary tree|tree|graph|stack|queue|array|pointer|paging|semaphore|deadlock|interrupt|cache|memory|cpu|i/o|instruction|addressing|pipeline|subnet|ethernet|process|thread|scheduling|algorithm|sorting|hashing|file system|operating system|data structure)\b', re.I)
    return bool(technical.search(joined))


def select_csbench(candidates, n):
    high = [r for r in candidates if r.get('speech_metadata', {}).get('speech_sensitive_score_v3', 0) >= 45]
    by_area = {}
    for rec in sorted(high, key=score_key):
        by_area.setdefault(rec['source']['csbench_domain'], []).append(rec)
    selected, seen = [], set()
    # Keep subarea diversity without forcing low-score fill-ins.
    floor = max(1, n // max(1, len(by_area)))
    for area in sorted(by_area):
        for rec in by_area[area][:floor]:
            if len(selected) >= n:
                break
            selected.append(rec); seen.add(rec['id'])
    for rec in sorted(high, key=score_key):
        if len(selected) >= n:
            break
        if rec['id'] not in seen:
            selected.append(rec); seen.add(rec['id'])
    return selected



def augment_computer_science_metadata(rec, regexes):
    meta = rec.get('speech_metadata') or {}
    feats = meta.setdefault('speech_sensitive_features', {})
    text = ' '.join([rec.get('question', ''), rec.get('answer', ''), ' '.join(rec.get('options') or [])])
    terms = []
    for regex in regexes:
        for m in regex.finditer(text):
            term = norm_text(m.group(0))
            if term and term.lower() not in {x.lower() for x in terms}:
                terms.append(term)
    for m in CS_ACRONYM_RE.finditer(text):
        term = norm_text(m.group(0))
        base = term[:-1] if term.endswith('s') and len(term) > 3 else term
        if ROMAN_RE.fullmatch(base) or base in {'TRUE', 'FALSE'}:
            continue
        if len(base) < 2:
            continue
        if term and term.lower() not in {x.lower() for x in terms}:
            terms.append(term)
    if terms:
        existing = {x.lower() for x in feats.get('domain_advanced_terms', [])}
        for term in terms[:20]:
            if term.lower() not in existing:
                feats.setdefault('domain_advanced_terms', []).append(term)
            if term.lower() not in {x.lower() for x in meta.get('critical_spans', [])}:
                meta.setdefault('critical_spans', []).append(term)
            if (term.upper() == term or '/' in term or '-' in term) and term.lower() not in {x.lower() for x in feats.get('spoken_written_mismatches', [])}:
                feats.setdefault('spoken_written_mismatches', []).append(term)
        core = set(meta.get('core_features') or [])
        core.add('computer_science_term')
        if any(t.upper() == t or '/' in t or '-' in t for t in terms):
            core.add('spoken_written_mismatch')
        meta['core_features'] = sorted(core)
    meta = csmod.clean_critical_spans(meta)
    meta = csmod.recompute_score(meta, rec.get('question', ''))
    rec['speech_metadata'] = meta
    return rec

def build_cybersecurity(existing_questions):
    vocab1 = v3.load_vocab(v3.VOCAB_MIN1)
    vocab10 = v3.load_vocab(v3.VOCAB_MIN10)
    rules = v3.load_abbreviation_rules(v3.ABBR_RULE_FILE)
    denylist = v3.load_denylist(v3.ABBR_DENYLIST_FILE)
    rows, rejected = [], []
    seen_q = set(existing_questions)
    for idx, item in enumerate(load_jsonl(CYBER_JSONL), 1):
        q = norm_text(item.get('instruction') or item.get('question'))
        inp = norm_text(item.get('input'))
        if inp:
            q = norm_text(q + ' ' + inp)
        a = norm_text(item.get('output') or item.get('answer'))
        nq = norm_question(q)
        if not q or not a:
            rejected.append({'source_id': idx, 'reason': 'empty_question_or_answer'}); continue
        if nq in seen_q:
            rejected.append({'source_id': idx, 'reason': 'duplicate_question'}); continue
        seen_q.add(nq)
        text = f'{q} {a}'
        if IMAGE_DEP_RE.search(text):
            rejected.append({'source_id': idx, 'reason': 'image_dependent'}); continue
        if HTML_RE.search(text):
            rejected.append({'source_id': idx, 'reason': 'html_or_ocr_noise'}); continue
        if len(q.split()) > 90:
            rejected.append({'source_id': idx, 'reason': 'question_too_long'}); continue
        if len(a.split()) > 90:
            rejected.append({'source_id': idx, 'reason': 'answer_too_long'}); continue
        rec = {
            'id': make_cyber_id(q, a, idx),
            'dataset': 'Cybersecurity_QA',
            'domain': 'Computer Science',
            'subdomain': 'Cybersecurity',
            'question_type': 'Open-ended',
            'question': q,
            'options': [],
            'answer': a,
            'source': {'split': 'all', 'source_id': idx},
        }
        meta, _ = v3.build_v3_metadata(rec, vocab1, vocab10, rules, denylist)
        cyber_terms = []
        for m in CYBER_TERM_RE.finditer(text):
            t = norm_text(m.group(0))
            if t and t.lower() not in {x.lower() for x in cyber_terms}:
                cyber_terms.append(t)
        if cyber_terms:
            feats = meta['speech_sensitive_features']
            existing = {x.lower() for x in feats.get('domain_advanced_terms', [])}
            for t in cyber_terms[:15]:
                if t.lower() not in existing:
                    feats['domain_advanced_terms'].append(t)
                    meta['critical_spans'].append(t)
            core = set(meta.get('core_features') or [])
            core.add('computer_science_term')
            if any(re.fullmatch(r'[A-Z0-9-]{2,}', t) for t in cyber_terms):
                core.add('spoken_written_mismatch')
            meta['core_features'] = sorted(core)
        meta = csmod.clean_critical_spans(meta)
        meta = csmod.recompute_score(meta, rec['question'])
        rec['speech_metadata'] = meta
        score = meta.get('speech_sensitive_score_v3', 0)
        core_count = len(meta.get('core_features') or [])
        if not cyber_terms and score < 45:
            rec['cybersecurity_reject_reason'] = 'weak_cybersecurity_evidence'
            rejected.append(rec); continue
        if score < 45 and core_count < 2:
            rec['cybersecurity_reject_reason'] = 'score_too_low'
            rejected.append(rec); continue
        rows.append(rec)
    return sorted(rows, key=score_key), rejected


def main():
    if not BACKUP.exists():
        shutil.copy2(SELECTED, BACKUP)
    current = load_jsonl(SELECTED)
    base = [r for r in current if r.get('dataset') not in {'CSBench_MCQ', 'Cybersecurity_QA'}]
    existing_q = {norm_question(r.get('question')) for r in base}
    base_cs = sum(1 for r in base if r.get('domain') == 'Computer Science')
    target_new_cs = max(0, TARGET_CS_TOTAL - base_cs)

    df = pd.read_parquet(CSBENCH_PARQUET)
    csbench_candidates, csbench_rejected = csmod.normalize_rows(df, existing_q)
    csbench_candidates = [augment_computer_science_metadata(r, [csmod.CS_DOMAIN_TERMS]) for r in csbench_candidates]
    if USE_CYBERSECURITY_QA:
        cyber_candidates, cyber_rejected = build_cybersecurity(existing_q | {norm_question(r.get('question')) for r in csbench_candidates})
        cyber_candidates = [augment_computer_science_metadata(r, [CYBER_TERM_RE]) for r in cyber_candidates]
    else:
        cyber_candidates, cyber_rejected = [], []

    cyber_target = max(0, target_new_cs - TARGET_CSBENCH) if USE_CYBERSECURITY_QA else 0
    cyber_selected = cyber_candidates[:cyber_target]
    remaining = target_new_cs - len(cyber_selected)
    csbench_selected = select_csbench(csbench_candidates, remaining)
    # If cybersecurity is short, fill from CSBench high-score candidates.
    if len(csbench_selected) + len(cyber_selected) < target_new_cs:
        seen = {r['id'] for r in csbench_selected}
        for rec in sorted(csbench_candidates, key=score_key):
            if len(csbench_selected) + len(cyber_selected) >= target_new_cs:
                break
            if rec['id'] not in seen and rec['speech_metadata']['speech_sensitive_score_v3'] >= 45:
                csbench_selected.append(rec); seen.add(rec['id'])

    final_rows = base + csbench_selected + cyber_selected
    write_jsonl(CSBENCH_SELECTED, csbench_selected)
    write_jsonl(CYBER_SCORED, cyber_candidates)
    write_jsonl(CYBER_SELECTED, cyber_selected)
    write_jsonl(COMBINED_SELECTED, csbench_selected + cyber_selected)
    write_jsonl(OUT_DIR / 'cybersecurity_rejected.jsonl', cyber_rejected)
    write_jsonl(SELECTED, final_rows)

    dom = Counter(r.get('domain') for r in final_rows)
    ds = Counter(r.get('dataset') for r in final_rows)
    cs_ds = Counter(r.get('dataset') for r in final_rows if r.get('domain') == 'Computer Science')
    qt = Counter(r.get('question_type') for r in final_rows)
    area = Counter(r['source'].get('csbench_domain') for r in csbench_selected)
    cyber_rej = Counter(r.get('cybersecurity_reject_reason') or r.get('reason') for r in cyber_rejected)
    csbench_scores = Counter(r['speech_metadata']['speech_sensitive_score_v3'] for r in csbench_selected)
    cyber_scores = Counter(r['speech_metadata']['speech_sensitive_score_v3'] for r in cyber_selected)

    lines = []
    lines.append('# Computer Science Source Addition Report')
    lines.append('')
    lines.append(f'- Final selected file: `{SELECTED}`')
    lines.append(f'- Backup before this rebuild: `{BACKUP}`')
    lines.append(f'- Base rows excluding CS added sources: {len(base):,}')
    lines.append(f'- Existing non-added Computer Science rows: {base_cs:,}')
    lines.append(f'- CSBench candidates: {len(csbench_candidates):,}; selected: {len(csbench_selected):,}')
    lines.append(f'- Cybersecurity_QA used: {USE_CYBERSECURITY_QA}')
    lines.append(f'- Cybersecurity_QA candidates: {len(cyber_candidates):,}; selected: {len(cyber_selected):,}')
    lines.append(f'- Final total rows: {len(final_rows):,}')
    lines.append(f'- Final Computer Science rows: {dom.get("Computer Science", 0):,}')
    lines.append('')
    lines.append('## Computer Science Dataset Mix')
    lines.append('')
    lines.append('| Dataset | Count |')
    lines.append('|---|---:|')
    for name in ['CSBench_MCQ', 'ATLAS', 'Cybersecurity_QA']:
        lines.append(f'| {name} | {cs_ds.get(name, 0):,} |')
    lines.append('')
    lines.append('## CSBench Area Mix')
    lines.append('')
    lines.append('| Area | Count |')
    lines.append('|---|---:|')
    for k, v in area.most_common():
        lines.append(f'| {k} | {v:,} |')
    lines.append('')
    lines.append('## Final Domain Distribution')
    lines.append('')
    lines.append('| Domain | Count |')
    lines.append('|---|---:|')
    for k, v in dom.most_common():
        lines.append(f'| {k} | {v:,} |')
    lines.append('')
    lines.append('## Final Question Type Distribution')
    lines.append('')
    lines.append('| Question Type | Count |')
    lines.append('|---|---:|')
    for k, v in qt.most_common():
        lines.append(f'| {k} | {v:,} |')
    lines.append('')
    lines.append('## Score Distribution')
    lines.append('')
    lines.append(f'- CSBench selected score counts: {dict(sorted(csbench_scores.items()))}')
    lines.append(f'- Cybersecurity selected score counts: {dict(sorted(cyber_scores.items()))}')
    lines.append(f'- Cybersecurity rejected reasons: {dict(cyber_rej.most_common())}')
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print('final_total', len(final_rows))
    print('final_computer_science', dom.get('Computer Science', 0))
    print('csbench_selected', len(csbench_selected))
    print('cybersecurity_selected', len(cyber_selected))
    print('report', REPORT)


if __name__ == '__main__':
    main()
