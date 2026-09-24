# Coordination Report: NyayaAnumana & INLegalLlama Access Status

**Project:** CiteJustice — Automated Legal Judgment Prediction & Dynamic Precedent Evolution Graph (DPEG) for Indian Courts  
**Task:** Follow up on NyayaAnumana Access (Coordination Milestone — Week 4)  
**Author:** Madhav Rakhonde (Coordination & Data Lead)  
**Collaborator:** Sai Sonawane (Graph Lead), Model Architecture Sub-team  
**Institution:** Vidya Pratishthan's Kamalnayan Bajaj Institute of Engineering and Technology (VPKBIET), Baramati  
**Date:** September 24, 2026  
**Status:** **RESOLVED & ACCESSIBLE** (Hugging Face Auth Flow & Fallback Routes Verified)

---

## 1. Executive Summary

As part of the Week 4 coordination sprint, we followed up on the acquisition of the **NyayaAnumana** corpus (702,945 Indian legal judgments) and the **INLegalLlama** model collection from the `L-NLProc` research group (led by Dr. Shubham Kumar Nigam, IIT Kanpur / University of Birmingham).

### Key Findings & Status:
1. **Repository Verification:** Confirmed that `L-NLProc` hosts **35 datasets** and **24 models** actively on Hugging Face.
2. **Access Gate Mechanics Identified:** The primary dataset `L-NLProc/NyayaAnumana-Classification-Data` is configured with `gated: auto` (academic terms click-through agreement). Unauthenticated downloads return `401 Client Error`.
3. **Authentication Solution:** Access is granted automatically upon accepting terms at the Hugging Face web portal (`https://huggingface.co/datasets/L-NLProc/NyayaAnumana-Classification-Data`) and authenticating via `HF_TOKEN`.
4. **Alternative Routes Discovered:**
   * **Direct GitHub Codebase:** `https://github.com/ShubhamKumarNigam/NyayaAnumana-and-INLegalLlama` is active and public, containing dataset architecture, classification baselines, and evaluation scripts.
   * **Ungated Complementary Datasets:** `L-NLProc/Realistic_LJP_Facts` (Apache-2.0) and `L-NLProc/PredEx` are ungated and download immediately without authentication.
5. **Citation & Ethics Compliance:** Added official citation (`@article{nigam2024nyayaanumana}`) to `docs/references.bib` to honor Dr. Nigam's academic attribution terms.

---

## 2. Investigation Details & Hugging Face Audit

Using the Hugging Face Hub API (`huggingface_hub.HfApi`), we audited all resources under the `L-NLProc` organization:

### 2.1 Cataloged Datasets (35 Total)
* **Core Classification:** `L-NLProc/NyayaAnumana-Classification-Data` (`dev`, `test`, `train` across `binary` and `ternary` tasks).
* **Explanation & Rationales:** `L-NLProc/NyayaAnumana-Explanation-Data` (ground-truth decision rationale annotations).
* **Pre-training Data:** `L-NLProc/InLegalLlama-training-data`.
* **Factual Extraction:** `L-NLProc/Realistic_LJP_Facts` (**Ungated / Apache-2.0**).
* **Rhetorical Segmentation:** `L-NLProc/LegalSeg_CSV` and `L-NLProc/LegalSeg_GNN_Predictions`.
* **Domain Retrieval:** `L-NLProc/NyayaRAG`.

### 2.2 Cataloged Models (24 Total)
* `L-NLProc/InLegalLlama` (Base Indian legal LLM).
* `L-NLProc/PredEx_InLegalBert_Pred` (Fine-tuned InLegalBERT).
* `L-NLProc/PredEx_Llama-2-7B_Pred_Instruction-Tuned`.
* `L-NLProc/LegalSeg_GNN` & `L-NLProc/LegalSeg_Hier_BiLSTM-CRF`.

---

## 3. Dataset Composition & File Schemas (From Official GitHub)

Analysis of the official repository confirms four primary dataset tiers:

| Prefix / Tier | Judicial Jurisdiction | Scope & Utility |
| :--- | :--- | :--- |
| **`CJPE_ext_SCI_`** | Supreme Court of India only | Highest judicial authority; aligns with our core DPEG corpus. |
| **`CJPE_ext_SCI_HCs_`** | Supreme Court + High Courts | Expands precedent graph to state appellate jurisprudence. |
| **`CJPE_ext_SCI_HCs_Tribunals_`** | SC + HCs + Tribunals (NCLT, NGT, ITAT) | Specialized regulatory and commercial disputes. |
| **`CJPE_ext_SCI_HCs_Tribunals_daily_orders_`** | SC + HCs + Tribunals + District Courts | Comprehensive national judicial coverage (702K cases). |
| **`2020_2024_single`** | Modern Cases (Jan 2020 – April 2024) | Strictly held-out temporal out-of-distribution evaluation. |

### Label Semantics:
* **Binary Task:** `1` = Accepted / Allowed, `0` = Rejected / Dismissed.
* **Ternary Task:** `0` = Rejected, `1` = Accepted, `2` = Multi-label (mixed outcomes / split rulings).

---

## 4. Team Action Guide: How to Authenticate & Download

Every team member (Sai, Madhav, and the Model team) must follow these 3 steps to access the gated corpus:

### Step 1: Accept the Academic Agreement on Hugging Face
1. Log in to [Hugging Face](https://huggingface.co).
2. Visit the dataset page:  
   👉 [https://huggingface.co/datasets/L-NLProc/NyayaAnumana-Classification-Data](https://huggingface.co/datasets/L-NLProc/NyayaAnumana-Classification-Data)
3. Fill in the brief research affiliation field (e.g., *Final Year B.Tech Project, VPKBIET Baramati*) and click **"Agree and access repository"**.  
   *(Access is granted automatically and instantaneously).*

### Step 2: Configure Your HF Token Locally
Generate a read token at [Hugging Face Tokens Settings](https://huggingface.co/settings/tokens) and configure it in your terminal:

```powershell
# In PowerShell:
$env:HF_TOKEN = "hf_your_personal_read_token_here"
```

Or run the CLI login:
```bash
.\venv\Scripts\huggingface-cli login
```

### Step 3: Run the Acquisition Script
Use our automated acquisition script inside `CiteJustice`:

```bash
# Verify connection:
.\venv\Scripts\python.exe scripts/download_nyayaanumana.py --list

# Download the Supreme Court subset:
.\venv\Scripts\python.exe scripts/download_nyayaanumana.py --token $env:HF_TOKEN --subset SCI
```

---

## 5. Email Correspondence Record & Follow-Up Log

### Email Log Summary:
* **To:** Dr. Shubham Kumar Nigam (`L-NLProc`, IIT Kanpur / Univ. of Birmingham)
* **From:** Madhav Rakhonde & Sai Sonawane (VPKBIET Baramati)
* **Date:** September 18, 2026 (Initial request) & September 23, 2026 (Acknowledgment)
* **Subject:** Request for Academic Access to NyayaAnumana & INLegalLlama for CiteJustice Project
* **Response:** Dr. Nigam confirmed that all datasets are freely accessible for non-commercial academic research via the `L-NLProc` Hugging Face collection, subject to proper BibTeX citation and adherence to ethical research standards.

### Standardized Citation in Project Docs:
The citation has been integrated into `docs/references.bib`:

```bibtex
@article{nigam2024nyayaanumana,
  title={NyayaAnumana \& INLegalLlama: The Largest Indian Legal Judgment Prediction Dataset and Specialized Language Model for Enhanced Decision Analysis},
  author={Nigam, Shubham Kumar and others},
  journal={arXiv preprint},
  year={2024},
  url={https://huggingface.co/collections/L-NLProc/nyayaanumana-and-inlegalllama-dataset}
}
```

---

## 6. Model Team Integration Next Steps

1. **Adopt `INLegalLlama` Backbone:** The model team should pull `L-NLProc/InLegalLlama` rather than generic LLaMA-3. It has already been pre-trained on Indian legal vocabulary (*quash, per incuriam, impugned, ratio decidendi*).
2. **Graph-LLM Fusion:** Node representations extracted from `cases.json` (as specified in `docs/schema.md`) will combine INLegalLlama's text representations with DPEG's graph topology embeddings.
