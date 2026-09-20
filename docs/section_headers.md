# Indian Judgment Section Header Patterns & Rhetorical Zones

**Project:** LexGraphFormer / CiteJustice  
**Module:** Data Engineering & Legal NLP Reference  
**Prepared For:** Sai & Madhav  
**Purpose:** Catalog of structural section headers, rhetorical zones, and regex segmentation patterns across Supreme Court and High Court judgments.

---

## 1. Why Section Headers Matter for LexGraphFormer

In **LexGraphFormer**, understanding *where* a precedent is cited within a judgment is crucial for edge classification in the **Dynamic Precedent Evolution Graph (DPEG)**:

* **Citations in `SUBMISSIONS / ARGUMENTS`:** These represent contentions advanced by advocates. They do **not** reflect judicial approval or precedent evolution. Treating them as `Followed` would introduce significant noise into the graph.
* **Citations in `ANALYSIS / DISCUSSION`:** These represent judicial scrutiny where the bench evaluates the legal doctrine.
* **Citations in `RATIO DECIDENDI / HELD / CONCLUSION`:** These represent binding judicial adoption or formal overruling (`Followed` or `Overruled`).

Segmenting raw judgments into rhetorical zones enables DPEG to assign confidence weights to edges based on zone hierarchy:
$$\text{Weight}(E) = f(\text{Zone}, \text{Treatment})$$

---

## 2. Structural Formatting Conventions

Indian judgments present headers in several typographical styles:
1. **Spaced-Out Capitalization:** `O R D E R`, `J U D G M E N T`, `F A C T S`
2. **Standard ALL CAPS:** `FACTS`, `THE FACTS`, `SUBMISSIONS`, `HELD`, `ORDER`
3. **Numbered / Roman Headings:** `I. FACTUAL BACKGROUND`, `II. RIVAL CONTENTIONS`, `III. ISSUES`, `IV. DISCUSSION`, `V. CONCLUSION`
4. **Narrative / In-line Triggers:** Many Indian judgments do not use markdown or formal section breaks; instead, the judge begins the section with a formulaic introductory sentence (e.g., *"The brief facts necessary for the disposal of the appeal are..."*).

---

## 3. Comprehensive Catalog of Section Headers by Rhetorical Zone

### 3.1 Preamble, Coram & Leave Grants
Marks the start of the judicial proceeding.

* **Explicit Headers:**
  * `IN THE SUPREME COURT OF INDIA`
  * `CRIMINAL APPELLATE JURISDICTION` / `CIVIL APPELLATE JURISDICTION`
  * `CIVIL APPEAL NO(S). ... OF ...`
  * `CRIMINAL APPEAL NO(S). ... OF ...`
  * `SPECIAL LEAVE PETITION (C / CRL.) NO(S). ...`
  * `WRIT PETITION (C / CRL.) NO(S). ...`
  * `CORAM:` / `BEFORE:` / `BENCH:`
  * `J U D G M E N T` / `JUDGMENT` / `O R D E R` / `ORDER`
* **In-line Formulaic Triggers:**
  * `Leave granted.`
  * `Special leave granted.`
  * `Delay condoned.`
  * `Heard learned counsel for the parties.`
  * `The following judgment of the Court was delivered by ...`

---

### 3.2 Facts / Background (Factual Matrix)
Narrates the events, FIR, trial court proceedings, or High Court impugned order.

* **Explicit Headers:**
  * `FACTS`
  * `THE FACTS`
  * `BRIEF FACTS`
  * `FACTS IN BRIEF`
  * `FACTS OF THE CASE`
  * `FACTUAL MATRIX`
  * `FACTUAL BACKGROUND`
  * `FACTUAL CONTEXT`
  * `BACKGROUND`
  * `CASE OF THE PROSECUTION` / `PROSECUTION CASE`
  * `CASE OF THE APPELLANT` / `CASE OF THE COMPLAINANT`
  * `GENESIS OF THE CASE`
* **In-line Formulaic Triggers:**
  * `Brief facts which are necessary for the disposal of these appeals are that...`
  * `Brief facts giving rise to these appeals are as follows...`
  * `The factual matrix leading to the filing of the present appeal is that...`
  * `Succinctly stated, the case of the prosecution is that...`
  * `The genesis of the prosecution case is...`
  * `The dispute arises out of...`

---

### 3.3 Submissions / Arguments / Contentions
Documents the competing positions of appellant and respondent counsel.

* **Explicit Headers:**
  * `SUBMISSIONS`
  * `ARGUMENTS`
  * `CONTENTIONS`
  * `RIVAL SUBMISSIONS`
  * `RIVAL CONTENTIONS`
  * `SUBMISSIONS ON BEHALF OF THE APPELLANT`
  * `SUBMISSIONS FOR THE APPELLANT`
  * `ARGUMENTS OF THE APPELLANT`
  * `APPELLANT'S CONTENTIONS`
  * `SUBMISSIONS ON BEHALF OF THE RESPONDENT`
  * `SUBMISSIONS FOR THE RESPONDENT`
  * `ARGUMENTS OF THE RESPONDENT`
  * `RESPONDENT'S CONTENTIONS`
  * `SUBMISSIONS OF THE AMICUS CURIAE`
* **In-line Formulaic Triggers:**
  * `Learned Senior Counsel appearing for the appellant contended that...`
  * `Mr. ..., learned Senior Counsel for the appellant, submitted that...`
  * `On the other hand, learned counsel for the respondent strenuously argued that...`
  * `Per contra, learned counsel appearing for the respondent submitted...`
  * `It was further urged by the learned counsel that...`
  * `In response, it is contended that...`

---

### 3.4 Issues / Points for Determination
Formulates the legal question the court must resolve.

* **Explicit Headers:**
  * `ISSUES`
  * `THE ISSUES`
  * `POINTS FOR CONSIDERATION`
  * `POINTS FOR DETERMINATION`
  * `QUESTION OF LAW`
  * `QUESTIONS OF LAW`
  * `SUBSTANTIAL QUESTION OF LAW`
  * `THE QUESTION`
  * `QUESTION FOR DECISION`
* **In-line Formulaic Triggers:**
  * `The short question that arises for our consideration is...`
  * `The question of law formulated for decision in this appeal is...`
  * `The core question which falls for determination is whether...`
  * `In the backdrop of the rival submissions, the following questions arise for consideration:`
  * `The principal issue to be decided is...`

---

### 3.5 Analysis / Discussion / Consideration
The core reasoning zone where judges analyze statutory provisions and precedents.

* **Explicit Headers:**
  * `ANALYSIS`
  * `OUR ANALYSIS`
  * `DISCUSSION`
  * `CONSIDERATION`
  * `REASONING`
  * `FINDINGS`
  * `EXAMINATION OF LAW`
  * `DELIBERATIONS`
  * `ASSESSMENT`
  * `LEGAL FRAMEWORK`
* **In-line Formulaic Triggers:**
  * `We have carefully considered the submissions made by both sides...`
  * `In order to appreciate the controversy, it is necessary to examine...`
  * `A perusal of Section ... reveals that...`
  * `It is a well-settled principle of law that...`
  * `Having heard learned counsel for the parties and perused the record...`
  * `We find considerable merit in the submission that...`

---

### 3.6 Held / Ratio Decidendi / Conclusion / Operative Order
The binding holding and disposition of the case.

* **Explicit Headers:**
  * `HELD`
  * `ORDER`
  * `O R D E R`
  * `CONCLUSION`
  * `CONCLUSIONS`
  * `RATIO DECIDENDI`
  * `FINDINGS AND CONCLUSION`
  * `FINAL ORDER`
  * `OPERATIVE PART`
  * `RESULT`
  * `DISPOSAL`
* **In-line Formulaic Triggers:**
  * `For the reasons stated above, the appeal is allowed / dismissed.`
  * `In view of the foregoing discussion, we are of the considered opinion that...`
  * `The impugned judgment and order passed by the High Court cannot be sustained and is accordingly set aside.`
  * `Resultantly, the appeals fail and are dismissed.`
  * `Order accordingly.`
  * `No order as to costs.`
  * `Pending applications, if any, stand disposed of.`

---

## 4. Production Regex Suite for Segmentation

```python
import re

# Comprehensive Header Regex for Boundary Detection
SECTION_HEADER_REGEX = {
    "FACTS": re.compile(
        r"(?im)^\s*(?:[I|V|X\d]+\.\s*)?(?:THE\s+)?(?:BRIEF\s+)?(?:FACTS|FACTUAL\s+(?:MATRIX|BACKGROUND|CONTEXT)|GENESIS\s+OF\s+THE\s+CASE|CASE\s+OF\s+THE\s+(?:PROSECUTION|APPELLANT|COMPLAINANT))\b"
    ),
    "SUBMISSIONS": re.compile(
        r"(?im)^\s*(?:[I|V|X\d]+\.\s*)?(?:RIVAL\s+)?(?:SUBMISSIONS|ARGUMENTS|CONTENTIONS)(?:\s+(?:ON\s+BEHALF\s+OF|FOR)\s+THE\s+(?:APPELLANT|RESPONDENT|PETITIONER|STATE|ACCUSED))?\b"
    ),
    "ISSUES": re.compile(
        r"(?im)^\s*(?:[I|V|X\d]+\.\s*)?(?:THE\s+)?(?:ISSUES?|POINTS?\s+FOR\s+(?:CONSIDERATION|DETERMINATION)|(?:SUBSTANTIAL\s+)?QUESTIONS?\s+OF\s+LAW)\b"
    ),
    "ANALYSIS": re.compile(
        r"(?im)^\s*(?:[I|V|X\d]+\.\s*)?(?:OUR\s+)?(?:ANALYSIS|DISCUSSION|CONSIDERATION|REASONING|FINDINGS|LEGAL\s+FRAMEWORK|DELIBERATIONS)\b"
    ),
    "CONCLUSION": re.compile(
        r"(?im)^\s*(?:[I|V|X\d]+\.\s*)?(?:O\s*R\s*D\s*E\s*R|ORDER|HELD|CONCLUSIONS?|RATIO\s+DECIDENDI|FINAL\s+ORDER|OPERATIVE\s+PART|RESULT|DISPOSAL)\b"
    )
}
```

---

## 5. Rhetorical Role Mapping for DPEG Edge Weighting

| Zone Name | Role in Judgment | Edge Extraction Rule for DPEG | Confidence Multiplier |
| :--- | :--- | :--- | :---: |
| `PREAMBLE` | Procedural metadata | Ignore citations (often jurisdiction statutes like Art. 136). | $0.0$ |
| `FACTS` | History of dispute | Background citation (e.g., lower court reference). | $0.3$ |
| `SUBMISSIONS` | Counsel's arguments | Extract as `CITED_BY_COUNSEL` (non-binding argument). | $0.1$ |
| `ISSUES` | Framing questions | Flag as thematic reference. | $0.5$ |
| `ANALYSIS` | Core legal deliberation | High probability of `Distinguished`, `Considered`, or `Followed`. | $0.8$ |
| `CONCLUSION` | Final ratio & decree | Highest authority for `Overruled` or `Followed`. | $1.0$ |
