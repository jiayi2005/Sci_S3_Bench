import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


spec = importlib.util.spec_from_file_location("domain_v2", "/tmp/build_domain_analysis_v2.py")
domain_v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(domain_v2)

OLD_ROOT = Path("/tmp/sci_s2s_bench_datasets")
NEW_ROOT = Path("/tmp/sci_s2s_bench_datasets_v2")
OUT_DIR = Path("/tmp/sci_s2s_bench_speech_sensitive_selection_v2")

TARGET_TOTAL = 5500
DOMAIN_CAP = 990
QUOTAS = {
    "Clinical Medicine": 700,
    "Chemistry": 700,
    "Materials Science": 600,
    "Physics": 600,
    "Life Sciences": 550,
    "Genomics": 550,
    "Climate Science": 550,
    "Earth Science": 450,
    "Astronomy": 400,
    "Computer Science": 400,
}


def stable_id(*parts):
    raw = "||".join(str(p) for p in parts)
    return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]


def safe_text(value):
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    if isinstance(value, (list, tuple)):
        return " ".join(safe_text(v) for v in value)
    return str(value)


def normalize_question(text):
    return re.sub(r"\s+", " ", safe_text(text).lower()).strip()


FORMULA_RE = re.compile(
    r"(\\\(|\\\[|\\ce\{|\\mathrm\{|\\frac|\\sum|\\alpha|\\beta|\\omega|[A-Z][a-z]?\d+(?:[A-Z][a-z]?\d*)+|[A-Z][a-z]?\{?\^\{?[-+]?\d|[ACGTUN]{12,}|[A-Z]{8,}|[A-Za-z0-9@+\-\[\]\(\)=#$\\/]{8,})"
)
ABBR_RE = re.compile(r"\b(?:[A-Z][A-Z0-9+\-]{1,}|[A-Z]\.[A-Z]\.|[a-z]RNA|sgRNA|mRNA|tRNA|pH|Ni-NTA|SDS-PAGE)\b")
UNIT_RE = re.compile(r"\b\d+(?:\.\d+)?\s?(?:°C|K|W\s?m[−-]?\d|mol|mmHg|mg|kg|mL|μL|µL|kJ|Hz|GHz|nm|cm|m/s|bp|kb|Da|kDa|ppm)\b")
SPECIAL_RE = re.compile(r"[μµαβγδΩω×÷±−→←↔≤≥≈≠∞∑∫√°¹²³₀-₉^_{}\\]|(?:\b\d+[A-Z][a-z]?\b)")
CODE_RE = re.compile(r"(```|def\s+\w+\(|import\s+\w+|class\s+\w+|np\.|pd\.|torch\.|return\s+|unittest)")
TERM_RE = re.compile(
    r"\b(?:NMR|DNA|RNA|protein|gene|genome|CRISPR|allele|SNP|enzyme|catalyst|molecule|spectr|polymer|quantum|Hamiltonian|Lagrangian|thermodynamic|geophys|climat|radiometer|hydrolog|seism|pathology|pharmacology|microbiology|diagnos|syndrome|anatomy|physiology|algorithm|function|library|API)\b",
    re.I,
)


def extract_spans(text):
    spans = []
    for regex in [UNIT_RE, ABBR_RE, FORMULA_RE, SPECIAL_RE, CODE_RE]:
        for m in regex.finditer(text):
            s = m.group(0).strip()
            if 1 < len(s) <= 80 and s not in spans:
                spans.append(s)
            if len(spans) >= 20:
                return spans
    return spans


def pronunciation_hints(spans):
    hints = []
    for s in spans[:20]:
        low = s.lower()
        hint = None
        if s == "1H":
            hint = "proton NMR / one-H"
        elif s == "13C":
            hint = "carbon-thirteen"
        elif "nmr" in low:
            hint = "N M R"
        elif "dna" in low:
            hint = "D N A"
        elif "rna" in low:
            hint = "R N A"
        elif "μ" in s or "µ" in s:
            hint = s.replace("μ", "micro").replace("µ", "micro")
        elif "°C" in s:
            hint = s.replace("°C", " degrees Celsius")
        elif re.search(r"[A-Z][a-z]?\d", s):
            hint = "spell exact formula"
        elif CODE_RE.search(s):
            hint = "read as code, preserve punctuation"
        if hint:
            hints.append({"span": s, "hint": hint})
    return hints


def score_sample(question, options, answer, domain, question_type):
    text = " ".join([safe_text(question), safe_text(options), safe_text(answer)])
    reasons = []
    score = 0.0
    if FORMULA_RE.search(text) or UNIT_RE.search(text) or CODE_RE.search(text):
        score += 2.0
        reasons.append("requires_exact_text")
    if ABBR_RE.search(text):
        score += 1.5
        reasons.append("contains_abbreviation")
    if SPECIAL_RE.search(text):
        score += 1.5
        reasons.append("contains_special_symbol")
    term_hits = len(TERM_RE.findall(text))
    long_terms = len(re.findall(r"\b[a-zA-Z]{11,}\b", text))
    if term_hits >= 2 or long_terms >= 4:
        score += 1.0
        reasons.append("high_terminology_density")
    if re.search(r"\b\d+[A-Za-z]|[A-Za-z]\d+|\{|\}|\^|_|/|\\|[+\-=#@]", text) or domain in {"Computer Science", "Chemistry", "Genomics"}:
        score += 1.0
        reasons.append("spoken_form_differs")
    if len(text) < 180 and len(reasons) == 0:
        score -= 1.0
        reasons.append("ordinary_short_text")
    if len(text) > 2500 and len(reasons) < 2:
        score -= 1.0
        reasons.append("long_context_not_speech_specific")
    score = max(0.0, min(5.0, score))
    spans = extract_spans(text)
    level = "high" if score >= 4 else "medium" if score >= 3 else "low" if score >= 2 else "very_low"
    return {
        "speech_sensitive_score": round(score, 2),
        "speech_sensitive_level": level,
        "speech_sensitive_reasons": reasons,
        "critical_spans": spans,
        "pronunciation_hints": pronunciation_hints(spans),
        "requires_exact_text": any(r in reasons for r in ["requires_exact_text", "contains_special_symbol"]),
    }


def make_record(dataset, domain, subdomain, question_type, question, options=None, answer=None, source=None):
    options = options or []
    source = source or {}
    rid = stable_id(dataset, domain, subdomain, question_type, question, answer)
    meta = score_sample(question, options, answer, domain, question_type)
    return {
        "id": rid,
        "dataset": dataset,
        "domain": domain,
        "subdomain": domain_v2.clean_name(subdomain, "General"),
        "question_type": question_type,
        "question": safe_text(question),
        "options": [safe_text(o) for o in options],
        "answer": safe_text(answer),
        "source": source,
        "speech_metadata": meta,
    }


def iter_science_s2s():
    root = OLD_ROOT / "Science_S2S_Bench"
    specs = [
        ("Astro-QA", root / "Astronomy/Astro-QA/json", "Astronomy", "Astronomy General", None),
        ("ChemBench", root / "Chemistry/ChemBench/json", "Chemistry", None, domain_v2.chembench_subdomain),
        ("ClimaQA_gold", root / "Earth_Science/ClimaQA/climaqa_gold/json", "Climate Science", "Climate Science", None),
        ("ClimaQA_silver", root / "Earth_Science/ClimaQA/climaqa_silver/json", "Climate Science", "Climate Science", None),
        ("BioASQ", root / "Life_Sciences/BioASQ/json", "Life Sciences", "Biomedical QA", None),
        ("Genome-Bench", root / "Life_Sciences/Genome-Bench/json", "Genomics", "Genome Protocol QA", None),
        ("MedXpertQA", root / "Life_Sciences/MedXpertQA/json", "Clinical Medicine", "Clinical Specialist QA", None),
        ("Lab-Bench", root / "Life_Sciences/lab-bench/json", "Life Sciences", "Biomedical Laboratory", None),
        ("MaScQA", root / "Material_Science/MaScQA/json", "Materials Science", "Materials Science General", None),
        ("PHYBench", root / "Physics/PHYBench/json", "Physics", "Physics General", None),
        ("UGPhysics", root / "Physics/UGPhysics/json", "Physics", "Physics General", None),
    ]
    for dataset, directory, domain, fixed_sub, sub_fn in specs:
        for path in sorted(directory.glob("*.json")):
            qtype = domain_v2.form_from_filename(path)
            for i, row in enumerate(domain_v2.load_json_list(path)):
                sub = sub_fn(row) if sub_fn else fixed_sub
                yield make_record(dataset, domain, sub, qtype, row.get("Question"), row.get("Options") or [], row.get("Answer"), {"path": str(path), "index": i})

    for path in sorted((root / "General_Science/SciKnowEval/json").glob("*.json")):
        for i, row in enumerate(domain_v2.load_json_list(path)):
            app = row.get("Appendix") or {}
            details = app.get("details") or {}
            domain = domain_v2.sciknow_domain(app.get("domain"))
            sub = domain_v2.pretty_task(details.get("subtask") or details.get("task") or "SciKnowEval General")
            yield make_record("SciKnowEval", domain, sub, "MCQA", row.get("Question"), row.get("Options") or [], row.get("Answer"), {"path": str(path), "index": i})


def iter_other_existing():
    for i, row in enumerate(domain_v2.load_json_list(OLD_ROOT / "QCBench/QCBench.json")):
        yield make_record("QCBench", "Chemistry", domain_v2.qchem_subdomain(row.get("class")), "Open numeric/short answer", row.get("question"), [], row.get("answer"), {"index": i, "unit": row.get("unit")})

    with domain_v2.zipfile.ZipFile(OLD_ROOT / "GeneTuring/SupplementaryTable1.csv.zip") as zf:
        with zf.open("SupplementaryTable1.csv") as f:
            df = pd.read_csv(f, encoding="latin1").drop_duplicates(subset=["Module", "Question", "Goldstandard"])
    for i, row in df.iterrows():
        yield make_record("GeneTuring", "Genomics", row["Module"], "Open generation/extraction", row["Question"], [], row["Goldstandard"], {"row": int(i)})

    for path in sorted((OLD_ROOT / "ATLAS").glob("*.jsonl")):
        for i, row in enumerate(domain_v2.read_jsonl(path)):
            domain = domain_v2.atlas_domain(row.get("subject_name"), row.get("sub_subject_name"))
            if domain == "Mathematics":
                continue
            ans = row.get("refined_standard_answer") or row.get("answer_ideas") or ""
            yield make_record("ATLAS", domain, row.get("sub_subject_name"), "Open-ended", row.get("question"), [], ans, {"path": str(path), "index": i})

    for part in ["Earth-Iron", "Earth-Silver"]:
        for path in sorted((OLD_ROOT / "EarthSE" / part / "data").glob("*.parquet")):
            df = pd.read_parquet(path)
            qtype = domain_v2.form_from_filename(path)
            for i, row in df.iterrows():
                domain = domain_v2.earthse_domain(row.get("subject"), row.get("sub_discipline"))
                sub = row.get("sub_discipline") or row.get("subject")
                yield make_record(f"EarthSE_{part}", domain, sub, qtype, row.get("question"), [], row.get("answer"), {"path": str(path), "idx": safe_text(row.get("idx"))})
    for path in sorted((OLD_ROOT / "EarthSE/Earth-Gold/data").glob("*.parquet")):
        df = pd.read_parquet(path)
        for i, row in df.iterrows():
            domain = domain_v2.earthse_domain(sphere=row.get("sphere"))
            q = " ".join([safe_text(row.get("user_0")), safe_text(row.get("user_1"))])
            ans = " ".join([safe_text(row.get("assistant_0")), safe_text(row.get("assistant_1"))])
            yield make_record("EarthSE_Earth-Gold", domain, row.get("sphere"), "Open-ended dialogue", q, [], ans, {"path": str(path), "idx": safe_text(row.get("idx"))})


def iter_new():
    for path in sorted((NEW_ROOT / "MedMCQA/data").glob("*.parquet")):
        df = pd.read_parquet(path)
        split = path.name.split("-")[0]
        for i, row in df.iterrows():
            opts = [row.get("opa"), row.get("opb"), row.get("opc"), row.get("opd")]
            cop = row.get("cop")
            ans = opts[int(cop)] if isinstance(cop, (int, float)) and not math.isnan(cop) and 0 <= int(cop) < len(opts) else ""
            subject = domain_v2.clean_name(row.get("subject_name"), "Medicine General")
            topic = domain_v2.clean_name(row.get("topic_name"), "")
            sub = f"{subject}: {topic}" if topic else subject
            yield make_record("MedMCQA", "Clinical Medicine", sub, "MCQA", row.get("question"), opts, ans, {"split": split, "id": row.get("id")})

    for path in sorted((NEW_ROOT / "MedQA_USMLE/data").glob("*.parquet")):
        df = pd.read_parquet(path)
        split = path.name.split("-")[0]
        for _, row in df.iterrows():
            opts = [row.get(f"ending{i}") for i in range(4)]
            label = int(row.get("label"))
            yield make_record("MedQA_USMLE", "Clinical Medicine", "Medical Exam QA", "MCQA", row.get("sent1"), opts, opts[label], {"split": split, "id": row.get("id")})

    for path in sorted((NEW_ROOT / "PubMedQA/data").glob("*.parquet")):
        df = pd.read_parquet(path)
        split = path.name.split("-")[0]
        for _, row in df.iterrows():
            data = row.get("data") or {}
            opts = list((data.get("Options") or {}).values())
            question = data.get("Question")
            context = " ".join(safe_text(x) for x in data.get("Context", []))
            yield make_record("PubMedQA", "Clinical Medicine", "Biomedical Literature QA", "MCQA", f"{question} {context}", opts, data.get("Correct Answer"), {"split": split, "id": row.get("id")})

    path = NEW_ROOT / "BigCodeBench/data/v0.1.4-00000-of-00001.parquet"
    if not path.exists():
        path = NEW_ROOT / "BigCodeBench/data/train-00000-of-00001.parquet"
    df = pd.read_parquet(path)
    for _, row in df.iterrows():
        yield make_record("BigCodeBench", "Computer Science", "Programming", "Code generation", row.get("instruct_prompt") or row.get("complete_prompt"), [], row.get("canonical_solution"), {"task_id": row.get("task_id")})

    for path in sorted((NEW_ROOT / "SciCode").glob("problems_*.jsonl")):
        for row in domain_v2.read_jsonl(path):
            q = " ".join([safe_text(row.get("problem_background_main")), safe_text(row.get("problem_description_main")), safe_text(row.get("problem_io"))])
            yield make_record("SciCode", "Computer Science", "Scientific Computing", "Code generation", q, [], row.get("general_solution"), {"problem_id": row.get("problem_id"), "path": str(path)})


def iter_all_records():
    yield from iter_science_s2s()
    yield from iter_other_existing()
    yield from iter_new()


def is_candidate(record, relaxed=False):
    score = record["speech_metadata"]["speech_sensitive_score"]
    reasons = [r for r in record["speech_metadata"]["speech_sensitive_reasons"] if not r.startswith("ordinary") and not r.startswith("long_context")]
    if relaxed:
        return score >= 2.0
    return score >= 3.0 or (score >= 2.0 and len(reasons) >= 2)


def write_schema():
    text = """# Speech Metadata Schema v2

Each JSONL record contains the normalized question-answer sample plus `speech_metadata`.

- `speech_sensitive_score`: rule score from 0 to 5.
- `speech_sensitive_level`: `high`, `medium`, `low`, or `very_low`.
- `speech_sensitive_reasons`: matched speech-sensitive feature labels.
- `critical_spans`: exact text spans likely to be degraded by speech input.
- `pronunciation_hints`: optional spoken-form hints for critical spans.
- `requires_exact_text`: true when exact symbols, formulae, code, units, or notation are central.

Selection uses the fixed 10-domain taxonomy in `domain_analysis/domain_taxonomy_v2.md`, target size 5,500, and per-domain cap 990.
"""
    (OUT_DIR / "speech_metadata_schema.md").write_text(text, encoding="utf-8")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_records = []
    with open(OUT_DIR / "all_scored_samples.jsonl", "w", encoding="utf-8") as f:
        for rec in iter_all_records():
            all_records.append(rec)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    deduped = []
    seen = set()
    for rec in sorted(all_records, key=lambda r: (-r["speech_metadata"]["speech_sensitive_score"], r["dataset"], r["id"])):
        key = normalize_question(rec["question"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(rec)

    selected = []
    selected_ids = set()
    quota_rows = []
    for domain, quota in QUOTAS.items():
        pool = [r for r in deduped if r["domain"] == domain and is_candidate(r)]
        relaxed_pool = [r for r in deduped if r["domain"] == domain and is_candidate(r, relaxed=True)]
        take_pool = pool if len(pool) >= quota else relaxed_pool
        take = take_pool[: min(quota, DOMAIN_CAP)]
        for rec in take:
            selected.append(rec)
            selected_ids.add(rec["id"])
        quota_rows.append({
            "domain": domain,
            "candidate_count": len(pool),
            "relaxed_candidate_count": len(relaxed_pool),
            "target_quota": quota,
            "selected_count": len(take),
            "shortfall": max(0, quota - len(take)),
        })

    if len(selected) < TARGET_TOTAL:
        counts = Counter(r["domain"] for r in selected)
        for rec in deduped:
            if rec["id"] in selected_ids or not is_candidate(rec, relaxed=True):
                continue
            if counts[rec["domain"]] >= DOMAIN_CAP:
                continue
            selected.append(rec)
            selected_ids.add(rec["id"])
            counts[rec["domain"]] += 1
            if len(selected) >= TARGET_TOTAL:
                break

    with open(OUT_DIR / "selected_5k_6k.jsonl", "w", encoding="utf-8") as f:
        for rec in selected:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    summary = Counter((r["domain"], r["dataset"], r["question_type"]) for r in selected)
    with open(OUT_DIR / "selection_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["domain", "dataset", "question_type", "selected_count"])
        for (domain, dataset, qtype), count in sorted(summary.items()):
            w.writerow([domain, dataset, qtype, count])

    selected_counts = Counter(r["domain"] for r in selected)
    with open(OUT_DIR / "domain_quota_report.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["domain", "candidate_count", "relaxed_candidate_count", "target_quota", "selected_count", "shortfall", "final_selected_count", "final_share"])
        w.writeheader()
        for row in quota_rows:
            domain = row["domain"]
            row["final_selected_count"] = selected_counts[domain]
            row["final_share"] = round(selected_counts[domain] / max(1, len(selected)), 4)
            w.writerow(row)

    with open(OUT_DIR / "manual_review_sample.jsonl", "w", encoding="utf-8") as f:
        by_domain = defaultdict(list)
        for rec in selected:
            if len(by_domain[rec["domain"]]) < 30:
                by_domain[rec["domain"]].append(rec)
        for domain in QUOTAS:
            for rec in by_domain[domain]:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    write_schema()
    print("all_scored", len(all_records))
    print("deduped", len(deduped))
    print("selected", len(selected))
    for domain, count in selected_counts.items():
        print(domain, count)


if __name__ == "__main__":
    main()
