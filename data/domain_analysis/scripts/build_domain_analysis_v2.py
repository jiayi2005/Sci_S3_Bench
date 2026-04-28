import csv
import json
import math
import os
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


OLD_ROOT = Path("/tmp/sci_s2s_bench_datasets")
NEW_ROOT = Path("/tmp/sci_s2s_bench_datasets_v2")
OUT_DIR = Path("/tmp/sci_s2s_bench_domain_analysis_v2")

TARGET_DOMAINS = [
    "Life Sciences",
    "Genomics",
    "Clinical Medicine",
    "Chemistry",
    "Materials Science",
    "Physics",
    "Earth Science",
    "Climate Science",
    "Astronomy",
    "Computer Science",
]

domain_sub_counts = defaultdict(Counter)
domain_sub_dataset_counts = defaultdict(Counter)
domain_sub_form_counts = defaultdict(Counter)
dataset_totals = Counter()
dataset_question_counts = Counter()
dataset_domain_counts = defaultdict(Counter)
dataset_form_counts = defaultdict(Counter)
dataset_notes = defaultdict(list)
excluded = Counter()


def clean_name(value, default="General"):
    if value is None:
        return default
    if isinstance(value, float) and math.isnan(value):
        return default
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return default
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"(?<!^)(?=[A-Z][a-z])", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.title()


def pretty_task(value):
    return clean_name(value, "General")


def add_count(dataset, domain, subdomain, count, form, basis="records"):
    if count <= 0:
        return
    if domain not in TARGET_DOMAINS:
        excluded[(dataset, domain)] += count
        return
    subdomain = clean_name(subdomain, "General")
    domain_sub_counts[(domain, subdomain)][basis] += count
    domain_sub_dataset_counts[(domain, subdomain)][dataset] += count
    domain_sub_form_counts[(domain, subdomain)][form] += count
    dataset_question_counts[dataset] += count
    dataset_domain_counts[dataset][domain] += count
    dataset_form_counts[dataset][form] += count


def add_dataset_total(dataset, total):
    dataset_totals[dataset] += int(total)


def load_json_list(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return list(data.values())
    raise TypeError(f"Unsupported JSON root in {path}: {type(data)}")


def form_from_filename(path):
    name = Path(path).stem.lower()
    if "mcqa" in name or "multiple_choice" in name:
        return "MCQA"
    if "judgment" in name or "true_false" in name:
        return "True/False"
    if "open" in name or "free_form" in name:
        return "Open-ended"
    if "fill_in" in name:
        return "Fill-in-the-blank"
    return clean_name(name)


def chembench_subdomain(row):
    category = row.get("Category")
    if category:
        return clean_name(category)
    app = row.get("Appendix") or {}
    if isinstance(app, dict):
        return clean_name(app.get("subfield") or app.get("name"), "Chemistry General")
    return "Chemistry General"


def qchem_subdomain(value):
    text = clean_name(value, "Chemistry General")
    mapping = {
        "Physical": "Physical Chemistry",
        "Analytical": "Analytical Chemistry",
        "Inorganic": "Inorganic Chemistry",
        "Organic": "Organic Chemistry",
        "Quantum": "Quantum Chemistry",
        "Biochemistry": "Biochemistry",
        "Polymer": "Polymer Chemistry",
        "General": "General Chemistry",
    }
    return mapping.get(text, text)


def sciknow_domain(value):
    return {
        "Biology": "Life Sciences",
        "Material": "Materials Science",
        "Materials": "Materials Science",
        "Material Science": "Materials Science",
        "Chemistry": "Chemistry",
        "Physics": "Physics",
    }.get(str(value), clean_name(value))


def atlas_domain(subject, sub_subject):
    subject = str(subject)
    sub = str(sub_subject or "")
    if subject == "Biology":
        if re.search(r"genetic|genomic|bioinformatics", sub, re.I):
            return "Genomics"
        return "Life Sciences"
    if subject == "Math":
        return "Mathematics"
    if subject == "Earth Science":
        if re.search(r"atmospheric|climate|meteorolog|cryosphere|glaciolog", sub, re.I):
            return "Climate Science"
        return "Earth Science"
    return {
        "Materials Science": "Materials Science",
        "Computer Science": "Computer Science",
        "Chemistry": "Chemistry",
        "Physics": "Physics",
    }.get(subject, clean_name(subject))


def earthse_domain(subject=None, subdiscipline=None, sphere=None):
    blob = " ".join([str(x or "") for x in [subject, subdiscipline, sphere]])
    if re.search(r"atmospheric|climat|meteorolog|cryosphere|glaciolog|polar science|polar sciences", blob, re.I):
        return "Climate Science"
    if re.search(r"ecology|bioscience|biosphere", blob, re.I):
        return "Life Sciences"
    return "Earth Science"


def read_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def process_science_s2s():
    root = OLD_ROOT / "Science_S2S_Bench"
    specs = [
        ("Astro-QA", root / "Astronomy/Astro-QA/json", "Astronomy", "Astronomy General", None),
        ("ChemBench", root / "Chemistry/ChemBench/json", "Chemistry", None, chembench_subdomain),
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
    for dataset, directory, domain, fixed_subdomain, subdomain_fn in specs:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.json")):
            rows = load_json_list(path)
            add_dataset_total(dataset, len(rows))
            form = form_from_filename(path)
            if subdomain_fn:
                counts = Counter(clean_name(subdomain_fn(r), fixed_subdomain or "General") for r in rows)
                for sub, count in counts.items():
                    add_count(dataset, domain, sub, count, form)
            else:
                add_count(dataset, domain, fixed_subdomain, len(rows), form)

    # Keep SciKnowEval, but split by its internal Appendix.domain.
    sci_dir = root / "General_Science/SciKnowEval/json"
    for path in sorted(sci_dir.glob("*.json")):
        rows = load_json_list(path)
        add_dataset_total("SciKnowEval", len(rows))
        form = "MCQA"
        grouped = Counter()
        for row in rows:
            app = row.get("Appendix") or {}
            details = app.get("details") or {}
            domain = sciknow_domain(app.get("domain"))
            sub = pretty_task(details.get("subtask") or details.get("task") or "SciKnowEval General")
            grouped[(domain, sub)] += 1
        for (domain, sub), count in grouped.items():
            add_count("SciKnowEval", domain, sub, count, form)

    # Explicitly excluded simple/general datasets.
    for directory in [root / "General_Science/ScienceQA/json", root / "General_Science/mmlu/json"]:
        for path in sorted(directory.glob("*.json")):
            rows = load_json_list(path)
            excluded[(Path(directory).parts[-2], "Excluded")] += len(rows)


def process_qcbench():
    path = OLD_ROOT / "QCBench/QCBench.json"
    rows = load_json_list(path)
    add_dataset_total("QCBench", len(rows))
    counts = Counter(qchem_subdomain(r.get("class")) for r in rows)
    for sub, count in counts.items():
        add_count("QCBench", "Chemistry", sub, count, "Open numeric/short answer")


def process_geneturing():
    path = OLD_ROOT / "GeneTuring/SupplementaryTable1.csv.zip"
    with zipfile.ZipFile(path) as zf:
        with zf.open("SupplementaryTable1.csv") as f:
            df = pd.read_csv(f, encoding="latin1")
    add_dataset_total("GeneTuring", len(df))
    unique = df.drop_duplicates(subset=["Module", "Question", "Goldstandard"])
    counts = unique["Module"].map(clean_name).value_counts()
    for sub, count in counts.items():
        add_count("GeneTuring", "Genomics", sub, int(count), "Open generation/extraction", "unique_questions")
    dataset_notes["GeneTuring"].append(f"Raw CSV rows: {len(df)}; unique questions: {len(unique)}. Subdomain/domain count uses unique questions.")


def process_atlas():
    rows = []
    for path in sorted((OLD_ROOT / "ATLAS").glob("*.jsonl")):
        rows.extend(read_jsonl(path))
    add_dataset_total("ATLAS", len(rows))
    grouped = Counter()
    for row in rows:
        domain = atlas_domain(row.get("subject_name"), row.get("sub_subject_name"))
        sub = clean_name(row.get("sub_subject_name"), "General")
        if domain == "Mathematics":
            excluded[("ATLAS", "Mathematics")] += 1
            continue
        grouped[(domain, sub)] += 1
    for (domain, sub), count in grouped.items():
        add_count("ATLAS", domain, sub, count, "Open-ended")
    dataset_notes["ATLAS"].append("Excluded 94 Mathematics records to keep the fixed 10-domain taxonomy.")


def process_earthse():
    root = OLD_ROOT / "EarthSE"
    for part in ["Earth-Iron", "Earth-Silver"]:
        for path in sorted((root / part / "data").glob("*.parquet")):
            df = pd.read_parquet(path)
            dataset = f"EarthSE_{part}"
            add_dataset_total(dataset, len(df))
            form = form_from_filename(path)
            grouped = Counter()
            for row in df[["subject", "sub_discipline"]].fillna("").to_dict("records"):
                domain = earthse_domain(row.get("subject"), row.get("sub_discipline"))
                sub = clean_name(row.get("sub_discipline") or row.get("subject"), "Earth Science General")
                grouped[(domain, sub)] += 1
            for (domain, sub), count in grouped.items():
                add_count(dataset, domain, sub, count, form)
    for path in sorted((root / "Earth-Gold/data").glob("*.parquet")):
        df = pd.read_parquet(path)
        dataset = "EarthSE_Earth-Gold"
        add_dataset_total(dataset, len(df))
        grouped = Counter()
        for sphere in df["sphere"].fillna("").astype(str):
            domain = earthse_domain(sphere=sphere)
            grouped[(domain, clean_name(sphere, "Earth Science General"))] += 1
        for (domain, sub), count in grouped.items():
            add_count(dataset, domain, sub, count, "Open-ended dialogue")


def process_new_clinical_cs():
    # MedMCQA
    dataset = "MedMCQA"
    for path in sorted((NEW_ROOT / "MedMCQA/data").glob("*.parquet")):
        df = pd.read_parquet(path)
        add_dataset_total(dataset, len(df))
        grouped = Counter()
        for row in df[["subject_name", "topic_name"]].to_dict("records"):
            subject = clean_name(row.get("subject_name"), "Medicine General")
            topic = clean_name(row.get("topic_name"), "")
            sub = f"{subject}: {topic}" if topic else subject
            grouped[sub] += 1
        for sub, count in grouped.items():
            add_count(dataset, "Clinical Medicine", sub, count, "MCQA")

    # MedQA-USMLE
    dataset = "MedQA_USMLE"
    total = 0
    for path in sorted((NEW_ROOT / "MedQA_USMLE/data").glob("*.parquet")):
        df = pd.read_parquet(path)
        total += len(df)
    add_dataset_total(dataset, total)
    add_count(dataset, "Clinical Medicine", "Medical Exam QA", total, "MCQA")

    # PubMedQA
    dataset = "PubMedQA"
    total = 0
    for path in sorted((NEW_ROOT / "PubMedQA/data").glob("*.parquet")):
        df = pd.read_parquet(path)
        total += len(df)
    add_dataset_total(dataset, total)
    add_count(dataset, "Clinical Medicine", "Biomedical Literature QA", total, "MCQA")

    # BigCodeBench: count only latest version to avoid duplicate snapshots.
    dataset = "BigCodeBench"
    path = NEW_ROOT / "BigCodeBench/data/v0.1.4-00000-of-00001.parquet"
    if not path.exists():
        path = NEW_ROOT / "BigCodeBench/data/train-00000-of-00001.parquet"
    df = pd.read_parquet(path)
    add_dataset_total(dataset, len(df))
    add_count(dataset, "Computer Science", "Programming", len(df), "Code generation")
    dataset_notes[dataset].append(f"Counted only {path.name} to avoid duplicate version snapshots.")

    # SciCode
    dataset = "SciCode"
    total = 0
    for path in sorted((NEW_ROOT / "SciCode").glob("problems_*.jsonl")):
        n = sum(1 for _ in read_jsonl(path))
        total += n
    add_dataset_total(dataset, total)
    add_count(dataset, "Computer Science", "Scientific Computing", total, "Code generation")


def join_counter(counter):
    return "; ".join(f"{k}:{v}" for k, v in sorted(counter.items(), key=lambda x: (-x[1], x[0])))


def write_outputs():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUT_DIR / "merged_domain_subdomain_counts.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["domain", "subdomain", "count", "datasets", "forms", "count_basis"])
        rows = []
        for key, basis_counts in domain_sub_counts.items():
            total = sum(basis_counts.values())
            basis = "; ".join(f"{k}:{v}" for k, v in basis_counts.items())
            rows.append((key[0], key[1], total, join_counter(domain_sub_dataset_counts[key]), join_counter(domain_sub_form_counts[key]), basis))
        for row in sorted(rows, key=lambda r: (TARGET_DOMAINS.index(r[0]), -r[2], r[1])):
            writer.writerow(row)

    with open(OUT_DIR / "merged_dataset_summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["dataset", "domains", "total_records", "question_like_count", "forms", "notes"])
        for dataset in sorted(dataset_totals):
            domains = "; ".join(k for k, _ in dataset_domain_counts[dataset].most_common())
            forms = join_counter(dataset_form_counts[dataset])
            notes = " ".join(dataset_notes[dataset])
            writer.writerow([dataset, domains, dataset_totals[dataset], dataset_question_counts[dataset], forms, notes])

    domain_totals = Counter()
    for (domain, _), basis_counts in domain_sub_counts.items():
        domain_totals[domain] += sum(basis_counts.values())

    with open(OUT_DIR / "domain_taxonomy_v2.md", "w", encoding="utf-8") as f:
        f.write("# Domain Taxonomy v2\n\n")
        f.write("Fixed 10-domain taxonomy after excluding MMLU and ScienceQA, splitting SciKnowEval by internal domain, and promoting Genomics, Clinical Medicine, and Climate Science to first-level domains.\n\n")
        f.write("## Domain Totals\n\n")
        f.write("| Domain | Count |\n|---|---:|\n")
        for domain in TARGET_DOMAINS:
            f.write(f"| {domain} | {domain_totals[domain]} |\n")
        f.write("\n## Normalization Rules\n\n")
        f.write("- MedXpertQA, MedMCQA, MedQA_USMLE, and PubMedQA are Clinical Medicine.\n")
        f.write("- GeneTuring and Genome-Bench are Genomics; ATLAS Biology records mentioning genetics/bioinformatics are also Genomics.\n")
        f.write("- ClimaQA is Climate Science; EarthSE atmospheric, meteorology, climatology, polar, cryosphere, and glaciology records are Climate Science.\n")
        f.write("- EarthSE ecology/bioscience/biosphere records are Life Sciences; remaining EarthSE records are Earth Science.\n")
        f.write("- SciKnowEval uses Appendix.domain: Biology -> Life Sciences, Material -> Materials Science, Chemistry -> Chemistry, Physics -> Physics.\n")
        f.write("- BigCodeBench counts only v0.1.4 to avoid duplicate version snapshots in the same repo.\n")
        f.write("- MMLU, ScienceQA, and ATLAS Mathematics are excluded from the fixed 10-domain analysis.\n")
        f.write("\n## Excluded Counts\n\n")
        f.write("| Source | Label | Count |\n|---|---|---:|\n")
        for (source, label), count in sorted(excluded.items()):
            f.write(f"| {source} | {label} | {count} |\n")

    print("Wrote", OUT_DIR)
    print("Domain totals:")
    for domain in TARGET_DOMAINS:
        print(f"{domain}\t{domain_totals[domain]}")


def main():
    process_science_s2s()
    process_qcbench()
    process_geneturing()
    process_atlas()
    process_earthse()
    process_new_clinical_cs()
    write_outputs()


if __name__ == "__main__":
    main()
