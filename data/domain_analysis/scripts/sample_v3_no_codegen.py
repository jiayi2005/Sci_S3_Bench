#!/usr/bin/env python3
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


DATA_ROOT = Path("/DB/rhome/heyangliu/sci_s2s_bench/data")
INPUT_JSONL = DATA_ROOT / "speech_sensitive_selection_v3/all_scored_samples_v3.jsonl"
OUT_DIR = DATA_ROOT / "speech_sensitive_selection_v3_no_codegen"

DOMAIN_SOFT_TARGETS = {
    "Clinical Medicine": 820,
    "Chemistry": 820,
    "Materials Science": 720,
    "Physics": 700,
    "Life Sciences": 700,
    "Genomics": 700,
    "Climate Science": 700,
    "Earth Science": 600,
    "Astronomy": 320,
}
COMPUTER_SCIENCE_MAX = 80
DATASET_SOFT_CAP = 0.60
EXCLUDED_QUESTION_TYPES = {"Code generation"}
SPACE_RE = re.compile(r"\s+")


def safe_text(value):
    return "" if value is None else str(value)


def norm_question(text):
    return SPACE_RE.sub(" ", safe_text(text).lower()).strip()


def strict_candidate(rec):
    meta = rec["speech_metadata"]
    return meta["speech_sensitive_score_v3"] >= 60 or (
        meta["speech_sensitive_score_v3"] >= 45 and len(meta.get("core_features", [])) >= 2
    )


def relaxed_candidate(rec):
    meta = rec["speech_metadata"]
    return meta["speech_sensitive_score_v3"] >= 40 and len(meta.get("core_features", [])) >= 1


def score_key(rec):
    meta = rec["speech_metadata"]
    return (
        -meta["speech_sensitive_score_v3"],
        -len(meta.get("core_features", [])),
        -len(meta.get("critical_spans", [])),
        rec.get("dataset", ""),
        rec.get("id", ""),
    )


def trim_targets(targets, quota):
    over = sum(targets.values()) - quota
    if over <= 0:
        return targets
    for ds in sorted(targets, key=lambda k: targets[k], reverse=True):
        if over <= 0:
            break
        remove = min(over, max(0, targets[ds] - 1))
        targets[ds] -= remove
        over -= remove
    return targets


def desired_dataset_targets(quota, pools):
    datasets = sorted(pools)
    if not datasets:
        return {}
    if len(datasets) == 1:
        return {datasets[0]: min(quota, len(pools[datasets[0]]))}
    min_floor = min(50, max(10, int(round(quota * 0.07))))
    targets = {ds: min(min_floor, len(pools[ds])) for ds in datasets}
    remaining = quota - sum(targets.values())
    if remaining <= 0:
        return trim_targets(targets, quota)
    soft_cap = int(math.ceil(quota * DATASET_SOFT_CAP))
    weights = {ds: math.sqrt(max(1, len(pools[ds]))) for ds in datasets}
    while remaining > 0:
        eligible = [ds for ds in datasets if targets[ds] < len(pools[ds]) and targets[ds] < soft_cap]
        if not eligible:
            eligible = [ds for ds in datasets if targets[ds] < len(pools[ds])]
        if not eligible:
            break
        total_weight = sum(weights[ds] for ds in eligible)
        progressed = False
        for ds in eligible:
            if remaining <= 0:
                break
            room_limit = soft_cap if targets[ds] < soft_cap else len(pools[ds])
            room = min(len(pools[ds]), room_limit) - targets[ds]
            if room <= 0:
                continue
            add = max(1, int(round(remaining * weights[ds] / total_weight)))
            add = min(add, room, remaining)
            targets[ds] += add
            remaining -= add
            progressed = True
        if not progressed:
            break
    return targets


def take_from_pool(pool, n, used_ids, used_questions):
    taken = []
    for rec in pool:
        if len(taken) >= n:
            break
        qkey = norm_question(rec.get("question"))
        if rec["id"] in used_ids or qkey in used_questions:
            continue
        taken.append(rec)
        used_ids.add(rec["id"])
        used_questions.add(qkey)
    return taken


def load_records():
    best = {}
    raw = 0
    excluded_type = Counter()
    with INPUT_JSONL.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            raw += 1
            rec = json.loads(line)
            if rec.get("question_type") in EXCLUDED_QUESTION_TYPES:
                excluded_type[rec.get("question_type")] += 1
                continue
            qkey = norm_question(rec.get("question"))
            if not qkey:
                continue
            prev = best.get(qkey)
            if prev is None or score_key(rec) < score_key(prev):
                best[qkey] = rec
    return list(best.values()), raw, excluded_type


def build_pools(records):
    strict = defaultdict(lambda: defaultdict(list))
    relaxed = defaultdict(lambda: defaultdict(list))
    all_pools = defaultdict(lambda: defaultdict(list))
    for rec in records:
        domain = rec.get("domain")
        dataset = rec.get("dataset")
        if domain in DOMAIN_SOFT_TARGETS or domain == "Computer Science":
            all_pools[domain][dataset].append(rec)
            if relaxed_candidate(rec):
                relaxed[domain][dataset].append(rec)
            if strict_candidate(rec):
                strict[domain][dataset].append(rec)
    for pools in (strict, relaxed, all_pools):
        for domain in pools:
            for dataset in pools[domain]:
                pools[domain][dataset].sort(key=score_key)
    return strict, relaxed, all_pools


def sample_domain(domain, target, strict, relaxed, all_pools, used_ids, used_questions):
    pools = strict[domain]
    if sum(len(v) for v in pools.values()) < target:
        pools = relaxed[domain]
    targets = desired_dataset_targets(target, pools)
    selected = []
    for dataset, count in sorted(targets.items(), key=lambda x: (-x[1], x[0])):
        selected.extend(take_from_pool(pools[dataset], count, used_ids, used_questions))
    if len(selected) < target:
        merged = []
        for dataset in sorted(relaxed[domain]):
            merged.extend(relaxed[domain][dataset])
        merged.sort(key=score_key)
        selected.extend(take_from_pool(merged, target - len(selected), used_ids, used_questions))
    # Do not over-force weak samples, except for Astronomy where we accept a small top-up.
    if domain == "Astronomy" and len(selected) < target:
        merged = []
        for dataset in sorted(all_pools[domain]):
            merged.extend(all_pools[domain][dataset])
        merged.sort(key=score_key)
        selected.extend(take_from_pool(merged, target - len(selected), used_ids, used_questions))
    return selected


def write_csv(path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_reports(selected, records, raw_count, excluded_type):
    total = len(selected)
    domain_counts = Counter(r["domain"] for r in selected)
    dataset_counts = Counter(r["dataset"] for r in selected)
    qtype_counts = Counter(r["question_type"] for r in selected)
    domain_dataset = Counter((r["domain"], r["dataset"]) for r in selected)
    domain_qtype = Counter((r["domain"], r["question_type"]) for r in selected)
    feature_counts = Counter()
    score_counts = Counter()
    for rec in selected:
        meta = rec["speech_metadata"]
        feature_counts.update(meta.get("core_features", []))
        score_counts[meta["speech_sensitive_score_v3"]] += 1

    write_csv(
        OUT_DIR / "domain_distribution.csv",
        ["domain", "selected_count", "share"],
        [{"domain": d, "selected_count": n, "share": round(n / total, 4)} for d, n in domain_counts.most_common()],
    )
    write_csv(
        OUT_DIR / "dataset_distribution.csv",
        ["dataset", "selected_count", "share"],
        [{"dataset": d, "selected_count": n, "share": round(n / total, 4)} for d, n in dataset_counts.most_common()],
    )
    write_csv(
        OUT_DIR / "question_type_distribution.csv",
        ["question_type", "selected_count", "share"],
        [{"question_type": q, "selected_count": n, "share": round(n / total, 4)} for q, n in qtype_counts.most_common()],
    )
    write_csv(
        OUT_DIR / "domain_dataset_distribution.csv",
        ["domain", "dataset", "selected_count", "share_within_domain", "share_total"],
        [
            {
                "domain": d,
                "dataset": ds,
                "selected_count": n,
                "share_within_domain": round(n / domain_counts[d], 4),
                "share_total": round(n / total, 4),
            }
            for (d, ds), n in sorted(domain_dataset.items())
        ],
    )
    write_csv(
        OUT_DIR / "domain_question_type_distribution.csv",
        ["domain", "question_type", "selected_count", "share_within_domain"],
        [
            {
                "domain": d,
                "question_type": qt,
                "selected_count": n,
                "share_within_domain": round(n / domain_counts[d], 4),
            }
            for (d, qt), n in sorted(domain_qtype.items())
        ],
    )
    write_csv(
        OUT_DIR / "feature_coverage.csv",
        ["feature", "selected_count", "share"],
        [{"feature": f, "selected_count": n, "share": round(n / total, 4)} for f, n in feature_counts.most_common()],
    )
    write_csv(
        OUT_DIR / "score_distribution.csv",
        ["score_v3", "selected_count", "share"],
        [{"score_v3": s, "selected_count": n, "share": round(n / total, 4)} for s, n in sorted(score_counts.items())],
    )
    write_csv(
        OUT_DIR / "sampling_config.csv",
        ["metric", "value"],
        [
            {"metric": "raw_scored_samples", "value": raw_count},
            {"metric": "deduped_after_excluding_code_generation", "value": len(records)},
            {"metric": "selected_count", "value": total},
            {"metric": "excluded_code_generation_raw", "value": excluded_type.get("Code generation", 0)},
            {"metric": "computer_science_policy", "value": f"no fixed quota; max {COMPUTER_SCIENCE_MAX}; code generation excluded"},
        ],
    )

    lines = [
        "# Speech-Sensitive v3 No-Codegen Selection Analysis",
        "",
        f"Final selected samples: {total}.",
        "",
        "`Code generation` samples are excluded because they are not suitable for S2S. Computer Science is no longer forced to a fixed domain quota; only non-code-generation CS candidates are retained up to a small cap.",
        "",
        "## Domain Distribution",
        "",
        "| Domain | Count | Share |",
        "|---|---:|---:|",
    ]
    for d, n in domain_counts.most_common():
        lines.append(f"| {d} | {n:,} | {n / total:.2%} |")
    lines.extend(["", "## Dataset Distribution", "", "| Dataset | Count | Share |", "|---|---:|---:|"])
    for d, n in dataset_counts.most_common():
        lines.append(f"| {d} | {n:,} | {n / total:.2%} |")
    lines.extend(["", "## Question Type Distribution", "", "| Type | Count | Share |", "|---|---:|---:|"])
    for q, n in qtype_counts.most_common():
        lines.append(f"| {q} | {n:,} | {n / total:.2%} |")
    lines.extend(["", "## Feature Coverage", "", "| Feature | Count | Share |", "|---|---:|---:|"])
    for f, n in feature_counts.most_common():
        lines.append(f"| {f} | {n:,} | {n / total:.2%} |")
    lines.extend(["", "## Notes", ""])
    lines.append(f"- Excluded raw `Code generation` records: {excluded_type.get('Code generation', 0):,}.")
    lines.append("- Computer Science now contains only ATLAS open-ended CS items because BigCodeBench and SciCode are code-generation datasets.")
    lines.append("- Total is intentionally around 6,000 rather than exactly 6,000.")
    (OUT_DIR / "selection_no_codegen_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    if not INPUT_JSONL.exists():
        raise RuntimeError(f"Missing input: {INPUT_JSONL}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records, raw_count, excluded_type = load_records()
    strict, relaxed, all_pools = build_pools(records)
    selected = []
    used_ids = set()
    used_questions = set()
    for domain, target in DOMAIN_SOFT_TARGETS.items():
        selected.extend(sample_domain(domain, target, strict, relaxed, all_pools, used_ids, used_questions))
    cs_pool = []
    for dataset in sorted(relaxed["Computer Science"]):
        cs_pool.extend(relaxed["Computer Science"][dataset])
    cs_pool.sort(key=score_key)
    selected.extend(take_from_pool(cs_pool, COMPUTER_SCIENCE_MAX, used_ids, used_questions))

    with (OUT_DIR / "selected_around6k_no_codegen.jsonl").open("w", encoding="utf-8") as f:
        for rec in selected:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    write_reports(selected, records, raw_count, excluded_type)
    print("raw_scored", raw_count)
    print("deduped_non_codegen", len(records))
    print("excluded_code_generation_raw", excluded_type.get("Code generation", 0))
    print("selected", len(selected))
    print("domain_counts", dict(Counter(r["domain"] for r in selected)))
    print("question_types", dict(Counter(r["question_type"] for r in selected)))


if __name__ == "__main__":
    main()
