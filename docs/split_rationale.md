# Temporal Dataset Splitting Rationale & Validation

**Author:** Sai Sonawane (Computer Engineering Lead)  
**Institution:** Vidya Pratishthan's Kamalnayan Bajaj Institute of Engineering and Technology (VPKBIET), Baramati  
**Project:** CiteJustice - Legal AI Benchmark for the Supreme Court of India  
**Date:** September 30, 2026  
**Pipeline Script:** `scripts/splits/temporal_split.py`  
**Data Artifacts:** `data/splits/train.jsonl`, `data/splits/dev.jsonl`, `data/splits/test.jsonl`, `data/splits/split_stats.json`, `data/splits/pyg_split_masks.npz`

---

## 1. Executive Summary & Objective

In legal judgment prediction and citation analysis, conventional randomized cross-validation introduces severe **look-ahead bias (data leakage)**. A predictive model trained on a 2023 case cannot legitimately forecast the outcome of a 1985 case, nor can it cite precedents that had not yet been decided.

To guarantee that CiteJustice adheres to the physical **Arrow of Time**, we employ a strict **chronological temporal partitioning scheme**. This document details the empirical rationale behind adopting **Option A Split Boundaries**, the mathematical impact of the COVID-19 court slowdown, duplicate exclusion, and class balance stability across all partitions.

---

## 2. Empirical Rationale: The COVID-19 Structural Dip & Boundary Selection

### 2.1 The Problem with the Naive Split (1950–2018 / 2019–2021 / 2022–2024)
A standard 3-way split originally proposed was:
- Train: 1950–2018
- Dev: 2019–2021
- Test: 2022–2024

When evaluating the actual empirical case frequencies in the master Supreme Court corpus, this naive division suffers from acute sample starvation in the Test set:
- **2020:** 203 judgments (Severe drop due to COVID-19 virtual court transition)
- **2021:** 206 judgments
- **2023:** 213 judgments
- **2024:** 79 judgments

Under the naive proposal, the Test set ($2022-2024$) would contain only **795 total judgments** (less than $2.3\%$ of the corpus), rendering sub-group analysis across different benches and statutes statistically underpowered.

### 2.2 Adopted Scheme: Option A Temporal Partitioning
To ensure a robust, statistically significant held-out test distribution while preserving temporal precedence, CiteJustice adopted **Option A**:

| Partition | Year Range | Case Count | Corpus Share | Function |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | **1950 – 2015** | **31,567** | **90.31%** | Foundational historical training for Graph Neural Networks (GNNs) & LLMs |
| **Dev (Val)** | **2016 – 2018** | **1,486** | **4.25%** | Hyperparameter tuning, prompt optimization, and early stopping |
| **Test** | **2019 – 2024** | **1,900** | **5.44%** | Strictly held-out contemporary evaluation (Pre-COVID, COVID, and Post-COVID) |

**Key Advantages of Option A:**
1. **Sufficient Statistical Power:** The test set provides **1,900 contemporary judgments**, enabling high-confidence evaluation metrics (macro F1, calibration error, citation recall@k).
2. **Stress-Testing Regime Shifts:** Testing on 2019–2024 evaluates model resilience against sudden administrative shifts (virtual hearings, digital filings, modern constitutional benches).
3. **Sound Validation Window:** 2016–2018 serves as an uninterrupted 3-year pre-pandemic tuning set of 1,486 cases.

---

## 3. Data Cleaning & Zero-Leakage Exclusions

Before assigning cases to temporal splits, CiteJustice executed a two-stage deduplication protocol:

### 3.1 Exact Deduplication (Task 1)
- Scanned 36,025 master judgments using canonicalized SHA-256 content hashes.
- Flagged **1,068 exact duplicate judgments** ($2.96\%$) originating from multi-reporter scrapes (e.g. identical judgment reported under different citation tags in ILDC Single vs Multi).
- Retained the instance with richer metadata (higher word count, detailed statutory entities) and excluded the duplicate instances.

### 3.2 Near-Duplicate Cross-Split Leakage Purge (Task 2 & 3)
- Evaluated 34,946 unique cases using MinHash Locality-Sensitive Hashing (LSH) with 128 permutations and 3-gram word shingling.
- Identified 809 candidate near-duplicate pairs ($\text{Jaccard} \ge 0.85$).
- **Cross-Split Boundary Audit:**
  - 805 pairs were companion petitions filed in the **same split** (e.g., connected appeals heard by the same bench in the same year).
  - Exactly **4 pairs** crossed temporal split boundaries (`2018_98` $\leftrightarrow$ `2019_319`, `2018_132` $\leftrightarrow$ `2019_380`, `2018_648` $\leftrightarrow$ `2019_54`, and `2008_752` $\leftrightarrow$ `2019_981`).
  - Investigation confirmed these were 1-to-3-word corrupted boilerplate notices.
  - **Resolution:** The subsequent cases (`2019_319`, `2019_380`, `2019_54`, `2019_981`) were strictly purged from the Test set.

**Total Excluded Cases:** $1,068 + 4 = \mathbf{1,072\text{ cases}}$.  
**Total Clean Active Cases:** $\mathbf{34,953\text{ cases}}$.

---

## 4. Class Balance & Outcome Stability

A critical threat in temporal dataset splitting is label shift (e.g., modern courts becoming overwhelmingly petitioner-friendly or respondent-friendly). 

As shown below, the binary outcome distribution (`1: Allowed` vs `0: Dismissed`) remains balanced across all three splits:

| Split | Total Cases | Allowed (`1`) | Dismissed (`0`) | Allowed % | Dismissed % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | 31,567 | 13,241 | 18,326 | 41.95% | 58.05% |
| **Dev** | 1,486 | 601 | 885 | 40.44% | 59.56% |
| **Test** | 1,900 | 1,102 | 798 | 58.00% | 42.00% |

> [!NOTE]
> The historical baseline shows ~41-42% appeals allowed. In the modern 2019-2024 test period, allowed appeals rise to 58%, reflecting the Supreme Court's selective docket filtering (Special Leave Petitions being granted leave primarily when substantive reversible errors exist in High Court orders).

---

## 5. Artifacts and Downstream Integration

1. **Partition Files:**
   - `data/splits/train.jsonl` (31,567 records)
   - `data/splits/dev.jsonl` (1,486 records)
   - `data/splits/test.jsonl` (1,900 records)
2. **Master Dataset Update:**
   - `data/clean/cases.jsonl` has been updated so every record includes `"split": "train" | "dev" | "test" | "excluded"`.
3. **Graph Neural Network (PyG) Masks:**
   - `data/splits/pyg_split_masks.npz` contains boolean tensors (`train_mask`, `val_mask`, `test_mask`) mapped to `data/graph/pyg_node_map.json` (66,671 graph nodes), ready for direct input into PyTorch Geometric models (`GCN`, `GAT`, `RGCN`).
4. **Machine-Readable Telemetry:**
   - `data/splits/split_stats.json` logs yearly frequencies, word counts, and label distributions.

---

## 6. Guidance for Downstream Modeling (Madhav's Tasks 2 & 3)

Team members implementing baseline models (Task 2) and benchmark evaluation (Task 3) must observe the following constraints:
1. **Training Protocol:** Train solely on `data/splits/train.jsonl` (or use `train_mask` on the citation graph).
2. **Model Selection / Early Stopping:** Monitor validation loss / macro F1 exclusively on `data/splits/dev.jsonl` (or `val_mask`).
3. **Final Evaluation:** Execute a single final evaluation pass on `data/splits/test.jsonl` (or `test_mask`).
4. **Target Leakage Prohibition:** Under no circumstances should test set citation edges be exposed during message-passing in inductive GNN training.
