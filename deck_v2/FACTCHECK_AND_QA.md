# DSASSASSIN deck — fact-check report & audience Q&A bank

This document does two things you asked for:
1. **Verification** — every quantitative claim and key technical statement in the deck cross-checked against the paper (`paper_reading.txt`, the full extracted text of the HPCA 2026 paper), with discrepancies fixed and important omissions noted.
2. **Student / audience question bank** — likely questions grouped by theme, each with a tight answer grounded in the paper.

---

## PART 1 — Verification against the paper

### A. Numbers that were checked and are CORRECT in the deck

| Claim in deck | Paper location | Status |
|---|---|---|
| Covert channel: DevTLB **17.19 kbps** | §I, §VI-A, Table IV | ✅ |
| DevTLB covert **bit error 4.63%** | §VI-A, Table IV | ✅ (but see note 1) |
| SWQ covert **4.02 kbps / 13.11%** | §VI-A, Table IV | ✅ |
| Website fingerprinting **85.73%** on 100 sites; **96.5%** on the 15-site subset; **1%** baseline | §VI-B | ✅ (correctly separated) |
| Keystroke **F1 92.0% (DevTLB) / 98.4% (SWQ)**; σ **5.29 ms / 1.21 ms** | §VI-C, Tables III–IV | ✅ |
| LLM fingerprinting **98.6%**, 8 models, 50 traces each, 8 ms slots | §VI-D, Table II | ✅ |
| DevTLB: **5 sub-entries** (src/src2/dst/dst2/comp), each **single slot**, direct-mapped (W=1,S=1), page granularity | §IV-B, Takeaway 1 | ✅ |
| Indexed by **engine ID then field**, **not PASID, not WQ** (E0/E1/E2) | §IV-B, Takeaway 2, Fig. 5 | ✅ |
| Hit ≈ **500 cycles**, miss **> 1000**, threshold **600–900**, ~**89-cycle** cloud shift | §IV-B, Fig. 4 | ✅ |
| Submission latency **constant (~700 cycles)**; SWQ channel via **DMWr / EFLAGS.ZF**, timer-free | §IV-C | ✅ |
| Arbiter **prefers work descriptors over batch** | §IV-A, §IV-C, Listing 5 | ✅ |
| Website sampling **10 µs × 400 = ~4 ms/slot**; **100 × 200 = 20,000 traces**, 80/20 | §VI-B | ✅ |
| Robustness table (local/noisy/cloud) values | §VI-E, Table III | ✅ |
| Mitigation overhead **15.7% (native DSA) / 17.9% (DTO)** at 256 B | §VII, Fig. 14 | ✅ |
| Platforms: Xeon 8468V local, 8475B Alibaba cloud, Linux 6.11, IDXD, VT-d scalable | §IV-B, §V-A | ✅ |
| PMU events EV_ATC_ALLOC / NO_ALLOC / HIT_PREV; attack uses only rdtsc / ZF | §IV-B, Table I | ✅ |
| Keystroke event counts: 512 GT; DevTLB 515 det / 15 FP / 61 FN / 500 TP; SWQ 511 / 7 FP / 9 FN / 507 TP | §VI-C | ✅ (quoted as-is in backup) |

### B. Discrepancies found and FIXED in this pass

1. **Comparison table was incomplete and slightly favourable (slide 42 / "Does it hold up?").**
   The earlier version showed only capacity / bit error / keystroke σ, which made DSASSASSIN look like it won everywhere. Table IV actually also reports **keystroke F1** and **website accuracy/F1** for the baselines, where the paper does **not** win every column:
   - **IPI keystroke F1 = 97.9%** *beats* DevTLB's 92.0% (only SWQ's 98.4% wins that column).
   - **DEVIOUS bit error = 2.18%** is *lower* (better) than DevTLB's 4.63%.
   - **DEVIOUS website accuracy = 98.9%** is *higher* than 85.7% (paper footnote: DEVIOUS traces include GPU fingerprints, and its IOTLB channel is since mitigated by PASID).
   - IPI website is reported as **F1 80.4%**, not a top-1 accuracy.
   → The slide now shows all these columns and a footnote, and the key line was changed from "≈4.98× capacity / ≈4.08× lower error" to the more defensible "**best on capacity (DevTLB) and keystroke timing (SWQ) — not on every axis**." (The ~5×/~4× multipliers are the paper's own abstract claim *against IPI specifically*, so they remain true as stated, just no longer the headline.)

2. **SWQ congestion threshold was missing (slide 25, "the trap").**
   The paper states contention via EFLAGS.ZF **only appeared when the transfer size reached ≥ 2²⁵ bytes (32 MiB)** (§IV-C). The deck now states the anchor copy must be large, with that number — important because it explains *why* a long memcpy is needed and bounds how "stealthy" the attack can be.

3. **Batch-fetcher wording tightened (slide 18).**
   Paper: the batch fetcher's *descriptor reads* and the *completion-record write* bypass DevTLB indexing. The deck now says "the batch fetcher's **own descriptor reads and completion-record writes**," matching §IV-B precisely (avoids implying that work executed *inside* a batch is invisible).

4. **Threat-model nuance added (slide 9).**
   §V-A contains an apparent tension: it says configuring engine-affinity/WQ settings requires root, then says setting affinity to a specific engine/queue does *not* require root. The deck speaker notes now flag this explicitly and give the sensible reading (creating/configuring queues via `accel-config` is privileged; binding to an existing portal is not). Kernel version 6.11.0-25 and the IDXD driver are now named.

5. **4.63% vs 4.64% inconsistency documented (backup "Reporting audit").**
   The paper's **abstract and contributions say 4.64%**; **§VI-A and Table IV say 4.63%.** The deck already used 4.63% (the results-section value); the backup audit slide now notes the discrepancy so you're not caught off guard.

6. **Co-location critique made precise (slide 48).**
   Paper §VI-C *does* describe an SWQ-discovery method for keystrokes (open a temporary SSH connection and probe candidate SWQs). The critique now credits that and narrows the valid complaint to: **engine binding is assumed, and large-scale co-location is not demonstrated** — rather than implying no discovery method exists at all.

### C. Important facts VERIFIED present (not missed)

- **Responsible disclosure to Intel PSIRT** — stated (acknowledged). ✅ in notes.
- **Negative control E2** (separate engines → no leak) — central, on the money-shot slide. ✅
- **Huge-page eviction** (a 2 MiB conflicting address evicts a 4 KiB entry; no per-page-size entries) — in slide 16 notes. ✅
- **Cross-page: only the final page's translation is cached** — slide 18. ✅
- **src2/dst share descriptor bytes (offset 24) but map to separate slots** — slide 17 + backup descriptor slide. ✅
- **VPP/memif on DPDK; DTO via runtime linker** as the two offload vectors — slides 31, 35, 38. ✅
- **Closed-world / fixed-prompt caveats; "timing not text"** — slides 32, 34, 35, 39, 48. ✅
- **Confidence intervals computed from 50 repetitions, geometric-mean baseline** — §VI-E; summarised on the robustness slide. ✅
- **Mitigation measures overhead but not residual leakage** — slide 45. ✅

### D. Minor things deliberately NOT changed (judgment calls)

- The **"footprint: light vs heavy / loud"** row on the weapons-comparison slide and the **detectability** critique are labelled *presenter interpretation* — they are reasonable inferences, not paper claims, and are flagged as such.
- The **~5× faster / ~4× more accurate** phrasing is retained only where attributed to the paper's own abstract (against IPI). It is not used as a general "beats everything" claim.

**Bottom line:** the core technical story (what DevTLB/SWQ are, how they were reverse-engineered, the two primitives, the four attacks, the engine-vs-queue result) matches the paper exactly. The only substantive correction was the **comparison table**, which previously under-reported the columns where baselines win; that is now shown honestly.

---

## PART 2 — Audience / student question bank

Grouped by theme. Each answer is short enough to say aloud and is grounded in the paper (section noted where useful).

### 1 — Threat model & realism (the questions you'll get most)

**Q: Isn't the real assumption here that the attacker is already co-located on the victim's engine? How realistic is that?**
Yes — that is the crux and the biggest limitation. The attack needs the attacker and victim to share a DSA *engine* (DevTLB channel) or a *work queue* (SWQ channel). Binding to a given engine/queue doesn't need root, but *ending up* on the victim's engine in a real multi-tenant cloud is a scheduling/provisioning question the paper doesn't fully solve. For SSH they show a discovery trick (probe candidate SWQs during a throwaway connection, §VI-C); engine co-location for the other attacks is assumed.

**Q: What privilege does the attacker actually need?**
`CAP_SYS_RAWIO` to submit descriptors, plus access to a DSA portal. No root, no ability to reconfigure the host DSA, no shared memory, no shared CPU core (§V-A).

**Q: Do the attacks need the privileged PMU counters?**
No. PMU/Perfmon (EV_ATC_*) is used only to *reverse-engineer and explain* the hardware. The live attacks read only `rdtsc` (DevTLB) or the `EFLAGS.ZF` flag after `ENQCMD` (SWQ) — both unprivileged (§IV-B, Table I).

**Q: Does the victim have to be using DSA?**
Yes. The victim must actually offload work to DSA — via DPDK/VPP (networking) or DTO (transparent memcpy offload). No DSA usage, no signal.

### 2 — Mechanism (DevTLB)

**Q: How is the DevTLB indexed, and why does that break isolation?**
By **engine ID, then descriptor field role** (src/src2/dst/dst2/comp) — *not* by virtual address and *not* by PASID. Each engine has five one-entry slots. So two VMs on the same engine share the same five slots, and either can evict the other's translation regardless of PASID (§IV-B, Takeaways 1–2).

**Q: You claim exactly one slot per field — how do you know it isn't, say, 2-way?**
The base→offset→base test (Listing 2): load `base`, touch a different page, re-check `base`. A within-page offset still hits; a cross-page offset always misses. If the slot held two entries, `base` would survive one conflicting access — it never does.

**Q: Why use a `noop` descriptor for probing?**
It touches only the completion-record slot, has minimal execution cost, and gives the cleanest hit/miss latency separation. The attacker primes its *own* completion-record page, so it never needs any victim address (§V-B).

**Q: Separate work queues should isolate tenants — why don't they?**
Because the DevTLB belongs to the *engine*, which sits *below* the queues. Experiment E1 (different queues, same engine) still shows cross-VM eviction. Only E2 (different engines) stops it. This is the single most important deployment takeaway.

**Q: Can the attacker learn *which address* the victim touched?**
No. The signal is binary presence/absence of activity on the engine ("someone evicted my slot"). It reveals *activity*, not addresses or data. All the application attacks are pattern-classification on top of that binary trace.

### 3 — Mechanism (SWQ)

**Q: If submission time is constant, where's the timing channel?**
There isn't one — that's the point. The leak is the *success/failure* of submission: a Deferrable Memory Write sets `EFLAGS.ZF` when the queue is full. It's a yes/no flag, not a duration (§IV-C). Timer-free.

**Q: Why does the congestion need a huge (32 MiB) copy?**
Contention through ZF only became observable at transfer sizes ≥ 2²⁵ bytes; a smaller anchor drains too fast to hold the queue near-full during the observation window (§IV-C).

**Q: Why can't the attacker just use a batch descriptor to congest?**
The in-engine arbiter de-prioritizes batch descriptors relative to work descriptors (they verified this by swapping submission order, Listing 5). So batch work is unreliable for holding the queue; a long ordinary `memcpy` is used instead.

### 4 — The attacks / evaluation

**Q: Is the 85.73% website result closed-world or open-world?**
Closed-world: 100 *known* sites, train and test drawn from the same set, 80/20 split. It is not open-world detection of arbitrary pages. (And 96.5% is only the 15-site subset shown in the confusion matrix — not the headline.)

**Q: Did they actually recover typed text / passwords?**
No. They recover keystroke *timing* (event detection + timestamps). They note timing could feed a downstream text-inference model, but end-to-end text recovery is not evaluated (§VI-C).

**Q: What does "fingerprinting an LLM" actually mean here?**
Classifying which of **8 known model configurations** is running, under **identical prompts** and fixed runtimes (llama.c CPU / ollama CPU-GPU). It does not recover weights, prompts, or outputs (§VI-D).

**Q: How robust are these to noise?**
Across quiet/noisy and local/cloud the metrics move by <1 point with tight 95% CIs (§VI-E). But "noise" = synthetic PCIe (2 GB/s NVMe) + memory (10 GB/s) pressure — not many real competing tenants on the same engine.

**Q: The keystroke F1 numbers — do the detection counts actually add up?**
Not perfectly. From the reported detections/FP/FN you can back out slightly different F1 values (≈97.4% / 98.5%) than the printed 92.0% / 98.4%. It doesn't change which primitive is better, but it's a reporting inconsistency worth knowing (backup "Reporting audit" slide).

### 5 — Comparison & novelty

**Q: Is this strictly better than prior cross-VM channels?**
No — better on two axes. DevTLB has ~5× the covert capacity and ~4× lower error than the IPI channel, and SWQ has the best keystroke timing. But IPI's keystroke F1 (97.9%) beats DevTLB (92.0%), and DEVIOUS has lower bit error and higher website accuracy (with GPU-fingerprint caveats). Different setups, not matched re-runs (Table IV).

**Q: What's genuinely new?**
First public microarchitectural reverse-engineering of Intel DSA; first attacks on the DevTLB (ATC) and on DMWr/SWQ; demonstration that these bypass VT-d PASID isolation across VMs.

### 6 — Defenses

**Q: What's the clean fix, and why isn't it deployed?**
Partition the DevTLB by PASID (like the IOTLB already is) and make the SWQ full/retry feedback privileged. Both cost the performance/area DSA exists to provide, and hiding the queue flag conflicts with legitimate submitters that need retry information. They're proposals, not shipped (§VII).

**Q: Does the random-insertion software mitigation actually work?**
They measure its *cost* (up to 15.7% native / 17.9% DTO at 256 B) but **not** its residual leakage — so it's an overhead study, not a proven defense (§VII, Fig. 14).

**Q: As an operator today, what do I do?**
Give sensitive tenants their own *engine* (not just their own queue — recall E1), avoid cross-tenant SWQ sharing, and disable DSA on the most sensitive code paths. Via `accel-config` (§VII).

### 7 — Scope / "gotcha" questions

**Q: Does encryption stop this?**
No. It leaks activity *patterns* (timing/occupancy), not content. Encrypting the data doesn't change when the accelerator runs.

**Q: Would simply removing the user timer kill it?**
It would hurt the DevTLB channel (which needs rdtsc) but not the SWQ channel, which reads a flag with no duration.

**Q: Does it work across CPU sockets / NUMA nodes, or only one DSA?**
The paper evaluates co-location on one DSA device; the DevTLB is per-engine and interference is engine-scoped (E2). Cross-device behaviour isn't claimed.

**Q: Could the victim detect the attack?**
Possibly for SWQ, since it actively congests a shared queue the victim is using (added latency/retries) — but the paper doesn't evaluate detectability. The DevTLB probe is much lighter (noops).

**Q: Is this reproducible?**
Artifact is public (MIT, github.com/hkustgz-secarch/dsassassin; Zenodo DOI 10.5281/zenodo.17799273), but it needs a DSA-capable Xeon with VT-d/IDXD and privileged setup; website collection alone takes hours-to-a-day (Appendix A).

### 8 — Harder / research-level questions (for a sophisticated audience)

- **Why is the DevTLB only single-entry per field — is that a bug or a deliberate area tradeoff?** The paper doesn't say; it's an observed implementation choice. A larger, PASID-partitioned DevTLB would close the channel at an area/throughput cost — exactly the proposed hardware fix.
- **Would the classifiers survive cross-day / cross-host splits?** Untested — a stated open question and one of the presenter's proposed follow-ups.
- **How does this compare conceptually to IOTLB attacks (DEVIOUS)?** Same family (device-side translation leakage) but the DevTLB is a *different, undocumented* structure that VT-d's PASID isolation was assumed to cover — and doesn't.
- **Is the covert "true capacity" error-corrected throughput or raw?** True/effective capacity after accounting for bit errors — which is why the capacity-vs-raw-rate curve peaks and then falls (Fig. 9).
