# DSASSASSIN — A Talk, Told as a Story

**Paper:** Chen, Li, Deng, Wang, Chen. *DSASSASSIN: Cross-VM Side-Channel Attacks by Exploiting Intel Data Streaming Accelerator.* HPCA 2026.
**Talk length:** 45–60 min. **Audience:** architecture / security researchers who know side channels but **not** DSA.

## How to read this document

This is not a spec sheet. It's the **script of the talk**. For each slide you get four things:

- **ON SLIDE** — the handful of things the audience should *see*.
- **THE STORY** — what you actually *say*, written as narration, not bullet points.
- **CONTEXT** — the background from the paper that makes the story make sense: what the jargon means, where the claim lives in the paper, and which section backs it. Added so you can explain, not just recite.
- **→ SEGUE** — the spoken sentence that *hands off* to the next slide, so the talk never feels like a list of disconnected facts.

**Grounding convention for CONTEXT (read this once):**
- A plain statement or one tagged **Paper:** is drawn from the paper, with the section noted (§I–§IX, Appendix A). Section map: §II-A DSA architecture · §II-B address translation (ATS/DevTLB) · §IV-B DevTLB reverse engineering · §IV-C shared work queue · §V-A threat model · §V-B/§V-C the two primitives · §VI-A covert · §VI-B website · §VI-C keystroke · §VI-D LLM · §VI-E noise · §VI-F comparison · §VII mitigation.
- **Not in the paper:** marks anything that is presenter framing, a metaphor, an outside fact, or a presenter-computed number. If it carries that tag, do **not** present it as the authors' claim. This tag is used deliberately and often — much of the talk's *narration* is framing laid over the paper's *facts*.

**The spine of the whole talk — one sentence you keep returning to:**
> *We built a wall around memory addresses. We forgot that the accelerator behind the wall still has a shared heartbeat — and you can hear it from the other side.*

Everything below is built to deliver that one idea and make the audience feel it tighten, slide by slide.

---

# ACT I — "THE WALL HAS A CRACK" (Slides 1–4) · ~4 min

### Slide 1 — Title
**ON SLIDE:** Paper title, authors (HKUST-GZ · Tsinghua), HPCA 2026, your name, date.

**THE STORY:** "Datacenters are in an arms race to get work *off* the CPU. Networking, storage, dedup, VM migration — all the boring memory-shuffling — is being handed to little accelerators. Intel's Data Streaming Accelerator is one of them, and it ships in every recent Xeon. Today's paper asks a question nobody had asked before: *when you move the work off the core, what happens to the secrets that used to live with it?* This is the first public security analysis of DSA, and the answer is uncomfortable."

**CONTEXT:**
- *What "the secrets that used to live with it" means (you asked about this line).* It is a narrative paraphrase, not a phrase from the paper. Concretely it points at two things the paper does talk about: (1) the **data** those memory operations touch, and more importantly (2) the **activity and timing patterns** of that work. On the CPU, memory operations like `memcpy` are a known source of leakage through caches and TLBs (§II-C). The paper's point is that when the operation is offloaded to DSA, that same observability reappears on the accelerator (§I). So "the secret" = the co-tenant's *activity pattern*, which the attack reconstructs — it never recovers stored data. Say it plainly if asked: "the thing that leaks is *that* work happened and *when*, not the bytes."
- **Paper:** DSA was introduced in Intel's 4th-generation Xeon Scalable processors, codename Sapphire Rapids (§I). It offloads `memset`, `memcpy`, `memcmp`, checksumming (CRC, DIF), and patching (§II-A).
- **Paper:** this is explicitly "the first security analysis of Intel DSA" (§I), and the findings were disclosed to Intel PSIRT, who acknowledged the issue (§I, Responsible disclosure).
- **Not in the paper:** "ships in every recent Xeon" is loose — the paper scopes it to 4th-gen and newer Xeon Scalable (Sapphire Rapids onward), not literally every Xeon. "Arms race" and "secrets" are presenter framing.

**→ SEGUE:** "Let me give you the whole punchline in one picture, before any of the machinery — because once you see it, everything else is just *how*."

---

### Slide 2 — The crack, in one picture
**ON SLIDE:** Two sealed VMs (victim = PASID A, observer = PASID B), each with a private address space, both plugging into one block labeled **"shared engine state / queue occupancy."** Caption: *they can't read each other's memory — but they can feel each other move.*

**THE STORY:** "Here's the setup for the entire talk. Two virtual machines. Intel VT-d gives each its own PASID — its own translation context — so neither can touch the other's memory. That protection is real, and it *does* kill the classic IOTLB attacks. But look at the bottom of the picture. Both VMs are using the *same physical accelerator*, and that accelerator has internal state it does **not** split between them. DSASSASSIN never reads a single byte of victim memory. It just watches the shared accelerator twitch. The lesson, stated bluntly: *confidentiality of addresses is not the same as confidentiality of activity.*"

**CONTEXT:**
- **Paper:** PASID = Process Address Space ID. VT-d in *scalable mode* assigns a PASID per process so each has isolated address translation, which "mitigates traditional IOTLB-based attacks" and enforces PASID-tagged isolation between processes and VMs (§I, §V-A). The paper's whole claim is that this isolation is bypassed at the DSA level (§I, §IX).
- **Paper:** the attack reads only the attacker's *own* signals — its own completion latency (`rdtsc`) or its own submission result (`EFLAGS.ZF`). The DevTLB itself is "assured read-only to devices" (§II-B), so victim data is never read; only the presence or absence of activity is inferred (§III).
- **Not in the paper:** "feel each other move" and "twitch" are the presenter's metaphor. The paper's own words are "infer co-tenant activity" and "leaking usage patterns across VMs" (§III).

**→ SEGUE:** "And 'activity' sounds vague and harmless — so let me show you exactly how un-harmless it is."

---

### Slide 3 — Why you should care: four real leaks
**ON SLIDE:** Four cards — Covert channel **17.19 kbps** (4.63% error); Website fingerprinting **85.73%** (100 sites, 1% baseline); SSH keystroke timing **98.4% F1**; LLM fingerprinting **98.6%**.

**THE STORY:** "That twitch is enough to build a covert channel at seventeen kilobits a second — five times faster and four times cleaner than the best prior cross-VM channel. It's enough to tell which of the top 100 websites a victim VM is loading, 86% of the time, when a coin-flip baseline is one percent. It's enough to time a victim's SSH keystrokes. And it's enough to tell which large language model is running next door. Same humble signal — 'the accelerator is busy' — four very different secrets."

**CONTEXT:**
- **Paper (the exact figures):** covert channel 17.19 kbps true capacity at 4.63% bit error (§VI-A); website fingerprinting 85.73% top-1 on the full 100 sites vs a 1% random baseline (§VI-B); keystroke F1 92.0% (DevTLB) and 98.4% (SWQ), timestamp σ 5.29 ms and 1.21 ms (§VI-C); LLM 98.6% validation accuracy over 8 models (§VI-D).
- **Paper:** "5× faster and 4× more accurate" is the authors' own abstract/§VI-F comparison, and it is specifically against the IPI covert channel [51] — not a claim of beating everything (§VI-F, Table IV).
- *Watch the website number.* 85.73% is the full-100 headline; 96.5% (which you'll see later) is only the 15-site confusion-matrix subset (§VI-B). Keep them separate.
- **Not in the paper:** "humble signal" and "four different secrets" are presenter framing. The number on the slide (98.4%) is the SWQ keystroke F1; the DevTLB keystroke F1 (92.0%) is lower — cite both so no one thinks keystrokes are uniformly ~98%.

**→ SEGUE:** "Now, I'm going to show you all four of these honestly — including which numbers are rock-solid and which I'd argue with the authors about. But to judge them, you need to understand the machine. So here's the plan."

---

### Slide 4 — The map
**ON SLIDE:** 6-act roadmap with time budget. Mark "I'll flag my own opinions in a different color from the paper's claims."

**THE STORY:** "Here's our route. First I'll show you the machine — what DSA is and what the attacker is actually allowed to do. Then the heart of the talk: the reverse engineering, which I'll tell as a detective story, because that's genuinely how it reads. Then the four attacks. Then defenses and how this stacks up against prior work. And finally my own critique — what I trust, what I don't, and what I'd test next. Hold your mechanism questions until after Act III; I promise the picture clicks into place there."

**CONTEXT:**
- The six acts map onto the paper's own structure, which is worth knowing if someone asks "where is X in the paper": §II background, §III motivation and challenges, §IV reverse engineering, §V attack primitives and threat model, §VI the four attacks and evaluation, §VII mitigation, §VIII related work, §IX conclusion, Appendix A artifact.
- **Not in the paper:** the time budget (minutes per act) and the "I'll color-code my opinions" convention are presenter delivery choices, not content from the paper. The act titles ("The wall has a crack", "My verdict", etc.) are the presenter's, not the paper's section names.

**→ SEGUE:** "So — what *is* this accelerator, and why does offloading create a place to spy?"

---

# ACT II — "MEET THE MACHINE" (Slides 5–12) · ~8 min

### Slide 5 — Act 2 divider: Meet the machine
**ON SLIDE:** Dark divider. "02 · Meet the machine" with three lines: What DSA is and how a job flows through it · The device-side translation cache (DevTLB) · The honest threat model — and two kinds of sharing.

**THE STORY:** "Act two. Before we can talk about leaks, we need the machine in front of us — what DSA is, where its cache lives, and what the attacker is actually allowed to do."

**CONTEXT:** A pacing beat, about 15 seconds; nothing new is claimed. **Not in the paper:** the act title and its three lines are the presenter's framing of what follows.

**→ SEGUE:** Advance straight into the next slide.

---

### Slide 6 — Offloading moves the secret, not just the work
**ON SLIDE:** 3-beat flow — common memory ops (memcpy/memset/memcmp/CRC) → DSA offload (descriptor + async execution) → observable state (translation cache + queue). Caption: *move the work, move the side channel.*

**THE STORY:** "DSA is a data mover. Software hands it the dull, bandwidth-heavy jobs — copy this, compare that, checksum this packet — and it does them asynchronously while the CPU does real work. Great for performance. But think like an attacker for a second. For years we've studied how these memory operations leak *on the CPU* — through caches, through TLBs. The industry's fix was partly to *move them somewhere else.* DSASSASSIN's whole premise is that 'somewhere else' is a brand-new, unstudied, shared place to watch. We didn't delete the side channel. We relocated it to a building with no security cameras."

**CONTEXT:**
- **Paper:** DSA is "a high-throughput data mover designed to offload and accelerate memory operations" — `memset`, `memcpy`, `memcmp`, checksumming, patching — which are "common in datacenter applications, storage, networking, deduplication, VM migration, and checkpointing" (§II-A).
- **Paper:** the motivation is that accelerators "bypass the CPU's well-established virtualization protections," and optimization in heterogeneous systems "may unintentionally open side-channel leakage vectors" (§III). Cache/TLB side channels on the CPU are established prior work (§II-C).
- **Not in the paper:** the claim that offloading was done *as a side-channel fix* ("the industry's fix was partly to move them") is **presenter framing** — the paper motivates offloading by performance/CPU-cycle savings, not security. The "building with no security cameras" line is a metaphor. Be careful not to state the authors claimed offloading was a security measure; they did not.

**→ SEGUE:** "To watch it, you have to know how a job flows through it. One job, end to end."

---

### Slide 7 — One job's journey through DSA
**ON SLIDE:** Pipeline (reuse **Fig. 1**): Application prepares descriptor → Portal + Work Queue (submit via MMIO) → Engine (decode→read→compute→write→notify) → Completion. Note work vs. batch descriptors, the arbiter.

**THE STORY:** "Follow one job. Software fills out a *descriptor* — a little form that says 'copy from here to there' — and writes it to an MMIO *portal*. The portal drops it into a *work queue*. An *engine* pulls it off the queue, does the memory work, and writes a *completion record* to tell you it's done. Remember just two things from this diagram, because the entire attack rides on them. One: *did my submission get into the queue, or was it rejected?* Two: *how long until my completion came back?* That's it. Two questions an attacker can ask about its *own* jobs — and the answers leak the neighbor."

**CONTEXT:**
- **Paper (§II-A, Fig. 1):** DSA accepts two descriptor types — *work descriptors* and *batch descriptors*. Software writes them to an MMIO *portal*, which forwards to a *work queue*; queues buffer and dispatch to *engines*. Batch engines fetch descriptors into internal buffers; an *arbiter* selects from either the batch buffer or the work queue. Each unit decodes, reads source, computes, writes destination, and notifies via a completion record or interrupt.
- **Paper:** memory accesses in pipeline stages 2, 3, 5 (read / compute / write) go through ATS — the address-translation path on the next slide (§II-A).
- *The "two handles" framing* is the presenter's distillation, but it is faithful: the paper's two actual observables are the submission result via `EFLAGS.ZF` (§IV-C) and the completion latency via `rdtsc` (§IV-B). Everything later is one of those two.
- **Not in the paper:** "a building with no cameras", "a little form" — presenter phrasing.

**→ SEGUE:** "There's one more component on this diagram I skipped — the thing that makes memory access fast, and the thing that betrays everyone. Let's zoom into it."

---

### Slide 8 — The device keeps its own secret cache: the DevTLB
**ON SLIDE:** Flow (reuse **Fig. 1** right): Device request (VA + PASID) → DevTLB/ATC (hit → reuse; miss → Translation Agent walks page table) → memory. Caption: *the cached translation is locked; its eviction is not.*

**THE STORY:** "To avoid asking the IOMMU for an address translation every single time, DSA caches translations *on the device itself* — the Device TLB, or DevTLB. Here's the subtle part, and it's the key to the whole paper. That cache is *read-only to the device* and it's *tagged by PASID* — so it does **not** leak the contents of a translation. Address confidentiality is genuinely safe. But a cache has a second behavior besides 'what it holds': *what it throws away.* If my neighbor's activity kicks my entry out of the cache, I can't see their address — but I can absolutely tell *they did something.* The paper's first weapon is eviction, not disclosure."

**CONTEXT:**
- **Paper (§II-B):** ATS = Address Translation Services. The device sends a virtual-address translation request to the *Translation Agent* (TA); the TA uses the PASID and context to walk the process's page table; the device receives the physical address, caches it in its DevTLB, and accesses memory directly. The DevTLB is the *Address Translation Cache* (ATC) in the PCIe/DSA specs. Hit → device gets the PA directly; miss → the TA intercepts and translates first.
- **Paper:** "To restrict malicious access, DevTLB is assured of read-only to devices" (§II-B). That is exactly why *contents* don't leak — the attacker can't read entries, only cause and detect *evictions* (§IV-B, Takeaway 2).
- **Not in the paper:** "the paper's first weapon is eviction, not disclosure" is presenter framing, but it is a faithful summary of the §IV-B result.

**→ SEGUE:** "Before I weaponize that, let me be scrupulously fair about what this attacker is and isn't allowed to do — because that's where a lot of accelerator papers quietly cheat, and this one mostly doesn't."

---

### Slide 9 — The honest threat model
**ON SLIDE:** Two columns. *Assumed:* DSA Xeon + IDXD + VT-d scalable mode; victim actually uses DSA; attacker can submit descriptors (`CAP_SYS_RAWIO`); shares the engine (DevTLB) or the SWQ; can set its own affinity (non-root). *NOT needed:* shared CPU core; shared memory; permission to read victim addresses; root / host DSA reconfiguration.

**THE STORY:** "Here's the deal. The attacker is unprivileged in the way that matters: no root, can't reconfigure the host's accelerator, can't read victim memory, and — importantly — does **not** share a CPU core with the victim. This is genuinely cross-core, cross-VM. But I want to be honest where the paper is quietly strong *and* quietly convenient. 'Unprivileged' still assumes the attacker was *provisioned access to the device* and ended up *co-located on the same engine or queue* as the victim. There's even a small tension in §V-A: it first says configuring engine affinity and queue settings needs root, then says choosing an engine or queue affinity does *not* — read that as 'creating queues is root via accel-config; binding to an existing portal isn't.' Co-location is an assumption, not a given, and I'll come back to it in my critique. Hold that thought."

**CONTEXT:**
- **Paper (§V-A):** the attacker runs arbitrary user-space code on Linux (6.11.0-25-generic in their setup) with the Intel IDXD driver, on 4th-gen-or-newer Xeon Scalable with DSA, VT-d in scalable mode. The attacker needs only the `CAP_SYS_RAWIO` capability to submit descriptors; is cross-VM with no shared memory or communication; and can run on a different CPU core. The victim uses DSA for production workloads.
- **The tension, verbatim:** §V-A says the attacker is "not assumed to be capable of configuring engine affinity and work queue settings, since this access to driver requires root privilege." Then §V (p. 8) says "setting DSA affinity to a specific engine or queue does not require root access." The reconciling reading: *creating/configuring* queues via `accel-config` is privileged; *binding* to an existing engine/queue portal is not. The paper calls these co-location assumptions "prevalent among DSA applications [24], [25], [42]" (§V).
- **Not in the paper:** "where a lot of accelerator papers quietly cheat" is presenter opinion.

**→ SEGUE:** "Co-location, though, is more subtle than it sounds — because there are *two* kinds of sharing here, and they are not the same kind of door."

---

### Slide 10 — Two doors, two different locks
**ON SLIDE:** Side by side. *DevTLB channel:* VMs can use **different queues** but the **same engine** → still leaks. *SWQ channel:* VMs must share the **same queue.** Caption in red: *separate queues do NOT save you if the engine is shared.*

**THE STORY:** "This slide is the one I'd tattoo on an operator's arm. The two attacks need two different kinds of sharing. The queue-contention attack needs the victim and attacker in the *same work queue* — fine, that's intuitive, don't share queues. But the DevTLB attack only needs the same *engine.* You can give the two VMs completely separate queues — which an operator would reasonably call 'isolation' — and the DevTLB channel *sails right through*, because the cache lives down at the engine, underneath the queues. If you remember one structural fact from this talk, make it this one."

**CONTEXT:**
- **Paper:** the DevTLB primitive (DSADevTLB) assumes the attacker "has access to a work queue bound to the same DSA engine as the victim's" — queues may differ (§V-B; §VI setup (a)). The SWQ primitive (DSASWQ) requires the attacker and victim to "share the same SWQ but use distinct logical queue entries" (§V-C; §VI setup (b)).
- **Paper (the proof this slide rests on):** experiment E1 — different work queues, same engine — still produces cross-VM eviction, "confirming that DevTLB entries are not indexed by work queue identifiers" (§IV-B). That is the whole basis for "separate queues don't save you."
- This slide is a promise the deck pays off twice more: at the money-shot (Slide 19) and in operator guidance (Slide 44).

**→ SEGUE:** "Everything I've claimed so far — 'the DevTLB isn't partitioned,' 'it's indexed by engine' — I've just asserted. The authors had *zero* documentation to go on. So how do you prove any of it? That's the detective story."

---

### Slide 11 — How do you reverse-engineer a black box?
**ON SLIDE:** Three questions — *What is shared?* (capacity, indexing, PASID) · *What is visible?* (privileged counters vs. user-visible latency/flags) · *What can it reveal?* (eviction→activity, admission→occupancy). Caption: *every claim is a microbenchmark that rules out an alternative.*

**THE STORY:** "There's no datasheet for DSA's internal cache. So the method is pure experimental science. You form a hypothesis — 'maybe the cache has one slot,' 'maybe it's split by PASID' — and you design a probe that would give you a *visibly different* result under each hypothesis. Run it, keep the hypothesis that survives, throw out the rest. The next ten minutes are a chain of these little experiments, and each one eliminates a possibility until only the scary truth is left standing."

**CONTEXT:**
- **Paper (§III, Challenges):** "Their internal characteristics, such as DevTLB capacity, replacement policies, and SWQ management logic, are undocumented and vendor-specific. Fully reverse-engineering these components is necessary." The authors build "a microbenchmark suite" for "the first microarchitectural-level reverse engineering of DSA" (§I, §IV).
- **Paper (an example of the hypothesis-test method):** for the DevTLB they explicitly hypothesize "a set-associative cache with W ways and S sets" and design microbenchmarks to decide W and S (§IV-B). That is the pattern the whole act follows.
- **Not in the paper:** the specific three-question framing ("what is shared / visible / reveal") is the presenter's organizing device, not a structure stated in the paper.

**→ SEGUE:** "One ground rule first, because it's a fair challenge to the whole paper: 'aren't you using privileged performance counters to do all this?'"

---

### Slide 12 — The tools vs. the weapon
**ON SLIDE:** Platforms (Xeon 8468V local, 8475B Alibaba cloud, VT-d scalable, SR-IOV). *Characterization (privileged PMU):* `EV_ATC_ALLOC`, `EV_ATC_NO_ALLOC`, `EV_ATC_HIT_PREV`. *Attack signal (unprivileged):* own completion time (`rdtsc`), `ENQCMD`/`EFLAGS.ZF`. Reuse **Table I**.

**THE STORY:** "Here's the answer, and it matters. To *understand* the hardware, yes, they use privileged performance counters — Perfmon — because that's how you get ground truth about hits and misses. But the *attack itself* never touches those. The attack reads one of two things any user can read: how long its own job took, or whether its own submission succeeded. So the counters are the microscope in the lab; they are not part of the weapon that goes out the door. Keep those two separate in your head for the rest of the talk. And note — they did all of this on both a local server and a real Alibaba cloud instance, which is why the 'does it survive the cloud' question has an answer."

**CONTEXT:**
- **Paper (§IV-B, Table I):** reverse engineering uses Intel Perfmon (a device-level PMU) with three events — `EV_ATC_ALLOC` (# DevTLB requests), `EV_ATC_NO_ALLOC` (# requests that don't trigger replacement), and `EV_ATC_HIT_PREV` (# hits; the primary signal).
- **Paper (the key separation):** "Perfmon is typically accessed via the Linux `perf`, which requires a privileged user. Therefore, we only use Perfmon for benchmarking the DSA. The side-channel attacks are performed by only reading the CPU timer or non-privileged registers" (§IV-B). So the "microscope vs weapon" distinction is the paper's own point, not just framing.
- **Paper (platforms):** local Intel Xeon Platinum 8468V and a public Alibaba Cloud instance on Xeon Platinum 8475B (§IV-B). In the attacks, DSA is virtualized with SR-IOV; SWQ sharing uses Scalable IOV (§VI). Note: the deck's on-slide line says "SR-IOV"; both terms appear — SR-IOV for the overall setup, Scalable IOV specifically for the shared-SWQ scenario.

**→ SEGUE:** "Microscope ready. Let's catch our first fact: what does a descriptor's *shape* have to do with the cache?"

---

# ACT III — "THE DETECTIVE STORY" (Slides 13–27) · ~16–18 min

> *Tell this act with momentum. Each slide is a clue. Keep saying "so now we know…" to show the picture assembling.*

### Slide 13 — Act 3 divider: The detective story
**ON SLIDE:** Dark divider. "03 · The detective story" with three lines: Each microbenchmark rules out an alternative · Five one-entry slots — indexed by engine and field, not PASID · Prime → Idle → Probe   and   Congest → Idle → Probe.

**THE STORY:** "Act three, the detective story. From here on, every slide is an experiment that rules something out, until only one explanation is left."

**CONTEXT:** A pacing beat, about 15 seconds; nothing new is claimed. **Not in the paper:** the act title and its three lines are the presenter's framing of what follows.

**→ SEGUE:** Advance straight into the next slide.

---

### Slide 14 — Clue #1: the opcode chooses which drawer you open
**ON SLIDE:** Four probe descriptors — `noop` (comp only, minimal probe), `memcmp` (src+src2), `memcpy` (src+dst), `dualcast` (src+dst+dst2). Reuse **Fig. 3**. Caption: *the opcode changes what each field means — and which cache slot it touches.*

**THE STORY:** "First clue. The cache isn't indexed by address the way you'd expect. It's indexed by the *role* a field plays in the descriptor — source, second source, destination, second destination, completion record. And the authors can *choose* which roles to exercise by choosing the opcode. A `noop` touches only the completion slot — that's the scalpel: cheapest possible job, cleanest possible timing. `dualcast` lights up four slots at once. By picking opcodes, they get surgical control over which part of the cache they poke."

**CONTEXT:**
- **Paper (§IV-A, Takeaway 2):** the DevTLB "does not use virtual or physical memory addresses to index entries. Instead, it indexes entries by engine ID and field type (e.g., src, src2)." The five field roles are src, src2, dst, dst2, comp.
- **Paper (§IV-B):** the four probe descriptors — `noop` (writes only the completion record), `memcmp`/COMPVAL (reads src + src2), `memcpy` (src + dst), `dualcast` (src → dst + dst2). The descriptor byte layout is Fig. 3; note offset 24 holds *dst OR src2* depending on opcode.
- **Paper:** `noop` is chosen because of "its low execution cost and distinguishable latency between DevTLB hits and misses" (§V-B). "Scalpel" is the presenter's word for that same idea.

**→ SEGUE:** "So the cache has these role-based drawers. Next question: how *big* is each drawer?"

---

### Slide 15 — The reveal: five drawers, one sock each
**ON SLIDE:** Engine 0 with five single-slot entries — src, src2, dst, dst2, comp — each "one page, one slot." Other engines have their own. Reuse **Fig. 2**. Caption: *one slot means one eviction is enough.*

**THE STORY:** "Here's where it's going — I'll show you the proof in a second, but let me spoil it so the experiments make sense. Each engine's DevTLB has exactly five entries, one per field role, and each entry holds exactly *one* translation. One. It's direct-mapped to the extreme. Why is that catastrophic for isolation? Because in a normal cache you need a whole 'eviction set' to kick someone out. Here, *any single different page* in that field role evicts the current occupant. There's no lock to pick — the drawer only fits one sock, so the moment the neighbor puts their sock in, yours is on the floor."

**CONTEXT:**
- **Paper (§IV-A, Takeaway 1):** "each engine's DevTLB consists of five sub-entries corresponding to different fields of the descriptor. As each sub-entry only maintains single slot, it is not isolated by PASID-tag." Confirmed in §IV-B as direct-mapped (W = 1, S = 1).
- **Paper:** accesses from the batch fetcher "are not cached" — the five slots are per *engine's processing unit* (§IV-A). Each engine has its own five slots (E2 later proves the engine boundary).
- **Not in the paper:** "one sock per drawer" and "no eviction set needed" are the presenter's metaphor for the single-slot, direct-mapped result. The underlying fact (single slot ⇒ any conflicting page evicts) is §IV-B.

**→ SEGUE:** "Big claim — 'exactly one slot.' Let's earn it. Experiment one."

---

### Slide 16 — Proof of 'one slot': the base–offset–base test
**ON SLIDE:** 3 steps — probe base → probe base+offset → probe base again. Result: offset < 4 KiB → still a hit; offset ≥ 4 KiB → miss. Reuse **Listing 2**. Caption: *one different page is all it takes.*

**THE STORY:** "Dead simple and completely convincing. Load a translation for a base address. Then touch a second address an 'offset' away. Then come back and check: is base still cached? When the offset stays inside the same 4-kilobyte page, base survives — so the cache works at *page* granularity, it ignores the low bits. But the instant the offset crosses into a different page, base is *gone*. If the drawer held even two translations, base would have survived. It didn't. Therefore: one slot. They even evict a 4K entry using a 2-megabyte huge-page address — so it doesn't even keep separate drawers per page size."

**CONTEXT:**
- **Paper (§IV-B, Listing 2):** probe base → probe base+OFFSET → probe base. With OFFSET < 4 KiB the counter records two hits (same page retained); with OFFSET ≥ 4 KiB, no hit on the final probe. This "confirms that the DevTLB caches translations at the page granularity, ignoring the lower 12 address bits," and the missing final hit "suggests that the DevTLB maintains only a single entry — implying a direct-mapped configuration (W = 1, S = 1)."
- **Paper:** "We also attempt to evict a DevTLB entry corresponding to a 4 KiB page using a conflicting address from a 2 MiB huge page and observe a successful eviction… the DevTLB does not maintain dedicated entries for different page sizes" (§IV-B).

**→ SEGUE:** "One slot per role. But are the roles really *independent* drawers — or does touching the source disturb the destination?"

---

### Slide 17 — Proof the drawers are independent — even when they share bits
**ON SLIDE:** Two mini-experiments. *Independent:* copy(src A, dst D) then copy(src B, dst D) → src evicted, **dst survives.** *Shared encoding, separate slots:* src2 and dst live in the *same descriptor bytes* but map to different slots → no interference. Reuse **Listings 3–4**.

**THE STORY:** "Watch this. Change the source, keep the destination — and the destination's translation is *still there.* So the drawers really are independent; poking one doesn't disturb another. Then the elegant one: the fields `src2` and `dst` are encoded in the *exact same bytes* of the descriptor — the hardware only tells them apart by the opcode. If the cache were lazy and indexed by those raw bytes, they'd collide. They don't. The hardware routes them to separate drawers based on *meaning*, not bit position. That's a remarkably clean result and it's what makes me trust this reverse engineering."

**CONTEXT:**
- **Paper (§IV-B, Listing 3):** `memcpy(src0, dst0)` then `memcpy(src1, dst0)` — a hit on dst0 shows "dst is independently indexed and not combined with src… each field type is indexed into a dedicated sub-entry." `dualcast` (one src, two dsts) varying src while keeping dst/dst2 gives two hits, confirming it.
- **Paper (§IV-B, Listing 4):** src2 and dst "occupy the same bits in the instruction format and are distinguished only by the operation type" (Fig. 3, offset 24). Mapping both to the same page under different opcodes yields "only a single hit… suggesting no interference between src2 and dst." Takeaway 1: all five field types index separate sub-entries, each one slot, no cross-field eviction.

**→ SEGUE:** "One more property of a drawer before we go cross-VM: when a job spans many pages, what does the drawer end up remembering?"

---

### Slide 18 — A drawer remembers the *last* thing, not the history
**ON SLIDE:** One descriptor crossing pages A→B→C→D; only **page D** (last segment) retained in the src slot. Note: the batch fetcher's *own* descriptor reads and completion-record writes *bypass* the cache. Caption: *it's a snapshot of recent state, not a log.*

**THE STORY:** "A big transfer gets split into per-page chunks, and the drawer only keeps the translation for the *final* page it touched. So it's a snapshot of the most recent activity in that role — not a history you can replay. Also useful: the batch-fetcher path and the completion-write path don't populate these drawers at all. For an attacker that's a design note — use ordinary work descriptors to create reliable interference, not batch tricks. We'll cash that in shortly."

**CONTEXT:**
- **Paper (§IV-B, Cross-page behaviors):** "DSA splits cross-page memory transactions into per-page segments" and "the DevTLB caches only the translation for the final page segment of a cross-page transaction."
- **Paper:** "neither the completion record write nor the descriptor reads by the batch fetcher are cached in the DevTLB, revealing that batch fetcher memory requests bypass DevTLB indexing" (§IV-B). This is the precise statement — it is the batch fetcher's *own* reads and the completion-record *write* that bypass, not the work executed inside a batch.
- **Not in the paper:** "snapshot, not a log" is presenter phrasing for the last-page-only result.

**→ SEGUE:** "Now the moment everything's been building to. We've characterized *one* engine's cache. What happens when the attacker and victim are different VMs?"

---

### Slide 19 — The money shot: eviction follows the ENGINE, not the queue
**ON SLIDE:** E0/E1/E2 table. E0: same queue, same engine → **miss** (interference). E1: *different* queue, same engine → **miss** (queue isolation fails!). E2: different queue, different engine → **hit** (no leak). Reuse **Fig. 5**. Caption: *E2 is the control that proves the mechanism.*

**THE STORY:** "Three experiments, two VMs, and the whole thesis lands here. E-zero: share a queue and an engine — the victim evicts the attacker. Fine, expected. E-one — this is the dangerous one: give them *separate queues* but the *same engine.* Still evicted. So the leak has *nothing to do with the queue* and PASID isn't partitioning this cache at all. And E-two is the beautiful part — the *negative control.* Put them on *separate engines*, and the attacker's entry survives. No leak. That control is what turns this from 'we found a bug' into 'we understand the bug': the cache is indexed by engine first, and interference is strictly engine-scoped. Separate engines fix it; separate queues don't."

**CONTEXT:**
- **Paper (§IV-B, Fig. 5):** two VMs (attacker and victim). The attacker primes DevTLB entries with its own addresses, idles; the victim submits a descriptor to evict; the attacker probes. E0 — same engine, shared queue → miss. E1 — same engine, separate queues → miss (so "DevTLB entries are not indexed by work queue identifiers"). E2 — separate engines → hit ("DevTLB entries are not shared across engines").
- **Paper (Takeaway 2):** "The DevTLB is indexed by engine ID and descriptor field type and is not isolated by PASIDs and virtual machines." Indexing is engine-first, then field.
- **Not in the paper:** "negative control" is the presenter's (accurate) term for E2; the paper describes E2 as showing entries are not shared across engines, which is exactly a control.

**→ SEGUE:** "That's the signal in privileged counters. But an attacker in the wild only has a clock. Is the signal still there when all you can do is time your own job?"

---

### Slide 20 — Yes — and the clock still works under noise
**ON SLIDE:** Four latency histograms (Local, Local+Noise, Cloud, Cloud+Noise). Hit ≈ 500 cycles, miss ≈ >1000, threshold ≈ 600–900. Reuse **Fig. 4**.

**THE STORY:** "Here's the attacker's actual view — just `rdtsc` on its own completion. Hits cluster around 500 cycles, misses above 1000. Two clean humps, easy to separate with a threshold. 'But the cloud is noisy,' you say — so they *deliberately* beat up the system: two gigabytes a second of NVMe traffic, ten gigabytes a second of memory copies. The humps shift a bit — about 89 cycles in the cloud — but they never merge. The clock alone, with no privilege, still tells hit from miss. The lab result survives contact with reality."

**CONTEXT:**
- **Paper (§IV-B, Distinguishable latency, Fig. 4):** DevTLB hits "consistently incur around 500 cycles," misses "exceeding 1,000 cycles," separable with "a threshold between 600 and 900 cycles." Measured across Local, Local+Noise, Cloud, Cloud+Noise. Before measuring, "both the page table and IOTLB are warmed up to eliminate their effects."
- **Paper (the noise):** PCIe pressure from "rapidly reading and writing NVMe SSD with 2 GB/s traffic," and memory pressure at "10 GB/s core memcpy bandwidth." "An average shift of 89 cycles in the cloud environment," but "the threshold remains clearly identifiable."

**→ SEGUE:** "We now have everything we need to state the first weapon cleanly. Three steps."

---

### Slide 21 — Weapon #1: Prime → Idle → Probe
**ON SLIDE:** 3 phases — **Prime** (noop caches *my own* comp page) → **Idle** (victim on same engine may evict) → **Probe** (noop again, time it). Fast = nobody moved (0); slow = victim moved (1). Reuse **Fig. 7** red path.

**THE STORY:** "It's Prime+Probe, the classic, but with a twist that makes it almost unfair. I prime a slot using *my own* completion-record address — so I never need to know, guess, or share anything of the victim's. I go quiet. If the victim runs *anything* on this engine, my single-slot drawer gets evicted. I probe by re-running my noop and timing it. Fast means my translation was still there — nobody moved. Slow means it got evicted — the victim moved. One bit of 'is the neighbor alive,' harvested from my own stopwatch."

**CONTEXT:**
- **Paper (§V-B):** three phases. *Prime* — submit a `noop` that writes to a chosen completion-record address, loading it into a DevTLB sub-entry; poll to confirm it is cached. *Idle* — wait longer than a typical DSA op; a victim on the same engine may evict the entry ("if the victim submits a job, a DevTLB eviction occurs (bit 1); otherwise… bit 0"). *Probe* — submit another `noop` to the same completion-record address, record completion time with `rdtsc`, compare to the threshold.
- The attacker only ever primes its *own* completion-record address — it never needs any victim address (§V-B). That is the "almost unfair" part, and it is in the paper.

**→ SEGUE:** "Pause on *why* that's such a clean primitive — because it tells you both its power and its limit."

---

### Slide 22 — Why it's powerful, and what it can't do
**ON SLIDE:** Three bullets — *no address guessing* (prime my own page) · *no eviction-set search* (one slot, one eviction) · *a broad activity signal* (meaning comes later from patterns). Caption: *the primitive gives a heartbeat; the application gives it meaning.*

**THE STORY:** "Compare this to a last-level-cache attack, where half the battle is building eviction sets and aligning addresses. Here the one-slot design *hands* you the eviction for free. That's the power. But be honest about the limit: the raw signal is coarse — it only says 'the engine was busy.' It can't tell you *what* ran. So every real attack you're about to see is really a *pattern-recognition* problem layered on top of this heartbeat. Keep that framing; it's exactly where my later critique bites."

**CONTEXT:**
- **Paper:** the attacker primes its own completion-record page (no victim address) (§V-B); the single-slot structure means a single conflicting page evicts (§IV-B); and "an unprivileged adversary can monitor DevTLB status at engine-level granularity using only noop descriptors" (§IV-B summary) — i.e., the signal is engine-level activity, not addresses or data.
- Every application attack in Act IV is in fact a classifier on top of this binary/activity signal (§VI-B, §VI-C, §VI-D) — so the "heartbeat → meaning" framing is consistent with how the paper structures the attacks.
- **Not in the paper:** the explicit "it gives a heartbeat; the application supplies meaning" slogan and the LLC-attack comparison are presenter framing. The underlying claim (coarse, engine-level activity signal) is grounded in §IV-B. This is the presenter's own setup for the Act VI critique.

**→ SEGUE:** "That's one of the two doors. The second one — the shared queue — behaves completely differently, and at first it looks like a dead end."

---

### Slide 23 — The dead end that wasn't: constant time, but a flag talks
**ON SLIDE:** Submission/completion latency vs. transfer size (reuse **Fig. 6**). Submission ≈ flat ~700 cycles; completion grows with size; queue-full shows up as a **flag**, not a time.

**THE STORY:** "You'd expect a shared queue to leak through timing — submit a job, see if it's slow because the queue's busy. The authors measure it and… submission time is *flat.* Constant. Timing is a dead end. But here's the save: submission uses a special instruction — a Deferrable Memory Write — and when the queue is *full*, the hardware refuses and sets a single CPU flag, `EFLAGS.ZF`. So the queue's fullness leaks not through *how long* but through *yes or no.* It's a timer-free channel. That's actually *better* than timing — no clock noise to fight."

**CONTEXT:**
- **Paper (§IV-C, Fig. 6):** completion latency grows (log-linearly) with transfer size, but "submission latency remains constant at approximately 700 cycles." So timing of submission is not a usable channel.
- **Paper:** DMWr (Deferrable Memory Write) is "a non-posted MMIO write used to signal submission status." On queue saturation, "the DSA communicates failure to the submitter by setting the `EFLAGS.ZF` flag," which "exposes internal queue state without requiring explicit timing measurements" (§IV-C, and Intel spec [23]). Takeaway 3: the ZF flag reveals queue-full without root and without timing.
- **Paper:** contention through ZF "is observed only when the transfer size reaches or exceeds 2^25 bytes" (§IV-C) — this is why the anchor copy must be large (Slide 25).

**→ SEGUE:** "To weaponize 'the queue is full,' you first have to be able to fill it on command — which means understanding how the queue schedules work."

---

### Slide 24 — Learning to hold the queue hostage
**ON SLIDE:** Two paths. *Admission:* portal → per-queue metadata checked at enqueue → constant-time full/not-full. *Execution:* work queue + batch buffer → arbiter, which **always prefers work descriptors over batch.** Reuse **Fig. 2** / **Listing 5**.

**THE STORY:** "Two things the authors had to pin down. First, the fullness check happens at enqueue time against config registers — in constant time — which is exactly why the flag signal has no timing dependence. Second, they reverse-engineer the *arbiter*: they race a work descriptor against a batch descriptor and find the work descriptor always wins, regardless of order. Why do we care? Because it tells the attacker how to hold the queue hostage reliably: use one long ordinary `memcpy` to pin the engine, not a batch trick the arbiter might de-prioritize."

**CONTEXT:**
- **Paper (§IV-A):** the single hardware queue is partitioned into virtual queues via configuration registers; each queue's metadata "is checked against the configuration registers at enqueue time," so "queue occupancy checks and congestion detection occur in constant time." That constant-time check is why the ZF signal has no timing component.
- **Paper (§IV-A / §IV-C, Listing 5):** the undocumented arbiter "prioritizes descriptors from the work queue over those from the batch buffer." They prove it by swapping submission order of a work and a batch descriptor and finding latency unchanged, so "batch descriptors cannot be reliably used for congestion-based attacks." Hence: use an ordinary long `memcpy`.

**→ SEGUE:** "So here's the trap they set."

---

### Slide 25 — The trap: leave exactly one seat open
**ON SLIDE:** Queue of N slots — one LONG COPY anchor + (N−2) fillers → occupancy N−1, one FREE seat. If the victim sits down, the queue is full. Reuse **Listing 6**. Caption: *race the probe against the long copy.*

**THE STORY:** "Picture a theater with N seats. The attacker buys all but one — a long-running copy holds the front row so the queue drains slowly, and filler jobs take the rest. Exactly one seat left. Now the attacker waits. If the victim submits a job, it takes that last seat and the house is full. Two practical details from the paper: the anchor copy has to be *big* — contention only appeared for transfers of 2²⁵ bytes or more, about 32 MiB — and the queue size is readable with `accel-config` without root, so the attacker knows exactly how many seats to buy. The whole thing is a stopwatch-free race against its own long copy finishing."

**CONTEXT:**
- **Paper (§V-C, Listing 6):** the attacker submits "one large `memcpy` descriptor to anchor the head of the SWQ, followed by `wq_size - 2` additional simple descriptors to fully occupy the queue" → effective occupancy wq_size − 1, one free slot.
- **Paper:** "The SWQ size (`wq_size`) can be read without root privileges using `accel-config`" (§IV-C). And the idle window "should be less than the execution time of the memcpy descriptor" so the queue stays near-full (§V-C).
- **Paper:** the large anchor is needed because contention via ZF "is observed only when the transfer size reaches or exceeds 2^25 bytes" (§IV-C) — i.e., 32 MiB. (The "32 MiB" gloss is the presenter's unit conversion of 2^25 bytes; it is exact.)
- **Not in the paper:** the "theater with N seats" is a metaphor.

**→ SEGUE:** "And checking whether the house filled up is a single instruction."

---

### Slide 26 — Weapon #2: Congest → Idle → Probe
**ON SLIDE:** **Congest** (long memcpy + fillers, near-full) → **Idle** (hold the window; victim may submit) → **Probe** (submit once, read `EFLAGS.ZF`). ZF=0 accepted (victim idle); ZF=1 rejected (victim moved). Reuse **Fig. 7** teal path.

**THE STORY:** "Same three-beat rhythm as the DevTLB attack, which is nice for the audience: prepare, wait, probe. Congest the queue to one-from-full. Hold it there. Then try to submit one job and look at the flag. If it went in, the victim stayed still. If it bounced, the victim took the last seat — they're active. No timer anywhere. The virtue is precision; the cost — and I'll hammer this later — is that this attack is *loud.* You're actively congesting a shared resource the victim is trying to use."

**CONTEXT:**
- **Paper (§V-C):** *Congest* — anchor `memcpy` + fillers to near-full. *Idle* — hold the window so the victim may submit to the last slot. *Probe* — `enqcmd` once and inspect `EFLAGS.ZF`: "If ZF is set (ZF = 1), it indicates that the submission failed due to a full queue, implying that the victim has also issued a submission during the idle window. Otherwise, the victim does not submit." Timer-free.
- **Not in the paper:** the "loud / active footprint" judgment is **presenter interpretation** — the paper does *not* evaluate how detectable or disruptive the congestion is. Flag it as your reading, not a measured result.

**→ SEGUE:** "Before we unleash these on real software, let's put them side by side, because they're good at different things."

---

### Slide 27 — Two weapons, two personalities
**ON SLIDE:** Compact comparison — resource (engine vs. same queue); signal (latency vs. flag); prep (prime vs. congest); timer (needed vs. none); footprint (light noops vs. heavy congestion); best at (covert bandwidth vs. keystroke timing). Mark the "footprint" row as *my read.*

**THE STORY:** "DevTLB is the quiet sniper: tiny noop probes, reaches anyone on the same engine, but needs a clock. SWQ is the blunt instrument: it has to actively jam a shared queue, reaches only queue-mates, but needs no clock and gives gorgeous timing. You'll see this personality split in the results — DevTLB wins the raw-bandwidth covert channel, SWQ wins keystroke timing. The 'how loud is it' column is my interpretation, not a table in the paper — I'll flag my opinions like that throughout."

**CONTEXT:**
- **Paper:** resource (DevTLB = same engine, queues may differ, §V-B; SWQ = same queue, §V-C); signal (completion latency, §IV-B; submission success/ZF, §IV-C); timer (DevTLB needs `rdtsc`; SWQ is timer-free, §IV-C); "best at" (DevTLB wins covert capacity 17.19 vs 4.02 kbps, §VI-A; SWQ wins keystroke timing 98.4% / 1.21 ms, §VI-C).
- **Not in the paper:** the **"footprint" row** (light noops vs. heavy congestion) and any detectability claim are **presenter interpretation** — reasonable inferences, but the paper does not report footprint or detectability. The deck labels this row as such; keep that label when you speak.

**→ SEGUE:** "Enough about the weapons. What do they actually *steal?* Let's start with the question every side-channel paper has to answer first: can this thing carry bits at all?"

---

# ACT IV — "WHAT IT STEALS" (Slides 28–39) · ~12–15 min

### Slide 28 — Act 4 divider: What it steals
**ON SLIDE:** Dark divider. "04 · What it steals" with three lines: A covert channel proves the channel carries bits · Websites, SSH keystrokes, and the LLM next door · Strong numbers — quoted honestly, caveats and all.

**THE STORY:** "Act four. We have two weapons. Now the question that matters: what do they actually steal?"

**CONTEXT:** A pacing beat, about 15 seconds; nothing new is claimed. **Not in the paper:** the act title and its three lines are the presenter's framing of what follows.

**→ SEGUE:** Advance straight into the next slide.

---

### Slide 29 — Can it even carry a message? The covert channel
**ON SLIDE:** Phase table — Synchronize (preamble of 1s) · Prepare (prime/congest) · Encode (1→submit, 0→idle) · Decode (time / read flag). Caption: *this proves capacity — not that real apps leak this cleanly.*

**THE STORY:** "A covert channel is the controlled experiment: make the 'victim' a *cooperative* sender and see how fast and cleanly you can move bits. Sender encodes a one by causing activity, a zero by staying idle; receiver reads the heartbeat. A little preamble of ones synchronizes the clocks. This is the capacity test — the cleanest possible conditions. Real victims are messier, and I'll keep that distinction sharp."

**CONTEXT:**
- **Paper (§VI-A):** an "asynchronous time-slicing protocol." As in the prior IPI covert channel [51], synchronization uses a "preamble of several consecutive '1' bits." Then the receiver primes the DevTLB or congests the SWQ; the sender encodes '1' by evicting entries / submitting to a congested SWQ, '0' by idling; the receiver decodes via DevTLB latency or SWQ congestion state.
- A covert channel assumes a *cooperative* sender, so it measures *capacity*, not whether an *oblivious* victim leaks — that distinction is the paper's own framing of why covert channels are "a widely adopted evaluation method… for demonstrating the feasibility of cross-domain leakage" (§VI-A).

**→ SEGUE:** "Under those clean conditions, how fast does it go?"

---

### Slide 30 — 17.19 kbps, and the bandwidth/error tradeoff
**ON SLIDE:** DevTLB **17.19 kbps** / 4.63% error; SWQ **4.02 kbps** / 13.11%. Raw-vs-true-capacity + error curves. Reuse **Fig. 9**. Caption: *push the raw rate too hard and useful throughput collapses.*

**THE STORY:** "DevTLB hits 17.19 kilobits a second at under 5% error — and remember the quiet-sniper personality, light probes pack tightly, so it beats SWQ on bandwidth. Notice the shape of these curves: as you crank the *raw* rate, errors climb until the *useful* throughput peaks and then falls off a cliff. That's why there's a 'best point.' And that 17-and-change is the number that's five times faster and four times cleaner than the prior state of the art. Capacity: proven."

**CONTEXT:**
- **Paper (§VI-A, Fig. 9):** DSADevTLB covert channel reaches "a peak true capacity of 17.19 Kbps with an average bit error rate of 4.63%"; DSASWQ reaches "4.02 Kbps with an error rate of 13.11%." Fig. 9 plots raw capacity vs. true (effective) capacity and error rate — the peak-then-fall shape is why there's an optimum.
- **Paper:** the 5×/4× claim is vs the IPI channel [51] (§VI-F). Note the abstract reports 4.64% while §VI-A and Table IV report 4.63% — a minor internal inconsistency in the paper (use 4.63%, the results-section value).
- *"True capacity" vs "raw capacity"* (ask-me-later): true capacity is the error-corrected effective throughput; raw is the attempted signaling rate (§VI-A, Fig. 9).

**→ SEGUE:** "But a cooperative sender is a toy. The real question is whether an *oblivious* victim leaks. First real target: what website are you browsing?"

---

### Slide 31 — Attack #1: websites leak through the network stack
**ON SLIDE:** Flow — website visit → VPP/memif (DPDK) moves packets with DSA → engine activity → attacker counts DevTLB misses. Reuse **Fig. 8**.

**THE STORY:** "Here's a realistic victim: a VM running VPP, a high-performance userspace network stack built on DPDK, which uses DSA to shuttle packets through shared memory. So every burst of network traffic becomes a burst of DSA activity on the shared engine. The attacker, co-located on that engine, just runs the quiet DevTLB probe and counts evictions over time. It never sees a packet — only the *rhythm* of the accelerator as pages load."

**CONTEXT:**
- **Paper (§VI, §VI-B, Fig. 8):** DPDK is not a standalone system, so the victim runs VPP (Vector Packet Processor), "a high-performance user-space network stack built on DPDK." In VPP, "DSA accelerates packet transfers within the shared memory interface (memif)." The attacker binds to a work queue on the same engine, runs DSADevTLB, and counts DevTLB misses per slot; "an increased number of DevTLB misses within a slot correlates with greater packet arrival activity" (§VI-B).
- The attacker observes only accelerator activity, never packet contents (§VI-B) — "rhythm" is the presenter's word for the per-slot miss count.

**→ SEGUE:** "That rhythm becomes a feature vector — let me show you the actual pipeline so you can judge it."

---

### Slide 32 — The pipeline, laid bare
**ON SLIDE:** Three cards — *Sampling* (probe every 10 µs, 400/slot ≈ 4 ms, feature = miss count) · *Model* (2× BiLSTM + attention + softmax) · *Data* (100 sites × 200 traces, 80/20 ≈ 16k/4k, Chrome 138). Caption in a box: *this is CLOSED-world.*

**THE STORY:** "Each website becomes a time series — roughly 250 slots, each slot just a count of how many times the probe got evicted. Feed that to an attention-BiLSTM, the standard tool for this. I want you to notice one honest word on this slide: *closed-world.* A hundred *known* sites, train and test drawn from the same hundred. That's a legitimate and strong experiment — but it is *not* 'detect any page on the open internet,' and I'll hold the authors to that distinction later."

**CONTEXT:**
- **Paper (§VI-B):** the attacker "samples the DevTLB state every 10 µs and aggregates every 400 samples into a single time slot (approximately 4 ms per slot)," counting DevTLB misses per slot, over 250 slots (Fig. 10). The feature per slot is the miss count.
- **Paper:** the classifier is "an Attention-based Bidirectional LSTM (BiLSTM)" — "two BiLSTM layers, followed by an attention mechanism… and a softmax output layer," with dropout. Dataset: headless Google Chrome 138.0, top-100 Alexa sites, 200 traces each, 80/20 train/test (so 20,000 traces → 16,000 / 4,000).
- **Not in the paper:** the word "closed-world" is the presenter's (accurate) label; the paper doesn't use the term, but its setup — train and test over the same fixed 100 known sites — is closed-world by construction.

**→ SEGUE:** "Does the signal actually look different per site, or is the model hallucinating? Look for yourself."

---

### Slide 33 — The traces really are different
**ON SLIDE:** Example miss-count traces for baidu / apple / microsoft over ~250 slots. Reuse **Fig. 10**. Caption: *shape is the fingerprint.*

**THE STORY:** "Three sites, three visibly different activity signatures — different burst timing, different heights. That's what the model keys on. No URLs, no content — just the silhouette of the accelerator working as the page loads. It's genuinely striking that something this coarse separates sites at all."

**CONTEXT:**
- **Paper (§VI-B, Fig. 10):** the figure shows DevTLB-miss traces across 250 slots for three example sites (baidu.com, apple.com, microsoft.com); "these traces exhibit unique characteristics, which can be leveraged for classification."
- The feature is purely the temporal shape of per-slot miss counts — a proxy for DSA activity during page load (§VI-B). No URL or payload is observed.

**→ SEGUE:** "So how well does it separate all one hundred?"

---

### Slide 34 — 85.73% — and the number you must not misquote
**ON SLIDE:** Full: 100 sites, **85.73%** top-1, 1% baseline. Subset shown in the confusion matrix: **15 sites, 96.5%.** Confusable pair highlighted (canva↔notion). Reuse **Fig. 11**.

**THE STORY:** "On all 100 sites: 85.73% versus a 1% coin-flip. Strong. Now — careful — the gorgeous confusion matrix in the paper is a *15-site subset* at 96.5%, and it is *not* the headline number. Don't let anyone, including yourself, quote 96.5% as the result. The honest headline is 85.73 on the full hundred. The misses are sensible: sites with similar traffic shapes, like canva and notion, blur together — the authors call that out as future work."

**CONTEXT:**
- **Paper (§VI-B, Fig. 11):** "On the full 100-website dataset, our model reaches a top-1 classification accuracy of 85.73%, significantly outperforming random guessing (1%)." The confusion matrix (Fig. 11) is "for a representative subset of 15 websites," on which accuracy is 96.5% — explicitly a subset, not the headline.
- **Paper:** "Relatively lower accuracy for certain domains (e.g., canva.com, notion.com) suggests overlapping traffic patterns… which we leave as future work to refine" (§VI-B).

**→ SEGUE:** "Websites are coarse. Can it get down to something as fine as individual keystrokes?"

---

### Slide 35 — Attack #2: your keystrokes, via transparent offload
**ON SLIDE:** Flow — SSH keypress → OpenSSH mem* calls → DTO transparently offloads to DSA → attacker observes eviction/congestion. Caption in a box: *timing, NOT recovered text.*

**THE STORY:** "This one's eerie. There's a library called DTO — DSA Transparent Offload — that silently redirects ordinary `memcpy`-style calls to the accelerator, *no code changes.* So an unmodified OpenSSH, handling each interactive keystroke packet, quietly generates DSA activity per keypress. The attacker times those. But here's the line I will not let blur: the paper recovers keystroke *timing* — when you typed — and notes that timing *could* feed a downstream text model. It does **not** demonstrate recovering what you typed. Timing, not text."

**CONTEXT:**
- **Paper (§VI, §VI-C):** DTO (DSA Transparent Offload) "relies on the Linux Runtime Linker to intercept and offload standard memory functions (e.g., `memset`, `memcpy`) to DSA" for unmodified applications. When a user types over SSH, OpenSSH "invoke[s] `mem*` routines… to handle packets," which DTO offloads to DSA, "producing measurable side effects in DevTLB or SWQ."
- **Paper (the boundary — state it exactly):** "our attack targets an earlier stage: inferring keystroke *timings* based on DSA activity." Timing "can… infer the text by feeding the dataset to a machine learning model [40]," but end-to-end text recovery is *not* demonstrated (§VI-C). Prior works [40], [55] reconstruct text; this one stops at timing.

**→ SEGUE:** "And both weapons can see those keypresses — here are the raw traces."

---

### Slide 36 — You can see the typing
**ON SLIDE:** Two panels — DevTLB latency trace with threshold, labeled "s s h ␣ r o o t"; SWQ contention trace, same labels + "connection closed." Reuse **Fig. 12**. Note: filtering by DTO byte / latency thresholds.

**THE STORY:** "Top panel, the DevTLB attack; bottom, the SWQ attack — both resolving the individual keystrokes of someone typing 'ssh root.' SWQ gives the crisper spikes, which foreshadows its better timing numbers. One honesty note you'll want for Q&A: events are filtered by byte-size and latency thresholds, so the exact event counts depend on those knobs — which matters for the next slide."

**CONTEXT:**
- **Paper (§VI-C, Fig. 12):** DevTLB (latency, top) and SWQ (contention, bottom) traces captured while typing `ssh root`. "The filter removes the data from our traces if it is labeled as `DTO_MIN_BYTES` (for both attacks) or probed latency ≥ 2,000 cycles (for DevTLB attack)."
- **Paper (the SWQ discovery trick — useful for Q&A):** to find the victim's queue, "one approach is to initiate a temporary SSH connection while concurrently probing candidate SWQs from a separate process" (§VI-C). (Note: this discovery method is shown for the SWQ/SSH case; engine binding for the other attacks is assumed — Slide 48.)

**→ SEGUE:** "So who wins — and here's where I stop being a cheerleader for a moment."

---

### Slide 37 — SWQ wins timing — and a caveat I owe you
**ON SLIDE:** DevTLB 92.0% F1 / 5.29 ms σ; SWQ **98.4% F1 / 1.21 ms σ.** Caveat box: *§VI-C detection counts don't fully reconcile with the printed F1 — see backup.*

**THE STORY:** "SWQ wins keystroke timing cleanly — 98.4% F1 and a 1.21-millisecond timing spread versus 5.29 for DevTLB, exactly what the timer-free design predicts. Use those headline numbers. But I owe you full disclosure: I worked through the paper's own detection, false-positive, and false-negative counts, and they don't perfectly reconcile with the printed F1. It doesn't overturn the conclusion — SWQ is clearly the better keystroke primitive — but a careful reader should know, and I've put the arithmetic in a backup slide. I'd rather you hear it from me than find it yourself."

**CONTEXT:**
- **Paper (§VI-C):** DevTLB F1 92.0%, σ 5.29 ms; SWQ F1 98.4%, σ 1.21 ms. The detailed counts: across 512 ground-truth keystrokes, DevTLB "captures 515 events with 15 false positives and 61 false negatives (500 true positives)," quoted recall 87.8% / precision 97.6%; SWQ "records 511 events with 7 false positives and only 9 false negatives (507 true positives)," recall 98.2% / precision 98.6%.
- **Not in the paper (presenter diagnostic):** those counts don't self-reconcile — 512 ground truth with 500 TP implies 12 FN, not the 61 FN printed; and TP/FP/FN recomputed F1 lands near 97.4% / 98.5%, not the printed 92.0% / 98.4%. This is a *presenter-computed audit* exposing an inconsistency, **not** a correction the paper makes. It doesn't change which primitive is better. Backup slide holds the full arithmetic.

**→ SEGUE:** "Last target, and the most topical: can it tell which AI model your neighbor is running?"

---

### Slide 38 — Attack #3: fingerprinting the LLM next door
**ON SLIDE:** 8 model choices — TinyStories (15M/42M/110M), LLaMA-2 7B, Gemma-3 (1B/4B), Qwen3 (1.7B/4B). Runtimes: llama.c (CPU) + ollama (CPU-GPU). 50 traces/model, identical prompts, 8 ms slots. Reuse **Table II**. Caption: *the label is a config — not weights, not prompts.*

**THE STORY:** "LLM inference constantly shuffles weights around memory, and with DTO those moves hit DSA. Different model sizes and architectures move memory in different rhythms. So the same probe, with a slightly longer 8-millisecond window to match weight-transfer cadence, becomes a model fingerprint. Be precise about the task, though: it's 'which of eight *known* configurations, under *identical* prompts.' Not stealing weights, not reading prompts, not open-world. Distinguishing known configs."

**CONTEXT:**
- **Paper (§VI-D, Table II):** 8 models — TinyStories (15M/42M/110M), Meta LLaMA 2 (7B), Gemma 3 (1B/4B), Qwen3 (1.7B/4B) — run on two runtimes, llama.c (CPU-only) and ollama (CPU-GPU hybrid). 50 traces per model, identical prompts, 80/20 split, 8 ms slots (800 samples) "to align with the timing of model weight transfers."
- **Paper (why it leaks):** LLM inference moves "model weights between CPU and GPU or across memory hierarchies," which "trigger observable DSA activity when offloaded via DTO" (§VI-D). The paper speculates patterns "could be used to infer internal model structure, such as transformer layer depth or model size."
- **Not in the paper:** "no weights or prompts are recovered" is a faithful reading of scope (the paper classifies the model from the trace; it does not claim weight/prompt recovery), but the paper doesn't phrase it as a disclaimer — present it as the correct scoping, not a paper quote.

**→ SEGUE:** "And within that controlled task, the result is almost uncomfortably good."

---

### Slide 39 — 98.6% — impressive, and bounded
**ON SLIDE:** **98.6%** validation accuracy, 8 choices. Traces: TinyStories 15M/42M/110M; Gemma-3 vs. Qwen3-4B. Reuse **Fig. 13**. Caption: *separability in a controlled set; open-world generality is unproven.*

**THE STORY:** "98.6%. The traces differ both across sizes within a family and across families at the same size, so the model picks up both axes. Genuinely impressive that an accelerator twitch distinguishes language models through two VM walls. But keep the fence around it: fixed prompts, fixed runtimes, same host. It proves these configurations are *separable*, not that you could fingerprint an arbitrary model in the wild. That caveat is the bridge into my assessment."

**CONTEXT:**
- **Paper (§VI-D, Fig. 13):** the Attention-BiLSTM classifier "achieves a validation accuracy of 98.6% in predicting the correct model from a given trace." Fig. 13 shows traces differ across sizes within a family (TinyStories 15M/42M/110M) and across families at a size (Gemma 3 vs. Qwen 3).
- **Not in the paper:** "separability, not open-world identification" is **presenter interpretation** consistent with the setup (identical prompts, fixed runtimes, same host, §VI-D). The paper does not test generalization to unseen prompts, runtimes, or hosts — so "open-world generality is unproven" is a scope observation, flagged as yours.

**→ SEGUE:** "Four attacks, all working. Now the three questions a skeptic asks: does it survive the real world, is it actually better than what we had, and can we stop it?"

---

# ACT V — "DOES IT HOLD UP?" (Slides 40–45) · ~6 min

### Slide 40 — Act 5 divider: Does it hold up?
**ON SLIDE:** Dark divider. "05 · Does it hold up?" with three lines: Robust across quiet / noisy and local / cloud · Better than prior work on capacity and timing — not every axis · The clean fix costs the thing DSA is for.

**THE STORY:** "Act five. The three questions a skeptic asks: does it survive the real world, is it better than what we had, and can we stop it?"

**CONTEXT:** A pacing beat, about 15 seconds; nothing new is claimed. **Not in the paper:** the act title and its three lines are the presenter's framing of what follows.

**→ SEGUE:** Advance straight into the next slide.

---

### Slide 41 — It barely flinches under stress
**ON SLIDE:** Matrix across Local / Noisy local / Cloud / Noisy cloud — all six Table III rows (DevTLB covert, SWQ covert, website, DevTLB keystroke F1, SWQ keystroke F1, LLM). Reuse **Table III**.

**THE STORY:** "Across quiet and noisy, local and cloud, most numbers barely move — tight confidence intervals, no collapse. So synthetic PCIe and memory pressure don't save you. The one row worth naming out loud is the DevTLB keystroke F1 — it swings a few points, from 90.5 up to 93.4, and noise or the cloud can even *raise* it. But I want precise language here: what they stressed was *background noise*, not *a dozen real tenants fighting over the same engine.* 'Robust to noise' is proven; 'robust to a busy multi-tenant host' is not the same claim, and I'll put it on the open-questions list."

**CONTEXT:**
- **Paper (§VI-E, Table III):** the four attacks (covert, website, SSH keystroke, LLM) are each repeated 50× to get 95% confidence intervals; x is the geometric mean of the Local (no-noise) run. All six rows now appear on the deck: DevTLB covert 17.19→16.52 kbps; SWQ covert 4.02→3.80 kbps; website 85.7→85.1%; DevTLB keystroke F1 92.0 / 90.5 / 93.4 / 93.0%; SWQ keystroke F1 98.4 / 98.2 / 99.1 / 98.9%; LLM 98.6→98.0%.
- **Paper:** "system noise and PCIe noise negligibly impact the attack performance" (§VI-E). The noise is the same synthetic PCIe + memory pressure as §IV-B.
- **Not in the paper:** "not a dozen real tenants fighting the same engine" is the presenter's precise reframing — the paper stresses *synthetic* noise, not *multi-tenant contention*. That gap is an open question (Slide 49), flagged as your point, not the paper's.
- *The "Local" column* on this slide is the paper's geometric-mean baseline value; the other columns are the reported noisy/cloud runs (§VI-E).

**→ SEGUE:** "Fine — it's stable. Is it actually better than the attacks we already knew about?"

---

### Slide 42 — Better on two axes, honestly not all
**ON SLIDE:** Table — IPI (3.45 kbps / 18.9% / keystroke F1 97.9% / 6.15 ms / website F1 80.4%); DEVIOUS/IOTLB (2.16 / 2.18% / — / 10.08 ms / 98.9%¹); This/DevTLB (17.19 / 4.63% / 92.0% / 5.29 ms / 85.7%); This/SWQ (4.02 / 13.11% / 98.4% / 1.21 ms / —). Footnote: ¹ DEVIOUS traces include GPU fingerprints; its IOTLB channel is since mitigated by PASID. Caption: *cross-paper numbers, not matched re-runs.*

**THE STORY:** "Versus the prior IPI covert channel, DevTLB is about five times the capacity at a quarter of the error — a real jump. And SWQ has the best keystroke timing of anyone here: highest F1 and a five-fold smaller timing deviation. But I'll be the fair referee on three counts. IPI's keystroke F1 — 97.9% — actually *beats* the DevTLB variant's 92%; only SWQ wins that column. DEVIOUS has a *lower* bit-error rate than either of these. And DEVIOUS's 98.9% website accuracy is higher than 85.7% — the paper notes those traces include GPU fingerprints and that the IOTLB channel has since been closed by PASID, which is fair, but it's still the higher number. DSASSASSIN wins on throughput and timing, not on literally every axis. And these are numbers lifted from different papers under different conditions — indicative, not a head-to-head bake-off."

**CONTEXT:**
- **Paper (§VI-F, Table IV):** compares against IPI [51], DEVIOUS [36], and (M)WAIT [65]. The authors claim up to "5× higher throughput and 4× lower bit error rate compared to the state-of-the-art IPI-based channel," top-2 website accuracy (top method "since mitigated by PASID isolation"), and "the highest F1 score and a 5× reduction in timing deviation" for keystrokes. "Blank entries indicate experiments not conducted or reported." Footnote: "The trace collected in DEVIOUS includes GPU fingerprints."
- **The three "fair-referee" facts are read straight from Table IV:** IPI keystroke F1 97.9% > DevTLB 92.0%; DEVIOUS bit error 2.18% < 4.63% and 13.11%; DEVIOUS website 98.9% > 85.7%. Those comparisons are table facts.
- **Not in the paper (framing):** "not on every axis" and "not a head-to-head bake-off" are presenter framing. The paper's own claim is that "all listed attacks operate under comparable settings and assumptions" (§VI-F) — you are gently pushing back on that, so say it's your qualification.

**→ SEGUE:** "So it's real, stable, and competitive. Can we actually fix it?"

---

### Slide 43 — The clean hardware fix costs the thing DSA is for
**ON SLIDE:** DevTLB → partition by PASID (cost: capacity/area/perf). SWQ → make queue-state feedback privileged (challenge: legit submitters need retry info). Caption: *these are proposals, not shipped fixes.*

**THE STORY:** "The root cause is structural: PASID *tags* the cache entries but doesn't *partition* the structure, and queue-full is a user-visible flag. The clean fix is to partition the DevTLB by PASID, just like the IOTLB already is. The irony: that costs capacity and performance — the exact things DSA exists to provide. And hiding the queue flag collides with the fact that honest submitters legitimately need to know the queue is full. There's no free lunch, and these are sketches, not deployed."

**CONTEXT:**
- **Paper (§VII, Hardware-Level Defenses):** for DSADevTLB, "introduce DevTLB partitioning based on PASID, analogous to the existing protections applied to IOTLB," which "may incur performance and area overhead" but "would provide strong isolation." For DSASWQ, "redesign[] the DMWr completion register as a privileged register, preventing unprivileged eavesdropping of queue state."
- These are *proposals*; the paper does not implement or evaluate either hardware change.
- **Not in the paper:** "costs the thing DSA is for" and "no free lunch" are presenter framing. The paper only says performance/area overhead and that hiding the flag conflicts with legitimate submitters. Don't attribute the sharper phrasing to the authors.

**→ SEGUE:** "Which pushes the burden onto operators today — and here the engine-versus-queue lesson comes roaring back."

---

### Slide 44 — What an operator can do right now
**ON SLIDE:** Table — DevTLB eviction / DSA engine / give sensitive tenants their own *engine*; SWQ feedback / shared queue / don't share SWQs; sensitive path / app / disable DSA. Caption in red: *separate queues do NOT close the DevTLB channel.*

**THE STORY:** "Practical guidance via accel-config: put sensitive tenants on their own *engine* — and I mean engine, not just queue, because — callback to slide 10 — separate queues leave the DevTLB channel wide open. Don't share work queues across trust boundaries. And for the crown-jewel code paths, just turn DSA off and eat the CPU cost. This is the one misconception most likely to bite a real operator, so I say it twice on purpose."

**CONTEXT:**
- **Paper (§VII, Software-Level Defenses):** "both attack primitives rely on access to shared engines or shared work queues," so "tenant workloads handling sensitive data should avoid using DSA configurations that permit resource sharing," achievable "by configuring the `accel-config`." "If exclusive access cannot be guaranteed, tenants may disable DSA acceleration for critical paths."
- **Paper:** "give the tenant its own *engine*, not just its own queue" is enforced by E1 — separate queues on the same engine still leak (§IV-B). That is why the red caption is a paper-grounded warning, not just emphasis.

**→ SEGUE:** "They prototype one defense and measure its price — which honestly previews my biggest criticism."

---

### Slide 45 — They measured the cost — but not the leftover leak
**ON SLIDE:** Software defense = inject random DevTLB entries. Max loss 15.7% (native DSA), 17.9% (DTO), at 256-byte transfers. Reuse **Fig. 14**. Caption: *overhead measured; residual leakage NOT measured.*

**THE STORY:** "Their software defense sprinkles random translations into the cache to confuse the attacker, and they honestly measure the cost — up to about 16–18% at small transfers, shrinking as transfers grow. But here's the gap, and it's the perfect transition to my critique: they measured what the defense *costs* but never measured how much leakage it *leaves behind.* So it's an overhead study, not a proven fix. Which raises the real question — how much of this whole paper should we actually believe?"

**CONTEXT:**
- **Paper (§VII, Fig. 14):** "Since no existing mitigation against DSASSASSIN, we implement a software-based DevTLB mitigation to illustrate the associated overhead. The partitioning algorithm periodically inserts random entries into DevTLB to mislead attackers." Overhead measured with dsa-perf-micros and DTO suites, 1,000 iterations, mean. "Performance degradation reaches up to 15.7% with native DSA acceleration and 17.9% with DTO, observed at the minimum tested transfer size (256 B)."
- **The gap is factual, not just opinion:** §VII reports only *overhead* for this mitigation; it reports no residual-leakage measurement for it. So "measured cost, not residual leak" is an accurate description of what the paper does and doesn't contain.

**→ SEGUE:** "Let me take off the narrator hat and give you my own verdict — the good first."

---

# ACT VI — "MY VERDICT" (Slides 46–50) · ~5 min

> *This entire act is explicitly presenter assessment. Say so. The CONTEXT here names which parts rest on the paper and which are your judgment.*

### Slide 46 — Act 6 divider: My verdict
**ON SLIDE:** Dark divider. "06 · My verdict" with three lines: The lasting contribution is the causal hardware analysis · Scope and reporting gaps qualify the headline claims · An isolation contract for shared accelerator state.

**THE STORY:** "Act six. Narrator hat off. Here is my own verdict — the good first, then the pushback."

**CONTEXT:** A pacing beat, about 15 seconds; nothing new is claimed. **Not in the paper:** the act title and its three lines are the presenter's framing of what follows.

**→ SEGUE:** Advance straight into the next slide.

---

### Slide 47 — What's genuinely excellent
**ON SLIDE:** Three strengths — *controlled reconstruction* (page/field/queue/engine, each falsifiable) · *a real negative control* (E2) · *two complementary interfaces* (latency + flag). Caption: *it reframes accelerator state as part of the isolation boundary.*

**THE STORY:** "My honest take: the lasting contribution is *not* the kilobit number — it's the reverse engineering. It's disciplined, it's falsifiable, and it has a genuine negative control in E2, which most exploit papers never bother with. It's the first public look inside DSA, and it reframes 'accelerator internal state' as something your isolation model has to account for. That reframing will outlive the specific numbers. Credit where due — and they disclosed to Intel."

**CONTEXT:**
- **Not in the paper (this whole slide is presenter assessment).** The *judgments* — "the lasting contribution," "disciplined," "will outlive the numbers" — are yours.
- The *facts* those judgments rest on are grounded: the staged microbenchmarks (§IV-B), the E2 negative control (§IV-B), the two observation interfaces — completion latency (§IV-B) and admission flag (§IV-C), "the first public analysis of DSA's microarchitecture" (§I, Contributions), and the responsible disclosure to Intel PSIRT (§I).

**→ SEGUE:** "Now the parts where I'd push back."

---

### Slide 48 — What I'd push back on
**ON SLIDE:** Table — provisioning/co-location → *who can really reach the victim*; closed-world/fixed-prompt → *how far accuracy generalizes*; active congestion → *victim impact + detectability*; metric inconsistencies → *confidence in exact numbers*. Caption: *the leakage is real; the deployment reach is undersold on evidence.*

**THE STORY:** "Four pushbacks. One: the whole thing rests on *co-location* — ending up on the victim's engine or queue. To be fair, the paper does sketch a discovery trick for the SSH case: open a throwaway SSH connection while probing candidate SWQs to find the one that twitches. But binding to the victim's *engine* is simply assumed, and large-scale co-location isn't demonstrated. Two: the classifiers are closed-world with fixed prompts; I don't yet know they generalize to unseen sites, unseen prompts, or another day's traffic. Three: the SWQ attack is *active* — you're jamming a queue the victim needs — so there are performance and *detectability* costs the paper doesn't really evaluate. Four: the keystroke metrics don't fully reconcile. None of this breaks the core finding — shared DSA state leaks activity across VMs, full stop. But it means the *shouting* headline numbers deserve more evidence before you build policy on them."

**CONTEXT:**
- **Not in the paper (presenter critique).** Each pushback is an inference from what the paper *doesn't* do, not a claim the authors make. Anchors so you can defend each one:
  - Co-location: §V-A/§V-B assume the attacker already shares the victim's engine/queue; a discovery method is shown *only* for the SSH/SWQ case (§VI-C), engine binding for the others is assumed.
  - Closed-world / fixed-prompt: website §VI-B (fixed 100 sites), LLM §VI-D (identical prompts) — generalization untested.
  - Active congestion / detectability: the SWQ attack actively congests a shared queue (§V-C); the paper does not evaluate victim impact or detectability.
  - Metric inconsistency: the keystroke count mismatch in §VI-C (Slide 37 / backup).
- The core finding you are *not* disputing — shared DSA state leaks across VMs despite PASID — is the paper's §IX conclusion.

**→ SEGUE:** "Which is really a gift — it's a to-do list. Here's what I'd run next."

---

### Slide 49 — The experiments I'd want to see
**ON SLIDE:** Three tracks (my proposals) — *Isolation* (residual leak + throughput under PASID-partitioned replacement) · *Generality* (cross-day/cross-host, unseen sites/prompts, matched runtimes) · *Deployment* (many tenants, victim latency/retries, probe detectability). Caption: *measure security and performance in the SAME setup.*

**THE STORY:** "If I supervised the follow-up: first, close the loop on that defense — measure leakage *and* throughput together, in one configuration, so we know the real security-performance curve. Second, break the closed world — train on one day, test on another; train on some sites, test on sites never seen. Third, study it under a crowd — many tenants, and measure how loud and how detectable the attacker actually is. These are *my* proposed experiments, not results in the paper — flagged as such."

**CONTEXT:**
- **Not in the paper.** Every experiment on this slide is presenter-proposed future work; the paper does not propose or run any of them. State this clearly — the slide already labels it "presenter-proposed."
- The only hooks the paper itself leaves open: the canva/notion overlap is "left as future work" (§VI-B), and the mitigation's residual leakage is unmeasured (§VII). Your three tracks generalize from those gaps.

**→ SEGUE:** "Let me bring it home to the one sentence we started with."

---

### Slide 50 — The takeaway, and a question for you
**ON SLIDE:** Three lines — (1) engine sharing exposes DevTLB replacement; (2) queue sharing exposes admission feedback; (3) application offload gives those signals meaning. Closing prompt: *what should an accelerator isolation contract actually guarantee?*

**THE STORY:** "So here's where we landed, and it's the sentence I opened with — now earned. We built a wall around addresses with VT-d, and it works. But the accelerator behind that wall has a shared heartbeat — in its translation cache and in its queue — and offloaded applications give that heartbeat *meaning*. As we shove more and more work onto accelerators, our isolation model has to grow to cover their internal state, not just memory addresses. So I'll leave you with the real open question: when a cloud sells you an 'isolated' accelerator, what exactly should that contract be required to guarantee? Thank you — let's discuss."

**CONTEXT:**
- **Paper (§IX, Conclusion):** DevTLB and SWQ "are not isolated by PASID despite VT-d protections"; the attacks work "without privileged access"; "accelerators represent a growing security blind spot in cloud systems"; the findings "show the requirement of stronger isolation mechanisms and new hardware-software defenses." The three on-slide lines map to Takeaways 1–3 (§IV) plus the application attacks (§VI).
- **Not in the paper:** the "shared heartbeat" metaphor and the closing discussion question ("what should an accelerator isolation contract guarantee?") are the presenter's. The paper calls for stronger isolation but does not frame it as an "isolation contract."

**→ SEGUE (to Q&A):** "I've got backup slides on the descriptor format, the metric audit, the full comparison table, and reproducibility — so throw your hardest questions at me."

---

# BACKUP (51–60) — one line each on *why* you'd flip to it, plus the grounding

- **51 — Glossary:** someone's lost in the acronyms. **CONTEXT:** every term is defined in the paper — DSA (§II-A), ATS/TA (§II-B), ATC/DevTLB (§II-B), PASID (§I), WQ/SWQ/DWQ (§II-A, §IV-A), DMWr/ENQCMD (§IV-C), DTO (§VI). Nothing here is presenter-invented.
- **52 — Descriptor byte layout (Fig. 3):** "how do you *know* fields map to slots?" **CONTEXT:** Fig. 3 shows offset 24 = *Destination (dst) OR Source2 (src2)* depending on opcode; the descriptor is PASID-tagged "to prevent other processes from executing it directly" (Fig. 3 caption, §IV-B). The slot mapping (offset → field → DevTLB sub-entry) is from §IV-A/§IV-B.
- **53 — Observation-window constraints:** calibration/timing questions. **CONTEXT:** DevTLB idle must exceed one DSA op so a victim can evict (§V-B); SWQ idle must be *shorter* than the anchor memcpy's execution time to keep the queue near-full (§V-C). All grounded.
- **54 — Keystroke metric audit:** the slide you promised on Slide 37. **CONTEXT:** the detection/FP/FN figures are the paper's (§VI-C: 512 GT; 515/15 and 511/7); the recomputed "diagnostic F1" (~97.4% / 98.5%) and the note that counts don't reconcile are **presenter-computed**, not a paper claim. Also notes the abstract's 4.64% vs §VI-A's 4.63%. Present as a diagnostic that exposes an inconsistency, not a repair of the experiment.
- **55 — Dataset arithmetic:** reproducibility. **CONTEXT:** website — 10 µs sampling, 400 samples/slot, 4 ms/slot, 100 sites × 200 traces = 20,000, 80/20 (§VI-B); LLM — 800 samples/slot, 8 ms, 8 models × 50 = 400 (§VI-D). The split totals (16,000/4,000; 320/80) are exact arithmetic from the stated 80/20.
- **56 — Metric definitions:** "what's 'true capacity' vs 'raw rate'? what's F1 here?" **CONTEXT:** true vs raw capacity is from Fig. 9 / §VI-A. **Not in the paper:** the F1 = 2TP/(2TP+FP+FN) formula and the generic metric glosses are standard definitions supplied for the audience, not stated verbatim in the paper.
- **57 — Full prior-work table (Table IV):** detailed comparison challenges. **CONTEXT:** reproduces Table IV (§VI-F) verbatim; blank cells = "experiments not conducted or reported"; the DEVIOUS GPU-fingerprint footnote is the paper's.
- **58 — Artifact & reproducibility:** hardware, victim software, links. **CONTEXT:** all from §I and Appendix A — github.com/hkustgz-secarch/dsassassin, Zenodo DOI 10.5281/zenodo.17799273, MIT license, Xeon 8468V + Alibaba `ecs.ebmc8i.48xlarge`, ~5 hours total (website collection alone ~a day), needs a DSA-capable Xeon with VT-d/IDXD and privileged setup.
- **59 — Prepared Q&A one-liners:** encryption / separate cores / separate queues / text recovery / timer removal / is the fix proven. **CONTEXT:** each answer traces to §§IV–VII (e.g., "separate queues help? SWQ yes, DevTLB also separate the engines" = E1, §IV-B; "is the fix proven? overhead measured, residual leakage not" = §VII).
- **60 — References & provenance:** citation, author PDF, artifact, HPCA record. **CONTEXT:** the paper citation and artifact/Zenodo links are from §I and Appendix A. **Not in the paper:** the author-hosted PDF URL (i.benx.dev/...) and the HPCA conference-site URL (2026.hpca-conf.org) are presenter-supplied provenance for *this talk's* sourcing, not links that appear in the paper itself.

---

## Delivery notes

- **The three callbacks that make it feel like one story, not 45 facts:** the opening "shared heartbeat" line (slides 1→2→50); "engine, not queue" (slides 10→19→44); "signal is a heartbeat, meaning comes from the app" (slides 22→32→48).
- **Color-code the claim type on every slide:** paper-fact vs. reported-number vs. *my opinion.* Say it out loud when you cross into opinion (slides 27, 37, 47–49). The CONTEXT blocks tell you exactly which is which — anything tagged **Not in the paper:** is where you must signal "this is my reading."
- **Pacing guards:** out of the detective act (through 27) by ~29 min; out of the attacks (through 39) by ~44 min.
- **Never cut:** 2, 10, 19, 21, 26, 50. **Compress verbally if long:** 18, 22, 33, 36, 45.
- **Reusable visuals (build once, re-highlight):** Fig. 1 pipeline, Fig. 2 DevTLB slots, Fig. 7 cross-VM setup.
- **Numbering:** slide numbers in this plan are the deck's page numbers, so plan N = PDF/PPTX page N. The five act dividers are pages 5, 13, 28, 40, 46; backup is pages 51–60.
