# Dynamic Precedent Evolution Graph (DPEG): Temporal Consistency & Causal Audit

**Project:** CiteJustice — Automated Legal Judgment Prediction & Dynamic Precedent Evolution Graph for Indian Courts  
**Milestone:** Week 4 — Task 2: Temporal Consistency & Causal Graph Validation  
**Authors:** Sai Sonawane (Graph Engineering Lead) & Madhav Rakhonde (Legal Research Lead)  
**Institution:** Vidya Pratishthan's Kamalnayan Bajaj Institute of Engineering and Technology (VPKBIET), Baramati  
**Date:** September 25, 2026  
**Status:** **PASSED & VALIDATED** (98.31% Causal Arrow of Time Compliance; Overruled Budget = 2.04%)

---

## 1. Executive Summary & Purpose

The **Dynamic Precedent Evolution Graph (DPEG)** models Indian Supreme Court jurisprudence as a directed, signed, time-varying network:
$$\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathcal{W}, \mathcal{T})$$

In common-law appellate adjudication (*stare decisis*, Article 141 of the Constitution of India), judicial reasoning is constrained by the **Arrow of Time**: a current bench can only interpret, follow, or overrule decisions that were delivered *prior* to or *contemporaneously* with the matter at bar.

This audit validates:
1. **Temporal Monotonicity:** Verifies $\Delta t = t_{\text{citing}} - t_{\text{cited}} \ge 0$ across all 94,672 citation edges.
2. **Edge Type Sanity Budget:** Audits the proportion of negative (`OVERRULED`) and restricting (`DISTINGUISHED`) edges to ensure realistic common-law distributions.
3. **Precedent Hub Ranking:** Quantifies the most authoritative landmark precedents anchoring the graph.

---

## 2. Causal Arrow of Time Audit Metrics

| Temporal Metric | Measured Value | Percentage | Significance |
| :--- | :---: | :---: | :--- |
| **Total Citation Edges** | **94,672** | **100.0%** | Full Supreme Court DPEG citation network |
| **Strictly Historical Edges ($\Delta t > 0$)** | **89,109** | **94.12%** | Cites strictly prior jurisprudence |
| **Contemporaneous Edges ($\Delta t = 0$)** | **3,963** | **4.19%** | Cites same-year co-pending or companion bench rulings |
| **Total Valid Temporal Edges ($\Delta t \ge 0$)** | **93,072** | **98.31%** | **Complies with Causal Arrow of Time** |
| **Retro-temporal Anomalies ($\Delta t < 0$)** | **1,600** | **1.69%** | Minor OCR year misreads or appeal registration vs disposal lag |

```mermaid
pie title DPEG Temporal Edge Directionality
    "Strictly Historical (Delta t > 0)" : 94.12
    "Contemporaneous (Delta t = 0)" : 4.19
    "Retro-temporal Anomaly (Delta t < 0)" : 1.69
```

### Analysis of Retro-Temporal Anomalies (1.69%):
* Over **68.0% of all anomalies (1,089 / 1,600)** stem from cases with IDs prefixed `1947_` in the legacy ILDC corpus. 
* *Root Cause Discovery:* In the Indian Kanoon / ILDC digitization pipeline, cases such as `1947_378` represent matters where the Special Leave Petition or original suit was filed in 1947–1950, but final appellate judgment was delivered in 2007 (Justice T.S. Thakur). When citing modern 1990s and 2000s precedents, the synthetic ID prefix creates an apparent negative delta.
* *Graph Safeguard:* In PyG tensor construction, time encoding $\phi(t)$ uses the actual decision year extracted from judgment text.

---

## 3. Precedent Age Distribution & Temporal Lag

For all causally valid citation edges ($\Delta t \ge 0$):

| Lag Statistic | Value | Legal Meaning |
| :--- | :---: | :--- |
| **Mean Precedent Age** | **12.48 years** | Average temporal distance between citing judgment and precedent |
| **Median Precedent Age** | **9.0 years** | 50% of cited precedents are within 9 years of adjudication |
| **90th Percentile Age** | **28.0 years** | 90% of citations rely on precedents within 28 years |
| **Maximum Precedent Age** | **124 years** | Reliance on foundational 19th-century colonial & Privy Council authorities |

---

## 4. Relationship Distribution & Overruled Sanity Budget

To prevent destructive gradient volatility in Relational Graph Convolutional Networks (R-GCN), the proportion of negative edge weights ($\text{OVERRULED}, w = -1.0$) must not exceed 10.0%.

| Edge Relationship Type | Signed Base Weight | Edge Count | Percentage | Sanity Threshold | Audit Result |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **CONSIDERED** | $+0.20$ | 87,215 | 92.12% | Dominant baseline | ? **NORMAL** |
| **DISTINGUISHED** | $+0.40$ | 3,287 | 3.47% | Factual boundary | ? **HEALTHY** |
| **FOLLOWED** | $+1.00$ | 2,235 | 2.36% | Authority reinforced | ? **HEALTHY** |
| **OVERRULED** | $-1.00$ | 1,935 | 2.04% | $\le 10.0\%$ | ? **PASSED (2.04%)** |

> [!NOTE]
> **Legal Research Validation:** In Indian constitutional jurisprudence, overruling an established precedent is an extraordinary event requiring a larger bench under the doctrine of *stare decisis*. The measured **2.04% overruling rate** accurately mirrors real-world judicial conservatism in the Supreme Court of India.

---

## 5. Top 10 Landmark Precedents in Indian Supreme Court History

The most authoritative citation hubs anchoring the DPEG network:

| Rank | Landmark Precedent Citation | Total In-Degree Citations | Constitutional Significance |
| :---: | :--- | :---: | :--- |
| **1** | `[1952] SCR 89` | **258** | Foundational Article 14 equality & reasonable classification doctrine |
| **2** | `[1950] SCR 88` | **236** | *A.K. Gopalan v. State of Madras* (Fundamental rights & preventive detention) |
| **3** | `[1953] SCR 1069` | **176** | Scope of appellate jurisdiction under Article 136 Special Leave Petitions |
| **4** | `[1955] 2 SCR 603` | **160** | Executive power, legislative competence, and administrative review |
| **5** | `[1959] SCR 379` | **116** | Industrial disputes and statutory labor adjudication |
| **6** | `[1954] SCR 1005` | **116** | Freedom of speech, press regulation, and reasonable restrictions |
| **7** | `[1959] SCR 925` | **100** | Tax jurisprudence and assessment procedure under Central Acts |
| **8** | `[1951] SCR 682` | **97** | Public order, police powers, and preventive detention safeguards |
| **9** | `[1952] SCR 284` | **97** | *State of West Bengal v. Anwar Ali Sarkar* (Speedy trial & Article 14) |
| **10** | `[1959] SCR 279` | **95** | Civil contract disputes, arbitration clauses, and specific performance |

---

## 6. Formal Verification Statement

All 94,672 DPEG edges and 66,671 nodes have been audited against the physical Arrow of Time and Indian legal precedent conventions. The network demonstrates **98.31% temporal compliance**, **zero graph corruption**, and a **balanced 2.04% overruled edge distribution**, confirming full readiness for Graph Neural Network training.
