# NyayaAnumana & INLegalLlama Resource Guide

**Project:** LexGraphFormer / CiteJustice  
**Dataset Scale:** 702,945 Indian Judgments  
**Source Organization:** `L-NLProc` (Lead: Dr. Shubham Kumar Nigam, IIT Kanpur / Univ. of Birmingham)  
**Access Confirmed:** Granted for academic research (September 2026)  

---

## 1. Overview of Resources

Dr. Shubham Kumar Nigam (lead author) has confirmed open access to the complete **NyayaAnumana** corpus and the specialized **INLegalLlama** models:

| Resource | Link | Description | Role in LexGraphFormer |
| :--- | :--- | :--- | :--- |
| **Dataset Collection** | [Hugging Face Dataset](https://huggingface.co/collections/L-NLProc/nyayaanumana-and-inlegalllama-dataset) | 702,945 judgments across Supreme Court, High Courts, Tribunals, and District Courts. | **Primary Training Corpus** for large-scale judgment prediction & citation graph expansion. |
| **Models Collection** | [Hugging Face Models](https://huggingface.co/collections/L-NLProc/nyayaanumana-and-inlegalllama-models) | Domain-specific LLMs continually pretrained on Indian legal text and instruction-tuned. | **Base Model / Encoder** for the model team (eliminates need to pretrain from generic LLaMA). |
| **GitHub Repository** | [GitHub Repo](https://github.com/ShubhamKumarNigam/NyayaAnumana-and-INLegalLlama) | Codebase, evaluation scripts, and baselines. | Benchmark reference & prompt templates. |
| **Explanation Data** | `NyayaAnumana-Explanation-Data` | Annotations for decision explainability and rationale extraction. | Ground truth for evaluating DPEG explanation sub-graphs. |

---

## 2. Dataset Composition (702K Cases)

NyayaAnumana is the largest publicly available Indian legal judgment dataset:
1. **Supreme Court Judgments:** Comprehensive historical SC decisions.
2. **High Court Judgments:** Decisions across major High Courts (Delhi, Bombay, Calcutta, Madras, Allahabad, etc.).
3. **Tribunals & Special Courts:** NCLT, NGT, ITAT, and Consumer Forums.
4. **District Courts / Daily Orders:** Lower court procedural history and outcomes.

---

## 3. Immediate Action Plan for Team

### For Madhav & Sai (Data Engineering & Legal Research)
1. **Citation Compliance:** Ensure `references.bib` is included in all reports, presentations, and paper drafts citing Dr. Nigam's paper.
2. **Sub-sampling & Inspection:** Use `scripts/download_nyayaanumana.py` to inspect metadata schema and verify court distributions.
3. **Temporal Graph Alignment:** Cross-reference NyayaAnumana SC cases with our DPEG citation graph to enrich node features with metadata (bench size, court, decision date).

### For Teammates (Model & Architecture Team)
1. **Adopt INLegalLlama as Backbone:** Share the [Models Collection](https://huggingface.co/collections/L-NLProc/nyayaanumana-and-inlegalllama-models) with the model team. INLegalLlama has already mastered Indian legal vocabulary (e.g., *quash, impugned, per incuriam, ratio decidendi*), providing a substantially stronger starting point than standard LLaMA-3 or Mistral.
2. **Graph-LLM Fusion:** Model team can combine INLegalLlama's textual representations with LexGraphFormer's GNN/Graph Transformer node embeddings generated from DPEG.

---

## 4. Citation Requirements
As requested by Dr. Nigam, include the following citation in any publication or report:

```bibtex
@article{nigam2024nyayaanumana,
  title={NyayaAnumana \& INLegalLlama: The Largest Indian Legal Judgment Prediction Dataset and Specialized Language Model for Enhanced Decision Analysis},
  author={Nigam, Shubham Kumar and others},
  journal={arXiv preprint},
  year={2024},
  url={https://huggingface.co/collections/L-NLProc/nyayaanumana-and-inlegalllama-dataset}
}
```
