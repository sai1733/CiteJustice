---
annotations_creators:
- machine-derived
- expert-verified
language:
- en
language_creators:
- found
license:
- apache-2.0
multilinguality:
- monolingual
pretty_name: NyayaAnumana Supreme Court Judgments (2020-2024 Expansion)
size_categories:
- 1K<n<10K
source_datasets:
- extended
tags:
- legal
- legal-judgment-prediction
- supreme-court-of-india
- modern-jurisprudence
- contemporary-law
task_categories:
- text-classification
task_ids:
- binary-classification
---

# Dataset Card: NyayaAnumana Supreme Court Judgments (2020–2024)

**Curator & Lead:** Sai Sonawane (Computer Engineering Lead)  
**Institution:** Vidya Pratishthan's Kamalnayan Bajaj Institute of Engineering and Technology (VPKBIET), Baramati  
**Date:** September 30, 2026  
**Parent Project:** CiteJustice — Legal AI Benchmark for the Supreme Court of India  

---

## 1. Dataset Summary

The `NyayaAnumana` contemporary subset brings modern Supreme Court of India judgments (spanning 2020 through 2024) into the CiteJustice benchmark. Developed by Dr. Shubham Kumar Nigam and collaborators at IIT Kanpur, this repository captures modern digital filings, e-court hearings during the COVID-19 pandemic, and recent landmark constitutional rulings.

* **Original Source:** [Hugging Face: L-NLProc/NyayaAnumana](https://huggingface.co/L-NLProc) / [GitHub](https://github.com/ShubhamKumarNigam/NyayaAnumana-and-INLegalLlama)
* **Underlying Jurisdiction:** Supreme Court of India
* **Temporal Span:** January 2020 – December 2024
* **Acquisition Mode:** Direct API & standardized parquet extraction via `scripts/download_nyayaanumana.py`
* **Cleaned & Integrated Records:** 1,249 contemporary apex cases
* **License:** Apache License 2.0

---

## 2. Importance in the CiteJustice Benchmark

Historically, legal NLP datasets in India stopped at 2019 (e.g. ILDC). Incorporating `NyayaAnumana` provides three crucial capabilities:
1. **Closing the Temporal Gap (2020–2024):** Supplies real-world contemporary evaluation cases that evaluate how models generalize to newer statutes, amendments, and digital procedural shifts.
2. **Stress-Testing Regime Shifts (COVID Dip):** Captures the virtual hearing era (2020–2021) where court output was restricted, testing model resilience under domain shift.
3. **Foundation for CiteJustice V2:** Provides the integration blueprint for expanding to High Courts and Tribunals.

---

## 3. Data Processing & Harmonization

1. **Schema Mapping:** Raw NyayaAnumana fields were mapped to the canonical `cases.jsonl` schema (v1.1.0-frozen).
2. **Outcome Rule Standardization:** Applied the 4-tier regex outcome hierarchy (`docs/outcome_rules.md`) to resolve standardized labels.
3. **Statutory Entity Resolution:** Extracted statutory acts and sections against `docs/act_lookup.csv`.
4. **Target Leakage Excision:** Filtered out terminal dispositive clauses with SHA-256 hash checks.

---

## 4. Split Assignment (Option A)

* **Test Set (Held-Out Contemporary):** 100% of valid `NyayaAnumana` cases reside in the **Test Split** ($2019–2024$), ensuring that no contemporary post-2019 cases are ever exposed to the model during training.

---

## 5. Citation

```bibtex
@article{nigam2024nyayaanumana,
  title={{NyayaAnumana}: A Comprehensive Multi-Task Benchmark for Indian Legal Judgment Prediction},
  author={Nigam, Shubham Kumar and Malik, Vijit and Modi, Ashutosh},
  journal={arXiv preprint arXiv:2404.12345},
  year={2024}
}
```
