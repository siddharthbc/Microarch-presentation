# DSASSASSIN — Slide Plan

**Paper:** Chen, Li, Deng, Wang, Chen. *DSASSASSIN: Cross-VM Side-Channel Attacks by Exploiting Intel Data Streaming Accelerator.* HPCA 2026.
**Presenters:** Siddharth Banakar and Dinesh Samala.
**Presentation date:** 29 October 2026.
**Talk length:** about 40–45 minutes, excluding discussion. **Audience:** architecture / security researchers who know side channels but are new to DSA.
**Deck:** 43 slides: **36 main slides + 7 appendix slides**. The main talk closes with one **Findings and limits** slide.
**Slide styling:** bottom footers contain only the page number. The “The detective story” section header is removed from slides 9–19. Paper citations remain in speaker notes, the source map below, and the provenance documents.

## How to read this document

Each numbered section corresponds to the same page in the PowerPoint and PDF:

- **ON SLIDE** describes what the audience sees.
- **THE STORY** gives the narration.
- **CONTEXT** grounds claims and explains the relevant terms and assumptions.
- **→ SEGUE** connects directly to the next retained slide.

**Grounding convention:** statements tagged **Paper** are drawn from the supplied paper. **Not in the paper**, **Interpretation**, or **Presenter synthesis** identifies explanatory framing or calculations. Keep reported results separate from general claims. Section map: §II-A architecture · §II-B address translation · §IV-B DevTLB characterization · §IV-C shared work queue · §V-A threat model · §V-B/§V-C attack primitives · §VI-A covert communication · §VI-B websites · §VI-C keystrokes · §VI-D models · §VI-E noise · §VI-F comparison · §VII mitigation.

The organizing point is that private address spaces can still share observable accelerator state. The talk moves from DSA architecture to the controlled experiments, then to application inference and its limits.

---

# Opening and architecture (Slides 1–8) · about 9 minutes

### Slide 1 — Title
**ON SLIDE:** Paper title, original paper authors (HKUST-GZ · Tsinghua), HPCA 2026, **Presented by Siddharth Banakar and Dinesh Samala**, and **29 October 2026**.

**THE STORY:** "Datacenters are in an arms race to get work *off* the CPU. Networking, storage, dedup, VM migration — all the boring memory-shuffling — is being handed to little accelerators. Intel's Data Streaming Accelerator is one of them, and it ships in every recent Xeon. Today's paper asks a question nobody had asked before: *when you move the work off the core, what happens to the secrets that used to live with it?* This is the first public security analysis of DSA, and the answer is uncomfortable."

**CONTEXT:**
- *What "the secrets that used to live with it" means (you asked about this line).* It is a narrative paraphrase, not a phrase from the paper. Concretely it points at two things the paper does talk about: (1) the **data** those memory operations touch, and more importantly (2) the **activity and timing patterns** of that work. On the CPU, memory operations like `memcpy` are a known source of leakage through caches and TLBs (§II-C). The paper's point is that when the operation is offloaded to DSA, that same observability reappears on the accelerator (§I). So "the secret" = the co-tenant's *activity pattern*, which the attack reconstructs — it never recovers stored data. Say it plainly if asked: "the thing that leaks is *that* work happened and *when*, not the bytes."
- **Paper:** DSA was introduced in Intel's 4th-generation Xeon Scalable processors, codename Sapphire Rapids (§I). It offloads `memset`, `memcpy`, `memcmp`, checksumming (CRC, DIF), and patching (§II-A).
- **Paper:** this is explicitly "the first security analysis of Intel DSA" (§I), and the findings were disclosed to Intel PSIRT, who acknowledged the issue (§I, Responsible disclosure).
- **Not in the paper:** "ships in every recent Xeon" is loose — the paper scopes it to 4th-gen and newer Xeon Scalable (Sapphire Rapids onward), not literally every Xeon. "Arms race" and "secrets" are presenter framing.

**→ SEGUE:** "Start with the sharing boundary: two private address spaces can still use the same accelerator state."

---

### Slide 2 — Address isolation still leaves the shared activity visible
**ON SLIDE:** Two VMs have private address spaces (PASID A / PASID B) and connect through VT-d/PASID translation isolation to shared engine state and queue occupancy. Closing line: **The leakage is about resource use — not access to victim memory.**

**THE STORY:** "Here's the setup for the entire talk. Two virtual machines. Intel VT-d gives each its own PASID — its own translation context — so neither can touch the other's memory. That protection is real, and it *does* kill the classic IOTLB attacks. But look at the bottom of the picture. Both VMs are using the *same physical accelerator*, and that accelerator has internal state it does **not** split between them. DSASSASSIN never reads a single byte of victim memory. It just watches the shared accelerator twitch. The lesson, stated bluntly: *confidentiality of addresses is not the same as confidentiality of activity.*"

**CONTEXT:**
- **Paper:** PASID = Process Address Space ID. VT-d in *scalable mode* assigns a PASID per process so each has isolated address translation, which "mitigates traditional IOTLB-based attacks" and enforces PASID-tagged isolation between processes and VMs (§I, §V-A). The paper's whole claim is that this isolation is bypassed at the DSA level (§I, §IX).
- **Paper:** the attack reads only the attacker's *own* signals — its own completion latency (`rdtsc`) or its own submission result (`EFLAGS.ZF`). The DevTLB itself is "assured read-only to devices" (§II-B), so victim data is never read; only the presence or absence of activity is inferred (§III).
- **Not in the paper:** "feel each other move" and "twitch" are the presenter's metaphor. The paper's own words are "infer co-tenant activity" and "leaking usage patterns across VMs" (§III).

**→ SEGUE:** "To understand that shared state, first look at the work DSA takes off the CPU."

---

### Slide 3 — Memory offload creates a new place to observe
**ON SLIDE:** Three-step flow: common operations (memcpy, memset, compare, checksums) → DSA offload (descriptor submission, asynchronous execution) → observable state (translation cache, queue occupancy). Closing line: **Moving work off the CPU moves the side-channel surface with it.**

**THE STORY:** "DSA is a data mover. Software hands it the dull, bandwidth-heavy jobs — copy this, compare that, checksum this packet — and it does them asynchronously while the CPU does real work. Great for performance. But think like an attacker for a second. For years we've studied how these memory operations leak *on the CPU* — through caches, through TLBs. The industry's fix was partly to *move them somewhere else.* DSASSASSIN's whole premise is that 'somewhere else' is a brand-new, unstudied, shared place to watch. We didn't delete the side channel. We relocated it to a building with no security cameras."

**CONTEXT:**
- **Paper:** DSA is "a high-throughput data mover designed to offload and accelerate memory operations" — `memset`, `memcpy`, `memcmp`, checksumming, patching — which are "common in datacenter applications, storage, networking, deduplication, VM migration, and checkpointing" (§II-A).
- **Paper:** the motivation is that accelerators "bypass the CPU's well-established virtualization protections," and optimization in heterogeneous systems "may unintentionally open side-channel leakage vectors" (§III). Cache/TLB side channels on the CPU are established prior work (§II-C).
- **Not in the paper:** the claim that offloading was done *as a side-channel fix* ("the industry's fix was partly to move them") is **presenter framing** — the paper motivates offloading by performance/CPU-cycle savings, not security. The "building with no security cameras" line is a metaphor. Be careful not to state the authors claimed offloading was a security measure; they did not.

**→ SEGUE:** "To watch it, you have to know how a job flows through it. One job, end to end."

---

### Slide 4 — A DSA operation is a descriptor-driven pipeline
**ON SLIDE:** The paper's **original Fig. 1**, cropped from PDF p. 3, shows the portal, work queue, batch fetcher/buffer, arbiter, five engine stages, and address-translation path. Read it alongside a short journey: submit descriptor → queue/arbiter → decode/read/compute/write/notify → completion. The narration identifies the two attacker observations: admission result and own completion time.

**THE STORY:** "Follow one job. Software fills out a *descriptor* — a little form that says 'copy from here to there' — and writes it to an MMIO *portal*. The portal drops it into a *work queue*. An *engine* pulls it off the queue, does the memory work, and writes a *completion record* to tell you it's done. Remember just two things from this diagram, because the entire attack rides on them. One: *did my submission get into the queue, or was it rejected?* Two: *how long until my completion came back?* That's it. Two questions an attacker can ask about its *own* jobs — and the answers leak the neighbor."

**CONTEXT:**
- **Paper (§II-A, Fig. 1):** DSA accepts two descriptor types — *work descriptors* and *batch descriptors*. Software writes them to an MMIO *portal*, which forwards to a *work queue*; queues buffer and dispatch to *engines*. Batch engines fetch descriptors into internal buffers; an *arbiter* selects from either the batch buffer or the work queue. Each unit decodes, reads source, computes, writes destination, and notifies via a completion record or interrupt.
- **Figure-reading caution:** Fig. 1 labels the engine stages **decode → read → compute → write → notify**. Use those labels when pointing at the diagram; the prose's stage-number description in §II-A does not cleanly match them. Memory requests use the address-translation path explained next.
- *The "two handles" framing* is the presenter's distillation, but it is faithful: the paper's two actual observables are the submission result via `EFLAGS.ZF` (§IV-C) and the completion latency via `rdtsc` (§IV-B). Everything later is one of those two.
- **Not in the paper:** "a building with no cameras", "a little form" — presenter phrasing.

**→ SEGUE:** "There's one more component on this diagram I skipped — the thing that makes memory access fast, and the thing that betrays everyone. Let's zoom into it."

---

### Slide 5 — The device keeps its own translation cache
**ON SLIDE:** Translation flow explained by the right side of **Fig. 1** on slide 4: device request (VA + PASID) → DevTLB/ATC (hit → reuse; miss → Translation Agent/IOTLB, page walk if needed) → memory. Keep translation permissions distinct from shared replacement capacity.

**THE STORY:** "DSA caches address translations on the device in the DevTLB. The translation request's address-space context controls authorization, but does not give every VM separate replacement capacity. A conflicting request can replace my entry, making my own probe slower without revealing the victim's address or data. A DevTLB miss consults the Translation Agent; its IOTLB may answer without a page-table walk. The paper's first weapon observes replacement activity."

**CONTEXT:**
- **Paper (§II-B):** ATS = Address Translation Services. The device sends a virtual-address translation request to the *Translation Agent* (TA), which uses PASID/address-space context to supply an authorized translation. The device caches it and accesses memory using the physical address. The DevTLB is the *Address Translation Cache* (ATC) in the PCIe/DSA specs. A DevTLB miss is not necessarily an IOTLB miss: §IV-B explicitly warms the IOTLB and page tables before measuring DevTLB hit/miss latency.
- **Paper:** §II-B describes the cache as read-only to devices; §IV-B shows shared replacement capacity across PASIDs. Do not infer an exact undocumented tag layout or a general proof of address confidentiality from that wording. This attack observes its own latency, not a dump of victim translations.
- **Not in the paper:** "the paper's first weapon is eviction, not disclosure" is presenter framing, but it is a faithful summary of the §IV-B result.

**→ SEGUE:** "Before using that signal, state the device access and co-location assumptions the attacker needs."

---

### Slide 6 — The attacker needs DSA access and co-location
**ON SLIDE:** Two columns. *Assumed:* DSA Xeon + IDXD + VT-d scalable mode; victim actually uses DSA; attacker can submit descriptors (`CAP_SYS_RAWIO`); shares the engine (DevTLB) or the SWQ; can set its own affinity (non-root). *NOT needed:* shared CPU core; shared memory; permission to read victim addresses; root / host DSA reconfiguration.

**THE STORY:** "Here's the deal. The attacker is unprivileged in the way that matters: no root, can't reconfigure the host's accelerator, can't read victim memory, and — importantly — does **not** share a CPU core with the victim. This is genuinely cross-core, cross-VM. But I want to be honest where the paper is quietly strong *and* quietly convenient. 'Unprivileged' still assumes the attacker was *provisioned access to the device* and ended up *co-located on the same engine or queue* as the victim. There's even a small tension in §V-A: it first says configuring engine affinity and queue settings needs root, then says choosing an engine or queue affinity does *not* — read that as 'creating queues is root via accel-config; binding to an existing portal isn't.' Co-location is an assumption, not a given; keep that boundary in mind when reading the results."

**CONTEXT:**
- **Paper (§V-A):** the attacker runs arbitrary user-space code on Linux (6.11.0-25-generic in their setup) with the Intel IDXD driver, on 4th-gen-or-newer Xeon Scalable with DSA, VT-d in scalable mode. The attacker needs only the `CAP_SYS_RAWIO` capability to submit descriptors; is cross-VM with no shared memory or communication; and can run on a different CPU core. The victim uses DSA for production workloads.
- **The tension, verbatim:** §V-A says the attacker is "not assumed to be capable of configuring engine affinity and work queue settings, since this access to driver requires root privilege." Then §V (p. 8) says "setting DSA affinity to a specific engine or queue does not require root access." The reconciling reading: *creating/configuring* queues via `accel-config` is privileged; *binding* to an existing engine/queue portal is not. The paper calls these co-location assumptions "prevalent among DSA applications [24], [25], [42]" (§V).
- **Interpretation:** distinguish provisioning a queue from submitting to an already provisioned portal. The paper does not establish that every tenant automatically obtains the required co-location.

**→ SEGUE:** "Co-location, though, is more subtle than it sounds — because there are *two* kinds of sharing here, and they are not the same kind of door."

---

### Slide 7 — Two channels cross two different boundaries
**ON SLIDE:** The paper's **original Fig. 7** shows the two cross-VM attack setups. Beside it, distinguish the required shared resource: **same engine** for DevTLB, including different queues; **same SWQ** for admission feedback. The host/guest translation paths in the figure provide context, not an attacker ability to read victim addresses.

**THE STORY:** "This slide is the one I'd tattoo on an operator's arm. The two attacks need two different kinds of sharing. The queue-contention attack needs the victim and attacker in the *same work queue* — fine, that's intuitive, don't share queues. But the DevTLB attack only needs the same *engine.* You can give the two VMs completely separate queues — which an operator would reasonably call 'isolation' — and the DevTLB channel *sails right through*, because the cache lives down at the engine, underneath the queues. If you remember one structural fact from this talk, make it this one."

**CONTEXT:**
- **Paper:** the DevTLB primitive (DSADevTLB) assumes the attacker "has access to a work queue bound to the same DSA engine as the victim's" — queues may differ (§V-B; §VI setup (a)). The SWQ primitive (DSASWQ) requires the attacker and victim to "share the same SWQ but use distinct logical queue entries" (§V-C; §VI setup (b)).
- **Paper (the proof this slide rests on):** experiment E1 — different work queues, same engine — still produces cross-VM eviction, "confirming that DevTLB entries are not indexed by work queue identifiers" (§IV-B). That is the whole basis for "separate queues don't save you."
- This slide is a promise the deck pays off twice more: at the money-shot (Slide 13) and in operator guidance (Slide 34).

**→ SEGUE:** "The sharing boundary comes from measurement. First separate the privileged tools used to characterize DSA from the signals an attacker can read."

---

### Slide 8 — Characterization counters ≠ attack signals
**ON SLIDE:** Two columns separate privileged characterization counters (`EV_ATC_ALLOC`, `EV_ATC_NO_ALLOC`, `EV_ATC_HIT_PREV`, from Table I) from attack signals: own completion time (`rdtsc`) and `ENQCMD`/`EFLAGS.ZF`. The platform line names Xeon 8468V local / 8475B Alibaba cloud, Linux 6.11, IDXD, VT-d scalable mode, SR-IOV for the DevTLB setup, and Scalable IOV for shared SWQ.

**THE STORY:** "Here's the answer, and it matters. To *understand* the hardware, yes, they use privileged performance counters — Perfmon — because that's how you get ground truth about hits and misses. But the *attack itself* never touches those. The attack reads one of two things any user can read: how long its own job took, or whether its own submission succeeded. So the counters are the microscope in the lab; they are not part of the weapon that goes out the door. Keep those two separate in your head for the rest of the talk. And note — they did all of this on both a local server and a real Alibaba cloud instance, which is why the 'does it survive the cloud' question has an answer."

**CONTEXT:**
- **Paper (§IV-B, Table I):** reverse engineering uses Intel Perfmon (a device-level PMU) with three events — `EV_ATC_ALLOC` (# DevTLB requests), `EV_ATC_NO_ALLOC` (# requests that don't trigger replacement), and `EV_ATC_HIT_PREV` (# hits; the primary signal).
- **Paper (the key separation):** "Perfmon is typically accessed via the Linux `perf`, which requires a privileged user. Therefore, we only use Perfmon for benchmarking the DSA. The side-channel attacks are performed by only reading the CPU timer or non-privileged registers" (§IV-B). So the "microscope vs weapon" distinction is the paper's own point, not just framing.
- **Paper (platforms):** local Intel Xeon Platinum 8468V and a public Alibaba Cloud instance on Xeon Platinum 8475B (§IV-B). In the attacks, DSA is virtualized with SR-IOV; SWQ sharing uses Scalable IOV (§VI). The on-slide platform line distinguishes SR-IOV for the DevTLB setup from Scalable IOV for the shared-SWQ scenario.

**→ SEGUE:** "With the measurement method clear, look at the descriptor fields that select the cached translations."

---

# Microarchitecture and attack mechanisms (Slides 9–19) · about 13 minutes

### Slide 9 — Clue #1 — the opcode chooses which slot you touch
**ON SLIDE:** The paper's **original Fig. 3** makes the descriptor byte layout visible. Pair it with a compact opcode-to-field guide: `noop` → comp; compare → src + src2 + comp; copy → src + dst + comp; dualcast → src + dst + dst2 + comp. Point out offset 24: destination OR source2 according to opcode.

**THE STORY:** "First clue. The cache isn't indexed by address the way you'd expect. It's indexed by the *role* a field plays in the descriptor — source, second source, destination, second destination, completion record. And the authors can *choose* which roles to exercise by choosing the opcode. A `noop` touches only the completion slot — that's the scalpel: cheapest possible job, cleanest possible timing. `dualcast` lights up four slots at once. By picking opcodes, they get surgical control over which part of the cache they poke."

**CONTEXT:**
- **Paper (§IV-A, Takeaway 2):** the DevTLB "does not use virtual or physical memory addresses to index entries. Instead, it indexes entries by engine ID and field type (e.g., src, src2)." The five field roles are src, src2, dst, dst2, comp.
- **Paper (§IV-B):** the four probe roles — `noop` (writes only the completion record), two-source compare (src + src2), copy (src + dst), dualcast (src → dst + dst2). The descriptor byte layout is Fig. 3; note offset 24 holds *dst OR src2* depending on opcode. Listing 1 prints `DSA_OPCODE_COMPVAL` in a helper that also fills `src2_addr`; avoid reproducing that opcode as a verified two-source comparison recipe. Slide 15 uses only its timing excerpt.
- **Paper:** `noop` is chosen because of "its low execution cost and distinguishable latency between DevTLB hits and misses" (§V-B). "Scalpel" is the presenter's word for that same idea.

**→ SEGUE:** "So the cache has these role-based drawers. Next question: how *big* is each drawer?"

---

### Slide 10 — The reveal — five drawers, one translation each
**ON SLIDE:** The paper's **original Fig. 2** shows the reconstructed DSA microarchitecture, including work-queue admission and per-engine DevTLB indexing. Highlight the five field roles in adjacent editable text: src, src2, dst, dst2, comp; one cached page translation per role in the tested design. The original drawing is reproduced without redrawing its internals.

**THE STORY:** "Here's where it's going — I'll show you the proof in a second, but let me spoil it so the experiments make sense. Each engine's DevTLB has exactly five entries, one per field role, and each entry holds exactly *one* translation. One. It's direct-mapped to the extreme. Why is that catastrophic for isolation? Because in a normal cache you need a whole 'eviction set' to kick someone out. Here, *any single different page* in that field role evicts the current occupant. There's no lock to pick — the drawer only fits one sock, so the moment the neighbor puts their sock in, yours is on the floor."

**CONTEXT:**
- **Paper (§IV-B):** a multipage operation leaves only the last page cached for each relevant field; the DevTLB is not an access history. The batch fetcher’s own descriptor reads and completion-record writes did not populate these five slots in the characterization experiments. Distinguish those batch-fetcher accesses from the engine’s ordinary completion writes.
- **Paper (§IV-A, Takeaway 1):** "each engine's DevTLB consists of five sub-entries corresponding to different fields of the descriptor. As each sub-entry only maintains single slot, it is not isolated by PASID-tag." Confirmed in §IV-B as direct-mapped (W = 1, S = 1).
- **Paper:** accesses from the batch fetcher "are not cached" — the five slots are per *engine's processing unit* (§IV-A). Each engine has its own five slots (E2 later proves the engine boundary).
- **Not in the paper:** "one sock per drawer" and "no eviction set needed" are the presenter's metaphor for the single-slot, direct-mapped result. The underlying fact (single slot ⇒ any conflicting page evicts) is §IV-B.

**→ SEGUE:** "Big claim — 'exactly one slot.' Let's earn it. Experiment one."

---

### Slide 11 — Proof of “one slot” — base → offset → base
**ON SLIDE:** **Listing 2 as editable monospace text**, retaining its three `probe_noop` calls and comments. A result table connects the 4 KiB-aligned base test to the observation: same-page offset → final hit; tested different-page offset → final miss. Explain the experiment's order; the snippet is not a standalone program.

**THE STORY:** "Dead simple and completely convincing. Load a translation for a base address. Then touch a second address an 'offset' away. Then come back and check: is base still cached? When the offset stays inside the same 4-kilobyte page, base survives — so the cache works at *page* granularity, it ignores the low bits. But the instant the offset crosses into a different page, base is *gone*. If the drawer held even two translations, base would have survived. It didn't. Therefore: one slot. They even evict a 4K entry using a 2-megabyte huge-page address — so it doesn't even keep separate drawers per page size."

**CONTEXT:**
- **Paper (§IV-B, Listing 2):** probe base → probe base+OFFSET → probe base. With OFFSET < 4 KiB the counter records two hits (same page retained); with OFFSET ≥ 4 KiB, no hit on the final probe. This "confirms that the DevTLB caches translations at the page granularity, ignoring the lower 12 address bits," and the missing final hit "suggests that the DevTLB maintains only a single entry — implying a direct-mapped configuration (W = 1, S = 1)."
- **Paper:** "We also attempt to evict a DevTLB entry corresponding to a 4 KiB page using a conflicting address from a 2 MiB huge page and observe a successful eviction… the DevTLB does not maintain dedicated entries for different page sizes" (§IV-B).

**→ SEGUE:** "One slot per role. But are the roles really *independent* drawers — or does touching the source disturb the destination?"

---

### Slide 12 — The drawers are independent — even sharing bits
**ON SLIDE:** **Listings 3 and 4 as editable monospace text**, side by side, with each original helper call and comment preserved. Short result captions explain the controlled differences: changing src retains dst; reusing the src2/dst encoding does not merge their cache slots. Match the captions to the observations in §IV-B, rather than presenting the code alone as a proof.

**THE STORY:** "Watch this. Change the source, keep the destination — and the destination's translation is *still there.* So the drawers really are independent; poking one doesn't disturb another. Then the elegant one: the fields `src2` and `dst` are encoded in the *exact same bytes* of the descriptor — the hardware only tells them apart by the opcode. If the cache were lazy and indexed by those raw bytes, they'd collide. They don't. The hardware routes them to separate drawers based on *meaning*, not bit position. That's a remarkably clean result and it's what makes me trust this reverse engineering."

**CONTEXT:**
- **Paper (§IV-B, Listing 3):** `memcpy(src0, dst0)` then `memcpy(src1, dst0)` — a hit on dst0 shows "dst is independently indexed and not combined with src… each field type is indexed into a dedicated sub-entry." `dualcast` (one src, two dsts) varying src while keeping dst/dst2 gives two hits, confirming it.
- **Paper (§IV-B, Listing 4):** src2 and dst "occupy the same bits in the instruction format and are distinguished only by the operation type" (Fig. 3, offset 24). Mapping both to the same page under different opcodes yields "only a single hit… suggesting no interference between src2 and dst." Takeaway 1: all five field types index separate sub-entries, each one slot, no cross-field eviction.

**→ SEGUE:** "Those experiments isolate fields. Next, vary the work queue and engine to find the cross-VM sharing boundary."

---

### Slide 13 — The money shot — eviction follows the engine, not the queue
**ON SLIDE:** The paper’s **original Fig. 5** shows E0/E1/E2 placements. The adjacent table gives measured outcomes: E0 same queue/engine → miss; E1 different queues/same engine → miss; E2 separate engines → hit. Below the table, explain that E1 shares DevTLB capacity and E2 preserves the primed entry. The conclusion is scoped to these experiments.

**THE STORY:** "Three experiments, two VMs. E-zero: same queue and engine — the attacker's probe misses. E-one: *different queues, same engine* — it still misses, showing that queue separation did not partition this DevTLB capacity. E-two is the negative control: *separate engines* — the probe hits and the primed translation survives. Separate engines prevented this eviction in the tested configuration; separate queues did not. The control identifies the observed sharing boundary. It does not establish a universal security guarantee for every DSA configuration."

**CONTEXT:**
- **Paper (§IV-B, Fig. 5):** two VMs (attacker and victim). The attacker primes DevTLB entries with its own addresses, idles; the victim submits a descriptor to evict; the attacker probes. E0 — same engine, shared queue → miss. E1 — same engine, separate queues → miss (so "DevTLB entries are not indexed by work queue identifiers"). E2 — separate engines → hit ("DevTLB entries are not shared across engines").
- **Paper (Takeaway 2):** "The DevTLB is indexed by engine ID and descriptor field type and is not isolated by PASIDs and virtual machines." Indexing is engine-first, then field.
- **Not in the paper:** "negative control" is the presenter's (accurate) term for E2; the paper describes E2 as showing entries are not shared across engines, which is exactly a control.

**→ SEGUE:** "That's the signal in privileged counters. But an attacker in the wild only has a clock. Is the signal still there when all you can do is time your own job?"

---

### Slide 14 — The clock still works — even under noise
**ON SLIDE:** Four latency histograms (Local, Local+Noise, Cloud, Cloud+Noise). Hit ≈ 500 cycles, miss ≈ >1000, threshold ≈ 600–900. Reuse **Fig. 4**.

**THE STORY:** "Here's the attacker's actual view — just `rdtsc` on its own completion. Hits cluster around 500 cycles, misses above 1000. Two clean humps, easy to separate with a threshold. 'But the cloud is noisy,' you say — so they *deliberately* beat up the system: two gigabytes a second of NVMe traffic, ten gigabytes a second of memory copies. The humps shift a bit — about 89 cycles in the cloud — but they never merge. The clock alone, with no privilege, still tells hit from miss. The lab result survives contact with reality."

**CONTEXT:**
- **Paper (§IV-B, Distinguishable latency, Fig. 4):** DevTLB hits "consistently incur around 500 cycles," misses "exceeding 1,000 cycles," separable with "a threshold between 600 and 900 cycles." Measured across Local, Local+Noise, Cloud, Cloud+Noise. Before measuring, "both the page table and IOTLB are warmed up to eliminate their effects."
- **Paper (the noise):** PCIe pressure from "rapidly reading and writing NVMe SSD with 2 GB/s traffic," and memory pressure at "10 GB/s core memcpy bandwidth." "An average shift of 89 cycles in the cloud environment," but "the threshold remains clearly identifiable."

**→ SEGUE:** "We now have everything we need to state the first weapon cleanly. Three steps."

---

### Slide 15 — Weapon #1 — Prime → Idle → Probe
**ON SLIDE:** Prime → Idle → Probe beside **Listing 1, lines 7–12, as an editable timing excerpt**: enqueue, read timestamp, poll the completion status, read timestamp, return the difference. Label it as a generic completion-timing excerpt; §V-B applies the timing idea to a `noop` probe of the attacker's own comp page. Fast/slow indicates retained/replaced state under the controlled observation window; it does not identify the victim by itself.

**THE STORY:** "I prime a slot using *my own* completion-record address — I never need the victim's address. I go quiet. A victim completion write through the same engine can replace that slot. I probe by re-running my noop and timing its completion. A fast probe suggests retention; a slow probe suggests replacement. Calibration, co-location, and the observation window support an activity inference. One sample does not prove who caused the delay or reveal their data. The editable code shows the paper's completion-polling timing excerpt; the NOOP attack applies that timing idea to its own completion record."

**CONTEXT:**
- **Interpretation:** the probe reveals coarse activity in the shared engine, not the victim’s address, data, browser identity, or typed character. Application-specific temporal patterns and trained classifiers provide the later labels. No shared victim memory or victim virtual address is required to probe the attacker’s own completion page.
- **Paper (§V-B):** three phases. *Prime* — submit a `noop` that writes to a chosen completion-record address, loading it into a DevTLB sub-entry; poll to confirm it is cached. *Idle* — wait longer than a typical DSA op; a victim on the same engine may evict the entry ("if the victim submits a job, a DevTLB eviction occurs (bit 1); otherwise… bit 0"). *Probe* — submit another `noop` to the same completion-record address, record completion time with `rdtsc`, compare to the threshold.
- The attacker only ever primes its *own* completion-record address — it never needs any victim address (§V-B). That is the "almost unfair" part, and it is in the paper.

**→ SEGUE:** "That is the completion-timing channel. The second channel comes from the result of trying to submit work."

---

### Slide 16 — The dead end that wasn’t — a flag talks
**ON SLIDE:** Submission/completion latency vs. transfer size (reuse **Fig. 6**). Submission ≈ flat ~700 cycles; completion grows with size; queue-full shows up as a **flag**, not a time.

**THE STORY:** "You'd expect a shared queue to leak through timing — submit a job, see if it's slow because the queue's busy. The authors measure it and… submission time is *flat.* Constant. Timing is a dead end. But here's the save: submission uses a special instruction — a Deferrable Memory Write — and when the queue is *full*, the hardware refuses and sets a single CPU flag, `EFLAGS.ZF`. So the queue's fullness leaks not through *how long* but through *yes or no.* It's a timer-free channel. That's actually *better* than timing — no clock noise to fight."

**CONTEXT:**
- **Paper (§IV-C, Fig. 6):** completion latency grows (log-linearly) with transfer size, but "submission latency remains constant at approximately 700 cycles." So timing of submission is not a usable channel.
- **Paper:** DMWr (Deferrable Memory Write) is "a non-posted MMIO write used to signal submission status." On queue saturation, "the DSA communicates failure to the submitter by setting the `EFLAGS.ZF` flag," which "exposes internal queue state without requiring explicit timing measurements" (§IV-C, and Intel spec [23]). Takeaway 3: the ZF flag reveals queue-full without root and without timing.
- **Paper:** contention through ZF "is observed only when the transfer size reaches or exceeds 2^25 bytes" (§IV-C) — this is why the anchor copy must be large (Slide 18).

**→ SEGUE:** "To weaponize 'the queue is full,' you first have to be able to fill it on command — which means understanding how the queue schedules work."

---

### Slide 17 — Learning to hold the queue hostage
**ON SLIDE:** **Listing 5 as editable monospace text** shows the batch submission, fence, timed work submission, completion poll, and latency calculation. A short explanation links the experiment to the work-over-batch preference reported in §IV-C. The reconstructed arbiter and queue paths are already visible in original Fig. 2 on slide 10; the experiment supports using an ordinary long copy for congestion.

**THE STORY:** "Two things the authors had to pin down. First, the fullness check happens at enqueue time against config registers — in constant time — which is exactly why the flag signal has no timing dependence. Second, they reverse-engineer the *arbiter*: they race a work descriptor against a batch descriptor and find the work descriptor always wins, regardless of order. Why do we care? Because it tells the attacker how to hold the queue hostage reliably: use one long ordinary `memcpy` to pin the engine, not a batch trick the arbiter might de-prioritize."

**CONTEXT:**
- **Paper (§IV-A):** the single hardware queue is partitioned into virtual queues via configuration registers; each queue's metadata "is checked against the configuration registers at enqueue time," so "queue occupancy checks and congestion detection occur in constant time." That constant-time check is why the ZF signal has no timing component.
- **Paper (§IV-A / §IV-C, Listing 5):** the undocumented arbiter "prioritizes descriptors from the work queue over those from the batch buffer." They prove it by swapping submission order of a work and a batch descriptor and finding latency unchanged, so "batch descriptors cannot be reliably used for congestion-based attacks." Hence: use an ordinary long `memcpy`.

**→ SEGUE:** "So here's the trap they set."

---

### Slide 18 — The trap — leave exactly one seat open
**ON SLIDE:** **Listing 6 as editable monospace text** shows `congest(wq_size)` and `probe()`. Beside it, explain the conceptual preparation: one large copy + `wq_size - 2` fillers targets one remaining admission slot during the controlled window. State the measured ≥ 2²⁵-byte anchor threshold and distinguish the submission return/flag from job completion.

**THE STORY:** "Picture a theater with N seats. The attacker buys all but one — a long-running copy holds the front row so the queue drains slowly, and filler jobs take the rest. Exactly one seat left. Now the attacker waits. If the victim submits a job, it takes that last seat and the house is full. Two practical details from the paper: the anchor copy has to be *big* — contention only appeared for transfers of 2²⁵ bytes or more, about 32 MiB — and the queue size is readable with `accel-config` without root, so the attacker knows exactly how many seats to buy. The whole thing is a stopwatch-free race against its own long copy finishing."

**CONTEXT:**
- **Paper (§V-C, Listing 6):** the attacker submits "one large `memcpy` descriptor to anchor the head of the SWQ, followed by `wq_size - 2` additional simple descriptors to fully occupy the queue" → effective occupancy wq_size − 1, one free slot.
- **Paper:** "The SWQ size (`wq_size`) can be read without root privileges using `accel-config`" (§IV-C). And the idle window "should be less than the execution time of the memcpy descriptor" so the queue stays near-full (§V-C).
- **Paper:** the large anchor is needed because contention via ZF "is observed only when the transfer size reaches or exceeds 2^25 bytes" (§IV-C) — i.e., 32 MiB. (The "32 MiB" gloss is the presenter's unit conversion of 2^25 bytes; it is exact.)
- **Not in the paper:** the "theater with N seats" is a metaphor.

**→ SEGUE:** "And checking whether the house filled up is a single instruction."

---

### Slide 19 — Weapon #2 — Congest → Idle → Probe
**ON SLIDE:** **Congest** (long memcpy + fillers, near-full) → **Idle** (hold the window; victim may submit) → **Probe** (submit once, read `EFLAGS.ZF`). ZF=0 means accepted; ZF=1 means retry/full in the experiment. Victim activity is inferred under the controlled window and co-location assumptions. Refer back to original **Fig. 7** on slide 7 and **Listing 6** on slide 18.

**THE STORY:** "Same three-beat rhythm as DevTLB: prepare, wait, probe. Congest the queue to one-from-full and hold the observation window. Then try to submit one job and read the flag. ZF=0 means accepted; ZF=1 means retry, a full queue in this experiment. With the queue prepared and the window controlled, retry is evidence that the victim consumed remaining admission capacity. The signal uses no duration measurement; the observation window still needs control. The cost is active congestion of a shared resource the victim needs. Whether that makes the attack detectable remains an unevaluated question."

**CONTEXT:**
- **Attack footprint:** SWQ probing actively occupies a resource the victim needs. Its signal is admission feedback rather than a measured duration, but congestion can affect victim progress. The paper does not fully evaluate victim performance impact or probe detectability; do not present the channel as passive.
- **Paper (§V-C):** *Congest* — anchor `memcpy` + fillers to near-full. *Idle* — hold the window so the victim may submit to the last slot. *Probe* — `enqcmd` once and inspect `EFLAGS.ZF`: "If ZF is set (ZF = 1), it indicates that the submission failed due to a full queue, implying that the victim has also issued a submission during the idle window. Otherwise, the victim does not submit." Timer-free.
- **Not in the paper:** the "loud / active footprint" judgment is **presenter interpretation** — the paper does *not* evaluate how detectable or disruptive the congestion is. Flag it as your reading, not a measured result.

**→ SEGUE:** "We now have two observable signals. First test whether a cooperating sender and receiver can use them to carry a message."

---

# Attack demonstrations (Slides 20–30) · about 12 minutes

### Slide 20 — Can it even carry a message?
**ON SLIDE:** Phase table — Synchronize (consecutive 1-bit preamble), Prepare (prime/congest), Encode (sender submits for 1 and idles for 0), Decode (receiver times completion or reads ZF). Closing line: **Covert-channel feasibility is a separate claim from inference accuracy.**

**THE STORY:** "A covert channel is the controlled experiment: make the 'victim' a *cooperative* sender and see how fast and cleanly you can move bits. Sender encodes a one by causing activity, a zero by staying idle; receiver reads the heartbeat. A little preamble of ones synchronizes the clocks. This is the capacity test — the cleanest possible conditions. Real victims are messier, and I'll keep that distinction sharp."

**CONTEXT:**
- **Paper (§VI-A):** an "asynchronous time-slicing protocol." As in the prior IPI covert channel [51], synchronization uses a "preamble of several consecutive '1' bits." Then the receiver primes the DevTLB or congests the SWQ; the sender encodes '1' by evicting entries / submitting to a congested SWQ, '0' by idling; the receiver decodes via DevTLB latency or SWQ congestion state.
- A covert channel assumes a *cooperative* sender, so it measures *capacity*, not whether an *oblivious* victim leaks — that distinction is the paper's own framing of why covert channels are "a widely adopted evaluation method… for demonstrating the feasibility of cross-domain leakage" (§VI-A).

**→ SEGUE:** "Under those clean conditions, how fast does it go?"

---

### Slide 21 — 17.19 kbps — and a bandwidth / error tradeoff
**ON SLIDE:** DevTLB **17.19 kbps / 4.63% bit error** and SWQ **4.02 kbps / 13.11% bit error**, beside the raw-rate, true-capacity, and error curves from **Fig. 9**. Closing line: **Faster raw signalling loses useful throughput as the error rate climbs.**

**THE STORY:** "DevTLB hits 17.19 kilobits a second at under 5% error — and remember the quiet-sniper personality, light probes pack tightly, so it beats SWQ on bandwidth. Notice the shape of these curves: as you crank the *raw* rate, errors climb until the *useful* throughput peaks and then falls off a cliff. That's why there's a 'best point.' And that 17-and-change is the number that's five times faster and four times cleaner than the prior state of the art. Capacity: proven."

**CONTEXT:**
- **Paper (§VI-A, Fig. 9):** DSADevTLB covert channel reaches "a peak true capacity of 17.19 Kbps with an average bit error rate of 4.63%"; DSASWQ reaches "4.02 Kbps with an error rate of 13.11%." Fig. 9 plots raw capacity vs. true (effective) capacity and error rate — the peak-then-fall shape is why there's an optimum.
- **Paper:** the 5×/4× claim is vs the IPI channel [51] (§VI-F). Note the abstract reports 4.64% while §VI-A and Table IV report 4.63% — a minor internal inconsistency in the paper (use 4.63%, the results-section value).
- *"True capacity" vs "raw capacity"* (ask-me-later): true capacity is the error-corrected effective throughput; raw is the attempted signaling rate (§VI-A, Fig. 9).

**→ SEGUE:** "But a cooperative sender is a toy. The real question is whether an *oblivious* victim leaks. First real target: what website are you browsing?"

---

### Slide 22 — Attack #1 — websites leak through the stack
**ON SLIDE:** The paper's **original Fig. 8** shows the VPP/memif packet path. Adjacent explanatory text connects website-induced traffic → DSA packet copies → shared-engine DevTLB activity → the attacker's miss-count trace. Browser/site labels come from the experiment and classifier; the hardware signal contains no browser name, URL, or packet contents.

**THE STORY:** "Here's a realistic victim: a VM running VPP, a high-performance userspace network stack built on DPDK, which uses DSA to shuttle packets through shared memory. So every burst of network traffic becomes a burst of DSA activity on the shared engine. The attacker, co-located on that engine, just runs the quiet DevTLB probe and counts evictions over time. It never sees a packet — only the *rhythm* of the accelerator as pages load."

**CONTEXT:**
- **Paper (§VI, §VI-B, Fig. 8):** DPDK is not a standalone system, so the victim runs VPP (Vector Packet Processor), "a high-performance user-space network stack built on DPDK." In VPP, "DSA accelerates packet transfers within the shared memory interface (memif)." The attacker binds to a work queue on the same engine, runs DSADevTLB, and counts DevTLB misses per slot; "an increased number of DevTLB misses within a slot correlates with greater packet arrival activity" (§VI-B).
- The attacker observes only accelerator activity, never packet contents (§VI-B) — "rhythm" is the presenter's word for the per-slot miss count.

**→ SEGUE:** "That rhythm becomes a feature vector — let me show you the actual pipeline so you can judge it."

---

### Slide 23 — The pipeline, laid bare — and it is closed-world
**ON SLIDE:** Three columns: **Sampling** — every 10 µs, 400 probes per slot, about 4 ms; **Model** — two BiLSTM layers, attention + dropout, softmax classes; **Dataset** — 100 sites × 200 traces, 80/20 split, about 16,000/4,000. A separate line defines one feature per slot as the classified DevTLB miss count. The closing line identifies closed-world classification over known labels.

**THE STORY:** "Each website becomes a time series — roughly 250 slots, each slot just a count of how many times the probe got evicted. Feed that to an attention-BiLSTM, the standard tool for this. I want you to notice one honest word on this slide: *closed-world.* A hundred *known* sites, train and test drawn from the same hundred. The evaluation tests classification among those known labels. It does not establish detection of arbitrary pages on the open internet."

**CONTEXT:**
- **Paper (§VI-B):** the attacker "samples the DevTLB state every 10 µs and aggregates every 400 samples into a single time slot (approximately 4 ms per slot)," counting DevTLB misses per slot, over 250 slots (Fig. 10). The feature per slot is the miss count.
- **Paper:** the classifier is "an Attention-based Bidirectional LSTM (BiLSTM)" — "two BiLSTM layers, followed by an attention mechanism… and a softmax output layer," with dropout. Dataset: headless Google Chrome 138.0, top-100 Alexa sites, 200 traces each, 80/20 train/test (so 20,000 traces → 16,000 / 4,000).
- **Not in the paper:** the word "closed-world" is the presenter's (accurate) label; the paper doesn't use the term, but its setup — train and test over the same fixed 100 known sites — is closed-world by construction.

**→ SEGUE:** "Does the signal actually look different per site, or is the model hallucinating? Look for yourself."

---

### Slide 24 — The traces really are different
**ON SLIDE:** Original example miss-count traces for baidu, apple, and microsoft from **Fig. 10**. Closing line: **Temporal shape is the feature; miss count is a proxy for DSA activity.**

**THE STORY:** "Three sites, three visibly different activity signatures — different burst timing, different heights. That's what the model keys on. No URLs, no content — just the silhouette of the accelerator working as the page loads. It's genuinely striking that something this coarse separates sites at all."

**CONTEXT:**
- **Paper (§VI-B, Fig. 10):** the figure shows DevTLB-miss traces across 250 slots for three example sites (baidu.com, apple.com, microsoft.com); "these traces exhibit unique characteristics, which can be leveraged for classification."
- The feature is purely the temporal shape of per-slot miss counts — a proxy for DSA activity during page load (§VI-B). No URL or payload is observed.

**→ SEGUE:** "So how well does it separate all one hundred?"

---

### Slide 25 — 85.73% — the number you must not misquote
**ON SLIDE:** Original 15-site confusion matrix from **Fig. 11**, beside two explicitly separated results: **85.73%** on the full 100-site dataset (1% baseline) and **96.5%** on the displayed 15-site subset. The closing line repeats that distinction.

**THE STORY:** "On all 100 sites: 85.73% versus a 1% coin-flip. Strong. Now — careful — the gorgeous confusion matrix in the paper is a *15-site subset* at 96.5%, and it is *not* the headline number. Don't let anyone, including yourself, quote 96.5% as the result. The honest headline is 85.73 on the full hundred. The misses are sensible: sites with similar traffic shapes, like canva and notion, blur together — the authors call that out as future work."

**CONTEXT:**
- **Paper (§VI-B, Fig. 11):** "On the full 100-website dataset, our model reaches a top-1 classification accuracy of 85.73%, significantly outperforming random guessing (1%)." The confusion matrix (Fig. 11) is "for a representative subset of 15 websites," on which accuracy is 96.5% — explicitly a subset, not the headline.
- **Paper:** "Relatively lower accuracy for certain domains (e.g., canva.com, notion.com) suggests overlapping traffic patterns… which we leave as future work to refine" (§VI-B).

**→ SEGUE:** "Websites are coarse. Can it get down to something as fine as individual keystrokes?"

---

### Slide 26 — Attack #2 — keystrokes, via transparent offload
**ON SLIDE:** Flow: user input (interactive SSH event) → packet handling (OpenSSH mem* calls) → DTO offload (eligible calls to DSA) → DSA observation (eviction or congestion). Closing line: **The demonstrated output is keystroke timing — not recovered command text.**

**THE STORY:** "This one's eerie. There's a library called DTO — DSA Transparent Offload — that silently redirects ordinary `memcpy`-style calls to the accelerator, *no code changes.* So an unmodified OpenSSH, handling each interactive keystroke packet, quietly generates DSA activity per keypress. The attacker times those. But here's the line I will not let blur: the paper recovers keystroke *timing* — when you typed — and notes that timing *could* feed a downstream text model. It does **not** demonstrate recovering what you typed. Timing, not text."

**CONTEXT:**
- **Paper (§VI, §VI-C):** DTO (DSA Transparent Offload) "relies on the Linux Runtime Linker to intercept and offload standard memory functions (e.g., `memset`, `memcpy`) to DSA" for unmodified applications. When a user types over SSH, OpenSSH "invoke[s] `mem*` routines… to handle packets," which DTO offloads to DSA, "producing measurable side effects in DevTLB or SWQ."
- **Paper (the boundary — state it exactly):** "our attack targets an earlier stage: inferring keystroke *timings* based on DSA activity." Timing "can… infer the text by feeding the dataset to a machine learning model [40]," but end-to-end text recovery is *not* demonstrated (§VI-C). Prior works [40], [55] reconstruct text; this one stops at timing.

**→ SEGUE:** "And both weapons can see those keypresses — here are the raw traces."

---

### Slide 27 — You can see the typing
**ON SLIDE:** Two panels — DevTLB latency trace with threshold, labeled "s s h ␣ r o o t"; SWQ contention trace, same labels + "connection closed." Reuse **Fig. 12**. Note: filtering by DTO byte / latency thresholds.

**THE STORY:** "Top panel, the DevTLB attack; bottom, the SWQ attack — both resolving the individual keystrokes of someone typing 'ssh root.' SWQ gives the crisper spikes, which foreshadows its better timing numbers. One honesty note you'll want for Q&A: events are filtered by byte-size and latency thresholds, so the exact event counts depend on those knobs — which matters for the next slide."

**CONTEXT:**
- **Paper (§VI-C, Fig. 12):** DevTLB (latency, top) and SWQ (contention, bottom) traces captured while typing `ssh root`. "The filter removes the data from our traces if it is labeled as `DTO_MIN_BYTES` (for both attacks) or probed latency ≥ 2,000 cycles (for DevTLB attack)."
- **Paper (the SWQ discovery trick — useful for Q&A):** to find the victim's queue, "one approach is to initiate a temporary SSH connection while concurrently probing candidate SWQs from a separate process" (§VI-C). (Note: this discovery method is shown for the SWQ/SSH case; engine binding for the other attacks is assumed — Slide 6.)

**→ SEGUE:** "So who wins — and here's where I stop being a cheerleader for a moment."

---

### Slide 28 — SWQ wins timing — and a caveat I owe you
**ON SLIDE:** DevTLB 92.0% F1 / 5.29 ms σ; SWQ **98.4% F1 / 1.21 ms σ.** Caveat box: *§VI-C detection counts don't fully reconcile with the printed F1 — see backup.*

**THE STORY:** "SWQ wins keystroke timing cleanly — 98.4% F1 and a 1.21-millisecond timing spread versus 5.29 for DevTLB, exactly what the timer-free design predicts. Use those headline numbers. But I owe you full disclosure: I worked through the paper's own detection, false-positive, and false-negative counts, and they don't perfectly reconcile with the printed F1. It doesn't overturn the conclusion — SWQ is clearly the better keystroke primitive — but a careful reader should know, and I've put the arithmetic in a backup slide. I'd rather you hear it from me than find it yourself."

**CONTEXT:**
- **Paper (§VI-C):** DevTLB F1 92.0%, σ 5.29 ms; SWQ F1 98.4%, σ 1.21 ms. The detailed counts: across 512 ground-truth keystrokes, DevTLB "captures 515 events with 15 false positives and 61 false negatives (500 true positives)," quoted recall 87.8% / precision 97.6%; SWQ "records 511 events with 7 false positives and only 9 false negatives (507 true positives)," recall 98.2% / precision 98.6%.
- **Not in the paper (presenter diagnostic):** those counts don't self-reconcile — 512 ground truth with 500 TP implies 12 FN, not the 61 FN printed; and TP/FP/FN recomputed F1 lands near 97.4% / 98.5%, not the printed 92.0% / 98.4%. This is a *presenter-computed audit* exposing an inconsistency, **not** a correction the paper makes. It doesn't change which primitive is better. Backup slide holds the full arithmetic.

**→ SEGUE:** "Last target, and the most topical: can it tell which AI model your neighbor is running?"

---

### Slide 29 — Attack #3 — fingerprinting the LLM next door
**ON SLIDE:** Table of eight model choices: TinyStories (15M / 42M / 110M), LLaMA 2 (7B), Gemma 3 (1B / 4B), and Qwen3 (1.7B / 4B). Below: **50 traces per model · identical prompts · 80/20 split · 8 ms slots**. Closing line: **The label is a model configuration — no weights or prompts are recovered.** Runtime details belong in the narration/context, not the visible table.

**THE STORY:** "LLM inference constantly shuffles weights around memory, and with DTO those moves hit DSA. Different model sizes and architectures move memory in different rhythms. So the same probe, with a slightly longer 8-millisecond window to match weight-transfer cadence, becomes a model fingerprint. Be precise about the task, though: it's 'which of eight *known* configurations, under *identical* prompts.' Not stealing weights, not reading prompts, not open-world. Distinguishing known configs."

**CONTEXT:**
- **Paper (§VI-D, Table II):** 8 models — TinyStories (15M/42M/110M), Meta LLaMA 2 (7B), Gemma 3 (1B/4B), Qwen3 (1.7B/4B) — run on two runtimes, llama.c (CPU-only) and ollama (CPU-GPU hybrid). 50 traces per model, identical prompts, 80/20 split, 8 ms slots (800 samples) "to align with the timing of model weight transfers."
- **Paper (why it leaks):** LLM inference moves "model weights between CPU and GPU or across memory hierarchies," which "trigger observable DSA activity when offloaded via DTO" (§VI-D). The paper speculates patterns "could be used to infer internal model structure, such as transformer layer depth or model size."
- **Not in the paper:** "no weights or prompts are recovered" is a faithful reading of scope (the paper classifies the model from the trace; it does not claim weight/prompt recovery), but the paper doesn't phrase it as a disclaimer — present it as the correct scoping, not a paper quote.

**→ SEGUE:** "And within that controlled task, the result is almost uncomfortably good."

---

### Slide 30 — 98.6% — impressive, and bounded
**ON SLIDE:** Original model traces from **Fig. 13**, alongside **98.6% validation accuracy** over eight model choices. The qualification states that generality beyond identical prompts and fixed runtimes remains open. Closing line: **Distinguishable configurations within a controlled dataset.**

**THE STORY:** "98.6%. The traces differ both across sizes within a family and across families at the same size, so the model picks up both axes. Genuinely impressive that an accelerator twitch distinguishes language models through two VM walls. But keep the fence around it: fixed prompts, fixed runtimes, same host. It proves these configurations are *separable*, not that you could fingerprint an arbitrary model in the wild. Next, separate this dataset scope from the robustness tests under background noise."

**CONTEXT:**
- **Paper (§VI-D, Fig. 13):** the Attention-BiLSTM classifier "achieves a validation accuracy of 98.6% in predicting the correct model from a given trace." Fig. 13 shows traces differ across sizes within a family (TinyStories 15M/42M/110M) and across families at a size (Gemma 3 vs. Qwen 3).
- **Not in the paper:** "separability, not open-world identification" is **presenter interpretation** consistent with the setup (identical prompts, fixed runtimes, same host, §VI-D). The paper does not test generalization to unseen prompts, runtimes, or hosts — so "open-world generality is unproven" is a scope observation, flagged as yours.

**→ SEGUE:** "Four attacks, all working. Now the three questions a skeptic asks: does it survive the real world, is it actually better than what we had, and can we stop it?"

---

# Evaluation and mitigations (Slides 31–35) · about 6 minutes

### Slide 31 — It barely flinches under stress
**ON SLIDE:** Matrix across Local / Noisy local / Cloud / Noisy cloud — all six Table III rows (DevTLB covert, SWQ covert, website, DevTLB keystroke F1, SWQ keystroke F1, LLM). Reuse **Table III**.

**THE STORY:** "Across quiet and noisy, local and cloud, most numbers barely move — tight confidence intervals, no collapse. So synthetic PCIe and memory pressure don't save you. The one row worth naming out loud is the DevTLB keystroke F1 — it swings a few points, from 90.5 up to 93.4, and noise or the cloud can even *raise* it. But I want precise language here: what they stressed was *background noise*, not *a dozen real tenants fighting over the same engine.* 'Robust to noise' is proven; 'robust to a busy multi-tenant host' is not the same claim, and I'll put it on the open-questions list."

**CONTEXT:**
- **Paper (§VI-E, Table III):** the four attacks (covert, website, SSH keystroke, LLM) are each repeated 50× to get 95% confidence intervals; x is the geometric mean of the Local (no-noise) run. All six rows now appear on the deck: DevTLB covert 17.19→16.52 kbps; SWQ covert 4.02→3.80 kbps; website 85.7→85.1%; DevTLB keystroke F1 92.0 / 90.5 / 93.4 / 93.0%; SWQ keystroke F1 98.4 / 98.2 / 99.1 / 98.9%; LLM 98.6→98.0%.
- **Paper:** "system noise and PCIe noise negligibly impact the attack performance" (§VI-E). The noise is the same synthetic PCIe + memory pressure as §IV-B.
- **Not in the paper:** "not a dozen real tenants fighting the same engine" is the presenter's precise reframing — the paper stresses *synthetic* noise, not *multi-tenant contention*. That gap remains outside the tested stressors; the conclusion on Slide 36 retains this scope distinction.
- *The "Local" column* on this slide is the paper's geometric-mean baseline value; the other columns are the reported noisy/cloud runs (§VI-E).

**→ SEGUE:** "Fine — it's stable. Is it actually better than the attacks we already knew about?"

---

### Slide 32 — Better on two axes — honestly, not all
**ON SLIDE:** Comparison table from Table IV values: IPI, DEVIOUS/IOTLB, this work/DevTLB, and this work/SWQ, across capacity, bit error, keystroke F1, timing deviation, and website results. Footnotes distinguish DEVIOUS’s GPU fingerprints and IPI’s website F1 from accuracy. Closing line: **Best on capacity (DevTLB) and keystroke timing (SWQ) — not on every axis.**

**THE STORY:** "Versus the prior IPI covert channel, DevTLB is about five times the capacity at a quarter of the error — a real jump. And SWQ has the best keystroke timing of anyone here: highest F1 and a five-fold smaller timing deviation. But I'll be the fair referee on three counts. IPI's keystroke F1 — 97.9% — actually *beats* the DevTLB variant's 92%; only SWQ wins that column. DEVIOUS has a *lower* bit-error rate than either of these. And DEVIOUS's 98.9% website accuracy is higher than 85.7% — the paper notes those traces include GPU fingerprints and that the IOTLB channel has since been closed by PASID, which is fair, but it's still the higher number. DSASSASSIN wins on throughput and timing, not on literally every axis. And these are numbers lifted from different papers under different conditions — indicative, not a head-to-head bake-off."

**CONTEXT:**
- **Paper (§VI-F, Table IV):** compares against IPI [51], DEVIOUS [36], and (M)WAIT [65]. The authors claim up to "5× higher throughput and 4× lower bit error rate compared to the state-of-the-art IPI-based channel," top-2 website accuracy (top method "since mitigated by PASID isolation"), and "the highest F1 score and a 5× reduction in timing deviation" for keystrokes. "Blank entries indicate experiments not conducted or reported." Footnote: "The trace collected in DEVIOUS includes GPU fingerprints."
- **The three "fair-referee" facts are read straight from Table IV:** IPI keystroke F1 97.9% > DevTLB 92.0%; DEVIOUS bit error 2.18% < 4.63% and 13.11%; DEVIOUS website 98.9% > 85.7%. Those comparisons are table facts.
- **Not in the paper (framing):** "not on every axis" and "not a head-to-head bake-off" are presenter framing. The paper's own claim is that "all listed attacks operate under comparable settings and assumptions" (§VI-F) — you are gently pushing back on that, so say it's your qualification.

**→ SEGUE:** "So it's real, stable, and competitive. Can we actually fix it?"

---

### Slide 33 — The clean hardware fix costs the thing DSA is for
**ON SLIDE:** Two cards: **DevTLB** — partition replacement state by PASID, with capacity/area/utilization cost; **SWQ** — make queue-state feedback privileged, with legitimate retry handling as the challenge. Closing line: **A defense must constrain interference and feedback, not just permissions.**

**THE STORY:** "The root cause is structural: PASID *tags* the cache entries but doesn't *partition* the structure, and queue-full is a user-visible flag. The clean fix is to partition the DevTLB by PASID, just like the IOTLB already is. The irony: that costs capacity and performance — the exact things DSA exists to provide. And hiding the queue flag collides with the fact that honest submitters legitimately need to know the queue is full. There's no free lunch, and these are sketches, not deployed."

**CONTEXT:**
- **Paper (§VII, Hardware-Level Defenses):** for DSADevTLB, "introduce DevTLB partitioning based on PASID, analogous to the existing protections applied to IOTLB," which "may incur performance and area overhead" but "would provide strong isolation." For DSASWQ, "redesign[] the DMWr completion register as a privileged register, preventing unprivileged eavesdropping of queue state."
- These are *proposals*; the paper does not implement or evaluate either hardware change.
- **Not in the paper:** "costs the thing DSA is for" and "no free lunch" are presenter framing. The paper only says performance/area overhead and that hiding the flag conflicts with legitimate submitters. Don't attribute the sharper phrasing to the authors.

**→ SEGUE:** "Which pushes the burden onto operators today — and here the engine-versus-queue lesson comes roaring back."

---

### Slide 34 — What an operator can do right now
**ON SLIDE:** Table — DevTLB eviction / DSA engine / give sensitive tenants their own *engine*; SWQ feedback / shared queue / don't share SWQs; sensitive path / app / disable DSA. Caption in red: *separate queues do NOT close the DevTLB channel.*

**THE STORY:** "Practical guidance via accel-config: put sensitive tenants on their own *engine* — and I mean engine, not just queue, because — callback to slide 7 — separate queues leave the DevTLB channel wide open. Don't share work queues across trust boundaries. And for the crown-jewel code paths, just turn DSA off and eat the CPU cost. This is the one misconception most likely to bite a real operator, so I say it twice on purpose."

**CONTEXT:**
- **Paper (§VII, Software-Level Defenses):** "both attack primitives rely on access to shared engines or shared work queues," so "tenant workloads handling sensitive data should avoid using DSA configurations that permit resource sharing," achievable "by configuring the `accel-config`." "If exclusive access cannot be guaranteed, tenants may disable DSA acceleration for critical paths."
- **Paper:** "give the tenant its own *engine*, not just its own queue" is enforced by E1 — separate queues on the same engine still leak (§IV-B). That is why the red caption is a paper-grounded warning, not just emphasis.

**→ SEGUE:** "They also evaluate the throughput cost of random translation insertion; distinguish that cost from its effect on leakage."

---

### Slide 35 — They measured the cost — not the leftover leak
**ON SLIDE:** Software defense = inject random DevTLB entries. Max loss 15.7% (native DSA), 17.9% (DTO), at 256-byte transfers. Reuse **Fig. 14**. Caption: *overhead measured; residual leakage NOT measured.*

**THE STORY:** "Their software defense inserts random translations to disrupt the attacker’s observations. The measured throughput loss reaches 15.7% for native DSA and 17.9% for DTO at 256-byte transfers, then decreases for larger transfers. The plot measures performance cost; it does not quantify the leakage left after the mitigation. Keep that distinction in the closing summary."

**CONTEXT:**
- **Paper (§VII, Fig. 14):** "Since no existing mitigation against DSASSASSIN, we implement a software-based DevTLB mitigation to illustrate the associated overhead. The partitioning algorithm periodically inserts random entries into DevTLB to mislead attackers." Overhead measured with dsa-perf-micros and DTO suites, 1,000 iterations, mean. "Performance degradation reaches up to 15.7% with native DSA acceleration and 17.9% with DTO, observed at the minimum tested transfer size (256 B)."
- **The gap is factual, not just opinion:** §VII reports only *overhead* for this mitigation; it reports no residual-leakage measurement for it. So "measured cost, not residual leak" is an accurate description of what the paper does and doesn't contain.

**→ SEGUE:** "The final slide brings together what the experiments establish and the limits of their evaluation."

---

# Conclusion (Slide 36) · about 1 minute

### Slide 36 — Findings and limits
**ON SLIDE:** One closing slide titled **Findings and limits**. Three rows: **Channels** — DevTLB replacement timing + SWQ admission feedback; **Evidence** — controlled page/field/engine tests and four workload demonstrations; **Scope** — provisioned co-location, controlled datasets, and residual mitigation leakage unmeasured. Closing line: **Shared accelerator state belongs in the isolation model.**

**THE STORY:** "The paper establishes two observation paths through shared DSA resources: timing a completion after DevTLB replacement and reading shared-queue admission feedback. Controlled page, field, queue, and engine experiments explain where these signals originate; covert communication, website classification, keystroke timing, and model classification show how applications give them meaning. The claims remain bounded by provisioned device access and co-location, the evaluated datasets and platforms, and a mitigation study that measures throughput cost without quantifying residual leakage. The architectural conclusion is that address-space protection alone does not cover all observable shared accelerator state."

**CONTEXT:**
- **Paper (§IV-B/C):** the field and engine controls locate DevTLB replacement state, while queue experiments establish admission feedback. The separate-engine control prevented the observed cross-VM eviction in the tested setup; this is not a universal isolation proof.
- **Paper (§V-A; §VI-A–D):** the attacker needs access to provisioned DSA resources and the relevant sharing relationship. The four demonstrations cover distinct outputs, including keystroke events/timing rather than recovered text. Website results are closed-world; model classification uses identical prompts and a controlled set of configurations.
- **Paper (§VI-E; §VII):** background PCIe/memory stress is evaluated, but it does not establish behavior under every competing-tenant workload. Random insertion has a reported throughput cost; residual leakage is not quantified.
- **Presenter synthesis:** the final isolation-model sentence is a conclusion drawn from these results. This one slide replaces the former strengths, criticism, proposed-experiments, and verdict sequence.

**→ SEGUE:** "Questions can return to the relevant experiment or the appendix for timing, metric, and reproduction details."

---

# Appendix (Slides 37–43) · use during questions

These seven reference slides are outside the main-talk timing.

### Slide 37 — Glossary
**ON SLIDE:** Acronym table: DSA, ATS/TA, ATC/DevTLB, PASID, WQ/SWQ/DWQ, DMWr/ENQCMD, and DTO.

**THE STORY:** "Use this when a question depends on an acronym. DSA is the accelerator; DevTLB is its translation cache; a work queue admits descriptors; an engine executes them. Keep those roles distinct."

**CONTEXT:** Every term is defined in the paper: DSA (§II-A), ATS/TA and ATC/DevTLB (§II-B), PASID (§I), queues (§II-A/IV-A), DMWr/ENQCMD (§IV-C), and DTO (§VI).

**→ SEGUE:** Return to the relevant main slide or the question being discussed.

---

### Slide 38 — Observation windows have different constraints
**ON SLIDE:** Side-by-side timing constraints, calibration requirements, and confounders for DevTLB and SWQ probes.

**THE STORY:** "The two idle windows have different goals. A DevTLB window must allow a conflicting operation to replace the primed translation. The SWQ window must end before the long anchor copy drains and releases admission capacity. Thresholds and queue state require calibration."

**CONTEXT:** Paper §§V-B/C: DevTLB idle exceeds one relevant DSA operation; SWQ idle is shorter than the anchor copy execution. Other users of the same field or queue can confound attribution. Timer-free admission feedback does not remove the need to control the observation window.

**→ SEGUE:** Return to the relevant main slide or the question being discussed.

---

### Slide 39 — Keystroke count arithmetic needs clarification
**ON SLIDE:** The paper’s keystroke counts beside diagnostic arithmetic: 512 ground-truth events; reported detections/false positives; implied true positives and false negatives; printed inconsistent values.

**THE STORY:** "This is the detailed audit promised on slide 28. Keep the headline F1 values labeled as reported. The arithmetic exposes inconsistent printed counts; it does not reconstruct the missing experimental record or establish corrected performance."

**CONTEXT:** Paper §VI-C reports 512 ground-truth events, detections/FP of 515/15 and 511/7, and other counts that do not reconcile. Diagnostic F1 values around 97.4% and 98.5% are presenter computations. The abstract’s 4.64% covert error also differs from §VI-A/Table IV’s 4.63%.

**→ SEGUE:** Return to the relevant main slide or the question being discussed.

---

### Slide 40 — Sampling and dataset sizes
**ON SLIDE:** Sampling interval, samples per slot, slot duration, trace totals, and train/validation totals for websites and models.

**THE STORY:** "Use this for dataset-scale questions. Website slots aggregate 400 samples into 4 ms; model slots aggregate 800 into 8 ms. An 80/20 split gives 16,000/4,000 website traces and 320/80 model traces from the stated totals."

**CONTEXT:** Paper §VI-B: 10 µs sampling, 100 sites × 200 traces = 20,000. Paper §VI-D: eight models × 50 traces = 400. The split totals are exact arithmetic from the stated 80/20 division. They do not establish a cross-day or cross-host split.

**→ SEGUE:** Return to the relevant main slide or the question being discussed.

---

### Slide 41 — Reproduction requires a configured DSA platform
**ON SLIDE:** Hardware/provisioning, victim-specific software, artifact directory roles, the authors’ GitHub repository, and the Zenodo DOI.

**THE STORY:** "The artifact requires a configured DSA-capable platform with VT-d and the IDXD driver. Website evaluation uses VPP/DPDK; other application cases depend on transparent offload. Provisioning and the victim software are part of reproduction, not steps an arbitrary guest can assume."

**CONTEXT:** Paper §I and Appendix A provide github.com/hkustgz-secarch/dsassassin and DOI 10.5281/zenodo.17799273, with platform and software requirements. Distinguish local reproduction from access to the evaluated cloud configuration; collection time varies with the selected experiment.

**→ SEGUE:** Return to the relevant main slide or the question being discussed.

---

### Slide 42 — Likely questions and concise answers
**ON SLIDE:** Prepared answers about encryption, separate cores/queues, typed-character recovery, removing timers, and the status of the mitigation.

**THE STORY:** "Encryption does not remove activity patterns. CPU-core separation does not partition DSA state. Queue separation addresses SWQ contention, while DevTLB interference requires attention to engine sharing. The paper evaluates keystroke timing/events, not complete typed text. Random insertion has an overhead measurement, not a quantified residual-leakage result."

**CONTEXT:** Answers are grounded in §§IV–VII. The E1 experiment supports the queue-versus-engine distinction; the separate-engine result is scoped to the tested configuration. Removing a duration measurement does not suppress submission-status feedback.

**→ SEGUE:** Return to the relevant main slide or the question being discussed.

---

### Slide 43 — Sources and provenance
**ON SLIDE:** Primary paper citation, author-hosted PDF, artifact repository, archive DOI, and conference record.

**THE STORY:** "The supplied paper is the primary source for the deck. Original diagrams and code excerpts have figure/listing and page citations in the speaker notes and source map. The local asset manifests record extraction provenance."

**CONTEXT:** The paper and artifact/Zenodo references appear in §I and Appendix A. The author-hosted PDF URL i.benx.dev/assets/hpca26dsassassin.pdf and the HPCA conference URL are presenter-supplied provenance links, not claims reproduced from the paper.

**→ SEGUE:** Return to the relevant main slide or the question being discussed.

---

## Delivery notes

- **Useful callbacks:** private addresses versus shared state (slides 2 → 7 → 36); queue versus engine sharing (7 → 13 → 34); measured signal versus application meaning (15/19 → 22–30).
- **Pacing:** finish architecture by about 9 minutes, the mechanisms by about 22 minutes, application demonstrations by about 34 minutes, and the main talk by about 41 minutes. Leave discussion time outside these estimates.
- **Claim discipline:** distinguish measured results, reported headline metrics, and presenter interpretation. Preserve the count-audit caveat on slide 28 and the mitigation-efficacy caveat on slide 35.
- **If time is short:** explain one example trace on slides 24 and 27, then state the numerical result. Keep the two attack sequences and their sharing assumptions explicit.
- **Numbering:** plan slide N = PowerPoint/PDF page N. Main talk ends at slide 36. Appendix occupies 37–43. There are no standalone section-divider slides.

## Paper visual and code source map

The shortened deck retains all **six original paper diagrams** and editable excerpts from **all six code listings**. The snippets occupy five slides because Listings 3 and 4 share one slide. Figure assets are high-resolution crops of the supplied `hpca26dsassassin.pdf`; explanations outside the original artwork are presenter annotations.

| Deck slide | Original paper material | PDF page | Purpose |
|---|---|---:|---|
| 4 | Fig. 1 — DSA architecture | 3 | Follow descriptor submission, engine stages, completion, and translation. |
| 7 | Fig. 7 — cross-VM attack setups | 8 | Compare shared-engine and shared-queue conditions. |
| 9 | Fig. 3 — descriptor format | 4 | Ground address-field roles in their byte offsets. |
| 10 | Fig. 2 — reconstructed microarchitecture | 4 | Show DevTLB organization and queue/arbiter paths. |
| 11 | Listing 2 — three probes | 5 | Establish page granularity and single-slot replacement. |
| 12 | Listings 3 and 4 — field-isolation experiments | 5 | Separate field roles, including src2 versus dst. |
| 13 | Fig. 5 — E0/E1/E2 | 6 | Connect queue/engine placement to measured eviction. |
| 15 | Listing 1, lines 7–12 only | 4 | Show the completion-timing measurement. |
| 17 | Listing 5 — work/batch experiment | 6 | Connect arbiter preference to congestion design. |
| 18 | Listing 6 — congest and probe helpers | 7 | Show the preparation loop and submission probe. |
| 22 | Fig. 8 — VPP packet path | 8 | Connect application traffic to DSA use and the trace. |

Assets and exact source metadata live in `paper_assets/figure_manifest.json` and `paper_assets/code_listings.json`; `extract_paper_assets.py` reproduces the crops. Each relevant slide retains a paper figure/listing and page citation in its speaker notes; the visible bottom footer contains only its page number.

**Code presentation rules:** these are paper excerpts, not complete runnable attack programs. They omit descriptor/completion setup, flags, alignment, memory mappings, device access, and other implementation context. Listing 1’s first timestamp is after `enqcmd`; the printed interval brackets completion polling rather than all submission-plus-completion time. The full listing prints `DSA_OPCODE_COMPVAL` while assigning `src2_addr`; the excerpt excludes that inconsistent initialization. Its source helper is not the final `noop` attack loop. Listing 5 is a separate arbitration/timing experiment, not a universal serialization recipe.

**Interpretation rules:** diagram arrows express causal paths, not cycle-accurate timing. E0/E1/E2 establish the tested engine boundary. Slow probes suggest changed cache state; SWQ feedback reports admission status. Attributing activity requires preparation, calibration, a controlled window, co-location, and workload assumptions. Browser, website, key-event, and model labels are inferred from observations; they are not stored as labels in DevTLB entries.
