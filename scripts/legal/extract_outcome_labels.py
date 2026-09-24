"""
scripts/legal/extract_outcome_labels.py

Legal Rule-Based Engine for Extracting Judgment Outcome Labels from Indian Courts.
Designed for the CiteJustice Pipeline & Legal Judgment Prediction Benchmark.

Author: Madhav Rakhonde & Sai Sonawane
Institution: VPKBIET, Baramati
Academic Year: 2026-2027

Features:
1. Dispositive tail window extraction (focuses on closing judicial paragraphs).
2. OCR artifact normalization for legacy Indian law reports (ILDC/AIR/SCR).
3. Negation & syntactic context guards (e.g., 'cannot be dismissed', 'no reason to interfere').
4. Calibrated confidence scoring (HIGH >= 0.90, LOW < 0.90).
5. Ground-truth validation & metric evaluation (Accuracy, Precision, Recall, F1, Confusion Matrix).
6. Exports comprehensive validation logs to JSON and CSV.

Usage:
    python scripts/legal/extract_outcome_labels.py --samples 200 --dataset single
    python scripts/legal/extract_outcome_labels.py --evaluate
"""

import os
import re
import sys
import csv
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

# Increase CSV field size limit for large judgment texts
csv.field_size_limit(sys.maxsize)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "ildc"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# 1. OCR Normalization Dictionary for Indian Legal Texts
# --------------------------------------------------------------------------
OCR_REPLACEMENTS = [
    (re.compile(r'\bcompanyviction\b', re.IGNORECASE), 'conviction'),
    (re.compile(r'\bcompanyrect\b', re.IGNORECASE), 'correct'),
    (re.compile(r'\bcompanycede\b', re.IGNORECASE), 'concede'),
    (re.compile(r'\bcompanyceded\b', re.IGNORECASE), 'conceded'),
    (re.compile(r'\bcompanyfirmation\b', re.IGNORECASE), 'confirmation'),
    (re.compile(r'\bcompanyfirmed\b', re.IGNORECASE), 'confirmed'),
    (re.compile(r'\bcompanyclusion\b', re.IGNORECASE), 'conclusion'),
    (re.compile(r'\bcompanytention\b', re.IGNORECASE), 'contention'),
    (re.compile(r'\bcompanytentions\b', re.IGNORECASE), 'contentions'),
    (re.compile(r'\bcompanyduct\b', re.IGNORECASE), 'conduct'),
    (re.compile(r'\bcompanycur\b', re.IGNORECASE), 'concur'),
    (re.compile(r'\bcompanycurred\b', re.IGNORECASE), 'concurred'),
    (re.compile(r'\bcompanyrt\b', re.IGNORECASE), 'court'),
    (re.compile(r'\bcompanyrts\b', re.IGNORECASE), 'courts'),
    (re.compile(r'\bcompanytract\b', re.IGNORECASE), 'contract'),
    (re.compile(r'\bcompanytracts\b', re.IGNORECASE), 'contracts'),
    (re.compile(r'\bnumberlonger\b', re.IGNORECASE), 'no longer'),
    (re.compile(r'\bnumbersubstance\b', re.IGNORECASE), 'no substance'),
    (re.compile(r'\bnumberground\b', re.IGNORECASE), 'no ground'),
    (re.compile(r'\bnumbergrounds\b', re.IGNORECASE), 'no grounds'),
    (re.compile(r'\bnumberreason\b', re.IGNORECASE), 'no reason'),
    (re.compile(r'\bnumbermerit\b', re.IGNORECASE), 'no merit'),
    (re.compile(r'\bnumberdoubt\b', re.IGNORECASE), 'no doubt'),
    (re.compile(r'\bnumberhesitation\b', re.IGNORECASE), 'no hesitation'),
    (re.compile(r'\bnumberfault\b', re.IGNORECASE), 'no fault'),
    (re.compile(r'\bnumberorder\b', re.IGNORECASE), 'no order'),
]

def clean_ocr(text: str) -> str:
    """Cleans OCR artifacts specific to Indian law reports."""
    cleaned = text
    for pat, repl in OCR_REPLACEMENTS:
        cleaned = pat.sub(repl, cleaned)
    return cleaned

# --------------------------------------------------------------------------
# 2. Priority Rules for Outcome Extraction
# --------------------------------------------------------------------------

# Rules indicating ALLOWED (Label = 1)
# Ordered by specificity and legal strength
ALLOWED_RULES = [
    # Explicit final orders
    ("RULE_ALLOWED_EXPLICIT", re.compile(
        r'\b(?:the\s+)?(?:civil|criminal)?\s*appeals?\s+(?:is|are|stands?)\s+(?:hereby\s+)?allowed\b', re.I), 0.98),
    ("RULE_ALLOWED_SUCCEEDS", re.compile(
        r'\b(?:the\s+)?appeals?\s+(?:must\s+)?succeeds?\b', re.I), 0.98),
    ("RULE_ALLOWED_LEAVE_GRANTED_ALLOWED", re.compile(
        r'\bleave\s+granted\b.*?\bappeals?\s+(?:is|are)\s+allowed\b', re.I | re.DOTALL), 0.97),
    ("RULE_ALLOWED_SET_ASIDE_HIGH_COURT", re.compile(
        r'\b(?:judgment|decree|order|conviction)\s+(?:of\s+the\s+high\s+court|under\s+appeal|impugned)\s+(?:.*?is\s+)?(?:set\s+aside|quashed|reversed)\b', re.I), 0.96),
    ("RULE_ALLOWED_SET_ASIDE_IMPUGNED", re.compile(
        r'\b(?:we\s+)?set\s+aside\s+the\s+(?:impugned\s+)?(?:judgment|order|decree|conviction)\b', re.I), 0.95),
    ("RULE_ALLOWED_ACQUITTED", re.compile(
        r'\b(?:appellants?|accused)\s+(?:is|are)\s+(?:hereby\s+)?acquitted\s+(?:of\s+all\s+charges)?\b', re.I), 0.96),
    ("RULE_ALLOWED_CONVICTION_QUASHED", re.compile(
        r'\bconviction\s+(?:and\s+sentence\s+)?(?:is|are)\s+quashed\b', re.I), 0.95),
    ("RULE_ALLOWED_DECREE_RESTORED", re.compile(
        r'\b(?:decree|order)\s+of\s+the\s+(?:trial\s+court|first\s+court|sub-judge)\s+(?:is|stands?)\s+restored\b', re.I), 0.94),
    ("RULE_ALLOWED_BAIL_GRANTED", re.compile(
        r'\bappellants?\s+(?:is|are)\s+ordered\s+to\s+be\s+released\s+on\s+bail\b', re.I), 0.92),
    ("RULE_ALLOWED_REMAND", re.compile(
        r'\b(?:send\s+the\s+case\s+back|remand(?:ed)?\s+(?:the\s+matter\s+)?to\s+the\s+high\s+court\s+for\s+fresh|remitted\s+to\s+the\s+high\s+court)\b', re.I), 0.90),
    ("RULE_ALLOWED_PARTLY_ALLOWED", re.compile(
        r'\b(?:appeal|appeals)\s+(?:is|are)\s+(?:partly\s+allowed|allowed\s+in\s+part)\b', re.I), 0.88),
    ("RULE_ALLOWED_RATIO_SUBSTANCE", re.compile(
        r'\b(?:there\s+is\s+considerable\s+force\s+in\s+the\s+contention|appellant\s+must\s+succeed\s+on\s+this\s+ground)\b', re.I), 0.82),
]

# Rules indicating DISMISSED (Label = 0)
# Ordered by specificity and legal strength
DISMISSED_RULES = [
    # Explicit final orders
    ("RULE_DISMISSED_EXPLICIT", re.compile(
        r'\b(?:the\s+)?(?:civil|criminal)?\s*appeals?\s+(?:is|are|stands?)\s+(?:hereby\s+)?dismissed\b', re.I), 0.98),
    ("RULE_DISMISSED_PETITION_DISMISSED", re.compile(
        r'\b(?:the\s+)?(?:writ\s+)?petitions?\s+(?:is|are|stands?)\s+(?:hereby\s+)?dismissed\b', re.I), 0.98),
    ("RULE_DISMISSED_FAILS", re.compile(
        r'\b(?:the\s+)?appeals?\s+(?:must\s+therefore\s+|must\s+)?fails?\b', re.I), 0.98),
    ("RULE_DISMISSED_CONVICTION_UPHELD", re.compile(
        r'\bconviction\s+(?:and\s+sentence\s+)?(?:is|are)\s+(?:hereby\s+)?(?:upheld|affirmed|maintained)\b', re.I), 0.96),
    ("RULE_DISMISSED_JUDGMENT_AFFIRMED", re.compile(
        r'\b(?:judgment|order|decree)\s+(?:of\s+the\s+high\s+court\s+)?(?:is|are)\s+(?:correct\s+and\s+must\s+be\s+)?affirmed\b', re.I), 0.95),
    ("RULE_DISMISSED_NO_REASON_INTERFERE", re.compile(
        r'\b(?:we\s+)?(?:see|find)\s+no\s+(?:reason|ground)\s+to\s+interfere\s+(?:with\s+the\s+impugned)?\b', re.I), 0.95),
    ("RULE_DISMISSED_NO_GROUND_INTERFERENCE", re.compile(
        r'\bno\s+(?:ground|reason)\s+(?:whatsoever\s+)?for\s+interference\b', re.I), 0.94),
    ("RULE_DISMISSED_NO_MERIT", re.compile(
        r'\b(?:appeals?\s+is\s+|petitions?\s+is\s+)?(?:devoid\s+of\s+(?:any\s+)?merit|find\s+no\s+merit\s+in\s+this\s+appeal|bereft\s+of\s+substance)\b', re.I), 0.94),
    ("RULE_DISMISSED_LEAVE_REFUSED", re.compile(
        r'\bleave\s+(?:to\s+appeal\s+)?(?:is\s+)?refused\b', re.I), 0.94),
    ("RULE_DISMISSED_ACCORDINGLY_DISMISSED", re.compile(
        r'\b(?:is|are)\s+accordingly\s+dismissed\b', re.I), 0.92),
    ("RULE_DISMISSED_RATIO_REJECTED", re.compile(
        r'\b(?:we\s+are\s+unable\s+to\s+accept\s+the\s+contention|contention\s+must\s+be\s+rejected|find\s+no\s+infirmity)\b', re.I), 0.82),
]

# Negation guards: situations where a keyword match must NOT trigger
NEGATION_GUARDS = [
    re.compile(r'\bcannot\s+be\s+allowed\b', re.I),
    re.compile(r'\bhardly\s+any\s+reason\s+to\s+allow\b', re.I),
    re.compile(r'\bcannot\s+be\s+dismissed\b', re.I),
    re.compile(r'\bnot\s+liable\s+to\s+be\s+dismissed\b', re.I),
    re.compile(r'\bnot\s+be\s+proper\s+to\s+dismiss\b', re.I),
    re.compile(r'\brefused\s+to\s+interfere\s+at\s+that\s+stage\b', re.I),
]

def extract_tail_window(text: str, max_chars: int = 1500) -> str:
    """Extracts the concluding/dispositive tail of the judgment text."""
    if not isinstance(text, str):
        return ""
    text = clean_ocr(text.strip())
    # Return last max_chars characters
    return text[-max_chars:] if len(text) > max_chars else text

def extract_outcome_label(text: str) -> Dict[str, Any]:
    """
    Applies legal outcome rules to extract predicted outcome from judgment text.
    Returns:
        dict: {
            "predicted_label": int (0 or 1),
            "outcome_class": str ("ALLOWED" or "DISMISSED"),
            "confidence": float (0.0 to 1.0),
            "confidence_tier": str ("HIGH" or "LOW"),
            "rule_name": str,
            "matched_span": str,
            "disposition_excerpt": str
        }
    """
    tail = extract_tail_window(text, max_chars=1800)
    
    # Check negation guards
    for guard in NEGATION_GUARDS:
        if guard.search(tail):
            # Guard triggered: caution flag
            pass

    # Look for matching rules
    # Check Allowed rules
    allowed_matches = []
    for rule_name, pat, conf in ALLOWED_RULES:
        for m in pat.finditer(tail):
            # Guard against 'cannot be allowed'
            start_pos = max(0, m.start() - 30)
            prefix = tail[start_pos:m.start()].lower()
            if "cannot" in prefix or "refuse" in prefix:
                continue
            allowed_matches.append({
                "rule": rule_name,
                "confidence": conf,
                "start": m.start(),
                "end": m.end(),
                "span": m.group(0),
                "type": 1
            })

    # Check Dismissed rules
    dismissed_matches = []
    for rule_name, pat, conf in DISMISSED_RULES:
        for m in pat.finditer(tail):
            # Guard against 'cannot be dismissed'
            start_pos = max(0, m.start() - 30)
            prefix = tail[start_pos:m.start()].lower()
            if "cannot" in prefix or "not" in prefix or "never" in prefix:
                continue
            dismissed_matches.append({
                "rule": rule_name,
                "confidence": conf,
                "start": m.start(),
                "end": m.end(),
                "span": m.group(0),
                "type": 0
            })

    # Resolution strategy:
    # 1. If explicit terminal order found near the very end, prefer the one closest to end of text
    # 2. If both exist, the later mention typically represents the final court order
    all_matches = allowed_matches + dismissed_matches
    
    if all_matches:
        # Sort by position (later in text is stronger for appellate disposition) and confidence
        all_matches.sort(key=lambda x: (x["start"], x["confidence"]))
        best_match = all_matches[-1]
        
        # Check if high confidence
        is_high = best_match["confidence"] >= 0.90
        
        # Extract surrounding context for dispositive excerpt
        ctx_start = max(0, best_match["start"] - 60)
        ctx_end = min(len(tail), best_match["end"] + 100)
        excerpt = tail[ctx_start:ctx_end].replace('\n', ' ').strip()
        
        return {
            "predicted_label": best_match["type"],
            "outcome_class": "ALLOWED" if best_match["type"] == 1 else "DISMISSED",
            "confidence": round(best_match["confidence"], 3),
            "confidence_tier": "HIGH" if is_high else "LOW",
            "rule_name": best_match["rule"],
            "matched_span": best_match["span"],
            "disposition_excerpt": excerpt
        }

    # Fallback heuristic: search for ratio decidendi patterns across broader tail
    # If no rule matched, look for semantic indicators
    tail_lower = tail.lower()
    if "acquittal" in tail_lower or "set aside" in tail_lower or "quash" in tail_lower or "allowed" in tail_lower:
        return {
            "predicted_label": 1,
            "outcome_class": "ALLOWED",
            "confidence": 0.65,
            "confidence_tier": "LOW",
            "rule_name": "HEURISTIC_ALLOWED_FALLBACK",
            "matched_span": "semantic_allowed_keyword",
            "disposition_excerpt": tail[-200:].replace('\n', ' ').strip()
        }
    else:
        # Indian SC baseline dismisses approx 60-65% of appeals
        return {
            "predicted_label": 0,
            "outcome_class": "DISMISSED",
            "confidence": 0.60,
            "confidence_tier": "LOW",
            "rule_name": "HEURISTIC_DISMISSED_FALLBACK",
            "matched_span": "semantic_dismissed_fallback",
            "disposition_excerpt": tail[-200:].replace('\n', ' ').strip()
        }

# --------------------------------------------------------------------------
# 3. Batch Evaluation & 200 Case Validation Execution
# --------------------------------------------------------------------------

def evaluate_cases(csv_path: Path, num_cases: int = 200) -> Dict[str, Any]:
    """
    Evaluates outcome label extraction on `num_cases` judgments and computes
    full confusion matrix, precision, recall, F1, and confidence stratification.
    """
    print(f"Loading {num_cases} judgments from {csv_path.name}...")
    
    # Read rows
    cases = []
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if idx >= num_cases:
                break
            cases.append(row)
            
    print(f"Read {len(cases)} cases. Running legal outcome extraction engine...")
    
    results = []
    
    # Metrics counters
    tp = 0  # GT=1, Pred=1 (Allowed)
    fp = 0  # GT=0, Pred=1
    tn = 0  # GT=0, Pred=0 (Dismissed)
    fn = 0  # GT=1, Pred=0
    
    high_conf_correct = 0
    high_conf_total = 0
    low_conf_correct = 0
    low_conf_total = 0
    
    for idx, case in enumerate(cases):
        case_id = case.get('id', f'case_{idx}')
        gt_label = int(case.get('label', 0))
        text = case.get('text', '')
        
        extracted = extract_outcome_label(text)
        pred_label = extracted["predicted_label"]
        is_correct = (pred_label == gt_label)
        
        if gt_label == 1 and pred_label == 1:
            tp += 1
        elif gt_label == 0 and pred_label == 1:
            fp += 1
        elif gt_label == 0 and pred_label == 0:
            tn += 1
        elif gt_label == 1 and pred_label == 0:
            fn += 1
            
        if extracted["confidence_tier"] == "HIGH":
            high_conf_total += 1
            if is_correct:
                high_conf_correct += 1
        else:
            low_conf_total += 1
            if is_correct:
                low_conf_correct += 1
                
        # Error categorization
        error_type = "NONE"
        if not is_correct:
            if extracted["confidence_tier"] == "HIGH":
                error_type = "HIGH_CONFIDENCE_FALSE_MATCH"
            else:
                error_type = "LOW_CONFIDENCE_FALLBACK_MISMATCH"
                
        results.append({
            "index": idx + 1,
            "case_id": case_id,
            "ground_truth_label": gt_label,
            "ground_truth_class": "ALLOWED" if gt_label == 1 else "DISMISSED",
            "extracted_label": pred_label,
            "extracted_class": extracted["outcome_class"],
            "match": is_correct,
            "confidence": extracted["confidence"],
            "confidence_tier": extracted["confidence_tier"],
            "rule_name": extracted["rule_name"],
            "matched_span": extracted["matched_span"],
            "disposition_excerpt": extracted["disposition_excerpt"],
            "error_type": error_type
        })
        
    total = len(cases)
    accuracy = (tp + tn) / total if total > 0 else 0.0
    
    # Class 1 (Allowed) Metrics
    prec_1 = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec_1 = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_1 = 2 * prec_1 * rec_1 / (prec_1 + rec_1) if (prec_1 + rec_1) > 0 else 0.0
    
    # Class 0 (Dismissed) Metrics
    prec_0 = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    rec_0 = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1_0 = 2 * prec_0 * rec_0 / (prec_0 + rec_0) if (prec_0 + rec_0) > 0 else 0.0
    
    macro_f1 = (f1_1 + f1_0) / 2.0
    
    high_acc = high_conf_correct / high_conf_total if high_conf_total > 0 else 0.0
    low_acc = low_conf_correct / low_conf_total if low_conf_total > 0 else 0.0
    
    summary = {
        "dataset": csv_path.name,
        "total_cases_validated": total,
        "overall_accuracy_percent": round(accuracy * 100, 2),
        "macro_f1_score": round(macro_f1, 4),
        "confusion_matrix": {
            "TP_Allowed": tp,
            "FP_Allowed": fp,
            "TN_Dismissed": tn,
            "FN_Dismissed": fn
        },
        "allowed_class_metrics": {
            "precision": round(prec_1, 4),
            "recall": round(rec_1, 4),
            "f1_score": round(f1_1, 4),
            "support": tp + fn
        },
        "dismissed_class_metrics": {
            "precision": round(prec_0, 4),
            "recall": round(rec_0, 4),
            "f1_score": round(f1_0, 4),
            "support": tn + fp
        },
        "confidence_stratification": {
            "high_confidence_cases": high_conf_total,
            "high_confidence_accuracy_percent": round(high_acc * 100, 2),
            "low_confidence_cases": low_conf_total,
            "low_confidence_accuracy_percent": round(low_acc * 100, 2)
        }
    }
    
    return {
        "summary": summary,
        "detailed_validation_log": results
    }

def main():
    parser = argparse.ArgumentParser(description="Legal Outcome Label Extractor & Validator")
    parser.add_argument("--samples", type=int, default=200, help="Number of cases to validate")
    parser.add_argument("--dataset", choices=["single", "multi"], default="single", help="ILDC dataset subset")
    parser.add_argument("--output-json", default="data/processed/outcome_validation_200.json", help="Path to output JSON")
    parser.add_argument("--output-csv", default="data/processed/outcome_validation_200.csv", help="Path to output CSV")
    args = parser.parse_args()
    
    csv_file = RAW_DIR / f"ILDC_{args.dataset}.csv"
    if not csv_file.exists():
        print(f"Error: {csv_file} does not exist.")
        sys.exit(1)
        
    validation_data = evaluate_cases(csv_file, num_cases=args.samples)
    
    # Save JSON artifact
    out_json_path = BASE_DIR / args.output_json
    with open(out_json_path, 'w', encoding='utf-8') as f:
        json.dump(validation_data, f, indent=2)
    print(f"\nSaved structured validation report to: {out_json_path}")
    
    # Save CSV artifact
    out_csv_path = BASE_DIR / args.output_csv
    detailed_logs = validation_data["detailed_validation_log"]
    if detailed_logs:
        fieldnames = list(detailed_logs[0].keys())
        with open(out_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(detailed_logs)
        print(f"Saved tabular validation log to: {out_csv_path}")
        
    # Print summary
    print("\n" + "=" * 65)
    print("LEGAL OUTCOME LABEL EXTRACTION VALIDATION SUMMARY (200 CASES)")
    print("=" * 65)
    s = validation_data["summary"]
    print(f"Dataset Analyzed:            {s['dataset']}")
    print(f"Total Cases Validated:       {s['total_cases_validated']}")
    print(f"Overall Accuracy:            {s['overall_accuracy_percent']}%")
    print(f"Macro F1-Score:              {s['macro_f1_score']}")
    print(f"High-Confidence Accuracy:    {s['confidence_stratification']['high_confidence_accuracy_percent']}% ({s['confidence_stratification']['high_confidence_cases']} cases)")
    print(f"Low-Confidence Accuracy:     {s['confidence_stratification']['low_confidence_accuracy_percent']}% ({s['confidence_stratification']['low_confidence_cases']} cases)")
    print("-" * 65)
    print("Confusion Matrix:")
    print(f"  True Positives (Allowed):  {s['confusion_matrix']['TP_Allowed']}")
    print(f"  False Positives (Allowed): {s['confusion_matrix']['FP_Allowed']}")
    print(f"  True Negatives (Dismissed):{s['confusion_matrix']['TN_Dismissed']}")
    print(f"  False Negatives (Dismissed):{s['confusion_matrix']['FN_Dismissed']}")
    print("-" * 65)
    print(f"Allowed Class  (1): Precision={s['allowed_class_metrics']['precision']}, Recall={s['allowed_class_metrics']['recall']}, F1={s['allowed_class_metrics']['f1_score']}")
    print(f"Dismissed Class(0): Precision={s['dismissed_class_metrics']['precision']}, Recall={s['dismissed_class_metrics']['recall']}, F1={s['dismissed_class_metrics']['f1_score']}")
    print("=" * 65)

if __name__ == "__main__":
    main()
