"""
scripts/graph/extract_citations.py

Week 3 - Task 1: Precedent Citation & Context Window Extraction Pipeline
Author: Sai Sonawane (CiteJustice)

1. Scans clean segmented judgments (ildc_*_segmented.jsonl) for all canonical citations (SCC, AIR, SCR, SCALE, INSC, Cri LJ).
2. Extracts dual-resolution context windows around each cited precedent:
   - Tight syntactical window (±50 words)
   - Extended discourse window (±250 words)
3. Maps each citation to its precise rhetorical zone (FACTS, SUBMISSIONS, ISSUES, ANALYSIS, CONCLUSION).
4. Verifies temporal sequence (cited_year <= citing_year).
5. Compiles candidate precedent citation edges for relationship classification and DPEG construction.

Usage:
    py scripts/graph/extract_citations.py --sample 50
    py scripts/graph/extract_citations.py --dataset single
    py scripts/graph/extract_citations.py --dataset multi
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
# 1. Canonical Citation Matchers (Output of Week 2 Step 2 Normalization)
# --------------------------------------------------------------------------
CANONICAL_CITATION_REGEX = re.compile(
    r"("
    r"\((?:19|20)\d{2}\)\s+(?:Supp\s+(?:\d+\s+)?)?(?:\d+\s+)?SCC\s+\d+"         # SCC: (2018) 1 SCC 1
    r"|AIR\s+(?:19|20)\d{2}\s+(?:SC|[A-Z][a-z]+)\s+\d+"                           # AIR: AIR 1973 SC 1461
    r"|\[(?:19|20)\d{2}\]\s+(?:\d+\s+)?SCR\s+\d+"                                 # SCR: [1950] SCR 869
    r"|\((?:19|20)\d{2}\)\s+(?:\d+\s+)?SCALE\s+\d+"                               # SCALE: (2002) 3 SCALE 456
    r"|(?:19|20)\d{2}\s+INSC\s+\d+"                                               # INSC: 2023 INSC 182
    r"|(?:19|20)\d{2}\s+Cri\s*LJ\s+\d+"                                           # Cri LJ: 1980 Cri LJ 142
    r")",
    re.IGNORECASE
)

YEAR_REGEX = re.compile(r"((?:19|20)\d{2})(?:[_\D]|$)")

def extract_year_from_id(case_id: str) -> int:
    """Extracts 4-digit calendar year from case ID (e.g. '2014_170' -> 2014)."""
    match = YEAR_REGEX.search(str(case_id))
    return int(match.group(1)) if match else None

def extract_year_from_citation(citation: str) -> int:
    """Extracts 4-digit publication year from a canonical legal citation."""
    match = YEAR_REGEX.search(citation)
    return int(match.group(1)) if match else None

def extract_context_window(text: str, match_start: int, match_end: int, num_words: int) -> str:
    """
    Slices num_words before and num_words after the citation match,
    returning a clean whitespace-normalized snippet.
    """
    pre_text = text[:match_start].rstrip()
    post_text = text[match_end:].lstrip()

    pre_words = pre_text.split()[-num_words:] if pre_text else []
    post_words = post_text.split()[:num_words] if post_text else []

    citation_str = text[match_start:match_end]
    snippet_words = pre_words + [citation_str] + post_words
    return " ".join(snippet_words)

def extract_citation_edges_from_case(case_data: dict) -> list[dict]:
    """
    Scans a single judgment across full text and rhetorical zones,
    extracting every precedent citation occurrence with dual context windows.
    """
    case_id = case_data.get("id", "unknown")
    label = case_data.get("label", "")
    split = case_data.get("split", "train")
    citing_year = extract_year_from_id(case_id)

    full_text = case_data.get("full_text") or ""
    if not full_text:
        # Fall back to concatenating zones if full_text is absent
        full_text = " ".join([
            case_data.get("facts", ""),
            case_data.get("submissions", ""),
            case_data.get("issues", ""),
            case_data.get("analysis", ""),
            case_data.get("conclusion", "")
        ]).strip()

    if not full_text:
        return []

    # Map zone character ranges within full_text (heuristic offset check)
    zones = ["facts", "submissions", "issues", "analysis", "conclusion"]
    zone_texts = {z: case_data.get(z, "") for z in zones if case_data.get(z)}

    edges = []
    seen_offsets = set()
    edge_idx = 0

    # Primary scan: find all matches across full_text
    for m in CANONICAL_CITATION_REGEX.finditer(full_text):
        c_start, c_end = m.start(), m.end()
        if (c_start, c_end) in seen_offsets:
            continue
        seen_offsets.add((c_start, c_end))

        cited_citation = m.group(0).strip()
        cited_year = extract_year_from_citation(cited_citation)

        # Determine rhetorical zone by checking where the citation text appears
        rhetorical_zone = "UNSPECIFIED"
        citation_in_context = full_text[max(0, c_start - 30): min(len(full_text), c_end + 30)]

        for z_name, z_content in zone_texts.items():
            if cited_citation in z_content or citation_in_context in z_content:
                rhetorical_zone = z_name.upper()
                break

        is_submission = (rhetorical_zone == "SUBMISSIONS")

        # Temporal validity: is cited_year <= citing_year?
        temporal_valid = True
        if citing_year and cited_year:
            temporal_valid = (cited_year <= citing_year)

        # Extract ±50 and ±250 word context windows
        ctx_50 = extract_context_window(full_text, c_start, c_end, num_words=50)
        ctx_250 = extract_context_window(full_text, c_start, c_end, num_words=250)

        edge_idx += 1
        edge_id = f"{case_id}_edge_{edge_idx:03d}"

        edges.append({
            "edge_id": edge_id,
            "citing_case_id": case_id,
            "citing_year": citing_year,
            "label": label,
            "split": split,
            "cited_citation": cited_citation,
            "cited_year": cited_year,
            "rhetorical_zone": rhetorical_zone,
            "is_submission": is_submission,
            "temporal_valid": temporal_valid,
            "char_start": c_start,
            "char_end": c_end,
            "context_window_50": ctx_50,
            "context_window_250": ctx_250,
        })

    return edges

def process_dataset(input_jsonl: Path, output_jsonl: Path, output_csv: Path, sample_size: int = None):
    print("=" * 70)
    print("CiteJustice - Week 3 Task 1: Citation & Context Window Extraction")
    print(f"Source JSONL : {input_jsonl}")
    print(f"Target JSONL : {output_jsonl}")
    print(f"Target CSV   : {output_csv}")
    print("=" * 70)

    if not input_jsonl.exists():
        print(f"Error: Input file {input_jsonl} does not exist.")
        sys.exit(1)

    print(f"Reading dataset: {input_jsonl.name}...")
    cases = []
    with open(input_jsonl, mode="r", encoding="utf-8") as f_in:
        for idx, line in enumerate(f_in):
            if not line.strip():
                continue
            cases.append(json.loads(line))
            if sample_size and len(cases) >= sample_size:
                break

    total_cases = len(cases)
    print(f"Loaded {total_cases:,} cases to process.\n")

    total_edges = 0
    cases_with_citations = 0
    zone_counts = {
        "FACTS": 0,
        "SUBMISSIONS": 0,
        "ISSUES": 0,
        "ANALYSIS": 0,
        "CONCLUSION": 0,
        "UNSPECIFIED": 0
    }
    temporal_anomalies = 0

    all_edges = []

    print("Extracting precedent citations and slicing context windows...")
    for idx, case_data in enumerate(cases, 1):
        case_edges = extract_citation_edges_from_case(case_data)
        if case_edges:
            cases_with_citations += 1
            total_edges += len(case_edges)
            for e in case_edges:
                z = e.get("rhetorical_zone", "UNSPECIFIED")
                zone_counts[z] = zone_counts.get(z, 0) + 1
                if not e.get("temporal_valid"):
                    temporal_anomalies += 1
            all_edges.extend(case_edges)

        if idx % 500 == 0 or idx == total_cases:
            print(f"  Processed {idx:,} / {total_cases:,} cases ({(idx/total_cases)*100:.1f}%) | Extracted {total_edges:,} citation edges...")

    # Write output JSONL (Production interface for relationship classification)
    with open(output_jsonl, mode="w", encoding="utf-8") as f_out:
        for e in all_edges:
            f_out.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"\n[OK] Citation context records saved to: {output_jsonl}")

    # Write output CSV (Quick inspection table)
    csv_fields = [
        "edge_id",
        "citing_case_id",
        "citing_year",
        "label",
        "split",
        "cited_citation",
        "cited_year",
        "rhetorical_zone",
        "is_submission",
        "temporal_valid",
        "context_50_preview"
    ]
    with open(output_csv, mode="w", encoding="utf-8", newline="") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=csv_fields)
        writer.writeheader()
        for e in all_edges:
            preview = e["context_window_50"][:150] + "..." if len(e["context_window_50"]) > 150 else e["context_window_50"]
            writer.writerow({
                "edge_id": e["edge_id"],
                "citing_case_id": e["citing_case_id"],
                "citing_year": e["citing_year"],
                "label": e["label"],
                "split": e["split"],
                "cited_citation": e["cited_citation"],
                "cited_year": e["cited_year"],
                "rhetorical_zone": e["rhetorical_zone"],
                "is_submission": e["is_submission"],
                "temporal_valid": e["temporal_valid"],
                "context_50_preview": preview
            })
    print(f"[OK] Inspection CSV summary saved to: {output_csv}")

    # Summary report
    print("\n" + "-" * 50)
    print("Execution Summary:")
    print(f"  Total cases processed          : {total_cases:,}")
    print(f"  Cases with precedent citations : {cases_with_citations:,} ({(cases_with_citations/total_cases)*100:.1f}%)")
    print(f"  Total citation edges extracted : {total_edges:,}")
    avg_edges = (total_edges / cases_with_citations) if cases_with_citations else 0
    print(f"  Avg citations per citing case  : {avg_edges:.2f}")
    print(f"  Temporal sequence valid (t1<=t2): {total_edges - temporal_anomalies:,} ({(1 - temporal_anomalies/max(1, total_edges))*100:.1f}%)")
    print("  Rhetorical zone distribution:")
    for z_name, z_count in sorted(zone_counts.items(), key=lambda x: x[1], reverse=True):
        if z_count > 0:
            print(f"    - {z_name:<13}: {z_count:>6,} edges ({(z_count/max(1, total_edges))*100:.1f}%)")
    print("-" * 50)

def main():
    parser = argparse.ArgumentParser(description="Extract citations and context windows for DPEG graph building.")
    parser.add_argument("--dataset", choices=["single", "multi"], default="single",
                        help="Dataset: 'single' (9,110 cases) or 'multi' (34,813 cases).")
    parser.add_argument("--sample", type=int, default=None,
                        help="Process only a sample of N cases for fast testing.")
    args = parser.parse_args()

    input_jsonl = CLEAN_DIR / f"ildc_{args.dataset}_segmented.jsonl"

    output_base = f"ildc_{args.dataset}"
    if args.sample:
        output_base += f"_sample_{args.sample}"

    output_jsonl = CLEAN_DIR / f"{output_base}_citation_contexts.jsonl"
    output_csv = CLEAN_DIR / f"{output_base}_citation_contexts_summary.csv"

    process_dataset(input_jsonl, output_jsonl, output_csv, sample_size=args.sample)

if __name__ == "__main__":
    main()
