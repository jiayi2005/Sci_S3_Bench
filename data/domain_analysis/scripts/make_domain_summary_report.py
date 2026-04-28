import csv
from collections import Counter, defaultdict
from pathlib import Path


BASE = Path("/DB/rhome/heyangliu/sci_s2s_bench/data/domain_analysis")
DATASET_CSV = BASE / "merged_dataset_summary.csv"
SUBDOMAIN_CSV = BASE / "merged_domain_subdomain_counts.csv"
OUT_MD = BASE / "dataset_domain_summary_report.md"
OUT_DATASET_TABLE = BASE / "dataset_domain_summary_table.csv"


DOMAIN_ORDER = [
    "Clinical Medicine",
    "Life Sciences",
    "Genomics",
    "Chemistry",
    "Materials Science",
    "Physics",
    "Earth Science",
    "Climate Science",
    "Astronomy",
    "Computer Science",
]


DISPLAY_DATASET = {
    "EarthSE_Earth-Iron": "Earth-Iron",
    "EarthSE_Earth-Silver": "Earth-Silver",
    "EarthSE_Earth-Gold": "Earth-Gold",
}


def fmt_int(value):
    return f"{int(value):,}"


def fmt_forms(forms):
    if not forms:
        return ""
    parts = []
    for part in forms.split(";"):
        part = part.strip()
        if not part or ":" not in part:
            continue
        k, v = part.rsplit(":", 1)
        label = k.strip()
        label = {
            "Open-ended": "open_ended",
            "True/False": "judgment/true_false",
            "Fill-in-the-blank": "fill_blank",
            "Open-ended dialogue": "multi-turn open dialogue",
            "Open numeric/short answer": "open numeric/short answer",
            "Code generation": "code generation",
            "Open generation/extraction": "open generation/extraction",
        }.get(label, label)
        parts.append(f"{label} {fmt_int(v)}")
    return "; ".join(parts)


def read_dataset_rows():
    rows = []
    with DATASET_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def read_subdomain_rows():
    rows = []
    with SUBDOMAIN_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["count"] = int(row["count"])
            rows.append(row)
    return rows


def main():
    dataset_rows = read_dataset_rows()
    subdomain_rows = read_subdomain_rows()

    with OUT_DATASET_TABLE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Dataset", "Domain", "Total", "Forms"])
        for row in dataset_rows:
            if (row["dataset"] == "GeneTuring"):
                total = "3,302 unique questions / 16,101 raw records"
            else:
                total = row["question_like_count"]
            writer.writerow([
                DISPLAY_DATASET.get(row["dataset"], row["dataset"]),
                row["domains"],
                total,
                fmt_forms(row["forms"]),
            ])

    domain_totals = Counter()
    domain_subs = defaultdict(list)
    domain_datasets = defaultdict(Counter)
    domain_forms = defaultdict(Counter)
    for row in subdomain_rows:
        domain = row["domain"]
        domain_totals[domain] += row["count"]
        domain_subs[domain].append((row["subdomain"], row["count"]))
        for part in row["datasets"].split(";"):
            part = part.strip()
            if ":" in part:
                ds, n = part.rsplit(":", 1)
                domain_datasets[domain][ds.strip()] += int(n)
        for part in row["forms"].split(";"):
            part = part.strip()
            if ":" in part:
                form, n = part.rsplit(":", 1)
                domain_forms[domain][form.strip()] += int(n)

    total_raw = sum(int(r["total_records"]) for r in dataset_rows)
    total_question_like = sum(int(r["question_like_count"]) for r in dataset_rows)
    multi_domain = [r["dataset"] for r in dataset_rows if ";" in r["domains"]]

    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("# Dataset and Domain Summary\n\n")
        f.write("This report summarizes the latest v2 domain analysis files in `domain_analysis/`.\n\n")
        f.write("Important taxonomy changes from the older table:\n\n")
        f.write("- `ClimaQA_gold`, `ClimaQA_silver`, and climate-related EarthSE records are `Climate Science`, not generic `Earth Science`.\n")
        f.write("- `MedXpertQA`, `MedMCQA`, `MedQA_USMLE`, and `PubMedQA` are `Clinical Medicine`, not `Life Sciences`.\n")
        f.write("- `GeneTuring` and `Genome-Bench` are `Genomics`.\n")
        f.write("- `SciKnowEval` is split into Chemistry, Materials Science, Life Sciences, and Physics, not `General Science`.\n")
        f.write("- `MMLU`, `ScienceQA`, and ATLAS Mathematics are excluded from this fixed 10-domain taxonomy.\n\n")

        f.write("## Dataset Table\n\n")
        f.write("| Dataset | Domain | Total | Forms |\n")
        f.write("|---|---|---:|---|\n")
        for row in dataset_rows:
            dataset = DISPLAY_DATASET.get(row["dataset"], row["dataset"])
            if row["dataset"] == "GeneTuring":
                total = "3,302 unique / 16,101 raw"
            else:
                total = fmt_int(row["question_like_count"])
            f.write(f"| {dataset} | {row['domains']} | {total} | {fmt_forms(row['forms'])} |\n")

        f.write("\n## Domain Totals\n\n")
        f.write("| Domain | Total | Subdomain count | Main datasets | Main forms |\n")
        f.write("|---|---:|---:|---|---|\n")
        for domain in DOMAIN_ORDER:
            datasets = "; ".join(f"{k} {fmt_int(v)}" for k, v in domain_datasets[domain].most_common(5))
            forms = "; ".join(f"{k} {fmt_int(v)}" for k, v in domain_forms[domain].most_common(5))
            f.write(f"| {domain} | {fmt_int(domain_totals[domain])} | {len(domain_subs[domain])} | {datasets} | {forms} |\n")

        f.write("\n## Subdomains by Domain\n\n")
        f.write("The full subdomain table is `merged_domain_subdomain_counts.csv`. Top subdomains are listed below; Clinical Medicine has many fine-grained MedMCQA topics, so only top 30 are shown here.\n\n")
        for domain in DOMAIN_ORDER:
            rows = sorted(domain_subs[domain], key=lambda x: (-x[1], x[0]))
            limit = 30 if domain == "Clinical Medicine" else len(rows)
            shown = rows[:limit]
            f.write(f"### {domain}\n\n")
            f.write(f"Total: {fmt_int(domain_totals[domain])}; subdomains: {len(rows)}.\n\n")
            f.write(", ".join(f"{name} ({fmt_int(count)})" for name, count in shown))
            if len(rows) > limit:
                f.write(f", ... plus {len(rows) - limit} more in `merged_domain_subdomain_counts.csv`")
            f.write("\n\n")

        f.write("## Summary of `merged_dataset_summary.csv`\n\n")
        f.write(f"- Dataset rows: {len(dataset_rows)}.\n")
        f.write(f"- Sum of `total_records`: {fmt_int(total_raw)}.\n")
        f.write(f"- Sum of `question_like_count`: {fmt_int(total_question_like)}.\n")
        f.write(f"- Multi-domain datasets: {', '.join(multi_domain)}.\n")
        f.write("- `GeneTuring` is counted as 16,101 raw CSV rows, but 3,302 unique questions for question-like analysis.\n")
        f.write("- `BigCodeBench` counts only `v0.1.4` to avoid duplicate version snapshots.\n\n")

        f.write("## Summary of `merged_domain_subdomain_counts.csv`\n\n")
        f.write(f"- Domain count: {len(domain_totals)}.\n")
        f.write(f"- Total domain/subdomain rows: {len(subdomain_rows)}.\n")
        f.write(f"- Total question-like count across included domains: {fmt_int(sum(domain_totals.values()))}.\n")
        f.write("- This file is the detailed source of truth for domain/subdomain counts, dataset contribution, form distribution, and count basis.\n")

    print(OUT_MD)
    print(OUT_DATASET_TABLE)


if __name__ == "__main__":
    main()
