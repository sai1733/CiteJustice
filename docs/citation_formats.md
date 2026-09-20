# Indian Legal Citation Formats & DPEG Edge Typing Reference

**Project:** LexGraphFormer — Legal Explainable Graph Transformer  
**Module:** Data Engineering & Legal Research Reference Document (Week 3 Preparation)  
**Authors:** Madhav & Sai  

---

## 1. Executive Summary & Significance for DPEG

In **LexGraphFormer**, our core innovation is the **Dynamic Precedent Evolution Graph (DPEG)**. Unlike typical Retrieval-Augmented Generation (RAG) pipelines that retrieve prior judgments based solely on embedding cosine similarity, DPEG models the **actual, evolving authority of case law over time**.

To construct DPEG:
1. **Nodes** represent judicial decisions ($J_1, J_2, \dots, J_n$) with temporal timestamps $t_i$.
2. **Directed Edges** $(J_i \xrightarrow{\text{treatment}} J_j)$ represent a citation where judgment $J_i$ cites an earlier precedent $J_j$.
3. **Edge Types** capture judicial treatment: `Followed`, `Distinguished`, `Overruled`, or `Considered`.

Because Indian judgments span over 75 years without a single uniform citation standard (prior to 2023), robust extraction requires recognizing all major Indian law reporters, court abbreviations, and the newly instituted **Neutral Citation System**.

---

## 2. Indian Legal Citation Formats

### 2.1 The Supreme Court Neutral Citation System (INSC)
Introduced in **2023** by the Chief Justice of India, the Supreme Court assigned uniform, vendor-neutral citations to all historical judgments from 1950 onwards.

* **Pattern:** `[Year] INSC [Number]`
* **Examples:**
  * `2023 INSC 544`
  * `2024 INSC 12`
  * `1973 INSC 182`
* **High Court Neutral Citations:**
  * Delhi High Court: `2023:DHC:1234`
  * Bombay High Court: `2023:BHC-OS:567` or `2023:BHC-AS:890`
  * Madras High Court: `2024:MHC:2345`

---

### 2.2 SCC (Supreme Court Cases — Eastern Book Company)
The most widely cited commercial law report in the Supreme Court of India.

* **Standard Format:** `(Year) Volume SCC Page`
  * `(2017) 10 SCC 1` (*K.S. Puttaswamy v. Union of India*)
  * `(1973) 4 SCC 225` (*Kesavananda Bharati v. State of Kerala*)
* **Supplementary Volumes:** `(Year) Supp (Vol) SCC Page`
  * `1993 Supp (1) SCC 645`
* **SCC Online (Electronic Database):** `Year SCC OnLine SC <doc_number>` or `Year SCC OnLine <HighCourt> <doc_number>`
  * `2021 SCC OnLine SC 892`
  * `2020 SCC OnLine Del 1412`

---

### 2.3 AIR (All India Reporter)
The oldest and most common reporter across both the Supreme Court and High Courts.

* **Supreme Court Format:** `AIR Year SC Page`
  * `AIR 1973 SC 1461`
  * `AIR 1950 SC 27` (*A.K. Gopalan v. State of Madras*)
* **High Court Format:** `AIR Year [Court_Abbreviation] Page`
  * `AIR 1975 Cal 120`
  * `AIR 1982 Bom 318`
  * `AIR 1999 Del 45`
* **Court Abbreviations for AIR:**
  * `SC`: Supreme Court
  * `All`: Allahabad High Court
  * `AP`: Andhra Pradesh High Court
  * `Bom`: Bombay High Court
  * `Cal`: Calcutta High Court
  * `Del`: Delhi High Court
  * `Guj`: Gujarat High Court
  * `HP`: Himachal Pradesh High Court
  * `J&K`: Jammu & Kashmir High Court
  * `Kar` / `Knt`: Karnataka High Court
  * `Ker`: Kerala High Court
  * `Mad`: Madras High Court
  * `MP`: Madhya Pradesh High Court
  * `Ori`: Orissa High Court
  * `Pat`: Patna High Court
  * `P&H`: Punjab & Haryana High Court
  * `Raj`: Rajasthan High Court

---

### 2.4 SCR (Supreme Court Reports — Official Government Reporter)
The official record published under the authority of the Supreme Court of India.

* **Format:** `[Year] Vol SCR Page` or `(Year) Vol SCR Page`
* **Examples:**
  * `[1950] SCR 869`
  * `[1973] Supp. SCR 1`
  * `[2008] 2 S.C.R. 553`

---

### 2.5 SCALE (Supreme Court Almanac) & SLT (Supreme Court Today)
Frequently cited in rapid judgment reporting.

* **SCALE:** `(Year) Vol SCALE Page` or `Year (Vol) SCALE Page`
  * `2002 (3) SCALE 456`
  * `(1996) 2 SCALE 112`
* **SLT:** `(Year) Vol SLT Page`
  * `(2004) 5 SLT 210`

---

### 2.6 High Court & Subject-Specific Reporters

| Reporter | Name | Primary Domain | Example Format |
| :--- | :--- | :--- | :--- |
| **Cri LJ / CrLJ** | Criminal Law Journal | Criminal Law | `1980 Cri LJ 142` |
| **DLT** | Delhi Law Times | Delhi HC / Civil / Commercial | `(2015) 218 DLT 12` |
| **Bom CR** | Bombay Cases Reporter | Bombay HC | `2018 (4) Bom.C.R. 78` |
| **GLR** | Gujarat Law Reporter | Gujarat HC | `(1998) 2 GLR 1400` |
| **MLJ** | Madras Law Journal | Madras HC / Civil | `(2005) 1 MLJ 450` |
| **ITR** | Income Tax Reports | Direct Tax / Corporate | `(2010) 325 ITR 243 (SC)` |
| **Comp Cas** | Company Cases | Corporate / Insolvency | `(2001) 104 Comp Cas 1` |
| **LLJ** | Labour Law Journal | Industrial / Employment | `(1995) II LLJ 345 SC` |

---

## 3. Comprehensive Regex Patterns for Extraction

Below are production-ready regular expressions to capture the main Indian citation formats during text normalization.

```python
import re

CITATION_PATTERNS = {
    # 1. Neutral Citation: 2023 INSC 123
    "NEUTRAL_INSC": r"\b(?P<year>(?:19|20)\d{2})\s+INSC\s+(?P<num>\d+)\b",
    
    # 2. High Court Neutral Citations: 2023:DHC:1234 or 2023:BHC-OS:567
    "NEUTRAL_HC": r"\b(?P<year>(?:19|20)\d{2})\s*:\s*(?P<court>[A-Z]{3,4}(?:-[A-Z]+)?)\s*:\s*(?P<num>\d+)\b",
    
    # 3. SCC: (2018) 1 SCC 1, 1993 Supp (1) SCC 645
    "SCC": r"\(?(?P<year>(?:19|20)\d{2})\)?\s+(?:Supp\s*(?:\(\d+\)\s*)?)?(?P<vol>\d+)?\s*SCC\s+(?P<page>\d+)\b",
    
    # 4. SCC Online: 2021 SCC OnLine SC 892
    "SCC_ONLINE": r"\b(?P<year>(?:19|20)\d{2})\s+SCC\s+OnLine\s+(?P<court>[A-Za-z\s]+?)\s+(?P<doc_num>\d+)\b",
    
    # 5. AIR: AIR 1973 SC 1461, AIR 1999 Del 45
    "AIR": r"\bAIR\s+(?P<year>(?:19|20)\d{2})\s+(?P<court>SC|All|AP|Bom|Cal|Del|Guj|HP|J&K|Kar|Knt|Ker|Mad|MP|Ori|Pat|P&H|Raj)\s+(?P<page>\d+)\b",
    
    # 6. SCR: [1950] SCR 869, [2008] 2 S.C.R. 553
    "SCR": r"\[(?P<year>(?:19|20)\d{2})\]\s+(?:Supp\.\s*)?(?P<vol>\d+)?\s*S\.?C\.?R\.?\s+(?P<page>\d+)\b",
    
    # 7. SCALE: 2002 (3) SCALE 456, (1996) 2 SCALE 112
    "SCALE": r"\(?(?P<year>(?:19|20)\d{2})\)?\s*(?:\((?P<vol>\d+)\)\s*)?SCALE\s+(?P<page>\d+)\b",
    
    # 8. Criminal Law Journal: 1980 Cri LJ 142
    "CRILJ": r"\b(?P<year>(?:19|20)\d{2})\s+(?:Cri\s*LJ|Cr\.?L\.?J\.?)\s+(?P<page>\d+)\b"
}

# Unified extraction regex
COMBINED_CITATION_REGEX = re.compile(
    r"|".join(f"(?P<{k}>{v})" for k, v in CITATION_PATTERNS.items()),
    flags=re.IGNORECASE
)
```

---

## 4. DPEG Edge Treatment Taxonomy & Classification Signals

When judgment $J_A$ cites precedent $J_B$, the relationship must be classified into one of the 4 DPEG edge types.

### 4.1 Taxonomy & Formal Semantics

| Edge Type | Semantics | Temporal Graph Effect |
| :--- | :--- | :--- |
| **`Followed`** | $J_A$ explicitly adopts, approves, or applies the ratio decidendi of $J_B$. | **Strengthens** authority of $J_B$ at time $t_A$. |
| **`Distinguished`** | $J_A$ finds $J_B$ inapplicable due to differences in factual matrix or statutory provisions. | **Constrains** domain of applicability of $J_B$ without invalidating it. |
| **`Overruled`** | $J_A$ (larger bench / appellate bench) declares $J_B$ bad law or nullifies its precedent value. | **Invalidates / terminates** authoritative weight of $J_B$ for future decisions. |
| **`Considered`** | $J_A$ discusses, examines, or cites $J_B$ as background without affirmative adoption or departure. | **Neutral** propagation of contextual relevance. |

---

### 4.2 Lexical Trigger Signals for Rule-Based & NER Classification

To classify the citation sentence window into one of the 4 edge types:

#### Type 1: `Overruled` (Priority 1 — Highest Negative Authority)
* **Trigger Keywords / Phrases:**
  * *overruled in*, *is hereby overruled*, *no longer good law*, *stand overruled*
  * *disapproved in*, *was not correctly decided*, *per incuriam*
  * *cannot be approved*, *decision in ... is erroneous*, *set aside on this point*
* **Example Sentence:**
  > *"We are of the considered opinion that the decision in **State of U.P. v. Ram Swarup (1974) 4 SCC 347** was rendered per incuriam and is accordingly **overruled**."*

#### Type 2: `Distinguished` (Priority 2 — Negative/Divergent Boundary)
* **Trigger Keywords / Phrases:**
  * *distinguishable on facts*, *distinguished*, *the facts in ... were entirely different*
  * *cannot apply to the present case*, *inapplicable to the facts at hand*
  * *has no application*, *stands on a different footing*, *turned on its own unique facts*
* **Example Sentence:**
  > *"The learned counsel placed reliance on **Ramanathan v. State (2001) 2 SCC 145**, but that decision is clearly **distinguishable on facts**, as the statutory embargo under Section 37 did not arise there."*

#### Type 3: `Followed` (Priority 3 — Positive Reinforcement)
* **Trigger Keywords / Phrases:**
  * *relied upon*, *followed*, *approved*, *squarely applies*
  * *we respectfully agree with the view taken in*, *binding ratio of*
  * *authoritative pronouncement in*, *in line with the principles laid down in*
  * *following the precedent of*, *we are guided by the dictum in*
* **Example Sentence:**
  > *"Applying the principles **followed** in **Maneka Gandhi v. Union of India (1978) 1 SCC 248**, we hold that procedure established by law must be just, fair, and reasonable."*

#### Type 4: `Considered` (Default / Informational Baseline)
* **Trigger Keywords / Phrases:**
  * *referred to*, *cited by*, *our attention was drawn to*
  * *was considered in*, *examined in*, *noticed in*
  * *as observed in*, *see also*, *vide*
* **Example Sentence:**
  > *"The learned Single Judge **referred to** the judgment in **Union of India v. Tulsiram Patel (1985) 3 SCC 398** during the hearing."*

---

## 5. Implementation Strategy for Week 3 Pipeline

```
Raw Judgment Text 
      │
      ▼
[1. Sentence Segmentation (spaCy / Legal-spacy)]
      │
      ▼
[2. Regex & Pattern Matcher: Identify Citation Occurrences]
      │  └── Extract: Citing Case, Cited Case, Year, Reporter, Page
      ▼
[3. Context Window Extraction (±2 Sentences around Citation)]
      │
      ▼
[4. Treatment Classifier: Hybrid Cascade]
      ├── Level 1: High-precision Regex Rule Filter (Overruled / Distinguished / Followed)
      └── Level 2: LegalBERT / RoBERTa Sequence Classifier (for ambiguous contexts)
      │
      ▼
[5. DPEG Edge Ingestion]
      └── Add edge: (SourceNode, TargetNode, edge_type, citation_year, context_snippet)
```
