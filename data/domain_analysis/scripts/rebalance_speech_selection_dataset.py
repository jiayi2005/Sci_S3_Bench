import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


BASE = Path("/DB/rhome/heyangliu/sci_s2s_bench/data/speech_sensitive_selection")
ALL_SCORED = BASE / "all_scored_samples.jsonl"

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


def norm_question(text):
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def useful_reasons(rec):
    return [
        r
        for r in rec["speech_metadata"].get("speech_sensitive_reasons", [])
        if not r.startswith("ordinary") and not r.startswith("long_context")
    ]


def strict_candidate(rec):
    score = rec["speech_metadata"].get("speech_sensitive_score", 0)
    return score >= 3 or (score >= 2 and len(useful_reasons(rec)) >= 2)


def relaxed_candidate(rec):
    return rec["speech_metadata"].get("speech_sensitive_score", 0) >= 2


def score_key(rec):
    meta = rec["speech_metadata"]
    return (
        -meta.get("speech_sensitive_score", 0),
        -len(meta.get("critical_spans", [])),
        rec["dataset"],
        rec["id"],
    )


def load_deduped_records():
    records = []
    with ALL_SCORED.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    best = {}
    for rec in sorted(records, key=score_key):
        key = norm_question(rec["question"])
        if key and key not in best:
            best[key] = rec
    return list(best.values()), len(records)


def desired_dataset_targets(domain, quota, pools):
    datasets = sorted(pools)
    if len(datasets) == 1:
        return {datasets[0]: min(quota, len(pools[datasets[0]]))}

    # Minimum inclusion: enough to matter, but capped for small sources.
    min_floor = min(50, max(10, int(round(quota * 0.08))))
    targets = {}
    for ds in datasets:
        targets[ds] = min(min_floor, len(pools[ds]))

    remaining = quota - sum(targets.values())
    if remaining <= 0:
        return trim_targets(targets, quota)

    # Soft cap: no source should dominate a domain if alternatives exist.
    # The cap can be exceeded only if other datasets are exhausted.
    soft_cap = int(math.ceil(quota * 0.60))
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
            room = min(len(pools[ds]), soft_cap if targets[ds] < soft_cap else len(pools[ds])) - targets[ds]
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


def take_from_pool(pool, n, used_ids, used_questions):
    taken = []
    for rec in pool:
        if len(taken) >= n:
            break
        qkey = norm_question(rec["question"])
        if rec["id"] in used_ids or qkey in used_questions:
            continue
        taken.append(rec)
        used_ids.add(rec["id"])
        used_questions.add(qkey)
    return taken


def main():
    deduped, raw_count = load_deduped_records()
    by_domain_dataset = defaultdict(lambda: defaultdict(list))
    strict_counts = defaultdict(Counter)
    relaxed_counts = defaultdict(Counter)

    for rec in deduped:
        if rec["domain"] not in QUOTAS:
            continue
        if relaxed_candidate(rec):
            by_domain_dataset[rec["domain"]][rec["dataset"]].append(rec)
            relaxed_counts[rec["domain"]][rec["dataset"]] += 1
            if strict_candidate(rec):
                strict_counts[rec["domain"]][rec["dataset"]] += 1

    for domain in by_domain_dataset:
        for dataset in by_domain_dataset[domain]:
            by_domain_dataset[domain][dataset].sort(key=score_key)

    selected = []
    used_ids = set()
    used_questions = set()
    dataset_report = []

    for domain, quota in QUOTAS.items():
        pools = by_domain_dataset[domain]
        targets = desired_dataset_targets(domain, quota, pools)
        domain_selected = []
        for dataset, target in sorted(targets.items(), key=lambda x: (-x[1], x[0])):
            taken = take_from_pool(pools[dataset], target, used_ids, used_questions)
            domain_selected.extend(taken)
            dataset_report.append(
                {
                    "domain": domain,
                    "dataset": dataset,
                    "relaxed_candidates": relaxed_counts[domain][dataset],
                    "strict_candidates": strict_counts[domain][dataset],
                    "target": target,
                    "selected": len(taken),
                }
            )

        if len(domain_selected) < quota:
            merged = []
            for dataset in sorted(pools):
                merged.extend(pools[dataset])
            merged.sort(key=score_key)
            fill = take_from_pool(merged, quota - len(domain_selected), used_ids, used_questions)
            domain_selected.extend(fill)

        selected.extend(domain_selected[: min(quota, DOMAIN_CAP)])

    # Safety fill, respecting the global cap, should normally be unnecessary.
    if len(selected) < TARGET_TOTAL:
        counts = Counter(r["domain"] for r in selected)
        merged = sorted(deduped, key=score_key)
        for rec in merged:
            if not relaxed_candidate(rec):
                continue
            if rec["domain"] not in QUOTAS or counts[rec["domain"]] >= QUOTAS[rec["domain"]]:
                continue
            qkey = norm_question(rec["question"])
            if rec["id"] in used_ids or qkey in used_questions:
                continue
            selected.append(rec)
            used_ids.add(rec["id"])
            used_questions.add(qkey)
            counts[rec["domain"]] += 1
            if len(selected) >= TARGET_TOTAL:
                break

    old_selected = BASE / "selected_5k_6k.jsonl"
    backup = BASE / "selected_5k_6k_domain_balanced_backup.jsonl"
    if old_selected.exists() and not backup.exists():
        backup.write_text(old_selected.read_text(encoding="utf-8"), encoding="utf-8")

    with old_selected.open("w", encoding="utf-8") as f:
        for rec in selected:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with (BASE / "selected_5k_6k_dataset_balanced.jsonl").open("w", encoding="utf-8") as f:
        for rec in selected:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    summary = Counter((r["domain"], r["dataset"], r["question_type"]) for r in selected)
    with (BASE / "selection_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["domain", "dataset", "question_type", "selected_count"])
        for (domain, dataset, qtype), count in sorted(summary.items()):
            w.writerow([domain, dataset, qtype, count])
    with (BASE / "selection_summary_dataset_balanced.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["domain", "dataset", "question_type", "selected_count"])
        for (domain, dataset, qtype), count in sorted(summary.items()):
            w.writerow([domain, dataset, qtype, count])

    domain_counts = Counter(r["domain"] for r in selected)
    with (BASE / "domain_quota_report.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["domain", "target_quota", "final_selected_count", "final_share"])
        for domain, quota in QUOTAS.items():
            w.writerow([domain, quota, domain_counts[domain], round(domain_counts[domain] / max(1, len(selected)), 4)])
    with (BASE / "domain_quota_report_dataset_balanced.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["domain", "target_quota", "final_selected_count", "final_share"])
        for domain, quota in QUOTAS.items():
            w.writerow([domain, quota, domain_counts[domain], round(domain_counts[domain] / max(1, len(selected)), 4)])

    by_dd = Counter((r["domain"], r["dataset"]) for r in selected)
    with (BASE / "dataset_balance_report.csv").open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["domain", "dataset", "relaxed_candidates", "strict_candidates", "target", "selected", "domain_selected", "dataset_share_in_domain"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        rows = []
        report_keys = {(r["domain"], r["dataset"]): r for r in dataset_report}
        for domain in QUOTAS:
            for dataset in sorted(by_domain_dataset[domain]):
                base = report_keys.get((domain, dataset), {})
                selected_count = by_dd[(domain, dataset)]
                rows.append(
                    {
                        "domain": domain,
                        "dataset": dataset,
                        "relaxed_candidates": relaxed_counts[domain][dataset],
                        "strict_candidates": strict_counts[domain][dataset],
                        "target": base.get("target", 0),
                        "selected": selected_count,
                        "domain_selected": domain_counts[domain],
                        "dataset_share_in_domain": round(selected_count / max(1, domain_counts[domain]), 4),
                    }
                )
        for row in rows:
            w.writerow(row)

    print("raw_scored", raw_count)
    print("deduped", len(deduped))
    print("selected", len(selected))
    for domain in QUOTAS:
        parts = ", ".join(f"{ds}:{by_dd[(domain, ds)]}" for ds in sorted(by_domain_dataset[domain]))
        print(domain, domain_counts[domain], parts)


if __name__ == "__main__":
    main()
