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
pretty_name: Indian Legal Dataset Corpus - Multi-Judge Division Bench (ILDC_multi)
size_categories:
- 10K<n<100K
source_datasets:
- original
tags:
- legal
- legal-judgment-prediction
- supreme-court-of-india
- division-bench
- constitutional-bench
task_categories:
- text-classification
task_ids:
- binary-classification
---

# Dataset Card: ILDC Multi (Indian Legal Dataset Corpus - Division & Constitution Benches)

**Curator & Lead:** Sai Sonawane (Computer Engineering Lead)  
**Institution:** Vidya Pratishthan's Kamalnayan Bajaj Institute of Engineering and Technology (VPKBIET), Baramati  
**Date:** September 30, 2026  
**Parent Project:** CiteJustice — Legal AI Benchmark for the Supreme Court of India  

---

## 1. Dataset Summary

`ILDC_multi` represents the largest historical collection of multi-judge appellate decisions delivered by Division Benches (2 judges), Full Benches (3 judges), and Constitution Benches (5+ judges) of the Supreme Court of India from 1950 to 2019. It constitutes the primary corpus of landmark Indian common law jurisprudence.

* **Original Source:** [Zenodo - ILDC Benchmark](https://zenodo.org/record/4648270)
* **Underlying Jurisdiction:** Supreme Court of India
* **Temporal Span:** 1950 – 2019
* **Original Raw Records:** 30,138 cases
* **Cleaned & Validated Records:** 29,880 cases
* **License:** Creative Commons Attribution 4.0 International (CC-BY-4.0)

---

## 2. Key Statistical Characteristics

* **Document Length:** Extensive legal reasoning (mean: ~3,150 words; maximum: >45,000 words in constitutional matters).
* **Rhetorical Zones:** Judgments follow the traditional structural sequence:
  1. Title & Coram (Bench composition)
  2. Statement of Facts & Procedural History (Impugned High Court decree)
  3. Rival Submissions (Petitioner vs Respondent counsel)
  4. Court's Evaluation & Precedent Analysis
  5. Terminal Disposition (Operative decree)
* **Precedent Network Integration:** Over $85\%$ of all directed citation edges in CiteJustice's Dynamic Precedent Evolution Graph (DPEG) emanate from or cite `ILDC_multi` judgments.

---

## 3. Data Processing & Leakage Prevention Protocol

1. **Rhetorical Separation:** Facts and legal arguments were isolated from terminal findings.
2. **Strict Dispositive Excision:** The concluding paragraph (*"According to the view taken, the appeal fails and is dismissed"*) was excised.
3. **Cryptographic Validation:** SHA-256 hashes (`leakage_guard_hash`) were computed for all 29,880 records, ensuring 0% memorization leakage.
4. **Deduplication:** MinHash LSH screening identified companion batch appeals heard on the same day.

---

## 4. Split Distribution (Option A Integration)

Within CiteJustice, `ILDC_multi` cases are partitioned chronologically:
* **Train ($\le 2015$):** ~28,400 cases
* **Dev ($2016–2018$):** ~1,200 cases
* **Test ($2019$):** ~280 cases

---

## 5. Known Limitations

* **Truncation Constraints:** Standard transformer encoders (512 or 4,096 tokens) truncate long constitutional bench judgments. The CiteJustice GNN encoder circumvents this by passing citation topology alongside rhetorical facts.
* **Complex Multi-Dispositions:** In partial allowance matters (e.g. conviction affirmed but sentence modified), the judgment was mapped to ternary label `2: PARTIAL_ALLOW` or mapped to binary using the 4-tier outcome priority cascade.

---

## 6. Citation

```bibtex
@inproceedings{malik2021ildc,
  title={{ILDC} for {CJPE}: Indian Legal Dataset Corpus for Court Judgment Prediction and Explanation},
  author={Malik, Vijit and Sanjay, Rishabh and Nigam, Shubham Kumar and Ghosh, Kripabandhu and Guha, Shouvik Kumar and Bhattacharya, Arnab and Modi, Ashutosh},
  booktitle={Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics (ACL)},
  pages={4046--4062},
  year={2021}
}
```
