---
annotations_creators:
- expert-annotated
language:
- en
language_creators:
- found
license:
- cc-by-4.0
multilinguality:
- monolingual
pretty_name: Indian Legal Dataset Corpus - Single Judge (ILDC_single)
size_categories:
- 1K<n<10K
source_datasets:
- original
tags:
- legal
- legal-judgment-prediction
- supreme-court-of-india
- indian-law
task_categories:
- text-classification
task_ids:
- binary-classification
---

# Dataset Card: ILDC Single (Indian Legal Dataset Corpus - Single Judge)

**Curator & Lead:** Sai Sonawane (Computer Engineering Lead)  
**Institution:** Vidya Pratishthan's Kamalnayan Bajaj Institute of Engineering and Technology (VPKBIET), Baramati  
**Date:** September 30, 2026  
**Parent Project:** CiteJustice — Legal AI Benchmark for the Supreme Court of India  

---

## 1. Dataset Summary

`ILDC_single` comprises single-bench appellate decisions from the Supreme Court of India, compiled by Malik et al. (ACL 2021). Within the CiteJustice framework, this dataset captures historical apex court jurisprudence where a single judge disposed of petitions, civil appeals, or chamber matters.

* **Original Source:** [Zenodo - ILDC Benchmark](https://zenodo.org/record/4648270)
* **Underlying Jurisdiction:** Supreme Court of India
* **Temporal Span:** 1950 – 2019
* **Original Records:** 5,082 cases
* **Cleaned & Validated Records:** 4,896 cases
* **License:** Creative Commons Attribution 4.0 International (CC-BY-4.0)

---

## 2. Data Structure & Fields

Every judgment in `ILDC_single` was normalized into the canonical CiteJustice Schema (v1.1.0):

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `case_id` | String | Unique slug identifier (e.g., `1962_142`) |
| `court` | String | Standardized to `"Supreme Court of India"` |
| `court_tier` | String | `"APEX"` |
| `year` | Integer | Year of judgment pronouncement (1950–2019) |
| `split` | String | Chronological assignment (`train`, `dev`, `test`, `excluded`) |
| `text_features.clean_text` | String | Full judgment text with OCR noise repaired and dispositive sentence excised |
| `outcome.binary_label` | Integer | `1` = Appeal Allowed / Accepted; `0` = Appeal Dismissed / Rejected |
| `outcome.confidence_tier` | String | `"HIGH"`, `"MEDIUM"`, or `"LOW"` |
| `statutory_entities.acts` | List[String] | Mentioned statutory acts (e.g., `Constitution of India, 1950`) |
| `statutory_entities.sections`| List[String] | Canonicalized section slugs (e.g., `IPC_302`, `CrPC_313`) |

---

## 3. Preprocessing Applied in CiteJustice

1. **Noise Removal:** Removed watermarks, scanned line numbers, and reporter artifacts (`SCC`, `SCR`, `AIR` repeated page headers).
2. **OCR Token Correction:** Rectified typical scan errors (`companyviction` $\rightarrow$ `conviction`, `numbermerit` $\rightarrow$ `no merit`).
3. **Cryptographic Target Leakage Guard:** Excised the terminal dispositive sentence from `clean_text` and validated zero overlap using SHA-256 `leakage_guard_hash`.
4. **Deduplication:** Screened against `ILDC_multi` to eliminate cross-reporter duplicates.

---

## 4. Known Limitations

* **Bench Size Imbalance:** Single-judge benches represent a minority of Supreme Court jurisprudence (as Article 145(3) mandates benches of 2, 3, or 5+ judges for substantial questions of constitutional interpretation).
* **Historical Scans:** Cases prior to 1970 contain occasional faint-type typography artifacts from original government presses.

---

## 5. Citation

```bibtex
@inproceedings{malik2021ildc,
  title={{ILDC} for {CJPE}: Indian Legal Dataset Corpus for Court Judgment Prediction and Explanation},
  author={Malik, Vijit and Sanjay, Rishabh and Nigam, Shubham Kumar and Ghosh, Kripabandhu and Guha, Shouvik Kumar and Bhattacharya, Arnab and Modi, Ashutosh},
  booktitle={Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics (ACL)},
  pages={4046--4062},
  year={2021}
}
```
