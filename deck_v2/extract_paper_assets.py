"""Reproduce selected paper figures/listings without altering their contents.

Run from any directory: python deck_v2/extract_paper_assets.py
Coordinates are PDF points, measured from the upper-left corner. PNGs use
5 pixels/point (360 dpi); both diagram-only and captioned figure crops are saved.
"""
from pathlib import Path
import hashlib
import json

import fitz

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent / "hpca26dsassassin.pdf"
OUT = HERE / "paper_assets"
SCALE = 5

FIGURES = [
    (1, 3, (70, 48, 538, 199), (49, 48, 563, 228),
     "Overview of DSA and ATS architecture",
     "Fig. 1. Overview of DSA and ATS architecture. ⋆Note that DSA accesses memory by sending a memory request to the root complex on the PCIe bus. The leftmost block is partially based on the die shot of Sapphire Rapids [48]."),
    (2, 4, (71, 47, 277, 156), (71, 47, 277, 174),
     "Revealed detail of DSA implementation",
     "Fig. 2. Revealed detail of DSA implementation."),
    (3, 4, (320, 136, 550, 241), (312, 136, 563, 271),
     "DSA Descriptor format",
     "Fig. 3. DSA Descriptor format. Note that the descriptor is tagged with PASID to prevent other processes from executing it directly."),
    (5, 6, (345, 47, 527, 181), (312, 47, 563, 211),
     "Three experiments distinguishing DevTLB indexing and cross-VM feasibility",
     "Fig. 5. Three experiments to distinguish the indexing policy of DevTLB and to identify the feasibility of a cross-VM attacker."),
    (7, 8, (333, 48, 538, 140), (312, 48, 563, 170),
     "Setup of cross-VM attacks on DSA",
     "Fig. 7. Setup of cross-VM attacks on DSA. The red line represents DSA_DevTLB attack flow, and the teal line shows DSA_SWQ attack flow."),
    (8, 8, (335, 179, 538, 251), (335, 179, 538, 271),
     "VPP memif architecture with attack scenario",
     "Fig. 8. VPP memif architecture with attack scenario."),
]

LISTINGS = [
    {
        "number": 1, "page": 4, "crop_points": [312, 578, 553, 699],
        "caption_crop_points": [312, 578, 553, 719],
        "caption": "Listing 1. Microbenchmark primitive for probing DevTLB.",
        "code": "uint64_t probe_memcmp(void* src, void* src2) {\n    uint64_t start, end;\n    struct dsa_hw_desc desc = {};\n    desc.opcode = DSA_OPCODE_COMPVAL;\n    desc.src_addr = src;\n    desc.src2_addr = src2;\n    enqcmd(wq_portal, &desc);\n    // time polling for completion\n    start = rdtsc();\n    while (comp.status == 0);\n    end = rdtsc();\n    return end - start;\n}",
        "notes": [
            "The paper prints DSA_OPCODE_COMPVAL while naming this probe_memcmp and supplying src and src2. Preserve that spelling when reproducing the paper; the two-source description and printed opcode are inconsistent.",
            "Section IV-B explicitly omits flag settings and address alignment, including Request Completion Record bits. Completion-record initialization/linkage and portal setup are not supplied by this listing. This is not a standalone runnable program.",
            "The timer starts after enqcmd returns. The measured quantity is completion polling latency, not ENQCMD admission latency."
        ],
        "timing_excerpt": {
            "original_lines": [7, 12], "crop_points": [312, 633.8, 497, 688],
            "code": "enqcmd(wq_portal, &desc);\n// time polling for completion\nstart = rdtsc();\nwhile (comp.status == 0);\nend = rdtsc();\nreturn end - start;"
        }
    },
    {
        "number": 2, "page": 5, "crop_points": [49, 44, 286, 76],
        "caption_crop_points": [49, 44, 286, 96],
        "caption": "Listing 2. Attempt to evict a DevTLB entry.",
        "code": "probe_noop(base); // base is 4KB aligned\nprobe_noop(base + OFFSET); // try evicting\nprobe_noop(base); // probe if base is present",
        "notes": ["The helper probe_noop is defined by analogy in the paper; setup is omitted. base is the completion-record address for noop, not a payload source address."]
    },
    {
        "number": 3, "page": 5, "crop_points": [312, 44, 549, 94],
        "caption_crop_points": [312, 44, 549, 114],
        "caption": "Listing 3. The memcpy example to discover additional entries.",
        "code": "// different page\nassert(PAGE_OF(src0) != PAGE_OF(dst0));\nprobe_memcpy(src0, dst0); // prime devtlb\n// src1 is on a different page with the src\nprobe_memcpy(src1, dst0);",
        "notes": ["Retains the original comment wording, including 'with the src'. PAGE_OF and the helper setup are omitted in the paper."]
    },
    {
        "number": 4, "page": 5, "crop_points": [312, 120, 546, 160],
        "caption_crop_points": [312, 120, 546, 181],
        "caption": "Listing 4. Overlapping fields with different types of operation.",
        "code": "// src2 overlaps dst\nprobe_memcmp(src, src2);\n// dst and src2 in same page\nprobe_memcpy(src, dst);",
        "notes": ["The src2 and dst addresses share a page and an encoding field but occupy independent DevTLB field slots."]
    },
    {
        "number": 5, "page": 6, "crop_points": [49, 44, 300, 94],
        "caption_crop_points": [49, 44, 300, 123],
        "caption": "Listing 5. Microbenchmark for determining the adjudication strategy of the in-engine arbiter. Two positions (Line 1 and Line 3) are swapped for comparison.",
        "code": "enqcmd(wq_portal, &batch_desc);// (1)\n_mm_sfence();\nenqcmd(wq_portal, &desc); start = rdtsc();// (2)\nwhile (desc_comp.status == 0);\nlatency = rdtsc() - start;",
        "notes": ["The paper compares swapping lines 1 and 3. Its observation is that the work descriptor has priority over batch-buffer descriptors; this listing is an experiment, not the congestion primitive."]
    },
    {
        "number": 6, "page": 7, "crop_points": [312, 44, 563, 130],
        "caption_crop_points": [312, 44, 563, 159],
        "caption": "Listing 6. Primitives of congest and probe in the attack on SWQ. The preparation of the descriptors is omitted.",
        "code": "struct dsa_hw_desc desc_buf[] = {...};\n\nvoid congest(int wq_size) {\n    enqcmd(wq_portal, &mass_desc);\n    for(int i = 1; i < wq_size - 1; i++)\n        enqcmd(wq_portal, &desc_buf[i]);\n}\n\nint probe() { return enqcmd(wq_portal, &desc); }",
        "notes": ["The paper explicitly omits descriptor preparation. The loop submits wq_size-2 lightweight descriptors after one long memcpy, aiming for wq_size-1 total queued descriptors.", "The enqcmd helper result indicates admission/retry; it does not indicate work completion. During the experiment, the idle interval must be shorter than the long copy's execution time."]
    },
]


def crop(doc, page, rect, name):
    pix = doc[page - 1].get_pixmap(matrix=fitz.Matrix(SCALE, SCALE),
                                 clip=fitz.Rect(rect), alpha=False)
    pix.save(str(OUT / name))
    return {"file": name, "crop_points": list(rect),
            "width_px": pix.width, "height_px": pix.height}


def main():
    OUT.mkdir(exist_ok=True)
    doc = fitz.open(PAPER)
    provenance = {
        "source_pdf": "hpca26dsassassin.pdf",
        "source_sha256": hashlib.sha256(PAPER.read_bytes()).hexdigest(),
        "paper_title": "DSASSASSIN: Cross-VM Side-Channel Attacks by Exploiting Intel Data Streaming Accelerator",
        "conference": "HPCA 2026", "pdf_page_numbering": "1-based",
        "coordinate_system": "PDF points from upper-left; 72 points per inch",
        "render_scale": SCALE, "render_dpi": 72 * SCALE,
        "modifications": "Only rectangular cropping and rasterization; original figure contents, colors, and labels retained. Captions supplied separately."
    }
    figures = []
    for number, page, rect, caption_rect, title, caption in FIGURES:
        figures.append({
            "number": number, "page": page, "title": title,
            "caption": caption,
            "diagram": crop(doc, page, rect, f"paper_fig{number}.png"),
            "with_caption": crop(doc, page, caption_rect, f"paper_fig{number}_captioned.png")
        })
    for listing in LISTINGS:
        n = listing["number"]
        listing["image"] = crop(doc, listing["page"], listing["crop_points"], f"paper_listing{n}.png")
        listing["image_with_caption"] = crop(doc, listing["page"], listing["caption_crop_points"], f"paper_listing{n}_captioned.png")
        listing["line_count"] = len(listing["code"].split("\n"))
        listing["code_with_line_numbers"] = "\n".join(
            f"{i:2d}  {line}" for i, line in enumerate(listing["code"].split("\n"), 1))
        if "timing_excerpt" in listing:
            excerpt = listing["timing_excerpt"]
            excerpt["image"] = crop(doc, listing["page"], excerpt["crop_points"], "paper_listing1_timing.png")
    (OUT / "figure_manifest.json").write_text(json.dumps({**provenance, "figures": figures}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "code_listings.json").write_text(json.dumps({
        **provenance,
        "transcription": "Original lexical spelling retained. Indentation reconstructed from PDF layout; PDF image crops are included as the visual source of truth. Line numbers are metadata, not executable code. These paper excerpts omit setup and are not standalone programs.",
        "listings": LISTINGS
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(figures)} figures and {len(LISTINGS)} code listings to {OUT}")


if __name__ == "__main__":
    main()
