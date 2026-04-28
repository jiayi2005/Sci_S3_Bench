# Normalization Notes

This directory uses the v2 fixed 10-domain taxonomy:

- Life Sciences
- Genomics
- Clinical Medicine
- Chemistry
- Materials Science
- Physics
- Earth Science
- Climate Science
- Astronomy
- Computer Science

Key rules:

- MMLU and ScienceQA are excluded as too simple/general.
- SciKnowEval is split by `Appendix.domain` into Chemistry, Life Sciences, Materials Science, and Physics.
- GeneTuring and Genome-Bench are promoted to Genomics.
- MedXpertQA, MedMCQA, MedQA_USMLE, and PubMedQA are Clinical Medicine.
- ClimaQA is Climate Science.
- EarthSE atmospheric, meteorology, climatology, polar, cryosphere, and glaciology records are Climate Science; ecology/bioscience/biosphere records are Life Sciences; remaining records are Earth Science.
- ATLAS Mathematics records are excluded to keep the fixed 10-domain taxonomy.
- BigCodeBench counts only the latest `v0.1.4` parquet file to avoid duplicate version snapshots.
