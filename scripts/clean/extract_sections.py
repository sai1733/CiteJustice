"""
scripts/clean/extract_sections.py

Pipeline module to segment raw Indian judgments into distinct rhetorical zones:
1. Facts (Factual Matrix, Trial background, FIR)
2. Submissions (Arguments of Appellant & Respondent Counsel)
3. Issues (Questions of Law formulated by the court)
4. Analysis (Legal reasoning, discussion of statutes & precedents)
5. Conclusion (Held, Ratio Decidendi, Final Operative Order)

Leverages:
- docs/section_headers.md (catalog of explicit headers and formulaic triggers)

Output:
- Structured JSON Lines (JSONL) file: data/clean/ildc_segmented_cases.jsonl
- Standard CSV with segmented fields for easy inspection.

Usage:
    python scripts/clean/extract_sections.py --sample 50
    python scripts/clean/extract_sections.py --dataset single
    python scripts/clean/extract_sections.py --dataset multi
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
RAW_DIR = BASE_DIR / "data" / "raw" / "ildc"
CLEAN_DIR = BASE_DIR / "data" / "clean"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# 1. Compiled Boundary Patterns for Explicit Section Headers
# --------------------------------------------------------------------------
ZONE_HEADER_PATTERNS = [
    ("FACTS", re.compile(
        r"(?im)^\s*(?:[I|V|X\d]+\.\s*)?(?:THE\s+)?(?:BRIEF\s+)?(?:FACTS|FACTUAL\s+(?:MATRIX|BACKGROUND|CONTEXT)|GENESIS\s+OF\s+THE\s+CASE|CASE\s+OF\s+THE\s+(?:PROSECUTION|APPELLANT|COMPLAINANT))\b"
    )),
    ("SUBMISSIONS", re.compile(
        r"(?im)^\s*(?:[I|V|X\d]+\.\s*)?(?:RIVAL\s+)?(?:SUBMISSIONS|ARGUMENTS|CONTENTIONS)(?:\s+(?:ON\s+BEHALF\s+OF|FOR)\s+THE\s+(?:APPELLANT|RESPONDENT|PETITIONER|STATE|ACCUSED))?\b"
    )),
    ("ISSUES", re.compile(
        r"(?im)^\s*(?:[I|V|X\d]+\.\s*)?(?:THE\s+)?(?:ISSUES?|POINTS?\s+FOR\s+(?:CONSIDERATION|DETERMINATION)|(?:SUBSTANTIAL\s+)?QUESTIONS?\s+OF\s+LAW)\b"
    )),
    ("ANALYSIS", re.compile(
        r"(?im)^\s*(?:[I|V|X\d]+\.\s*)?(?:OUR\s+)?(?:ANALYSIS|DISCUSSION|CONSIDERATION|REASONING|FINDINGS|LEGAL\s+FRAMEWORK|DELIBERATIONS)\b"
    )),
    ("CONCLUSION", re.compile(
        r"(?im)^\s*(?:[I|V|X\d]+\.\s*)?(?:O\s*R\s*D\s*E\s*R|ORDER|HELD|CONCLUSIONS?|RATIO\s+DECIDENDI|FINAL\s+ORDER|OPERATIVE\s+PART|RESULT|DISPOSAL)\b"
    )),
]

# --------------------------------------------------------------------------
# 2. In-line Formulaic Triggers (Used when explicit headers are absent)
# --------------------------------------------------------------------------
INLINE_TRIGGERS = [
    ("FACTS", re.compile(
        r"(?i)(?:brief\s+facts\s+(?:which\s+are\s+necessary|leading|giving\s+rise)|the\s+factual\s+matrix\s+leading|the\s+prosecution\s+case\s+is\s+that|the\s+dispute\s+arises\s+out\s+of)\b"
    )),
    ("SUBMISSIONS", re.compile(
        r"(?i)(?:learned\s+(?:senior\s+)?counsel\s+(?:appearing\s+for|for)\s+the\s+(?:appellant|petitioner|respondent)\s+(?:contended|submitted|argued)|per\s+contra,\s+learned\s+counsel)\b"
    )),
    ("ANALYSIS", re.compile(
        r"(?i)(?:we\s+have\s+carefully\s+considered\s+the\s+submissions|having\s+heard\s+learned\s+counsel|in\s+order\s+to\s+appreciate\s+the\s+controversy|it\s+is\s+a\s+well-settled\s+principle\s+of\s+law)\b"
    )),
    ("CONCLUSION", re.compile(
        r"(?i)(?:for\s+the\s+reasons\s+stated\s+above,\s+the\s+appeal|in\s+view\s+of\s+the\s+(?:foregoing|above)\s+discussion|the\s+impugned\s+judgment.*?is\s+accordingly\s+set\s+aside|resultantly,\s+the\s+appeals?\s+(?:fail|are\s+dismissed|succeeds?))\b"
    )),
]

def segment_judgment_text(text: str) -> dict:
    """
    Partitions raw judgment text into rhetorical zones:
    facts, submissions, issues, analysis, conclusion.
    Falls back gracefully to full_text if boundaries are ambiguous.
    """
    if not isinstance(text, str) or not text.strip():
        return {
            "facts": "",
            "submissions": "",
            "issues": "",
            "analysis": "",
            "conclusion": "",
            "full_text": ""
        }

    # Step 1: Collect boundary candidate positions
    boundaries = []

    # Priority A: Check explicit headers
    for zone_name, pat in ZONE_HEADER_PATTERNS:
        for m in pat.finditer(text):
            boundaries.append((m.start(), zone_name, "explicit"))

    # Priority B: Check inline formulaic triggers if fewer than 2 explicit headers found
    if len(boundaries) < 2:
        for zone_name, pat in INLINE_TRIGGERS:
            for m in pat.finditer(text):
                # Avoid duplicate boundaries near already found markers
                if not any(abs(m.start() - b[0]) < 200 for b in boundaries):
                    boundaries.append((m.start(), zone_name, "inline"))

    # Sort boundaries chronologically
    boundaries.sort(key=lambda x: x[0])

    # If no structural zones detected, assign entire content to facts and fallback
    if not boundaries:
        # Heuristic split for unstructured judgment: first 40% facts, next 45% analysis, final 15% conclusion
        total_len = len(text)
        p1 = int(total_len * 0.40)
        p2 = int(total_len * 0.85)
        return {
            "facts": text[:p1].strip(),
            "submissions": "",
            "issues": "",
            "analysis": text[p1:p2].strip(),
            "conclusion": text[p2:].strip(),
            "full_text": text.strip()
        }

    # Step 2: Slice text into zones based on detected boundaries
    zones = {
        "facts": [],
        "submissions": [],
        "issues": [],
        "analysis": [],
        "conclusion": []
    }

    # Text before the first boundary is typically Preamble or Early Facts
    if boundaries[0][0] > 0:
        zones["facts"].append(text[:boundaries[0][0]])

    for i in range(len(boundaries)):
        start_idx, zone_name, _ = boundaries[i]
        end_idx = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(text)
        slice_text = text[start_idx:end_idx].strip()
        
        target_key = zone_name.lower()
        if target_key in zones:
            zones[target_key].append(slice_text)

    # Consolidate slices
    return {
        "facts": "\n\n".join(zones["facts"]).strip(),
        "submissions": "\n\n".join(zones["submissions"]).strip(),
        "issues": "\n\n".join(zones["issues"]).strip(),
        "analysis": "\n\n".join(zones["analysis"]).strip(),
        "conclusion": "\n\n".join(zones["conclusion"]).strip(),
        "full_text": text.strip()
    }

def process_dataset(input_file: Path, output_jsonl: Path, output_csv: Path, sample_size: int = None):
    print("=" * 65)
    print("CiteJustice - Rhetorical Zone Extraction Pipeline")
    print(f"Source : {input_file}")
    print(f"Target JSONL: {output_jsonl}")
    print(f"Target CSV  : {output_csv}")
    print("=" * 65)

    if not input_file.exists():
        print(f"Error: Input file {input_file} does not exist.")
        sys.exit(1)

    print(f"Reading dataset: {input_file.name}...")
    rows = []
    with open(input_file, mode="r", encoding="utf-8", errors="replace") as f_in:
        reader = csv.DictReader(f_in)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        
        count = 0
        for row in reader:
            rows.append(row)
            count += 1
            if sample_size and count >= sample_size:
                break

    total_records = len(rows)
    print(f"Loaded {total_records:,} cases to process.\n")

    segmented_records = []
    cases_with_facts = 0
    cases_with_arguments = 0
    cases_with_conclusion = 0

    print("Segmenting judgments into rhetorical zones...")
    for idx, row in enumerate(rows, 1):
        src_text = (
            row.get("text_with_normalized_sections")
            or row.get("normalized_text")
            or row.get("cleaned_text")
            or row.get("text", "")
        )

        zones = segment_judgment_text(src_text)

        rec = {
            "id": row.get("id", str(idx)),
            "label": row.get("label", ""),
            "split": row.get("split", "train"),
            "citations_found": row.get("citations_found", "[]"),
            "statutory_sections": row.get("statutory_sections", "[]"),
            "facts": zones["facts"],
            "submissions": zones["submissions"],
            "issues": zones["issues"],
            "analysis": zones["analysis"],
            "conclusion": zones["conclusion"],
            "full_text": zones["full_text"],
        }
        segmented_records.append(rec)

        if zones["facts"]:
            cases_with_facts += 1
        if zones["submissions"]:
            cases_with_arguments += 1
        if zones["conclusion"]:
            cases_with_conclusion += 1

        if idx % 500 == 0 or idx == total_records:
            print(f"  Processed {idx:,} / {total_records:,} cases ({(idx/total_records)*100:.1f}%)...")

    # Save to JSON Lines (Preferred interface for GNN & LangChain prompt builders)
    with open(output_jsonl, mode="w", encoding="utf-8") as f_jsonl:
        for r in segmented_records:
            f_jsonl.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n[OK] Segmented JSONL saved to: {output_jsonl}")

    # Save preview CSV
    csv_fields = ["id", "label", "split", "facts_len", "arguments_len", "conclusion_len", "citations_found", "statutory_sections"]
    with open(output_csv, mode="w", encoding="utf-8", newline="") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=csv_fields)
        writer.writeheader()
        for r in segmented_records:
            writer.writerow({
                "id": r["id"],
                "label": r["label"],
                "split": r["split"],
                "facts_len": len(r["facts"]),
                "arguments_len": len(r["submissions"]),
                "conclusion_len": len(r["conclusion"]),
                "citations_found": r["citations_found"],
                "statutory_sections": r["statutory_sections"]
            })
    print(f"[OK] Inspection CSV saved to: {output_csv}")

    print("\n" + "-" * 40)
    print("Execution Summary:")
    print(f"  Cases processed              : {total_records:,}")
    print(f"  Cases with Facts segmented   : {cases_with_facts:,} ({(cases_with_facts/total_records)*100:.1f}%)")
    print(f"  Cases with Arguments found   : {cases_with_arguments:,} ({(cases_with_arguments/total_records)*100:.1f}%)")
    print(f"  Cases with Conclusion parsed : {cases_with_conclusion:,} ({(cases_with_conclusion/total_records)*100:.1f}%)")
    print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Segment judgments into Facts, Submissions, and Conclusion.")
    parser.add_argument("--dataset", choices=["single", "multi"], default="single",
                        help="Dataset to segment: 'single' (9,110 cases) or 'multi' (34,816 cases).")
    parser.add_argument("--sample", type=int, default=None,
                        help="Process only a sample of N cases for fast testing.")
    args = parser.parse_args()

    # Cascade inputs: prefer Task 4 (english) -> Task 3 (sections) -> Task 2 -> Task 1 -> raw
    t4_input = CLEAN_DIR / f"ildc_{args.dataset}_english_primary.csv"
    t3_input = CLEAN_DIR / f"ildc_{args.dataset}_sections_normalized.csv"
    t2_input = CLEAN_DIR / f"ildc_{args.dataset}_citations_normalized.csv"
    t1_input = CLEAN_DIR / f"ildc_{args.dataset}_noise_removed.csv"
    raw_input = RAW_DIR / ("ILDC_single.csv" if args.dataset == "single" else "ILDC_multi.csv")

    if t4_input.exists():
        input_path = t4_input
    elif t3_input.exists():
        input_path = t3_input
    elif t2_input.exists():
        input_path = t2_input
    elif t1_input.exists():
        input_path = t1_input
    else:
        input_path = raw_input

    output_base = f"ildc_{args.dataset}"
    if args.sample:
        output_base += f"_sample_{args.sample}"

    output_jsonl = CLEAN_DIR / f"{output_base}_segmented.jsonl"
    output_csv = CLEAN_DIR / f"{output_base}_segmented_summary.csv"

    process_dataset(input_path, output_jsonl, output_csv, sample_size=args.sample)

if __name__ == "__main__":
    main()
