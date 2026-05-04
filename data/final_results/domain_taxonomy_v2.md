# Domain Taxonomy v2

Fixed 10-domain taxonomy after excluding MMLU and ScienceQA, splitting SciKnowEval by internal domain, and promoting Genomics, Clinical Medicine, and Climate Science to first-level domains.

## Domain Totals

| Domain | Count |
|---|---:|
| Life Sciences | 11684 |
| Genomics | 4022 |
| Clinical Medicine | 209328 |
| Chemistry | 11137 |
| Materials Science | 6190 |
| Physics | 4098 |
| Earth Science | 2861 |
| Climate Science | 4569 |
| Astronomy | 2016 |
| Computer Science | 1281 |

## Normalization Rules

- MedXpertQA, MedMCQA, MedQA_USMLE, and PubMedQA are Clinical Medicine.
- GeneTuring and Genome-Bench are Genomics; ATLAS Biology records mentioning genetics/bioinformatics are also Genomics.
- ClimaQA is Climate Science; EarthSE atmospheric, meteorology, climatology, polar, cryosphere, and glaciology records are Climate Science.
- EarthSE ecology/bioscience/biosphere records are Life Sciences; remaining EarthSE records are Earth Science.
- SciKnowEval uses Appendix.domain: Biology -> Life Sciences, Material -> Materials Science, Chemistry -> Chemistry, Physics -> Physics.
- BigCodeBench counts only v0.1.4 to avoid duplicate version snapshots in the same repo.
- MMLU, ScienceQA, and ATLAS Mathematics are excluded from the fixed 10-domain analysis.

## Excluded Counts

| Source | Label | Count |
|---|---|---:|
| ATLAS | Mathematics | 94 |
| ScienceQA | Excluded | 2211 |
| mmlu | Excluded | 27878 |
