# Indian Legal Citation Signals & Judicial Treatment Catalog

**Project:** CiteJustice — Automated Legal Judgment Prediction & Dynamic Precedent Evolution Graph (DPEG)  
**Module:** Graph Engineering & Legal NLP Reference  
**Prepared By:** Madhav (Legal Research & Domain Taxonomy)  
**Target Consumer:** Sai Sonawane (for `scripts/graph/classify_relationship.py`)  
**Status:** Production Reference Specification  

---

## 1. Executive Summary & Purpose

In common-law systems like India, the doctrine of *stare decisis* (Article 141 of the Constitution of India) governs how past judicial decisions bind future benches. However, judicial treatment of precedent is not binary; it evolves through distinct jurisprudential actions:
1. **`OVERRULED`**: A higher or larger bench expressly extinguishes the binding authority of a past judgment, declaring it incorrect law.
2. **`DISTINGUISHED`**: The court acknowledges the past precedent but determines that its factual matrix or statutory context differs, rendering it inapplicable to the case at bar.
3. **`FOLLOWED`**: The court affirmatively approves, adopts, and applies the *ratio decidendi* of the cited case to resolve the present dispute.
4. **`CONSIDERED`**: The court mentions, cites, summarizes, or neutrally discusses the case as part of historical discourse or counsel submissions without explicitly adopting or rejecting its core holding.

This document compiles **15–20 real-world judicial phrases for each category** extracted from Indian Supreme Court and High Court judgments, defines **priority-ordered regex patterns**, and specifies **context window parameters** for Sai to implement in `scripts/graph/classify_relationship.py`.

---

## 2. Priority Hierarchy for Automated Classification

When scanning a context window around a citation, multiple signal keywords may co-occur (e.g., *"Counsel argued that the decision was followed in X, but we overrule it"*). 

Sai must evaluate the signals in **strict priority order**:

$$\mathbf{OVERRULED} \succ \mathbf{DISTINGUISHED} \succ \mathbf{FOLLOWED} \succ \mathbf{CONSIDERED}$$

| Priority | Relationship Label | Edge Type in DPEG | Default Confidence | Rationale |
| :---: | :---: | :---: | :---: | :--- |
| **1** | `OVERRULED` | Negative / Extinguishing | `0.90` (Strict) / `0.75` (Heuristic) | Overruling is rare, severe, and extinguishes precedent authority. Highest priority to catch. |
| **2** | `DISTINGUISHED` | Contrastive / Boundary | `0.85` (Strict) / `0.75` (Heuristic) | Restricts the scope of a precedent to specific factual boundaries. |
| **3** | `FOLLOWED` | Positive / Reinforcing | `0.85` (Strict) / `0.75` (Heuristic) | Reaffirms and extends precedent authority across temporal slices. |
| **4** | `CONSIDERED` | Neutral / Informational | `0.50` (Default fallback) | General discussion, counsel reliance, or statutory background. |

---

## 3. Real Judicial Phrasing & Signal Catalog (15–20 Examples per Class)

### 3.1 `OVERRULED` (Priority 1)
*Precedent is deprived of authoritative force by a competent bench (larger bench or Supreme Court).*

#### Observed Real-World Judicial Phrasing:
1. *"We hereby overrule the decision in..."*
2. *"The view taken by this Court in [...] cannot be sustained and is accordingly overruled."*
3. *"The decision in [...] does not lay down the correct law and stands overruled."*
4. *"We are of the considered opinion that [...] was erroneously decided and must be overruled."*
5. *"The principle enunciated in [...] is no longer good law in view of the subsequent Constitution Bench decision."*
6. *"We are unable to subscribe to the view expressed in [...] and the same is hereby set aside."*
7. *"To the extent of the inconsistency, the judgment in [...] stands impliedly overruled."*
8. *"The decision in [...] was rendered per incuriam, ignoring the mandatory statutory provisions, and cannot be treated as binding precedent."*
9. *"We express our respectful disagreement with the ratio in [...] and overrule the same."*
10. *"The High Court fell into grave error in relying on [...] which has already been overruled by this Court."*
11. *"The proposition laid down in [...] is contrary to the constitutional mandate and is overruled."*
12. *"We find that the reasoning in [...] is fundamentally flawed and cannot be approved."*
13. *"In our considered view, [...] ceased to be good law following the amendment."*
14. *"We depart from the view expressed in [...] and hold that..."*
15. *"The majority opinion in [...] stands superseded by..."*
16. *"The judgment in [...] must be confined to its own facts and cannot be considered good law for the proposition that..."*
17. *"Having examined the statutory scheme, we overrule the contrary view taken in..."*

#### Negative Lookaheads / Guards for `OVERRULED`:
* Avoid false positives from negated phrases: `not been overruled`, `number been overruled` (ILDC OCR artifact), `cannot be said to be overruled`, `has not been departed from`.
* Avoid advocate claims: *"Mr. Counsel contended that the decision stood overruled..."* (Check rhetorical zone — if in `SUBMISSIONS`, assign lower confidence `0.55`).

---

### 3.2 `DISTINGUISHED` (Priority 2)
*Court recognizes the legal principle of the cited case but finds it inapplicable due to differing facts or statutory provisions.*

#### Observed Real-World Judicial Phrasing:
1. *"The decision in [...] is distinguishable on facts and has no application to the present case."*
2. *"This judgment is wholly distinguishable and does not apply at all to the facts of the present case."*
3. *"The reliance placed by the learned counsel on [...] is completely misplaced."*
4. *"The facts in [...] were entirely different from the factual matrix before us."*
5. *"The decision in [...] turned on its own peculiar facts and cannot assist the appellant."*
6. *"We find that [...] is clearly inapplicable to the controversy in hand."*
7. *"The principle laid down in [...] was rendered in the context of a totally different statutory enactment."*
8. *"That was a case where the dispute arose under [...] and therefore the ratio therein cannot be attracted here."*
9. *"The learned Single Judge erred in applying [...] without noticing the crucial distinction that..."*
10. *"We are unable to accept the submission that [...] governs this case, as the facts are markedly distinguishable."*
11. *"In [...], the court was concerned with [...], whereas in the instant case..."*
12. *"The cited authority dealt with a pre-amendment scenario and has no bearing on the present controversy."*
13. *"The ratio in [...] cannot be stretched to cover cases where..."*
14. *"A bare reading of [...] shows that it has no relevance to the issue raised herein."*
15. *"We distinguish the judgment in [...] on the ground that there was no statutory bar in that case."*
16. *"The decision cited is of no assistance to the respondent because..."*
17. *"Unlike the situation in [...], in the present case the prosecution has failed to establish..."*
18. *"The observations in [...] must be read in the light of the facts appearing therein and cannot be applied mechanically."*

#### Negative Lookaheads / Guards for `DISTINGUISHED`:
* Avoid general English use of "distinction": `distinction between murder and culpable homicide`, `distinction was drawn between`, `without distinction of caste or creed`.
* Guard pattern: Require proximity between the distinction verb/adjective and the precedent citation or case name within 15 words.

---

### 3.3 `FOLLOWED` (Priority 3)
*Court adopts, reinforces, and treats the cited case's ratio decidendi as binding and dispositive.*

#### Observed Real-World Judicial Phrasing:
1. *"Following the judgment in [...], we hold that..."*
2. *"The law laid down in [...] has been consistently followed by this Court in a catena of decisions."*
3. *"We are in respectful agreement with the principles enunciated in..."*
4. *"The controversy in the present appeal is squarely covered by the decision in..."*
5. *"Applying the ratio of [...], the impugned order cannot be sustained."*
6. *"This Court in [...] has authoritatively settled that..."*
7. *"We reiterate the view taken by the three-Judge Bench in..."*
8. *"The proposition is firmly established in view of the authoritative pronouncement in..."*
9. *"We find no reason to take a view different from what was held in..."*
10. *"The High Court rightly followed the binding precedent of this Court in..."*
11. *"The question of law raised herein is no longer res integra and stands concluded by..."*
12. *"In view of the settled legal position emerging from [...], the appeal must succeed."*
13. *"We fully endorse and adopt the reasoning of this Court in..."*
14. *"Palvinder Kaur's decision has been followed in various later decisions, including..."*
15. *"The principles governing [...] have been lucidly summarized in [...] and we respectfully adhere to them."*
16. *"Guided by the dictum in [...], we are satisfied that..."*
17. *"It is well settled in [...] that judgments cannot be read mechanically..."*
18. *"We concur with the view expressed by the Division Bench in..."*

#### Negative Lookaheads / Guards for `FOLLOWED`:
* Avoid non-precedent usage: `procedure followed by the investigating officer`, `course followed by the High Court`, `inquiry followed`, `followed by an order dated`.
* Guard pattern: `follow(ed|ing)?\s+(?:the\s+)?(?:ratio|judgment|decision|principle|dictum|law|ruling|view)` or `followed in`.

---

### 3.4 `CONSIDERED` (Priority 4 - Default Fallback)
*Court refers to, notices, or discusses a precedent without an explicit positive or negative disposition.*

#### Observed Real-World Judicial Phrasing:
1. *"In that decision, this Court referred to its earlier judgment in..."*
2. *"Reference was made to the decision in..."*
3. *"Our attention was invited to the observations in..."*
4. *"Learned counsel for the appellant placed strong reliance upon..."*
5. *"The Court in [...] observed that..."*
6. *"In support of this contention, reliance was placed on..."*
7. *"We have carefully considered the decision cited at the Bar in..."*
8. *"The scope of Section [...] was noticed in..."*
9. *"A similar question arose for consideration in..."*
10. *"The observations made in [...] were cited by the respondent."*
11. *"In [...], this Court had occasion to examine the provisions of..."*
12. *"The learned counsel drew our attention to paragraph [...] of the judgment in..."*
13. *"The High Court adverted to the decision in..."*
14. *"Extensive reference was made to the findings in..."*
15. *"The principles were discussed at length in..."*
16. *"In [...], the Constitution Bench dealt with a similar challenge."*

---

## 4. Ready-to-Use Python Regex Specification for Sai

Sai can copy this dictionary directly into `scripts/graph/classify_relationship.py`:

```python
import re

# Priority-ordered signal regex suite
# Evaluate in order: OVERRULED -> DISTINGUISHED -> FOLLOWED -> (Default: CONSIDERED)

RELATIONSHIP_SIGNALS = {
    "OVERRULED": [
        re.compile(r"\b(?:is|are|was|were|stands?|hereby)?\s*(?:expressly|impliedly)?\s*overruled?\b", re.I),
        re.compile(r"\bno\s+longer\s+(?:good|sound)\s+law\b", re.I),
        re.compile(r"\brendered\s+per\s+incuriam\b", re.I),
        re.compile(r"\b(?:cannot|unable\s+to)\s+(?:subscribe|agree)\s+(?:with|to)\s+the\s+view\b", re.I),
        re.compile(r"\bset\s+aside\s+the\s+view\s+in\b", re.I),
        re.compile(r"\bdepart(?:ed)?\s+from\s+the\s+(?:view|ratio)\b", re.I),
        re.compile(r"\b(?:erroneously|incorrectly)\s+decided\b", re.I),
    ],
    
    "DISTINGUISHED": [
        re.compile(r"\b(?:is|are|was|were|wholly|clearly)?\s*distinguish(?:able|ed)?\b", re.I),
        re.compile(r"\bhas\s+no\s+application\b", re.I),
        re.compile(r"\b(?:inapplicable|not\s+applicable)\s+to\s+the\s+facts\b", re.I),
        re.compile(r"\b(?:misplaced|untenable)\s+reliance\b", re.I),
        re.compile(r"\bfacts\s+(?:in|of)\s+.*?\s+(?:were|are)\s+(?:entirely|markedly|completely)\s+different\b", re.I),
        re.compile(r"\bturned\s+on\s+its\s+own\s+(?:peculiar\s+)?facts\b", re.I),
        re.compile(r"\bcannot\s+(?:assist|help)\s+the\s+(?:appellant|petitioner|respondent)\b", re.I),
        re.compile(r"\bdistinction\s+between\s+the\s+facts\b", re.I),
    ],
    
    "FOLLOWED": [
        re.compile(r"\bfollow(?:ing|ed)?\s+(?:the\s+)?(?:ratio|judgment|decision|principle|dictum|law|ruling|view)\b", re.I),
        re.compile(r"\bhas\s+been\s+followed\s+in\b", re.I),
        re.compile(r"\brespectful\s+agreement\s+with\b", re.I),
        re.compile(r"\bsquarely\s+covered\s+by\b", re.I),
        re.compile(r"\bapplying\s+the\s+ratio\s+of\b", re.I),
        re.compile(r"\bauthoritatively\s+settled\b", re.I),
        re.compile(r"\breiterate\s+(?:the\s+)?(?:view|principle|law)\b", re.I),
        re.compile(r"\bconsistently\s+held\b", re.I),
        re.compile(r"\bconcur\s+with\s+the\s+view\b", re.I),
        re.compile(r"\bno\s+longer\s+res\s+integra\b", re.I),
        re.compile(r"\bapproved\s+by\s+this\s+Court\b", re.I),
    ],
    
    "CONSIDERED": [
        re.compile(r"\breferr?ed\s+to\b", re.I),
        re.compile(r"\brelied\s+upon\b", re.I),
        re.compile(r"\bcited\s+by\b", re.I),
        re.compile(r"\bnoticed\s+in\b", re.I),
        re.compile(r"\bconsidered\s+(?:in|by)\b", re.I),
        re.compile(r"\bplaced\s+reliance\s+(?:on|upon)\b", re.I),
        re.compile(r"\bobservations?\s+in\b", re.I),
        re.compile(r"\battention\s+was\s+(?:drawn|invited)\b", re.I),
    ]
}

# Negation & False Positive filter
NEGATION_GUARDS = [
    re.compile(r"\b(?:not|number|never|hardly)\s+(?:been\s+)?overruled\b", re.I),
    re.compile(r"\bcannot\s+be\s+said\s+to\s+be\s+overruled\b", re.I),
    re.compile(r"\bdistinction\s+between\s+(?!the\s+case|the\s+decision)", re.I),
    re.compile(r"\bprocedure\s+followed\b", re.I),
    re.compile(r"\bcourse\s+followed\b", re.I),
    re.compile(r"\bfollowed\s+by\s+(?:an?\s+)?(?:order|inquiry|investigation|notice)\b", re.I),
]
```

---

## 5. Context Window & Spatial Guidelines for Edge Extraction

1. **Tight Syntactical Window ($\pm 50$ words):**
   * Precedent name/citation and treatment verb usually occur within the same sentence or adjacent sentence.
   * If a signal is found within $\pm 50$ words, assign **`confidence = 0.85`**.

2. **Discourse Window ($\pm 250$ words):**
   * If a signal appears in the broader paragraph, check whether an intervening citation exists.
   * If another precedent citation is closer to the keyword, bind the signal to that closer precedent instead.
   * If bound via discourse window without closer citation, assign **`confidence = 0.70`**.

3. **Rhetorical Zone Integration (`docs/section_headers.md`):**
   * Citations in `HELD / RATIO DECIDENDI / CONCLUSION`: **Boost confidence by $+0.10$** (Court's definitive holding).
   * Citations in `ANALYSIS / DISCUSSION`: Standard confidence.
   * Citations in `SUBMISSIONS / ARGUMENTS`: **Cap confidence at $0.55$** and tag `is_submission = True` (Argument by counsel, not binding court treatment).
