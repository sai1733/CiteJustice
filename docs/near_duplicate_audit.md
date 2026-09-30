# Legal Audit & Empirical Review of Near-Duplicate Judgments

**Project:** CiteJustice — Legal AI Benchmark for the Supreme Court of India  
**Author:** Sai Sonawane (Computer Engineering Lead)  
**Institution:** Vidya Pratishthan's Kamalnayan Bajaj Institute of Engineering and Technology (VPKBIET), Baramati  
**Date:** September 30, 2026  
**Status:** **Completed & Formally Validated** (Week 5 Legal Milestone)  
**Artifact References:** `data/clean/near_duplicates.csv`, `data/clean/near_dedup_stats.json`, `scripts/dedup/near_dedup.py`

---

## 1. Executive Summary

In Indian appellate jurisprudence, the Supreme Court frequently hears **batch matters (companion petitions)** simultaneously. Under Order XIX of the Supreme Court Rules (2013), where multiple Special Leave Petitions (SLPs) or Civil/Criminal Appeals challenge the same common High Court order, the registry tags them together to be argued before a single bench. When the bench pronounces judgment, it often delivers an identical operative judgment for each separate appeal number, differing only in party names, memo dates, or procedural cross-references.

In standard NLP benchmarks, failing to distinguish between **companion batch petitions** and **spurious boilerplate duplication** leads to two major pitfalls:
1. **False Deletion:** Deleting valid legal appeals filed by different citizens against distinct lower-court decrees.
2. **Cross-Boundary Contamination (Data Leakage):** Allowing a companion twin of a training case to appear in the test set, creating artificial 100% memorized accuracy.

This audit report documents the legal and textual review of the **809 candidate near-duplicate pairs** flagged by our MinHash Locality-Sensitive Hashing (LSH) pipeline ($\text{Jaccard} \ge 0.85$, 128 permutations).

---

## 2. Telemetry & Categorization Breakdown

| Classification Category | Pair Count | Proportion | Legal Characteristics | Action Taken |
| :--- | :---: | :---: | :--- | :--- |
| **Companion Bench Petitions** | **721** | **89.12%** | Same year, same bench, substantive text (>500 words), tagged batch appeals | **Retained in Same Split** (Never separated) |
| **Temporal Boilerplate Orders** | **84** | **10.38%** | Different years, short orders (<100 words), standard disposal/settlement text | **Monitored; Valid Legal Disposals** |
| **Cross-Boundary Leak Candidates** | **4** | **0.50%** | Different years crossing Train/Dev/Test partition boundaries | **Purged from Test/Dev Set** |
| **Total Evaluated Pairs** | **809** | **100.0%** | Mean Jaccard Similarity: **94.18%** | **100% Audit Complete** |

---

## 3. Case Studies & Deep-Dive Textual Analysis

### 3.1 Category A: Substantive Companion Bench Matters (Legally Valid Batch Appeals)

#### Case Study 1: Connected Civil Appeals (`2012_622` $\leftrightarrow$ `2012_777`)
* **Similarity:** Jaccard = **1.0000** (128 MinHash permutations)
* **Text Length:** 3,873 words each
* **Year:** 2012 | **Bench:** Supreme Court Apex Bench
* **Text Comparison:**
  * Both judgments share identical legal questions regarding land acquisition under the Land Acquisition Act, 1894. The preamble, recitation of submissions, High Court findings, and constitutional interpretation match word-for-word across paragraphs 1 through 45.
  * The only differences reside in the lead memo: `Civil Appeal No. 4390 of 2012` vs `Civil Appeal No. 4391 of 2012` and the specific survey plot numbers.
* **Legal Finding:** These are legitimate companion appeals. In Indian law, each appellant is entitled to a formal decree in their own appeal. Deleting one would distort node degree in the citation graph.
* **Protocol Decision:** **RETAINED**. Both cases reside strictly within the **Train Split** ($\le 2015$).

#### Case Study 2: Complex Taxation Batch Appeals (`2009_1466` $\leftrightarrow$ `2009_2131`)
* **Similarity:** Jaccard = **1.0000**
* **Text Length:** 7,114 words (`2009_1466`) vs 7,064 words (`2009_2131`)
* **Year:** 2009 | **Bench:** Two-Judge Taxation Division
* **Text Comparison:**
  * Detailed assessment of Section 80-IA and Section 80-IB of the Income Tax Act, 1961. The bench pronounced a master judgment in the lead matter and passed an identical judgment in the connected appeal.
* **Protocol Decision:** **RETAINED** within the Train split.

---

### 3.2 Category B: Temporal Boilerplate & Consent Decrees

#### Case Study: Formulaic Disposals (`2008_165` $\leftrightarrow$ `2008_1980` $\leftrightarrow$ `2008_420`)
* **Similarity:** Jaccard = **1.0000**
* **Text Length:** 19 to 20 words each
* **Text Sample:**
  > *"Leave granted. In terms of the signed order, the appeals are disposed of. No order as to costs."*
* **Legal Finding:** These represent ultra-short chamber or motion-bench disposal orders. While they share identical wording, they correspond to different SLP docket numbers disposed of on different motion days.
* **Protocol Decision:** **RETAINED**, but tagged as low-information records (`word_count < 50`) in downstream tokenizers.

---

### 3.3 Category C: Cross-Boundary Leak Investigation & Purge

During our boundary crossing audit, exactly **4 pairs** exhibited cross-split membership:

| Case A (Earlier Split) | Year A | Case B (Later Split) | Year B | Jaccard Sim | Underlying Cause | Final Resolution |
| :--- | :---: | :--- | :---: | :---: | :--- | :--- |
| `2018_98` (Dev) | 2018 | `2019_319` (Test) | 2019 | 1.0000 | 3-word fragment: *"Deepak Gupta, J."* | **Purged `2019_319` from Test** |
| `2018_132` (Dev) | 2018 | `2019_380` (Test) | 2019 | 1.0000 | 2-word fragment: *"V.RAMANA, J."* | **Purged `2019_380` from Test** |
| `2018_648` (Dev) | 2018 | `2019_54` (Test) | 2019 | 1.0000 | 1-word fragment: *"K.SIKRI,J."* | **Purged `2019_54` from Test** |
| `2008_752` (Train) | 2008 | `2019_981` (Test) | 2019 | 0.9219 | 20-word boilerplate order | **Purged `2019_981` from Test** |

* **Audit Finding:** The investigation revealed that `2019_54`, `2019_319`, and `2019_380` were corrupted judge name header fragments originating from multi-reporter scrapes, which mirrored similar scraps from 2018.
* **Action Taken:** All 4 test-side cases were strictly purged from the test set in `scripts/splits/temporal_split.py`. As a result, **zero cross-split near-duplicate leakage exists in CiteJustice**.

---

## 4. Policy Recommendations for Model Architecture (Phase 2)

Based on this legal review, the model sub-team must implement the following safeguards:
1. **Do Not Over-Purge Companion Appeals in Training:** Retaining batch appeals in `train.jsonl` reflects real courtroom empirical distribution (certain legal issues arise repeatedly in bulk).
2. **Prevent Cluster Leakage in Cross-Validation:** If evaluating on training sub-folds, group companion matters by `(year, bench)` to prevent train-val contamination within folds.
3. **Handle Ultra-Short Orders:** Models must filter or apply length-masking on records with `word_count < 50` during rhetorical zone classification.

---

## 5. Formal Certification

I hereby certify that all 809 candidate near-duplicate pairs identified by MinHash LSH have been audited for legal fidelity. Zero cross-boundary leakage remains in the final dataset partitions.

**Sai Sonawane**  
Computer Engineering Lead, CiteJustice Project  
VPKBIET, Baramati  
September 30, 2026
