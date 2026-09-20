# Indian Legal Section Citation Formats & Regex Extraction Guide

**Project:** LexGraphFormer / CiteJustice  
**Module:** Data Engineering & Legal Research Reference  
**Prepared For:** Sai (Regex & Pipeline Automation) & Madhav  
**Purpose:** Comprehensive catalog of statutory section citation variants observed across Supreme Court and High Court judgments, along with production-grade regex extraction patterns.

---

## 1. Overview of Section Citations in Indian Judgments

Indian judges, law clerks, and court reporters employ diverse conventions when citing statutory provisions. Unlike US legal citations which strictly follow The Bluebook, Indian judgments blend:
1. Traditional British common-law abbreviations (`s.`, `ss.`, `sec.`)
2. Indian court vernacular (`u/s`, `r/w`, `u/sec.`)
3. Full statutory references (`under Section 302 of the Indian Penal Code`)
4. Combined offense strings (`Sections 302/149/120B IPC`)
5. Procedural codes with Orders and Rules (`Order VII Rule 11 CPC`)
6. Constitutional provisions (`Article 21`, `Art. 226/227`)

To build an accurate Knowledge Graph and extract statutory relations for the **Dynamic Precedent Evolution Graph (DPEG)**, our extractor must handle all of these syntactic variants.

---

## 2. Catalog of Observed Section Citation Variants

### 2.1 Single Section Variants
| Style | Examples Observed in Judgments | Common Context |
| :--- | :--- | :--- |
| **Full Word** | `Section 302`, `Section 439`, `Section 138` | Standard formal judicial prose |
| **Abbreviated (Sec./sec.)** | `Sec. 302`, `Sec 302`, `sec. 302`, `sec 438` | Shorthand in factual summaries |
| **Abbreviated (S./s.)** | `S. 302`, `S.302`, `s. 302`, `s.482` | Common-law / older SC judgments |
| **Section Symbol (§)** | `§ 302`, `§302`, `§ 420` | Academic citations / recent e-SCR |
| **Vernacular "Under Section"** | `u/s 302`, `u/s. 302`, `U/S 302`, `U/s 302`, `u/s.302` | Police FIRs, trial court orders quoted in SC |
| **Compound Under Section** | `u/sec. 302`, `under section 302`, `under sec. 420` | Procedural narrations |
| **With Statute Name** | `Section 302 IPC`, `Sec. 302, IPC`, `Section 138 of the NI Act`, `Section 482 of the Code` | Specific penal or civil attribution |

---

### 2.2 Subsections, Clauses, Sub-clauses, and Explanations
Judgments frequently cite specific sub-provisions which alter the legal standard (e.g., bail under Section 437(1) vs 439(2)):

| Sub-provision Type | Examples Observed |
| :--- | :--- |
| **Parenthetical Subsections** | `Section 138(1)(b)`, `Sec. 439(2)`, `Section 300(3)`, `Section 3(1)(x)` |
| **Spaced Parentheses** | `Section 138 (1) (b)`, `Section 437 (1)` |
| **Spelled-Out Subsections** | `sub-section (1) of Section 300`, `sub-section (2) of Section 482` |
| **Clauses** | `Clause (a) of Section 138`, `clause (b) of sub-section (1) of Section 14` |
| **Provisos** | `proviso to Section 138`, `first proviso to Section 148`, `second proviso to Section 37` |
| **Explanations** | `Explanation to Section 300`, `Explanation 1 to Section 405`, `Explanation (b) to Section 498A` |

---

### 2.3 Multiple Sections & Compound Offenses
In criminal jurisprudence, charges are rarely filed under a single section. They appear as combined strings, slash-separated offenses, or "read with" joint liability provisions:

| Compound Type | Examples Observed | Semantics |
| :--- | :--- | :--- |
| **Plural Full Word** | `Sections 302 and 34`, `Sections 420, 468, 471 and 120-B` | Cumulative charges |
| **Plural Abbreviation** | `Secs. 302/149`, `Ss. 302, 307`, `ss. 406/420`, `Secs 302, 307` | Quick notation |
| **Slash-Delimited Charges** | `Sections 420/468/471/34/120-B IPC`, `u/s 302/34/149` | Joint liability / conspiracy |
| **Hyphenated Offense Codes** | `Section 120-B`, `Section 498-A`, `Section 304-B` | Letter-suffixed statutory additions |
| **"Read With" (r/w) Formats** | `Section 302 read with 34`, `Section 302 r/w Section 34`, `u/s 302 r/w 149 IPC`, `Sec. 420 r/w 120B` | Vicarious liability / common intention |
| **Range of Sections** | `Sections 300 to 304`, `Sections 101-104 Evidence Act`, `Sec. 19 to 24 Contract Act` | Statutory chapters / topical spans |

---

### 2.4 Constitutional Articles
Constitutional citations differ from statutory sections:

| Constitutional Style | Examples Observed |
| :--- | :--- |
| **Full Word** | `Article 21`, `Article 226`, `Article 32`, `Article 136` |
| **Abbreviated** | `Art. 21`, `Art 21`, `Arts. 14, 19 and 21` |
| **Plural / Combined** | `Articles 226 and 227`, `Articles 226/227 of the Constitution` |
| **With Clauses** | `Article 311(2)`, `Article 19(1)(a)`, `Article 22(5)`, `Clause (1) of Article 311` |

---

### 2.5 Civil Procedure: Orders and Rules (CPC)
In civil appeals, citations reference the First Schedule of the Code of Civil Procedure, 1908:

| CPC Style | Examples Observed | Meaning |
| :--- | :--- | :--- |
| **Standard** | `Order VII Rule 11`, `Order 7 Rule 11` | Rejection of plaint |
| **Abbreviated** | `O. VII, R. 11`, `O. 7, r. 11`, `O. 39 R. 1 & 2` | Injunction applications |
| **Plural Rules** | `Order 39 Rules 1 and 2`, `Order 41 Rules 23 and 27` | Temporary injunction / additional evidence |

---

## 3. Production Regex Suite for Sai (`pipelines/section_extractor.py`)

Here are modular, tested regular expressions for extraction:

```python
import re

SECTION_REGEXES = {
    # 1. Standard single section with prefix (Section, Sec., S., §, u/s)
    # Matches: "Section 302", "Sec. 439", "s.482", "§302", "u/s 302", "U/S. 420"
    "SINGLE_SECTION": re.compile(
        r"(?i)\b(?:under\s+section|u/s\.?|u/sec\.?|section|sec\.?|s\.?|§)\s*(?P<section>\d+[A-Z]?(?:\([0-9a-zA-Z]+\))*)\b"
    ),

    # 2. Compound slash-separated offenses (e.g. "302/34", "420/468/471/120-B")
    # Matches: "Sections 420/468/471/34/120-B IPC", "u/s 302/34"
    "COMPOUND_SLASH": re.compile(
        r"(?i)\b(?:under\s+sections?|u/s\.?|sections?|secs?\.?|ss?\.?)\s*(?P<sections>\d+[A-Z]?(?:/\d+[A-Z]?)+)(?:\s+(?P<act>[A-Z\.\s]+))?\b"
    ),

    # 3. "Read with" (r/w) joint liability constructs
    # Matches: "Section 302 read with Section 34", "Sec. 420 r/w 120B IPC"
    "READ_WITH": re.compile(
        r"(?i)\b(?:section|sec\.?|s\.?|u/s\.?)\s*(?P<sec1>\d+[A-Z]?)\s+(?:read\s+with|r/w)\s+(?:section|sec\.?|s\.?)?\s*(?P<sec2>\d+[A-Z]?)(?:\s+(?P<act>[A-Z\.\s]+))?\b"
    ),

    # 4. Plural comma/and separated sections
    # Matches: "Sections 302, 307 and 120-B", "Secs. 147, 148, 149"
    "PLURAL_SECTIONS": re.compile(
        r"(?i)\b(?:sections|secs\.?|ss\.?)\s*(?P<sections>\d+[A-Z]?(?:,\s*\d+[A-Z]?)*(?:\s*(?:and|or|&)\s*\d+[A-Z]?)+)(?:\s+(?:of\s+the\s+)?(?P<act>[A-Za-z\.\s]+))?\b"
    ),

    # 5. Constitutional Articles
    # Matches: "Article 21", "Art. 226", "Articles 14, 19 and 21", "Article 19(1)(a)"
    "CONSTITUTIONAL_ARTICLE": re.compile(
        r"(?i)\b(?:articles?|arts?\.?)\s*(?P<article>\d+[A-Z]?(?:\([0-9a-zA-Z]+\))*(?:\s*(?:,|and|or|/)\s*\d+[A-Z]?(?:\([0-9a-zA-Z]+\))*)*)(?:\s+of\s+the\s+Constitution(?:\s+of\s+India)?)?\b"
    ),

    # 6. CPC Orders and Rules
    # Matches: "Order VII Rule 11", "Order 39 Rules 1 and 2", "O. 7, R. 11"
    "CPC_ORDER_RULE": re.compile(
        r"(?i)\b(?:order|o\.)\s*(?P<order>[IVXLCDM\d]+)\s*(?:rules?|r\.)\s*(?P<rule>\d+(?:\s*(?:,|and|&)\s*\d+)*)(?:\s*(?:of\s+the\s+)?(?:C\.?P\.?C\.?|Code\s+of\s+Civil\s+Procedure))?\b"
    )
}
```

---

## 4. Normalization Guidelines for Week 3 Pipeline

When extracting sections to build nodes or edge features in DPEG:
1. **Canonicalize Section Identifiers:** Convert `u/s 302`, `S.302`, `Sec 302` into canonical form: `SEC_302`.
2. **Resolve Act Associations:**
   * If an explicit act follows (e.g., `Section 302 IPC`), link directly to statute `IPC` (`act_lookup.csv`).
   * If no act is explicitly stated, look back within a 2-sentence context window. If a criminal context is established (e.g., *FIR, police station, charge sheet, bail*), default to the primary procedural/substantive statute (`IPC` / `CrPC`).
3. **Decompose Compound Citations:**
   * `Sections 302/34 IPC` $\rightarrow$ generate two statutory nodes/references: `IPC:SEC_302` and `IPC:SEC_34` linked with a `CO_CHARGED_WITH` or `READ_WITH` relation.
