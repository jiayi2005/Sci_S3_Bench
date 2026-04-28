#!/usr/bin/env python3
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


DATA_ROOT = Path("/DB/rhome/heyangliu/sci_s2s_bench/data")
INPUT_JSONL = DATA_ROOT / "speech_sensitive_selection/all_scored_samples.jsonl"
OUT_DIR = DATA_ROOT / "speech_sensitive_selection_v3"
VOCAB_MIN1 = DATA_ROOT / "GigaSpeech/vocab_min_freq_1.txt"
VOCAB_MIN10 = DATA_ROOT / "GigaSpeech/vocab_min_freq_10.txt"
ABBR_RULE_FILE = Path("/DB/rhome/heyangliu/science_abbreviation_eval/rules/abbreviation_pron.tsv")
ABBR_DENYLIST_FILE = Path("/DB/rhome/heyangliu/science_abbreviation_eval/noise_abbr_denylist_v4.txt")
V2_SELECTED = DATA_ROOT / "speech_sensitive_selection/selected_5k_6k.jsonl"

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

ABBR_PATTERN = re.compile(r"\b((?=[A-Z0-9]*[A-Z])[A-Z0-9]{2,}s?|[a-z]+[A-Z][a-zA-Z0-9]*)\b")
HYPHEN_ABBR_PATTERN = re.compile(r"\b(?:[A-Za-z0-9]{1,8}-){1,3}[A-Za-z0-9]{1,12}\b")
TOKEN_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_'’-]{2,}\b")
SPACE_RE = re.compile(r"\s+")

UNIT_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s?(?:"
    r"mm\s?Hg|mEq\s?/L|mg\s?/dL|g\s?/dL|ng\s?/mL|pg\s?/mL|"
    r"µg\s?/mL|μg\s?/mL|µg\s?/dL|μg\s?/dL|"
    r"mL\s?/min|L\s?/min|"
    r"°C|K|Pa|kPa|MPa|GPa|mmHg|atm|bar|"
    r"W\s?m[−-]?\d|J|kJ|eV|V|mV|A|mA|Hz|kHz|MHz|GHz|"
    r"mol|mmol|µmol|μmol|M|mM|µM|μM|"
    r"g|mg|µg|μg|kg|mL|µL|μL|L|"
    r"m|cm|mm|µm|μm|nm|km|m/s|"
    r"bp|kb|Mb|Da|kDa|ppm|ppb|%)"
    r"(?=$|[\s,.;:)\]])"
)
LATEX_RE = re.compile(
    r"(\\ce\{[^}]{1,120}\}|\\\([^)]{1,160}\\\)|\\\[[\s\S]{1,220}?\\\]|\$[^$]{1,160}\$|"
    r"\\(?:frac|sum|int|alpha|beta|gamma|delta|omega|Omega|mathrm|mathbf|rightarrow|leftarrow)\b)"
)
NMR_RE = re.compile(r"\b(?:1H|13C|19F|31P)\s*NMR\b|\bNMR\b")
SMILES_RE = re.compile(r"\[START_SMILES\].{1,220}?\[END_SMILES\]|\bSMILES\b[:\s]+[A-Za-z0-9@+\-\[\]\(\)=#$\\/]{5,}")
CHEM_PAREN_RE = re.compile(r"(?:\([A-Z][A-Za-z0-9]*\)\d*)+[A-Z][A-Za-z0-9]*")
EQUATION_RE = re.compile(r"\b[A-Za-z0-9_{}^\\()+\-*/=<>≤≥≈≠→←↔]{2,}\s*(?:=|->|→|←|↔|≤|≥|≈|≠)\s*[A-Za-z0-9_{}^\\()+\-*/=<>≤≥≈≠→←↔]{1,}")
SEQUENCE_RE = re.compile(r"\b[ACGTUNacgtun]{12,}\b")
PROTEIN_SEQ_RE = re.compile(r"\b[ACDEFGHIKLMNPQRSTVWY]{15,}\b")
SNP_RE = re.compile(r"\brs\d+\b|\bc\.\d+[ACGT]>[ACGT]\b|\bp\.[A-Z][a-z]{2}\d+[A-Z][a-z]{2}\b")
GENE_SYMBOL_RE = re.compile(r"\b[A-Z]{2,}[A-Z0-9-]{0,8}\d?\b")
CODE_RE = re.compile(
    r"```[\s\S]{1,800}?```|`[^`]{2,120}`|\b(?:def|class|import|from|return|raise)\s+[A-Za-z_]\w*|"
    r"\b[A-Za-z_]\w*\s*\(|\b(?:np|pd|torch|tf|sklearn|plt|os|sys|json|re)\.[A-Za-z_]\w*|"
    r"(?:/[\w.-]+){2,}"
)
SPECIAL_SYMBOL_RE = re.compile(r"[μµαβγδΩωλθπσ×÷±−→←↔≤≥≈≠∞∑∫√°¹²³₀-₉^_{}\\]")

ELEMENTS = {
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
    "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr",
    "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe",
    "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra",
    "Ac", "Th", "Pa", "U", "Np", "Pu",
}

COMMON_NON_TERMS = {
    "presented", "features", "feature", "suggestive", "prolonged", "treatment", "condition", "improved",
    "associated", "generalized", "clinical", "diagnosis", "question", "answer", "option", "options", "correct",
    "following", "identify", "choice", "select", "choose", "statement", "example", "method", "result", "results",
    "study", "studies", "system", "systems", "model", "models", "analysis", "process", "value", "values",
    "increase", "decrease", "higher", "lower", "important", "significant", "different", "similar", "gases", "gase",
}
ABBR_STOPWORDS = {"THE", "AND", "FOR", "THIS", "TRUE", "FALSE", "NOT", "YES", "NO", "FROM", "WITH", "THESE", "SELECT", "PICK", "BEST"}

LAB_LABEL_RE = re.compile(
    r"(?<=[A-Za-z0-9/%])"
    r"(?=(?:pH|P(?:a)?O2|P(?:a)?CO2|HCO3|Na|K|Cl|BUN|Cr|creatinine|glucose|lactate|"
    r"WBC|RBC|Hb|Hgb|platelets)\b\s*:?)"
)
FUSED_UNIT_WORD_RE = re.compile(r"\b(Hg|dL|mL|L)(?=(?:calculated|creatinine|glucose|lactate)\b)", re.I)
FUSED_LAB_FRAGMENT_RE = re.compile(
    r"(?:Hg|dL|mEq|L)(?:pH|P(?:a)?O2|P(?:a)?CO2|HCO3|Na|K|Cl|BUN|glucose|creatinine|calculated)",
    re.I,
)
CLINICAL_LAB_MARKERS = {
    "ABG", "ABGS", "BP", "RR", "HR", "O2", "CO2", "PO2", "PAO2", "PCO2", "PACO2", "HCO3",
    "PH", "NA", "K", "CL", "BUN", "CR", "WBC", "RBC", "HB", "HGB",
}
GENE_CONTEXT_RE = re.compile(
    r"\b(gene|genetic|genomic|genotype|mutation|mutant|variant|allele|snp|locus|brca|egfr|"
    r"oncogene|tumou?r suppressor|chromosome|transcript|sequence|sequencing)\b",
    re.I,
)

DOMAIN_AFFIXES = {
    "Clinical Medicine": re.compile(
        r"(itis|emia|aemia|osis|pathy|ectomy|otomy|plasty|scopy|graphy|gram|cyte|blast|coccus|bacillus|mycin|cycline|azole|vir|statin|toxin|ase|oma|uria|pnea|rrhea)$|"
        r"(neuro|cardio|hepato|nephro|onco|osteo|angio|encephal|broncho|gastro|immuno|patho|pharmaco|microbio|hemo|haemo)",
        re.I,
    ),
    "Life Sciences": re.compile(r"(ase|ome|omics|genic|genesis|phyte|phage|cyte|blast|troph|taxon|biotic|enzyme|protein|peptide|ecolog|biofilm|proteo)", re.I),
    "Genomics": re.compile(r"(gene|genom|allele|snp|locus|crispr|grna|srna|mrna|trna|sequence|nucleotide|transcript|plasmid|protein|codon|exon|intron)", re.I),
    "Chemistry": re.compile(r"(methyl|ethyl|propyl|butyl|phenyl|benz|amine|amide|oxide|sulf|phosph|chlor|fluor|brom|iod|acet|nitr|alkyl|aryl|polymer|catal|solvent|lipophil|toxicity|smiles)", re.I),
    "Materials Science": re.compile(r"(lattice|alloy|polymer|composite|crystal|crystalline|diffusion|valence|nanotube|graphene|semiconductor|ferroelectric|perovskite|metall)", re.I),
    "Physics": re.compile(r"(quantum|hamilton|lagrang|thermodynamic|electromagnetic|spectro|phonon|fermion|boson|relativ|diffraction|polarization)", re.I),
    "Earth Science": re.compile(r"(hydro|geo|seism|tectono|sediment|stratig|petro|mineral|oceanograph|limnolog|geomorph|litho)", re.I),
    "Climate Science": re.compile(r"(climat|meteorolog|atmospher|cryosphere|glaciolog|aerosol|radiative|hydrometeor|permafrost|paleoclim)", re.I),
    "Astronomy": re.compile(r"(astro|cosmo|stellar|galax|nebula|quasar|pulsar|exoplanet|redshift|ecliptic)", re.I),
    "Computer Science": re.compile(r"(algorithm|function|runtime|compiler|tensor|numpy|pandas|python|java|javascript|api|dataset|module|exception|parameter)", re.I),
}


def die_if_missing(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"Required file missing or empty: {path}")


def load_vocab(path: Path) -> set:
    vocab = set()
    with path.open(encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line.strip():
                continue
            vocab.add(line.split()[0].strip().lower())
    return vocab


def load_abbreviation_rules(path: Path) -> dict:
    rules = {}
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            abbr = (row.get("abbr") or "").strip()
            if not abbr:
                continue
            item = {
                "abbr": abbr,
                "canonical_reading": (row.get("canonical_reading") or "").strip(),
                "pron_type": (row.get("pron_type") or "other").strip(),
                "confidence_tier": (row.get("confidence_tier") or "low_conf").strip(),
                "rule_id": (row.get("rule_id") or abbr).strip(),
                "notes": (row.get("notes") or "").strip(),
                "is_rule_confirmed": True,
            }
            rules[abbr] = item
            for variant in (row.get("variants") or "").split(","):
                variant = variant.strip()
                if variant:
                    rules[variant] = item
    overrides = {
        "BRCA1": ("BRCA1", "brica one", "mixed_alnum", "low_conf", "override_brca1"),
        "SDS-PAGE": ("SDS-PAGE", "s d s page", "mixed_alnum", "high_conf", "override_sds_page"),
        "Ni-NTA": ("Ni-NTA", "nickel n t a", "mixed_alnum", "high_conf", "override_ni_nta"),
        "NMR": ("NMR", "n m r", "spell_out", "high_conf", "override_nmr"),
        "CT": ("CT", "c t", "spell_out", "high_conf", "override_ct"),
        "MRI": ("MRI", "m r i", "spell_out", "high_conf", "override_mri"),
        "EEG": ("EEG", "e e g", "spell_out", "high_conf", "override_eeg"),
        "ECG": ("ECG", "e c g", "spell_out", "high_conf", "override_ecg"),
        "CNS": ("CNS", "c n s", "spell_out", "high_conf", "override_cns"),
        "AHP": ("AHP", "a h p", "spell_out", "high_conf", "override_ahp"),
        "GIS": ("GIS", "g i s", "spell_out", "high_conf", "override_gis"),
        "pH": ("pH", "p h", "camel_case", "high_conf", "override_ph"),
        "dL": ("dL", "deciliter", "unit", "high_conf", "override_dl"),
        "mL": ("mL", "milliliter", "unit", "high_conf", "override_ml"),
        "uL": ("uL", "microliter", "unit", "high_conf", "override_ul"),
        "µL": ("µL", "microliter", "unit", "high_conf", "override_microliter"),
        "μL": ("μL", "microliter", "unit", "high_conf", "override_microliter"),
        "mEq": ("mEq", "milliequivalent", "unit", "high_conf", "override_meq"),
        "mmHg": ("mmHg", "millimeters of mercury", "unit", "high_conf", "override_mmhg"),
        "eV": ("eV", "electron volt", "unit", "high_conf", "override_ev"),
        "meV": ("meV", "milli electron volt", "unit", "high_conf", "override_mev"),
        "CO": ("CO", "carbon monoxide", "chemical_formula", "high_conf", "override_co"),
        "CO2": ("CO2", "carbon dioxide", "chemical_formula", "high_conf", "override_co2"),
        "O2": ("O2", "oxygen", "chemical_formula", "high_conf", "override_o2"),
        "HCO3": ("HCO3", "bicarbonate", "chemical_formula", "high_conf", "override_hco3"),
        "PCO2": ("PCO2", "p c o two", "mixed_alnum", "high_conf", "override_pco2"),
        "PO2": ("PO2", "p o two", "mixed_alnum", "high_conf", "override_po2"),
        "BP": ("BP", "blood pressure", "clinical_abbreviation", "high_conf", "override_bp"),
        "RR": ("RR", "respiratory rate", "clinical_abbreviation", "high_conf", "override_rr"),
        "HR": ("HR", "heart rate", "clinical_abbreviation", "high_conf", "override_hr"),
        "ABG": ("ABG", "arterial blood gas", "clinical_abbreviation", "high_conf", "override_abg"),
        "ABGs": ("ABG", "arterial blood gases", "clinical_abbreviation", "high_conf", "override_abgs"),
        "BUN": ("BUN", "blood urea nitrogen", "clinical_abbreviation", "high_conf", "override_bun"),
        "BiPAP": ("BiPAP", "bye pap", "clinical_abbreviation", "low_conf", "override_bipap"),
        "Bi-pap": ("BiPAP", "bye pap", "clinical_abbreviation", "low_conf", "override_bipap_hyphen"),
        "Bi-PAP": ("BiPAP", "bye pap", "clinical_abbreviation", "low_conf", "override_bipap_hyphen"),
        "COPD": ("COPD", "c o p d", "spell_out", "high_conf", "override_copd"),
        "IV": ("IV", "intravenous", "clinical_abbreviation", "high_conf", "override_iv"),
    }
    for surface, (abbr, reading, pron_type, tier, rule_id) in overrides.items():
        rules[surface] = {
            "abbr": abbr,
            "canonical_reading": reading,
            "pron_type": pron_type,
            "confidence_tier": tier,
            "rule_id": rule_id,
            "notes": "local v3 override",
            "is_rule_confirmed": True,
        }
    return rules


def load_denylist(path: Path) -> set:
    return {line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()}


def safe_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    if isinstance(value, (list, tuple)):
        return " ".join(safe_text(x) for x in value)
    return str(value)


def normalize_scoring_text(text: str) -> str:
    text = safe_text(text)
    # Dataset exports sometimes concatenate lab-panel fields, producing fake
    # tokens such as HgPCO2, LHCO3, LBUN, and dLglucose. Normalize only for
    # feature extraction; the original question text remains unchanged.
    text = re.sub(r",(?=[A-Za-z])", ", ", text)
    text = re.sub(r"(?<=[A-Za-z0-9])\.(?=[A-Z])", ". ", text)
    text = FUSED_UNIT_WORD_RE.sub(r"\1 ", text)
    text = LAB_LABEL_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def unique_keep_order(items):
    seen = set()
    out = []
    for item in items:
        if item is None:
            continue
        key = json.dumps(item, sort_keys=True, ensure_ascii=False) if isinstance(item, dict) else str(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def normalize_abbreviation(surface: str) -> str:
    token = surface.strip()
    if len(token) > 2 and token.endswith("s") and ABBR_PATTERN.fullmatch(token[:-1]):
        token = token[:-1]
    return token


def infer_pron_type(surface: str) -> str:
    if any(ch.isdigit() for ch in surface) and any(ch.isalpha() for ch in surface):
        return "mixed_alnum"
    if any(ch.islower() for ch in surface) and any(ch.isupper() for ch in surface):
        return "camel_case"
    if surface.isupper():
        return "spell_out"
    return "other"


def spell_reading(surface: str) -> str:
    words = []
    digit_words = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}
    for ch in surface.replace("-", " "):
        if ch.isalpha():
            words.append(ch.lower())
        elif ch.isdigit():
            words.append(digit_words[ch])
        elif ch.isspace():
            continue
    return " ".join(words)


def extract_abbreviations(text: str, domain: str, vocab10: set, rules: dict, denylist: set) -> list:
    hits = []
    seen = set()
    for regex in (HYPHEN_ABBR_PATTERN, ABBR_PATTERN):
        for match in regex.finditer(text):
            surface = match.group(0)
            if surface.lower().endswith("-year-old"):
                continue
            if regex is HYPHEN_ABBR_PATTERN and surface not in rules:
                if re.fullmatch(r"[A-Z][a-z]+-[A-Z][a-z]+", surface):
                    continue
                if sum(1 for ch in surface if ch.isupper()) < 2:
                    continue
            if not any(ch.isupper() for ch in surface):
                continue
            normalized = normalize_abbreviation(surface)
            rule = rules.get(surface) or rules.get(normalized)
            if normalized in denylist or surface in denylist or normalized.upper() in ABBR_STOPWORDS:
                continue
            if not rule and normalized in {"II", "III", "IV", "VI", "VII", "VIII", "IX", "XI", "XII"}:
                continue
            if not rule and domain == "Chemistry" and re.fullmatch(r"[BCNOFPSI0-9]{2,12}", surface):
                continue
            if not rule and normalized.isupper() and normalized.lower() in vocab10 and len(normalized) > 2:
                continue
            key = (match.start(), match.end(), normalized)
            if key in seen:
                continue
            seen.add(key)
            if rule:
                item = {
                    "surface": surface,
                    "abbr": rule["abbr"],
                    "canonical_reading": rule["canonical_reading"],
                    "pron_type": rule["pron_type"],
                    "confidence_tier": rule["confidence_tier"],
                    "rule_id": rule["rule_id"],
                    "span_start": match.start(),
                    "span_end": match.end(),
                    "is_rule_confirmed": True,
                }
            else:
                pron_type = infer_pron_type(surface)
                item = {
                    "surface": surface,
                    "abbr": normalized,
                    "canonical_reading": spell_reading(surface) if pron_type in {"spell_out", "mixed_alnum", "camel_case"} else "",
                    "pron_type": pron_type,
                    "confidence_tier": "candidate_only",
                    "rule_id": "",
                    "span_start": match.start(),
                    "span_end": match.end(),
                    "is_rule_confirmed": False,
                }
            hits.append(item)
    hits.sort(key=lambda x: (x["span_start"], x["span_end"], x["surface"]))
    return hits


def is_chemical_formula_token(token: str) -> bool:
    if len(token) < 2 or not re.search(r"[A-Z]", token):
        return False
    if token.isupper() and not re.search(r"\d", token) and len(token) <= 4:
        return False
    pos = 0
    parts = []
    while pos < len(token):
        m = re.match(r"[A-Z][a-z]?", token[pos:])
        if not m:
            return False
        sym = m.group(0)
        if sym not in ELEMENTS:
            return False
        pos += len(sym)
        m2 = re.match(r"\d*", token[pos:])
        pos += len(m2.group(0))
        parts.append(sym)
    return len(parts) >= 2 and (len(set(parts)) >= 2 or bool(re.search(r"\d", token)))


def extract_regex_spans(regex, text, limit=80):
    spans = []
    for m in regex.finditer(text):
        s = SPACE_RE.sub(" ", m.group(0).strip())
        if 1 < len(s) <= limit:
            spans.append(s)
    return unique_keep_order(spans)


def extract_chemical_formulas(text: str) -> list:
    spans = []
    spans.extend(extract_regex_spans(NMR_RE, text, 80))
    spans.extend(extract_regex_spans(SMILES_RE, text, 240))
    spans.extend(extract_regex_spans(CHEM_PAREN_RE, text, 80))
    for raw in re.findall(r"\b[A-Z][A-Za-z0-9]{1,20}\b", text):
        if is_chemical_formula_token(raw):
            spans.append(raw)
    return unique_keep_order(spans)


def extract_specials(text: str, domain: str) -> dict:
    units = extract_regex_spans(UNIT_RE, text, 80)
    formulas = []
    formulas.extend(extract_regex_spans(LATEX_RE, text, 220))
    formulas.extend(extract_regex_spans(EQUATION_RE, text, 180))
    formulas.extend(extract_chemical_formulas(text))
    gene_seq = extract_regex_spans(SEQUENCE_RE, text, 220)
    if domain in {"Genomics", "Life Sciences", "Clinical Medicine"}:
        gene_seq.extend(extract_regex_spans(PROTEIN_SEQ_RE, text, 220))
        gene_seq.extend(extract_regex_spans(SNP_RE, text, 80))
        for m in GENE_SYMBOL_RE.finditer(text):
            s = m.group(0)
            upper = s.upper()
            local_context = text[max(0, m.start() - 80): m.end() + 80]
            if upper in CLINICAL_LAB_MARKERS:
                continue
            if domain == "Clinical Medicine" and not GENE_CONTEXT_RE.search(local_context):
                continue
            if s not in ABBR_STOPWORDS and len(s) <= 12 and (re.search(r"\d", s) or domain == "Genomics"):
                gene_seq.append(s)
    code_spans = extract_regex_spans(CODE_RE, text, 220) if domain == "Computer Science" else []
    special_expr = extract_regex_spans(SPECIAL_SYMBOL_RE, text, 10)
    return {
        "units": unique_keep_order(units),
        "formulas": unique_keep_order(formulas),
        "gene_or_sequence_spans": unique_keep_order(gene_seq),
        "code_spans": unique_keep_order(code_spans),
        "special_expressions": unique_keep_order(special_expr),
    }


def token_base(token: str) -> str:
    tok = token.strip("'’_-").lower()
    if tok.endswith("'s"):
        tok = tok[:-2]
    if len(tok) > 3 and tok.endswith("s"):
        tok_singular = tok[:-1]
        return tok_singular
    return tok


def is_domain_advanced(term: str, surface: str, domain: str, context: str, abbreviation_surfaces: set) -> bool:
    lower = term.lower()
    if lower in COMMON_NON_TERMS or len(lower) < 4:
        return False
    if surface in abbreviation_surfaces:
        return True
    if re.search(r"\d", surface) and domain in {"Genomics", "Chemistry", "Clinical Medicine", "Computer Science", "Materials Science"}:
        return True
    if DOMAIN_AFFIXES.get(domain) and DOMAIN_AFFIXES[domain].search(lower):
        return True
    if domain in {"Clinical Medicine", "Life Sciences"} and re.search(r"\b[A-Z][a-z]+ [a-z]{3,}\b", context) and surface[0].isupper():
        return True
    if domain == "Chemistry" and re.search(r"(chloro|fluoro|bromo|iodo|methyl|ethyl|hydroxy|carbox|benz|phenyl)", lower):
        return True
    if domain == "Computer Science" and ("_" in surface or "." in surface):
        return True
    return False


def extract_oov_terms(text: str, domain: str, vocab1: set, vocab10: set, abbreviation_surfaces: set) -> dict:
    min1_terms = []
    min10_terms = []
    advanced = []
    for m in TOKEN_RE.finditer(text):
        surface = m.group(0).strip()
        if len(surface) > 45:
            continue
        if FUSED_LAB_FRAGMENT_RE.search(surface):
            continue
        base = token_base(surface)
        if not base or base in COMMON_NON_TERMS:
            continue
        oov1 = base not in vocab1
        oov10 = base not in vocab10
        if not oov10:
            continue
        if not is_domain_advanced(base, surface, domain, text[max(0, m.start() - 80): m.end() + 80], abbreviation_surfaces):
            continue
        if oov1:
            min1_terms.append(surface)
        if oov10:
            min10_terms.append(surface)
        advanced.append(surface)
    return {
        "gigaspeech_oov_min1_terms": unique_keep_order(min1_terms),
        "gigaspeech_oov_min10_terms": unique_keep_order(min10_terms),
        "domain_advanced_terms": unique_keep_order(advanced),
    }


def text_easy_proxy(rec: dict, feature_count: int) -> dict:
    q = safe_text(rec.get("question"))
    answer = safe_text(rec.get("answer"))
    options = rec.get("options") or []
    words = len(q.split())
    reasons = []
    is_easy = True
    if rec.get("question_type") == "MCQA" and 2 <= len(options) <= 10:
        reasons.append("clear_mcqa_options")
    if answer and len(answer.split()) <= 40:
        reasons.append("short_or_exact_answer")
    if words <= 260:
        reasons.append("self_contained_question_length")
    if feature_count > 0:
        reasons.append("difficulty_concentrated_in_speech_sensitive_spans")
    if words > 520:
        is_easy = False
        reasons.append("long_context_dominant")
    if feature_count == 0:
        is_easy = False
        reasons.append("no_speech_sensitive_feature")
    return {"is_likely_text_easy": is_easy, "reasons": reasons}


def classify_pronunciation(abbr_hits: list, formulas: list) -> dict:
    letter_spelled = []
    conventional = []
    review = []
    for hit in abbr_hits:
        item = {
            "surface": hit["surface"],
            "abbr": hit["abbr"],
            "canonical_reading": hit.get("canonical_reading", ""),
            "pron_type": hit.get("pron_type", "other"),
            "confidence_tier": hit.get("confidence_tier", "candidate_only"),
            "rule_id": hit.get("rule_id", ""),
        }
        if hit.get("is_rule_confirmed"):
            if hit.get("pron_type") == "spell_out":
                letter_spelled.append(item)
            else:
                conventional.append(item)
        else:
            review.append(item)
    for span in formulas:
        if span == "1H NMR":
            conventional.append({"surface": span, "canonical_reading": "proton n m r", "pron_type": "chemistry_conventional", "confidence_tier": "high_conf", "rule_id": "override_1h_nmr"})
        elif span == "13C NMR":
            conventional.append({"surface": span, "canonical_reading": "carbon-thirteen n m r", "pron_type": "chemistry_conventional", "confidence_tier": "high_conf", "rule_id": "override_13c_nmr"})
    return {
        "letter_spelled": unique_keep_order(letter_spelled),
        "conventional_readings": unique_keep_order(conventional),
        "needs_manual_pronunciation_check": unique_keep_order(review),
    }


def build_v3_metadata(rec: dict, vocab1: set, vocab10: set, abbr_rules: dict, denylist: set) -> tuple:
    text = normalize_scoring_text(" ".join([safe_text(rec.get("question")), safe_text(rec.get("options")), safe_text(rec.get("answer"))]))
    domain = rec.get("domain", "")
    abbr_hits = extract_abbreviations(text, domain, vocab10, abbr_rules, denylist)
    abbr_surfaces = {h["surface"] for h in abbr_hits} | {h["abbr"] for h in abbr_hits}
    specials = extract_specials(text, domain)
    oov = extract_oov_terms(text, domain, vocab1, vocab10, abbr_surfaces)

    features = {
        **oov,
        "abbreviations": abbr_hits,
        "special_expressions": specials["special_expressions"],
        "units": specials["units"],
        "formulas": specials["formulas"],
        "gene_or_sequence_spans": specials["gene_or_sequence_spans"],
        "code_spans": specials["code_spans"],
        "spoken_written_mismatches": [],
    }
    mismatch_spans = []
    mismatch_spans.extend([h["surface"] for h in abbr_hits])
    for key in ["units", "formulas", "gene_or_sequence_spans", "code_spans", "special_expressions"]:
        mismatch_spans.extend(features[key])
    features["spoken_written_mismatches"] = unique_keep_order(mismatch_spans)

    core = set()
    if features["gigaspeech_oov_min1_terms"]:
        core.add("strong_oov_min1")
    if features["gigaspeech_oov_min10_terms"]:
        core.add("weak_oov_min10")
    if abbr_hits:
        core.add("abbreviation")
    if features["formulas"] or features["special_expressions"]:
        core.add("formula_or_expression")
    if features["units"]:
        core.add("unit")
    if features["gene_or_sequence_spans"]:
        core.add("gene_or_sequence")
    if features["code_spans"]:
        core.add("code_expression")
    if features["spoken_written_mismatches"]:
        core.add("spoken_written_mismatch")

    proxy = text_easy_proxy(rec, len(core))
    score = 0
    reasons = []
    # Strong OOV implies min10 OOV, so do not double-count both vocabulary
    # thresholds in the score. Both are still retained as features.
    if "strong_oov_min1" in core:
        score += 30
        reasons.append("strong_oov_min1")
    elif "weak_oov_min10" in core:
        score += 15
        reasons.append("weak_oov_min10")
    if "abbreviation" in core:
        score += 20
        reasons.append("abbreviation")
    if {"formula_or_expression", "unit", "gene_or_sequence", "code_expression"} & core:
        score += 25
        reasons.append("exact_text_expression")
    if "spoken_written_mismatch" in core:
        score += 10
        reasons.append("spoken_written_mismatch")
    if proxy["is_likely_text_easy"]:
        score += 10
        reasons.append("text_easy_proxy")
    if len(core) == 0 and len(safe_text(rec.get("question"))) < 220:
        score -= 20
        reasons.append("ordinary_short_text_no_professional_expression")
    if len(safe_text(rec.get("question")).split()) > 520 and len(core) < 2:
        score -= 15
        reasons.append("long_context_dominant")
    score = max(0, min(100, score))
    level = "high" if score >= 75 else "medium" if score >= 60 else "low" if score >= 45 else "very_low"
    critical = []
    for key in [
        "gigaspeech_oov_min1_terms",
        "gigaspeech_oov_min10_terms",
        "abbreviations",
        "units",
        "formulas",
        "gene_or_sequence_spans",
        "code_spans",
        "special_expressions",
    ]:
        values = features[key]
        if key == "abbreviations":
            critical.extend(h["surface"] for h in values)
        else:
            critical.extend(values)
    critical = unique_keep_order(critical)[:40]
    metadata = {
        "speech_sensitive_score_v3": score,
        "speech_sensitive_level": level,
        "speech_sensitive_reasons": reasons,
        "core_features": sorted(core),
        "speech_sensitive_features": features,
        "pronunciation": classify_pronunciation(abbr_hits, features["formulas"]),
        "text_easy_proxy": proxy,
        "critical_spans": critical,
        "requires_exact_text": bool({"formula_or_expression", "unit", "gene_or_sequence", "code_expression"} & core),
    }
    return metadata, core


def is_strict_candidate(rec: dict) -> bool:
    meta = rec["speech_metadata"]
    score = meta["speech_sensitive_score_v3"]
    core_count = len(meta.get("core_features", []))
    return score >= 60 or (score >= 45 and core_count >= 2)


def is_relaxed_candidate(rec: dict) -> bool:
    meta = rec["speech_metadata"]
    return meta["speech_sensitive_score_v3"] >= 40 and len(meta.get("core_features", [])) >= 1


def norm_question(text: str) -> str:
    return SPACE_RE.sub(" ", safe_text(text).lower()).strip()


def score_key(rec: dict):
    meta = rec["speech_metadata"]
    return (
        -meta["speech_sensitive_score_v3"],
        -len(meta.get("core_features", [])),
        -len(meta.get("critical_spans", [])),
        rec.get("dataset", ""),
        rec.get("id", ""),
    )


def desired_dataset_targets(domain: str, quota: int, pools: dict) -> dict:
    datasets = sorted(pools)
    if len(datasets) == 1:
        return {datasets[0]: min(quota, len(pools[datasets[0]]))}
    min_floor = min(50, max(10, int(round(quota * 0.08))))
    targets = {ds: min(min_floor, len(pools[ds])) for ds in datasets}
    remaining = quota - sum(targets.values())
    if remaining <= 0:
        return trim_targets(targets, quota)
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


def trim_targets(targets: dict, quota: int) -> dict:
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
        qkey = norm_question(rec.get("question"))
        if rec["id"] in used_ids or qkey in used_questions:
            continue
        taken.append(rec)
        used_ids.add(rec["id"])
        used_questions.add(qkey)
    return taken


def sample_records(scored_records: list) -> list:
    best_by_question = {}
    for rec in sorted(scored_records, key=score_key):
        qkey = norm_question(rec.get("question"))
        if qkey and qkey not in best_by_question:
            best_by_question[qkey] = rec
    deduped = list(best_by_question.values())
    strict_pools = defaultdict(lambda: defaultdict(list))
    relaxed_pools = defaultdict(lambda: defaultdict(list))
    all_pools = defaultdict(lambda: defaultdict(list))
    for rec in deduped:
        domain = rec.get("domain")
        dataset = rec.get("dataset")
        if domain not in QUOTAS:
            continue
        all_pools[domain][dataset].append(rec)
        if is_relaxed_candidate(rec):
            relaxed_pools[domain][dataset].append(rec)
        if is_strict_candidate(rec):
            strict_pools[domain][dataset].append(rec)
    for pools in (strict_pools, relaxed_pools, all_pools):
        for domain in pools:
            for dataset in pools[domain]:
                pools[domain][dataset].sort(key=score_key)

    selected = []
    used_ids = set()
    used_questions = set()
    for domain, quota in QUOTAS.items():
        pools = strict_pools[domain]
        if sum(len(v) for v in pools.values()) < quota:
            pools = relaxed_pools[domain]
        targets = desired_dataset_targets(domain, quota, pools)
        domain_selected = []
        for dataset, target in sorted(targets.items(), key=lambda x: (-x[1], x[0])):
            domain_selected.extend(take_from_pool(pools[dataset], target, used_ids, used_questions))
        if len(domain_selected) < quota:
            merged = []
            for dataset in sorted(relaxed_pools[domain]):
                merged.extend(relaxed_pools[domain][dataset])
            merged.sort(key=score_key)
            domain_selected.extend(take_from_pool(merged, quota - len(domain_selected), used_ids, used_questions))
        if len(domain_selected) < quota:
            merged = []
            for dataset in sorted(all_pools[domain]):
                merged.extend(all_pools[domain][dataset])
            merged.sort(key=score_key)
            domain_selected.extend(take_from_pool(merged, quota - len(domain_selected), used_ids, used_questions))
        selected.extend(domain_selected[: min(quota, DOMAIN_CAP)])
    return selected


def write_csv(path: Path, fieldnames: list, rows: list) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def write_reports(scored_records: list, selected: list, term_stats: dict, rejected_counter: Counter, feature_counter: Counter) -> None:
    selected_ids = {r["id"] for r in selected}
    domain_counts = Counter(r["domain"] for r in selected)
    summary = Counter((r["domain"], r["dataset"], r["question_type"]) for r in selected)
    write_csv(
        OUT_DIR / "selection_summary_v3.csv",
        ["domain", "dataset", "question_type", "selected_count"],
        [{"domain": d, "dataset": ds, "question_type": qt, "selected_count": n} for (d, ds, qt), n in sorted(summary.items())],
    )
    write_csv(
        OUT_DIR / "domain_quota_report_v3.csv",
        ["domain", "target_quota", "final_selected_count", "final_share"],
        [{"domain": d, "target_quota": q, "final_selected_count": domain_counts[d], "final_share": round(domain_counts[d] / max(1, len(selected)), 4)} for d, q in QUOTAS.items()],
    )
    by_dd = Counter((r["domain"], r["dataset"]) for r in selected)
    candidate_dd = Counter((r["domain"], r["dataset"]) for r in scored_records if is_relaxed_candidate(r))
    strict_dd = Counter((r["domain"], r["dataset"]) for r in scored_records if is_strict_candidate(r))
    rows = []
    for domain in QUOTAS:
        datasets = sorted({ds for d, ds in candidate_dd if d == domain} | {ds for d, ds in by_dd if d == domain})
        for dataset in datasets:
            rows.append({
                "domain": domain,
                "dataset": dataset,
                "relaxed_candidates": candidate_dd[(domain, dataset)],
                "strict_candidates": strict_dd[(domain, dataset)],
                "selected": by_dd[(domain, dataset)],
                "domain_selected": domain_counts[domain],
                "dataset_share_in_domain": round(by_dd[(domain, dataset)] / max(1, domain_counts[domain]), 4),
            })
    write_csv(OUT_DIR / "dataset_balance_report_v3.csv", ["domain", "dataset", "relaxed_candidates", "strict_candidates", "selected", "domain_selected", "dataset_share_in_domain"], rows)

    review = {}
    for rec in scored_records:
        for item in rec["speech_metadata"]["pronunciation"]["needs_manual_pronunciation_check"]:
            key = item["surface"]
            cur = review.setdefault(key, {"surface": key, "abbr": item.get("abbr", ""), "pron_type": item.get("pron_type", ""), "count": 0, "selected_count": 0, "domains": Counter(), "datasets": Counter(), "example_id": rec["id"]})
            cur["count"] += 1
            cur["selected_count"] += int(rec["id"] in selected_ids)
            cur["domains"][rec["domain"]] += 1
            cur["datasets"][rec["dataset"]] += 1
    review_rows = []
    for _, item in sorted(review.items(), key=lambda kv: (-kv[1]["selected_count"], -kv[1]["count"], kv[0]))[:5000]:
        review_rows.append({
            "surface": item["surface"],
            "abbr": item["abbr"],
            "pron_type": item["pron_type"],
            "count": item["count"],
            "selected_count": item["selected_count"],
            "domains": "; ".join(f"{k}:{v}" for k, v in item["domains"].most_common()),
            "datasets": "; ".join(f"{k}:{v}" for k, v in item["datasets"].most_common()),
            "example_id": item["example_id"],
        })
    write_csv(OUT_DIR / "pronunciation_review_queue.csv", ["surface", "abbr", "pron_type", "count", "selected_count", "domains", "datasets", "example_id"], review_rows)

    oov_rows = []
    for term, item in term_stats.items():
        oov_rows.append({
            "term": term,
            "oov_min1": item["oov_min1"],
            "oov_min10": item["oov_min10"],
            "count": item["count"],
            "selected_count": item["selected_count"],
            "domains": "; ".join(f"{k}:{v}" for k, v in item["domains"].most_common()),
            "datasets": "; ".join(f"{k}:{v}" for k, v in item["datasets"].most_common()),
            "example_question_id": item["example_id"],
        })
    oov_rows.sort(key=lambda r: (-int(r["selected_count"]), -int(r["count"]), r["term"].lower()))
    write_csv(OUT_DIR / "gigaspeech_oov_term_report.csv", ["term", "oov_min1", "oov_min10", "count", "selected_count", "domains", "datasets", "example_question_id"], oov_rows)
    write_csv(OUT_DIR / "rejected_samples_report.csv", ["reason", "count"], [{"reason": k, "count": v} for k, v in rejected_counter.most_common()])
    write_csv(OUT_DIR / "feature_coverage_report_v3.csv", ["feature", "count"], [{"feature": k, "count": v} for k, v in feature_counter.most_common()])

    v2_ids = set()
    if V2_SELECTED.exists():
        with V2_SELECTED.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    v2_ids.add(json.loads(line)["id"])
    overlap = len(v2_ids & selected_ids)
    write_csv(
        OUT_DIR / "v2_v3_comparison_report.csv",
        ["metric", "value"],
        [
            {"metric": "v2_selected_count", "value": len(v2_ids)},
            {"metric": "v3_selected_count", "value": len(selected_ids)},
            {"metric": "overlap_count", "value": overlap},
            {"metric": "replacement_count", "value": max(0, len(selected_ids) - overlap)},
            {"metric": "overlap_rate_vs_v3", "value": round(overlap / max(1, len(selected_ids)), 4)},
        ],
    )


def write_schema() -> None:
    schema = """# Speech Metadata Schema v3

V3 uses two GigaSpeech vocabularies and abbreviation pronunciation rules.

- `gigaspeech_oov_min1_terms`: terms absent from `vocab_min_freq_1.txt`.
- `gigaspeech_oov_min10_terms`: terms absent from `vocab_min_freq_10.txt`.
- `domain_advanced_terms`: OOV terms that also pass domain-specialized filters.
- `abbreviations`: abbreviation hits with surface, normalized abbr, reading, pron_type, confidence_tier, and rule_id.
- `pronunciation.letter_spelled`: known letter-by-letter readings.
- `pronunciation.conventional_readings`: lexicalized or special readings.
- `pronunciation.needs_manual_pronunciation_check`: candidate abbreviations without confirmed reading rules.
- `text_easy_proxy`: rule-based proxy for text-answerable but speech-sensitive samples.
- `speech_sensitive_score_v3`: 0-100 score used for selection.
"""
    (OUT_DIR / "speech_metadata_schema_v3.md").write_text(schema, encoding="utf-8")


def main() -> None:
    for path in [INPUT_JSONL, VOCAB_MIN1, VOCAB_MIN10, ABBR_RULE_FILE, ABBR_DENYLIST_FILE]:
        die_if_missing(path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    vocab1 = load_vocab(VOCAB_MIN1)
    vocab10 = load_vocab(VOCAB_MIN10)
    abbr_rules = load_abbreviation_rules(ABBR_RULE_FILE)
    denylist = load_denylist(ABBR_DENYLIST_FILE)

    scored_records = []
    term_stats = {}
    rejected_counter = Counter()
    feature_counter = Counter()
    score_counter = Counter()
    out_all = OUT_DIR / "all_scored_samples_v3.jsonl"
    with INPUT_JSONL.open(encoding="utf-8") as fin, out_all.open("w", encoding="utf-8") as fout:
        for idx, line in enumerate(fin, start=1):
            if not line.strip():
                continue
            rec = json.loads(line)
            meta, core = build_v3_metadata(rec, vocab1, vocab10, abbr_rules, denylist)
            rec["speech_metadata"] = meta
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            scored_records.append(rec)
            score_counter[meta["speech_sensitive_score_v3"]] += 1
            if core:
                for feat in core:
                    feature_counter[feat] += 1
            else:
                feature_counter["no_core_feature"] += 1
            if not is_strict_candidate(rec):
                if not core:
                    rejected_counter["no_speech_sensitive_feature"] += 1
                elif meta["speech_sensitive_score_v3"] < 45:
                    rejected_counter["score_below_45"] += 1
                else:
                    rejected_counter["score_below_candidate_threshold"] += 1
            for term in meta["speech_sensitive_features"]["domain_advanced_terms"]:
                key = term.lower()
                item = term_stats.setdefault(key, {"term": term, "oov_min1": False, "oov_min10": False, "count": 0, "selected_count": 0, "domains": Counter(), "datasets": Counter(), "example_id": rec["id"]})
                item["count"] += 1
                item["domains"][rec["domain"]] += 1
                item["datasets"][rec["dataset"]] += 1
                if term in meta["speech_sensitive_features"]["gigaspeech_oov_min1_terms"]:
                    item["oov_min1"] = True
                if term in meta["speech_sensitive_features"]["gigaspeech_oov_min10_terms"]:
                    item["oov_min10"] = True
            if idx % 50000 == 0:
                print(f"scored={idx}", flush=True)

    selected = sample_records(scored_records)
    selected_ids = {r["id"] for r in selected}
    for rec in selected:
        for term in rec["speech_metadata"]["speech_sensitive_features"]["domain_advanced_terms"]:
            key = term.lower()
            if key in term_stats:
                term_stats[key]["selected_count"] += 1

    with (OUT_DIR / "selected_5k_6k_v3.jsonl").open("w", encoding="utf-8") as f:
        for rec in selected:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    by_domain = Counter(r["domain"] for r in selected)
    write_reports(scored_records, selected, term_stats, rejected_counter, feature_counter)
    write_schema()
    print("input_scored", len(scored_records))
    print("selected", len(selected))
    print("score_distribution_top", score_counter.most_common(20))
    for domain in QUOTAS:
        print(domain, by_domain[domain])


if __name__ == "__main__":
    main()
