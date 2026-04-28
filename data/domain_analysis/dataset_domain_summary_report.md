# Dataset and Domain Summary

This report summarizes the latest v2 domain analysis files in `domain_analysis/`.

Important taxonomy changes from the older table:

- `ClimaQA_gold`, `ClimaQA_silver`, and climate-related EarthSE records are `Climate Science`, not generic `Earth Science`.
- `MedXpertQA`, `MedMCQA`, `MedQA_USMLE`, and `PubMedQA` are `Clinical Medicine`, not `Life Sciences`.
- `GeneTuring` and `Genome-Bench` are `Genomics`.
- `SciKnowEval` is split into Chemistry, Materials Science, Life Sciences, and Physics, not `General Science`.
- `MMLU`, `ScienceQA`, and ATLAS Mathematics are excluded from this fixed 10-domain taxonomy.

## Dataset Table

| Dataset | Domain | Total | Forms |
|---|---|---:|---|
| ATLAS | Physics; Materials Science; Chemistry; Earth Science; Computer Science; Genomics; Life Sciences; Climate Science | 704 | open_ended 704 |
| Astro-QA | Astronomy | 2,016 | MCQA 1,699; judgment/true_false 317 |
| BigCodeBench | Computer Science | 1,140 | code generation 1,140 |
| BioASQ | Life Sciences | 4,719 | open_ended 4,719 |
| ChemBench | Chemistry | 2,785 | MCQA 2,542; open_ended 243 |
| ClimaQA_gold | Climate Science | 473 | MCQA 292; open_ended 181 |
| ClimaQA_silver | Climate Science | 2,000 | MCQA 1,000; open_ended 1,000 |
| Earth-Gold | Earth Science; Climate Science; Life Sciences | 300 | multi-turn open dialogue 300 |
| Earth-Iron | Earth Science; Climate Science; Life Sciences | 4,133 | open_ended 2,000; MCQA 818; fill_blank 769; judgment/true_false 546 |
| Earth-Silver | Earth Science; Climate Science; Life Sciences | 1,000 | fill_blank 250; MCQA 250; open_ended 250; judgment/true_false 250 |
| GeneTuring | Genomics | 3,302 unique / 16,101 raw | open generation/extraction 3,302 |
| Genome-Bench | Genomics | 661 | MCQA 661 |
| Lab-Bench | Life Sciences | 1,116 | MCQA 1,116 |
| MaScQA | Materials Science | 285 | MCQA 285 |
| MedMCQA | Clinical Medicine | 193,155 | MCQA 193,155 |
| MedQA_USMLE | Clinical Medicine | 12,723 | MCQA 12,723 |
| MedXpertQA | Clinical Medicine | 2,450 | MCQA 2,450 |
| PHYBench | Physics | 100 | open_ended 100 |
| PubMedQA | Clinical Medicine | 1,000 | MCQA 1,000 |
| QCBench | Chemistry | 350 | open numeric/short answer 350 |
| SciCode | Computer Science | 80 | code generation 80 |
| SciKnowEval | Chemistry; Materials Science; Life Sciences; Physics | 22,620 | MCQA 22,620 |
| UGPhysics | Physics | 74 | open_ended 74 |

## Domain Totals

| Domain | Total | Subdomain count | Main datasets | Main forms |
|---|---:|---:|---|---|
| Clinical Medicine | 209,328 | 2824 | MedMCQA 193,155; MedQA_USMLE 12,723; MedXpertQA 2,450; PubMedQA 1,000 | MCQA 209,328 |
| Life Sciences | 11,684 | 35 | SciKnowEval 5,221; BioASQ 4,719; Lab-Bench 1,116; EarthSE_Earth-Iron 422; EarthSE_Earth-Silver 115 | MCQA 6,464; Open-ended 4,969; Fill-in-the-blank 115; True/False 88; Open-ended dialogue 48 |
| Genomics | 4,022 | 18 | GeneTuring 3,302; Genome-Bench 661; ATLAS 59 | Open generation/extraction 3,302; MCQA 661; Open-ended 59 |
| Chemistry | 11,137 | 37 | SciKnowEval 7,885; ChemBench 2,785; QCBench 350; ATLAS 117 | MCQA 10,427; Open-ended 360; Open numeric/short answer 350 |
| Materials Science | 6,190 | 18 | SciKnowEval 5,765; MaScQA 285; ATLAS 140 | MCQA 6,050; Open-ended 140 |
| Physics | 4,098 | 13 | SciKnowEval 3,749; ATLAS 175; PHYBench 100; UGPhysics 74 | MCQA 3,749; Open-ended 349 |
| Earth Science | 2,861 | 78 | EarthSE_Earth-Iron 2,087; EarthSE_Earth-Silver 512; EarthSE_Earth-Gold 184; ATLAS 78 | Open-ended 1,225; MCQA 537; Fill-in-the-blank 503; True/False 412; Open-ended dialogue 184 |
| Climate Science | 4,569 | 19 | ClimaQA_silver 2,000; EarthSE_Earth-Iron 1,624; ClimaQA_gold 473; EarthSE_Earth-Silver 373; EarthSE_Earth-Gold 68 | Open-ended 2,108; MCQA 1,696; Fill-in-the-blank 401; True/False 296; Open-ended dialogue 68 |
| Astronomy | 2,016 | 1 | Astro-QA 2,016 | MCQA 1,699; True/False 317 |
| Computer Science | 1,281 | 6 | BigCodeBench 1,140; SciCode 80; ATLAS 61 | Code generation 1,220; Open-ended 61 |

## Subdomains by Domain

The full subdomain table is `merged_domain_subdomain_counts.csv`. Top subdomains are listed below; Clinical Medicine has many fine-grained MedMCQA topics, so only top 30 are shown here.

### Clinical Medicine

Total: 209,328; subdomains: 2824.

Medical Exam Qa (12,723), Surgery (10,702), Dental (10,405), Medicine (9,425), Pathology (8,429), Pharmacology (7,346), Social & Preventive Medicine (6,220), Microbiology (5,912), Gynaecology & Obstetrics (5,871), Anatomy (5,804), Physiology (4,319), Pediatrics (4,273), Ophthalmology (4,138), Biochemistry (4,108), Forensic Medicine (3,655), Unknown (3,418), Radiology (2,837), Ent (2,480), Clinical Specialist Qa (2,450), Psychiatry (2,368), Anaesthesia (1,695), Anatomy: General Anatomy (1,691), Skin (1,216), Biomedical Literature Qa (1,000), Orthopaedics (902), Pathology: General Pathology (874), Social & Preventive Medicine: Communicable Diseases (841), Microbiology: Virology (828), Medicine: C.V.S (747), Surgery: G.I.T (737), ... plus 2794 more in `merged_domain_subdomain_counts.csv`

### Life Sciences

Total: 11,684; subdomains: 35.

Biomedical Qa (4,719), Bioinspiredllm Qa (1,484), Bio Rxiv Qa (1,320), Biomedical Laboratory (1,116), Pub Med Qa (896), Detailed Understanding (444), Protocol Qa (317), Aquatic Ecology And Limnological Ecology (263), Chem Rxiv Qa (220), Proteotoxicity Prediction Mcq (195), Gb1 Ftness Prediction (100), Protein Protein Interaction (100), Stability Prediction (100), Ecosystem Ecology (96), Biosphere (48), Biogeochemistry (46), Laboratory Safety Test Mcq (45), Population Ecology (41), Landscape Ecology (32), Biogeography (27), Biophysics And Biochemistry (15), Community Ecology (13), Molecular Biology And Biotechnology (11), Restoration Ecology (7), Ecology (5), Cell Biology (4), Ecological Engineering (4), Regional Ecology (4), Neuroscience And Psychology (3), Physiology And Integrative Biology (3), Immunology (2), Agricultural Ecology (1), Historical Ecology (1), Soil Ecology (1), Urban Ecology (1)

### Genomics

Total: 4,022; subdomains: 18.

Genome Protocol Qa (661), Human Genome Dna Alignment Programming (300), Multi Species Dna Alignment Programming (300), Snp Location (300), Gene Disease Association (201), Gene Alias (200), Gene Location (200), Gene Name Conversion (200), Gene Name Extraction (200), Gene Ontology (200), Gene Snp Association (200), Human Genome Dna Alignment (200), Multi Species Dna Alignment (200), Protein Coding Genes (200), Tf Regulation (200), Dna Sequence Extraction (101), Amino Acid Translation (100), Genetics And Bioinformatics (59)

### Chemistry

Total: 11,137; subdomains: 37.

Chem Rxiv Qa (2,525), Bioinspiredllm Qa (1,514), Chemical Preference (1,000), Detailed Understanding (703), Toxicity And Safety (675), Organic Chemistry (438), Reaction Pred Mcq (400), Physical Chemistry (373), Lipophilicity Value Prediction (340), Reaction Mechanism Inference (310), S2W (301), Retrosynthesis Mcq (300), I2W (299), Inorganic Chemistry (207), Laboratory Safety Test Mcq (194), Analytical Chemistry (188), Pub Med Qa (177), General Chemistry (165), Esol Value Prediction (160), Mol Toxicity Mcq (153), Bio Rxiv Qa (150), Materials Science (83), Protocol Qa (59), S2 Rotbonds (59), S2 Hbonddonor (56), S2 Hbondacc (50), I2 Atoms (40), Technical Chemistry (40), Quantum Chemistry (39), I2 Rotbonds (33), I2 Heavyatoms (27), Biochemistry (24), I2 Hbonddonor (21), I2 Hbondacc (14), Polymer Chemistry (12), Theoretical And Computational Chemistry (6), Chemical Engineering And Technology (2)

### Materials Science

Total: 6,190; subdomains: 18.

Material Literature Qa (2,637), Safety Mcq (1,010), Material Toxicity Mcq (612), Material Detailed Understanding (400), Materials Science General (285), Eah And Fe Analysis (246), Density And First Ip Factors (235), Material Data Extraction (170), Lattice Volume Calculation (160), Diffusion Rate Analysis (149), Valence Electron Difference Calculation (146), Composite Materials (64), Organic Polymer Materials (23), Material Synthesis And Processing (15), Metallic Materials (13), Material Testing And Analysis Technology (11), Fundamentals Of Materials Science (7), Material Surfaces And Interfaces (7)

### Physics

Total: 4,098; subdomains: 13.

Physics Literature Qa (1,839), General Physics Calculation (800), Security Mcq (416), Physics Detailed Understanding (400), Laboratory Safety Test Mcq (294), Physics General (174), Electrodynamics (50), Classical Mechanics (48), Quantum Mechanics (33), Thermodynamics And Statistical Physics (22), Relativity (11), Fluid Mechanics (6), Astrophysics (5)

### Earth Science

Total: 2,861; subdomains: 78.

Ocean Physics (494), Sedimentology (229), River Hydrology And Estuarine Hydrology (213), Groundwater Hydrology (147), Physical Geography (129), Mineralogy And Petrology (121), Tectonophysics (102), Seismology (99), Hydrological Measurement (85), Quaternary Geology (80), Atmosphere (68), Hydrosphere (67), Hydrological Physics (62), Lithosphere (49), Limnology (48), Remote Sensing Oceanography (48), Experimental Geophysics (47), Stratigraphy (46), Ocean Chemistry (42), Ecohydrology (40), Engineering Geology (40), Ocean Geology (40), Hydrogeology (39), Geodynamics (36), Computational Geophysics (32), Structural Geology (26), Geomagnetism (25), Volcanology (25), Environmental Oceanography (22), Urban Geography (22), Other Disciplines In Geography (21), Other Disciplines In Solid Earth Geophysics (21), Regional Hydrology (21), Geodesy (19), Geography (19), Geomorphology (17), Human Geography (16), Ocean Biology (16), Geothermal Science (15), Economic Geology (14), Exploration Geophysics (14), Environmental Geology (13), Hydrology (13), Regional Geography (11), Hydrological Engineering (10), Remote Sensing Geology (10), Paleogeography (9), Space Physics (9), Solid Earth Geophysics (7), Hydrological Geography (6), Geoelectricity (5), Geology (5), Marine Science (5), Gravimetry (4), Geochemistry (3), Historical Geography (3), Other (3), Paleomagnetism (3), None (2), Polar Oceanography (2), Regional Geology (2), Stellar Astronomy (2), Urban Hydrology (2), Water Treatment And Wastewater Management (2), Academic Publishing And Peer Review (1), Hydrological Economics (1), Hydrological Modeling (1), Intellectual Property Law (1), Machine Learning And Artificial Intelligence (1), Machine Learning And Data Science (1), Mathematics (1), Metamorphic Petrology (1), Not Applicable (1), Other Disciplines In Geology (1), Paleontology (1), Soil Science (1), Solar Physics (1), Tourism Geography (1)

### Climate Science

Total: 4,569; subdomains: 19.

Climate Science (2,473), Meteorology (466), Climatology (393), Atmospheric Physics (261), Atmospheric Chemistry (241), Glaciology (211), Atmospheric Remote Sensing (149), Numerical Weather Prediction And Simulation (110), Hydrometeorology (89), Cryosphere (68), Hydrological Meteorology (50), Polar Climate Science (24), Paleoclimatology (15), Polar Oceanography (7), Permafrost Science (5), Solar Physics (4), Air Quality And Pollution (1), Cosmology And Astrophysics (1), Solar Energy And Solar Radiation (1)

### Astronomy

Total: 2,016; subdomains: 1.

Astronomy General (2,016)

### Computer Science

Total: 1,281; subdomains: 6.

Programming (1,140), Scientific Computing (80), Computer System Architecture (27), Artificial Intelligence (16), Fundamental Disciplines Of Computer Science And Technology (15), Computer Software (3)

## Summary of `merged_dataset_summary.csv`

- Dataset rows: 23.
- Sum of `total_records`: 270,079.
- Sum of `question_like_count`: 257,186.
- Multi-domain datasets: ATLAS, EarthSE_Earth-Gold, EarthSE_Earth-Iron, EarthSE_Earth-Silver, SciKnowEval.
- `GeneTuring` is counted as 16,101 raw CSV rows, but 3,302 unique questions for question-like analysis.
- `BigCodeBench` counts only `v0.1.4` to avoid duplicate version snapshots.

## Summary of `merged_domain_subdomain_counts.csv`

- Domain count: 10.
- Total domain/subdomain rows: 3049.
- Total question-like count across included domains: 257,186.
- This file is the detailed source of truth for domain/subdomain counts, dataset contribution, form distribution, and count basis.
