# DSASSASSIN paper presentation

Presentation materials for **DSASSASSIN: Cross-VM Side-Channel Attacks by Exploiting Intel Data Streaming Accelerator**, by Ben Chen, Kunlin Li, Shuwen Deng, Dongsheng Wang, and Yun Chen (HPCA 2026).

**Presenters:** Siddharth Banakar and Dinesh Samala

**Presentation date:** 29 October 2026

The current v2 presentation contains **43 slides: 36 main slides and 7 appendix slides**, with speaker notes on every slide. It is intended for a 40–45 minute talk for architecture and security audiences. The main talk ends with one **Findings and limits** slide.

| File | Contents |
| --- | --- |
| [PowerPoint presentation](deck_v2/output/DSASSASSIN_v2.pptx) | Editable 43-slide deck with speaker notes. |
| [PDF preview](deck_v2/output/DSASSASSIN_v2.pdf) | PDF export of the same 43 slides. |
| [Slide plan](deck_v2/SLIDE_PLAN.md) | Slide-by-slide narrative, paper context, and transitions. |
| [Fact-check report and audience Q&A](deck_v2/FACTCHECK_AND_QA.md) | Claim verification, paper inconsistencies, corrections, and discussion questions. |
| [Slide manifest](deck_v2/output/slide_manifest.json) | Slide titles, section labels, source references, timings, and backup-slide flags. |
| [Figure provenance](deck_v2/paper_assets/figure_manifest.json) and [code listings](deck_v2/paper_assets/code_listings.json) | Source pages, crop metadata, and exact code text. |
| [Build script](deck_v2/build.py) | Regenerates the current deck from the included source and assets. |

Open the PowerPoint file in PowerPoint to present and access the speaker notes, or use the PDF for quick reading. The slide plan and fact-check report use the numbering of this v2 deck.

Six original paper diagrams and editable excerpts from all six code listings are included. Bottom footers show only page numbers; source citations remain in speaker notes and the accompanying documents.

The presentation covers Intel DSA, its DevTLB and shared work queues, the two attack primitives, cross-VM application case studies, and proposed mitigations. The keystroke result concerns event timing; the paper does not demonstrate recovery of typed characters. Consult the fact-check document for the scope of reported results and inconsistencies in the paper.

These are presentation materials about the cited research paper. Research findings and original figures are attributed to the paper's authors in the deck and accompanying documents.

## Rebuild

The build uses Windows with Segoe UI and Consolas fonts. Close the output deck in PowerPoint before rebuilding. From the repository root:

```powershell
python -m pip install python-pptx Pillow lxml
python deck_v2/build.py --no-com
```

This writes `deck_v2/output/DSASSASSIN_v2.pptx`. With Microsoft PowerPoint installed, run `python deck_v2/build.py` without `--no-com` to also export the PDF and slide images through [export.ps1](deck_v2/export.ps1).

The figure crops and chart assets required by the build are included in `deck_v2/paper_assets/` and `presentation_assets/`. Optional re-extraction with [extract_paper_assets.py](deck_v2/extract_paper_assets.py) requires PyMuPDF (`python -m pip install PyMuPDF`) and the original paper PDF saved as `hpca26dsassassin.pdf` at the repository root. The source PDF is not included; the recorded hash identifies the version used for these crops.
