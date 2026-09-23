"""
scripts/graph/classify_relationship.py

Week 3 - Task 2: Precedent Relationship Classification Pipeline
Author: Sai Sonawane (CiteJustice)

Classifies candidate precedent citation edges into 4 canonical legal relationships:
1. OVERRULED      (Priority 1: Authority extinguished)
2. DISTINGUISHED  (Priority 2: Precedent deemed factually/statutorily inapplicable)
3. FOLLOWED       (Priority 3: Ratio decidendi reaffirmed and adopted)
4. CONSIDERED     (Priority 4 / Fallback: Mentioned or discussed neutrally)

Based on:
- docs/citation_signals.md (signal taxonomy & priority hierarchy by Madhav)
- docs/citation_validation.md (empirical validation & negation guards)

Usage:
    py scripts/graph/classify_relationship.py --sample 50
    py scripts/graph/classify_relationship.py --dataset single
    py scripts/graph/classify_relationship.py --dataset multi
"""

import os
import re
import sys
import csv
import json
import argparse
from pathlib import Path

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CLEAN_DIR = BASE_DIR / "data" / "clean"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# 1. Priority-Ordered Signal Patterns (from docs/citation_signals.md)
# --------------------------------------------------------------------------
RELATIONSHIP_SIGNALS = {
    "OVERRULED": [
        re.compile(r"\b(?:is|are|was|were|stands?|hereby)?\s*(?:expressly|impliedly)?\s*overrul(?:ed?|ing)\b", re.I),
        re.compile(r"\bno\s+longer\s+(?:good|sound)\s+law\b", re.I),
        re.compile(r"\brendered\s+per\s+incuriam\b", re.I),
        re.compile(r"\b(?:cannot|unable\s+to)\s+(?:subscribe|agree)\s+(?:with|to)\s+the\s+view\b", re.I),
        re.compile(r"\bset\s+aside\s+the\s+view\s+in\b", re.I),
        re.compile(r"\bdepart(?:ed)?\s+from\s+the\s+(?:view|ratio)\b", re.I),
        re.compile(r"\b(?:erroneously|incorrectly)\s+decided\b", re.I),
    ],
    "DISTINGUISHED": [
        re.compile(r"\b(?:is|are|was|were|wholly|clearly)?\s*distinguish(?:able|ed?|ing)\b", re.I),
        re.compile(r"\bhas\s+no\s+application\b", re.I),
        re.compile(r"\b(?:inapplicable|not\s+applicable)\s+to\s+the\s+facts\b", re.I),
        re.compile(r"\b(?:misplaced|untenable)\s+reliance\b", re.I),
        re.compile(r"\bfacts\s+(?:in|of)\s+.*?\s+(?:were|are)\s+(?:entirely|markedly|completely)\s+different\b", re.I),
        re.compile(r"\bturned\s+on\s+its\s+own\s+(?:peculiar\s+)?facts\b", re.I),
        re.compile(r"\bcannot\s+(?:assist|help)\s+the\s+(?:appellant|petitioner|respondent)\b", re.I),
        re.compile(r"\bdistinction\s+between\s+(?:the\s+facts|the\s+two\s+cases|the\s+decisions)\b", re.I),
    ],
    "FOLLOWED": [
        re.compile(r"\bfollow(?:ing|ed)?\s+(?:the\s+)?(?:ratio|judgment|decision|principle|dictum|law|ruling|view)\b", re.I),
        re.compile(r"\b(?:we|court)\s+(?:shall\s+)?follow(?:ed|s)?\s+(?:the\s+)?(?:decision|view|ratio|ruling|judgment)?\b", re.I),
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

# --------------------------------------------------------------------------
# 2. Negation & False Positive Filter Guards (from docs/citation_validation.md)
# --------------------------------------------------------------------------
NEGATION_GUARDS = {
    "OVERRULED": [
        re.compile(r"\b(?:not|number|never|hardly)\s+(?:been\s+)?overruled\b", re.I),
        re.compile(r"\bcannot\s+be\s+said\s+to\s+be\s+overruled\b", re.I),
        re.compile(r"\bhas\s+not\s+been\s+departed\s+from\b", re.I),
        re.compile(r"\b(?:doctrine\s+of\s+)?prospective\s+overrul(?:ing|ed)\b", re.I),
    ],
    "DISTINGUISHED": [
        re.compile(r"\bdistinction\s+between\s+(?!the\s+case|the\s+decision|the\s+facts)", re.I),
        re.compile(r"\bwithout\s+distinction\b", re.I),
    ],
    "FOLLOWED": [
        re.compile(r"\bprocedure\s+followed\b", re.I),
        re.compile(r"\bcourse\s+followed\b", re.I),
        re.compile(r"\bfollowed\s+by\s+(?:an?\s+)?(?:order|inquiry|investigation|notice|charge|prosecution)\b", re.I),
    ]
}

def is_negated_or_guarded(text: str, relationship: str) -> bool:
    """Checks whether the relationship keyword in text is invalidated by a guard rule."""
    guards = NEGATION_GUARDS.get(relationship, [])
    for g in guards:
        if g.search(text):
            return True
    return False

def classify_citation_edge(edge_data: dict) -> dict:
    """
    Evaluates context windows in strict priority order:
    OVERRULED > DISTINGUISHED > FOLLOWED > CONSIDERED.
    Assigns calibrated confidence scores based on window proximity and rhetorical zone.
    """
    ctx_50 = edge_data.get("context_window_50", "")
    ctx_250 = edge_data.get("context_window_250", "")
    rhetorical_zone = edge_data.get("rhetorical_zone", "UNSPECIFIED")
    is_submission = edge_data.get("is_submission", False)

    relationship = "CONSIDERED"
    confidence = 0.50
    matched_window = "none"
    matched_pattern = "default_fallback"

    # Evaluation Priority Order
    priority_order = ["OVERRULED", "DISTINGUISHED", "FOLLOWED", "CONSIDERED"]

    # Base confidence mappings by priority and window size
    base_confidences = {
        "tight_50": {
            "OVERRULED": 0.90,
            "DISTINGUISHED": 0.85,
            "FOLLOWED": 0.85,
            "CONSIDERED": 0.65
        },
        "discourse_250": {
            "OVERRULED": 0.75,
            "DISTINGUISHED": 0.70,
            "FOLLOWED": 0.70,
            "CONSIDERED": 0.55
        }
    }

    found_classification = False

    # Pass 1: Scan tight syntactical window (±50 words)
    for rel in priority_order:
        if found_classification:
            break
        patterns = RELATIONSHIP_SIGNALS[rel]
        for pat in patterns:
            match = pat.search(ctx_50)
            if match:
                # Check for false positive / negation guards
                if not is_negated_or_guarded(ctx_50, rel):
                    relationship = rel
                    confidence = base_confidences["tight_50"][rel]
                    matched_window = "tight_50"
                    matched_pattern = match.group(0).strip()
                    found_classification = True
                    break

    # Pass 2: If no tight match, scan extended discourse window (±250 words)
    if not found_classification:
        for rel in priority_order:
            if found_classification:
                break
            patterns = RELATIONSHIP_SIGNALS[rel]
            for pat in patterns:
                match = pat.search(ctx_250)
                if match:
                    if not is_negated_or_guarded(ctx_250, rel):
                        relationship = rel
                        confidence = base_confidences["discourse_250"][rel]
                        matched_window = "discourse_250"
                        matched_pattern = match.group(0).strip()
                        found_classification = True
                        break

    # Pass 3: Rhetorical Zone Confidence Modulation
    if rhetorical_zone == "CONCLUSION":
        # Final holding: boost confidence by +0.10
        confidence = min(0.98, confidence + 0.10)
    elif is_submission or rhetorical_zone == "SUBMISSIONS":
        # Counsel contention: cap confidence at 0.55
        confidence = min(0.55, confidence)

    # Attach classification fields to edge object
    classified_edge = dict(edge_data)
    classified_edge["relationship"] = relationship
    classified_edge["confidence"] = round(confidence, 2)
    classified_edge["matched_window"] = matched_window
    classified_edge["matched_pattern"] = matched_pattern

    return classified_edge

def process_dataset(input_jsonl: Path, output_jsonl: Path, output_csv: Path, sample_size: int = None):
    print("=" * 70)
    print("CiteJustice - Week 3 Task 2: Precedent Relationship Classification")
    print(f"Source JSONL : {input_jsonl}")
    print(f"Target JSONL : {output_jsonl}")
    print(f"Target CSV   : {output_csv}")
    print("=" * 70)

    if not input_jsonl.exists():
        print(f"Error: Input file {input_jsonl} does not exist.")
        sys.exit(1)

    print(f"Reading dataset: {input_jsonl.name}...")
    edges = []
    with open(input_jsonl, mode="r", encoding="utf-8") as f_in:
        for line in f_in:
            if not line.strip():
                continue
            edges.append(json.loads(line))
            if sample_size and len(edges) >= sample_size:
                break

    total_edges = len(edges)
    print(f"Loaded {total_edges:,} candidate citation edges to classify.\n")

    rel_counts = {
        "OVERRULED": 0,
        "DISTINGUISHED": 0,
        "FOLLOWED": 0,
        "CONSIDERED": 0
    }
    window_counts = {
        "tight_50": 0,
        "discourse_250": 0,
        "none": 0
    }

    classified_edges = []
    print("Classifying precedent relationships via priority hierarchy...")
    for idx, edge in enumerate(edges, 1):
        c_edge = classify_citation_edge(edge)
        classified_edges.append(c_edge)

        rel = c_edge["relationship"]
        rel_counts[rel] = rel_counts.get(rel, 0) + 1

        w = c_edge["matched_window"]
        window_counts[w] = window_counts.get(w, 0) + 1

        if idx % 2000 == 0 or idx == total_edges:
            print(f"  Classified {idx:,} / {total_edges:,} edges ({(idx/total_edges)*100:.1f}%)...")

    # Save to classified JSONL
    with open(output_jsonl, mode="w", encoding="utf-8") as f_out:
        for c in classified_edges:
            f_out.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"\n[OK] Classified edges JSONL saved to: {output_jsonl}")

    # Save to inspection CSV
    csv_fields = [
        "edge_id",
        "citing_case_id",
        "citing_year",
        "cited_citation",
        "cited_year",
        "relationship",
        "confidence",
        "matched_window",
        "matched_pattern",
        "rhetorical_zone",
        "is_submission",
        "temporal_valid",
        "context_preview"
    ]
    with open(output_csv, mode="w", encoding="utf-8", newline="") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=csv_fields)
        writer.writeheader()
        for c in classified_edges:
            preview = c["context_window_50"][:140] + "..." if len(c["context_window_50"]) > 140 else c["context_window_50"]
            writer.writerow({
                "edge_id": c["edge_id"],
                "citing_case_id": c["citing_case_id"],
                "citing_year": c["citing_year"],
                "cited_citation": c["cited_citation"],
                "cited_year": c["cited_year"],
                "relationship": c["relationship"],
                "confidence": c["confidence"],
                "matched_window": c["matched_window"],
                "matched_pattern": c["matched_pattern"],
                "rhetorical_zone": c["rhetorical_zone"],
                "is_submission": c["is_submission"],
                "temporal_valid": c["temporal_valid"],
                "context_preview": preview
            })
    print(f"[OK] Classified inspection CSV saved to: {output_csv}")

    # Summary table
    print("\n" + "-" * 50)
    print("Execution Summary:")
    print(f"  Total edges evaluated        : {total_edges:,}")
    print("  Relationship class distribution:")
    for r_name in ["OVERRULED", "DISTINGUISHED", "FOLLOWED", "CONSIDERED"]:
        cnt = rel_counts.get(r_name, 0)
        pct = (cnt / total_edges) * 100 if total_edges else 0
        print(f"    - {r_name:<14}: {cnt:>6,} edges ({pct:>5.1f}%)")
    print("  Signal resolution window:")
    for w_name, w_cnt in window_counts.items():
        pct = (w_cnt / total_edges) * 100 if total_edges else 0
        print(f"    - {w_name:<14}: {w_cnt:>6,} edges ({pct:>5.1f}%)")
    print("-" * 50)

def main():
    parser = argparse.ArgumentParser(description="Classify precedent citation relationships for DPEG.")
    parser.add_argument("--dataset", choices=["single", "multi"], default="single",
                        help="Dataset: 'single' (12,764 edges) or 'multi' (79,294 edges).")
    parser.add_argument("--sample", type=int, default=None,
                        help="Process only a sample of N edges for fast testing.")
    args = parser.parse_args()

    input_jsonl = CLEAN_DIR / f"ildc_{args.dataset}_citation_contexts.jsonl"

    output_base = f"ildc_{args.dataset}"
    if args.sample:
        output_base += f"_sample_{args.sample}"

    output_jsonl = CLEAN_DIR / f"{output_base}_classified_edges.jsonl"
    output_csv = CLEAN_DIR / f"{output_base}_classified_edges_summary.csv"

    process_dataset(input_jsonl, output_jsonl, output_csv, sample_size=args.sample)

if __name__ == "__main__":
    main()
