# DSASSASSIN: presentation plan and speaking script

**Presenters:** Siddharth Banakar and Dinesh Samala.
**Presentation date:** 29 October 2026.
**Paper:** Ben Chen, Kunlin Li, Shuwen Deng, Dongsheng Wang, and Yun Chen. *DSASSASSIN: Cross-VM Side-Channel Attacks by Exploiting Intel Data Streaming Accelerator.* HPCA 2026.
**Deck:** 25 main slides, with no appendix slides. The final slide is a single evidence-based conclusion.
**Timing:** about 25-30 minutes, excluding discussion. The suggested slide allocations total 29 minutes 5 seconds.

[PowerPoint](output/DSASSASSIN_v3.pptx) | [PDF](output/DSASSASSIN_v3.pdf) | [Read-aloud transcript](TRANSCRIPT_v3.md) | [Transcript PDF for rehearsal](TRANSCRIPT_v3.pdf) | [Structured story data](story_v3.json)

## Presentation plan

| Section | Slides | Subtopics | Suggested time |
| --- | --- | --- | --- |
| Opening | 1-2 | Introduce the paper, the question, and the route through the talk. | 1 min 30 s |
| The system | 3-9 | Why offload and which operations DSA supports; Request execution and IOMMU/VT-d translation; Virtual pages, physical memory, descriptor fields, and sharing. | 8 min 30 s |
| Evidence and attacks | 10-16 | Capacity, field-isolation, and engine experiments; Completion timing and DevTLB probing; Arbitration and shared-queue probing. | 8 min 50 s |
| From signals to inference | 17-20 | Measurements, events, and time windows; Covert communication; Website traffic, traces, and trained labels. | 4 min 40 s |
| Workload results | 21-23 | Keystroke events and timing; Model-configuration classification; Noise experiments and evaluation limits. | 3 min 40 s |
| Mitigations and conclusions | 24-25 | Engine and queue separation; Proposed hardware changes and mitigation cost; What the experiments establish. | 1 min 55 s |

## How to use this plan

The **Speaking script** is written to be spoken directly. Its final paragraph leads into the next slide. The standalone transcript contains only those spoken paragraphs, with matching slide headings. Source references, code walkthroughs, and accuracy notes stay outside the spoken script so they do not interrupt delivery.

The PowerPoint speaker notes use the same transcript from `story_v3.json`. Slide N in this plan corresponds to slide N in the PowerPoint and page N in the PDF. The visible slide footers contain only page numbers. Source citations remain in notes and this plan.

The talk follows one causal path: why offload, how a request is translated and executed, which resource is shared, what the probe observes, and how repeated observations support an application inference. It distinguishes the measured signal from the inferred label and keeps the deployment assumptions explicit.

## Slide-by-slide plan

### Slide 1: DSASSASSIN

**Section:** Opening. **Suggested time:** 45 seconds.

**On slide**

- Paper title and original authors
- Presented by Siddharth Banakar and Dinesh Samala
- 29 October 2026

**Speaking script**

Hi everyone. We're Siddharth Banakar and Dinesh Samala, and today we're presenting DSASSASSIN. The paper studies Intel's Data Streaming Accelerator, or DSA, which moves memory operations away from the CPU.

The question is fairly simple. If two virtual machines share that accelerator, can one learn something about the other's activity without reading its memory? The authors show two ways that this can happen. We'll explain the hardware first, walk through the experiments and code, and then show how those observations become application-level inferences.

**Source:** Chen, Li, Deng, Wang, and Chen. DSASSASSIN, HPCA 2026. Sections I and II, pp. 1-3.

**Context and accuracy notes**

- The paper studies Intel DSA on the evaluated Xeon platforms. Avoid claiming that DSA is present in every recent Xeon.
- The named presenters are distinct from the five original paper authors.

---

### Slide 2: Presentation plan

**Section:** Opening. **Suggested time:** 45 seconds.

**On slide**

- The system: why offload, DSA requests, IOMMU/VT-d translation, and sharing
- Evidence and attacks: field tests, engine controls, DevTLB and SWQ probes
- From signals to inference: activity traces, covert communication, and websites
- Workload results: keystroke events, model configurations, and tested noise
- Mitigations and conclusions: sharing boundaries, proposed defenses, and remaining limits

**Speaking script**

Here's the route we'll take. First, we'll look at why memory operations are offloaded, then follow a DSA request and its address translations. That gives us the pieces we need to understand what the virtual machines share.

Then we'll look at the experiments and the two attacks. After that, we'll follow a probe result into a trace and an inference. We'll finish with the application results, the evaluation limits, and the proposed mitigations. The first question is why these memory operations are being sent to an accelerator at all.

**Source:** Presentation organization based on paper Sections II, IV, V, VI, and VII.

**Context and accuracy notes**

- This agenda is presenter organization, not a separate empirical claim. Slides 1 and 2 introduce the talk; the five sections cover slides 3-25.

---

### Slide 3: Why offload memory operations?

**Section:** The system. **Suggested time:** 80 seconds.

**On slide**

- Free CPU time for application work: bulk operations consume CPU execution cycles
- Asynchronous submission lets the CPU compute while DSA moves or transforms buffers
- Example paths: network buffers, storage, and VM checkpoints
- Operations: copy or dualcast, fill, compare, CRC/DIF integrity work, and delta records
- Submission overhead and memory bandwidth still matter

**Speaking script**

Before we look at the attack, why use DSA at all? A CPU can already copy and compare memory, but moving large buffers repeatedly uses instruction-execution time and ties up cores that could be doing application work.

The program selects these bulk jobs; ordinary CPU loads and stores still execute on the CPU. DSA takes those bulk operations as asynchronous jobs. While it handles a buffer, the CPU can work on something else, provided the program doesn't need that result yet. That can help with network buffers, storage, and virtual-machine checkpoints.

The supported jobs include copies and dualcast, which copies one source to two destinations; filling and comparing memory; CRC checksums and DIF integrity operations; and creating or applying delta records.

There is still submission and completion overhead, so small jobs aren't automatically faster when offloaded. DSA also doesn't create extra DRAM bandwidth. The benefit depends on the operation and workload. The security question is what happens when different tenants share the hardware doing that work.

**Source:** Paper Section II-A, pp. 2-3, and Section IV-B for dualcast; Intel DSA memory-bandwidth optimization article and 4th-generation Xeon OVS-DPDK tuning guide (official links in context).

**Context and accuracy notes**

- DSA is a data-movement and transformation accelerator. Offload can free CPU execution resources and allow independent computation to overlap with asynchronous work; it does not remove memory-bandwidth limits.
- Dualcast copies one source to two destinations. Fill writes a repeated pattern. Compare can compare buffers or compare against a pattern. CRC and DIF operations support integrity generation/checking. Delta-record operations create or apply a representation of changes.
- CRC means cyclic redundancy check. DIF means data integrity field. These are integrity mechanisms, not a claim that DSA performs general encryption.
- Network buffers, storage operations, and VM checkpoints are examples of data-movement workloads. They are motivation and use cases, not three additional attacks evaluated in this paper.
- Submission, queueing, synchronization, and completion processing have costs. Benefits depend on transfer size, batching, parallel work, CPU implementation, and available memory bandwidth.
- The program or offload library selects eligible bulk jobs. DSA does not transparently execute every ordinary CPU load and store.
- Intel explains CPU-cycle relief, asynchronous overlap, and the unchanged peak DRAM-bandwidth constraint in its DSA optimization article: https://www.intel.com/content/www/us/en/developer/articles/technical/accelerate-memory-bandwidth-bound-kernels-with-dsa.html
- Intel's fourth-generation Xeon OVS-DPDK guide explains that descriptor creation and completion waiting can outweigh CPU-copy time for small packets. The crossover depends on the workload and configuration: https://www.intel.com/content/www/us/en/developer/articles/guide/tuning-guide-ovs-dpdk-dsa-4th-gen-xeon-scalable.html

---

### Slide 4: Private addresses can still share hardware

**Section:** The system. **Suggested time:** 60 seconds.

**On slide**

- Two VMs with separate address spaces
- Both submit work to one physical DSA
- Shared engine state and queue capacity remain observable

**Speaking script**

Imagine two virtual machines using the same physical accelerator. Their memory is protected, so the attacker can't simply load an address and read the victim's data. Requests carry an address-space identity, and the translation system checks which memory they may access.

But address permissions don't automatically separate every internal hardware resource. Both VMs may still use the same engine or compete for admission to the same queue. The attacker can submit its own requests and observe whether they were accepted or how long they took to finish.

That's the distinction to keep in mind throughout this talk. The observation is about shared resource activity. Any later claim about a website or a keystroke has to be inferred from that observation. To see where those signals come from, let's follow a DSA request.

**Source:** Paper Sections I, II-B, III, and V-A, pp. 1-3 and 7-8.

**Context and accuracy notes**

- PASID identifies an address-space context; do not equate address authorization with independent replacement capacity.
- The paper's cross-VM setup has no shared memory or direct communication channel between attacker and victim. Covert-channel experiments separately use cooperating sender and receiver roles.

---

### Slide 5: How one DSA request completes

**Section:** The system. **Suggested time:** 75 seconds.

**On slide**

- Original Figure 1: CPU, portal, work queue, engine, memory, and translation path
- Decode, read, compute, write, notify within the original diagram
- Four-step summary: prepare descriptor, submit to portal, execute in engine, write completion
- Submission acceptance and completion are observations of the attacker's own work

**Speaking script**

A program starts by preparing a descriptor. Think of it as a small request record containing the operation, the relevant addresses, and where to report completion. The program submits that descriptor through a portal, and the work queue buffers it for an engine.

On the original diagram, follow the request into the processing unit. The stages are decode, read, compute, write, and notify. The engine may need address translations before issuing memory transactions. Once the work is complete, the completion record tells the submitting program that it can continue.

There are two different moments to observe here. A submission can be accepted before the operation has finished. So the attacker can ask, 'Did my request get into the queue?' It can also ask, 'How long did my request take to complete?' Those become the two channels. First, we need to understand the translations used along this path.

**Source:** Paper Figure 1 and Sections II-A/B, pp. 2-3.

**Context and accuracy notes**

- Figure 1 contains functional stages, not a cycle-accurate instruction schedule. Use the drawn stage names because the prose's numeric stage references are inconsistent.
- The batch fetcher and arbiter select and prepare work within the engine. Their scheduling behavior is revisited with Listing 5.
- Accepted submission does not imply completed operation.

---

### Slide 6: How IOMMU and VT-d protect device accesses

**Section:** The system. **Suggested time:** 100 seconds.

**On slide**

- IOMMU: translates device accesses and checks permissions
- Intel VT-d: the Intel architecture for I/O translation and isolation
- DSA DevTLB: cached page mapping, address-space context, and access permissions
- Miss: ATS request to the host IOMMU; host IOTLB hit or page-table walk; mapping and permissions returned
- Hit: reuse the authorized cached mapping to access a physical page in RAM
- Physical pages hold ordinary source, destination, and completion buffers
- Address permissions remain enforced while shared replacement state can reveal activity

**Speaking script**

Now let's make the address-translation path concrete. An IOMMU translates device memory requests and checks whether those accesses are allowed. Intel VT-d is Intel's architecture for this I/O translation and isolation.

A request is interpreted in its device and address-space context. PASID identifies a process address space within that context; it isn't a globally meaningful identity by itself. The translation maps the requested address to a physical address and supplies the relevant access permissions. Under virtualization, that may involve multiple translation stages rather than one flat lookup.

DSA keeps reusable translations in its device-side cache, the DevTLB. On a hit, it reuses an authorized cached mapping. On a miss, it sends an ATS translation request to the host's Translation Agent, associated with the IOMMU. The host may answer from its IOTLB cache. Otherwise, it may need a page-table walk to resolve the request.

The physical page is simply a region of RAM backing the data, perhaps a source buffer, destination buffer, or completion record. Physical describes its address, not a new type of storage. The DevTLB holds mapping information, context, and permissions, not those bytes or an application name. Let's now look at how many translations each engine retains.

**Source:** Paper Section II-B and Figure 1, pp. 2-3, and Section IV-B, pp. 4-6; Intel Scalable I/O, VT-d, and host-IOTLB documentation (official links in context).

**Context and accuracy notes**

- IOMMU means input/output memory management unit. It translates and authorizes device DMA accesses. DMA means direct memory access.
- Intel VT-d means Intel Virtualization Technology for Directed I/O. It is Intel's I/O translation and isolation architecture, implemented through DMA-remapping hardware; it is not an alternative name for the device-side DevTLB.
- PASID means Process Address Space Identifier. It selects a process address-space context together with the relevant device/translation context; a PASID number alone is not a globally unique identity.
- ATS means Address Translation Services. A device can request an address translation from the host Translation Agent. A successful response provides the translated address and access-permission information that can be cached by the device.
- The IOTLB is the Input/Output Translation Lookaside Buffer in the host translation path. A DevTLB miss does not necessarily cause a page-table walk because the IOTLB may satisfy the translation request.
- A request can be rejected if the mapping or permissions do not allow the requested access. The diagram shows the successful authorized translation path.
- The cached mapping includes relevant context and permission information. The slide is a conceptual path, not a reconstructed bit-level entry format or a claim that every VM has its own replacement capacity.
- A physical page is ordinary RAM viewed by physical address. It can back source data, destination buffers, instructions, or a completion record. Application data lives in those pages, not in the translation-cache entry.
- Virtualized translation can involve multiple stages. The diagram deliberately collapses those stages to explain the device cache, host translation path, and physical memory.
- The paper warms IOTLB and page-table state during DevTLB characterization. Shared replacement capacity can leak activity even when address-space permissions remain enforced.
- DevTLB means Device Translation Lookaside Buffer. In this presentation it is the device-side address-translation cache, distinct from the host IOTLB.
- Intel's Scalable I/O article describes PASID-selected client address spaces, translated host physical addresses, and the ATS path between a device cache and host IOMMU: https://www.intel.com/content/www/us/en/developer/articles/technical/scalable-io-between-accelerators-host-processors.html
- Intel describes VT-d as its I/O virtualization and isolation technology: https://www.intel.com/content/www/us/en/support/articles/000058162.html
- Intel's VTune documentation distinguishes the host remapping hardware and its IOTLB cache: https://www.intel.com/content/www/us/en/docs/vtune-profiler/cookbook/2025-0/analyze-uncore-perfmon-events-for-intel-ddio.html
- Translation permissions are shown as architectural information, not as a reverse-engineered claim about literal DevTLB entry bits.

---

### Slide 7: Five translation slots per engine

**Section:** The system. **Suggested time:** 65 seconds.

**On slide**

- Original Figure 2: reconstructed DSA structure
- Five field roles: src, src2, dst, dst2, comp
- One cached translation per role in the tested implementation

**Speaking script**

The authors reverse-engineered the structure shown here. On their tested hardware, each engine has five translation slots. They correspond to the source, second source, destination, second destination, and completion-record fields. Each slot retains one translation.

That small capacity makes replacement easy to observe. Suppose my completion record is on page A, and its translation is currently in the completion slot. A later completion write using another page can replace it. When I access my own page again, I may have to fetch its translation again, which can make my request slower.

Notice what I haven't learned. I still don't know the other page's address or contents. I have evidence that the shared state changed. Also, this is the organization measured on the tested platforms, not a claim about every possible accelerator design. The next question is how a descriptor selects one of these slots.

**Source:** Paper Figure 2 and Sections IV-A/B, pp. 4-6.

**Context and accuracy notes**

- The five one-entry field slots are an empirical finding. Shared replacement capacity is separate from permission to use another address space's translation.
- For cross-page transactions, the paper reports that only the final page segment's translation remains in the corresponding slot.
- The batch fetcher's own descriptor reads and completion-record writes bypass this indexing path. Distinguish them from engine completion writes used by the NOOP probe.

---

### Slide 8: Descriptor fields select the slot

**Section:** The system. **Suggested time:** 65 seconds.

**On slide**

- Original Figure 3: 64-byte descriptor
- Operation-to-field table with completion writing enabled
- Offset 24 means src2 for compare and dst for copy

**Speaking script**

Here's the descriptor format from the paper. The important point is that the operation determines what each address field means. A copy uses source and destination addresses. A compare uses two source addresses. With completion writing enabled, both also use the completion-record address.

Look at offset 24. For a compare operation, those bytes represent the second source. For a copy, the same bytes represent the destination. The researchers found that these roles use separate translation slots, even though they share a position in the descriptor. We'll see the code that tests that shortly.

A NOOP is especially useful for probing because it avoids moving a payload while still writing a completion record when configured to do so. That gives the attacker a simple way to exercise its own completion slot. Before looking at the experiments, let's make the required sharing conditions explicit.

**Source:** Paper Figure 3 and Section IV-B, pp. 4-5.

**Context and accuracy notes**

- Relevant descriptor offsets are 8 for completion, 16 for source, 24 for destination or second source, and 40 for second destination.
- The operation table uses semantic operation names. Listing 1 prints DSA_OPCODE_COMPVAL in a helper described as a two-source compare; the slides do not silently treat that constant as a verified two-buffer compare encoding.
- NOOP probing depends on completion-record setup and flags. Those prerequisites are omitted from the short printed listings.

---

### Slide 9: The sharing assumptions for each channel

**Section:** The system. **Suggested time:** 65 seconds.

**On slide**

- Original Figure 7: cross-VM sharing setup
- DevTLB channel: same engine, possibly different queues
- SWQ channel: same shared work queue
- Provisioned DSA access, co-location, and CAP_SYS_RAWIO submission capability

**Speaking script**

The two channels require different kinds of sharing. For the translation-cache channel, the attacker and victim need access to the same engine. Their work queues can be different. For the queue channel, they need to share the same shared work queue, or SWQ.

These are assumptions about the deployment. The paper gives the attacker provisioned access to DSA and explicitly requires the CAP_SYS_RAWIO capability for descriptor submission. It doesn't give the attacker authority to reconfigure the host's engines and queues. So we shouldn't describe this as an attack available to every ordinary process by default.

Within that setup, the VMs don't share memory, and the attack doesn't require a shared CPU core. The attacker observes its own submissions and completions. With those conditions clear, we can look at the experiments that establish the cache's capacity and sharing boundary.

**Source:** Paper Figure 7 and Section V-A, pp. 7-8.

**Context and accuracy notes**

- Section V-A explicitly names CAP_SYS_RAWIO. Provisioning and submission capability must remain visible in the threat model.
- The paper distinguishes privileged queue/engine configuration from use of an existing binding, but its affinity wording is not fully consistent. Treat engine/queue co-location as an assumption rather than a universally available operation.
- Figure 7 includes both sender/receiver and attacker/victim role labels. These refer to covert-channel and side-channel cases, not four mandatory simultaneous processes.

---

### Slide 10: One conflicting page can replace a slot

**Section:** Evidence and attacks. **Suggested time:** 75 seconds.

**On slide**

- Editable Listing 2: base, base plus OFFSET, base
- Within one 4 KiB page: reuse hit
- Different page: replacement and final miss

**Speaking script**

This is the capacity experiment. The first call uses base and puts its translation into the tested slot. The second call uses base plus an offset. The third call returns to base so the researchers can check whether its translation survived.

When the second address stays within the same four-kilobyte page, the final access reuses the translation. When it moves to another page, the final access misses. Across their experiments, that behavior supports a single cached entry for the field: one conflicting page is enough to replace it.

For the NOOP helper, base means the completion-record address. It isn't a victim buffer that the attacker somehow knows. The code shown here is a short experimental excerpt, so the descriptor setup and completion flags aren't included. This establishes capacity within a field. Next, we need to check whether different fields share that same entry.

**Code walkthrough for preparation**

1. probe_noop(base): establish the attacker's completion-page translation.
2. probe_noop(base + OFFSET): test a same-page or conflicting-page access.
3. probe_noop(base): observe whether the original translation was retained.

**Source:** Paper Listing 2 and Section IV-B, p. 5.

**Context and accuracy notes**

- The paper also reports eviction of a 4 KiB translation by an address on a 2 MiB huge page, suggesting no separate per-page-size entries in the tested structure.
- Do not claim that one three-call observation alone proves an arbitrary cache's entire organization. The conclusion follows from the reported characterization suite.
- Listing 2 is a microbenchmark excerpt, not a complete runnable attack.

---

### Slide 11: Source and destination use separate slots

**Section:** Evidence and attacks. **Suggested time:** 80 seconds.

**On slide**

- Editable Listings 3 and 4
- Change source while retaining destination
- Reuse a page across src2 and dst roles
- Observed reuse follows field meaning

**Speaking script**

The first listing asks whether changing the source also destroys the destination's cached translation. It copies from one source to a destination, then changes the source page while keeping the destination the same. The destination still contributes a hit. That tells us the source and destination have independent cached state.

The second listing tests the overlapping descriptor position we saw earlier. It compares two buffers, then performs a copy. The second source from the compare and the destination from the copy are placed on the same page. If those two roles shared an entry, that page could provide a reuse hit in the copy.

Instead, the reported reuse comes only from the unchanged source role. The second-source translation doesn't act as a destination translation. So it is the field's meaning that matters, not just the address or its byte position in the descriptor. Now we can test which engine shares those slots.

**Code walkthrough for preparation**

1. Listing 3 first checks that source and destination are on different pages, primes with probe_memcpy(src0, dst0), then changes only the source to src1.
2. Listing 4 calls probe_memcmp(src, src2), then probe_memcpy(src, dst), with src2 and dst on the same page. The unchanged source supplies the reported reuse hit.

**Source:** Paper Listings 3 and 4, Figure 3, and Section IV-B, p. 5.

**Context and accuracy notes**

- The paper extends the independence test to dualcast, retaining two destination hits while changing the source.
- Listing 4 reports one hit from src rather than the two hits expected if src2 and dst shared an entry.
- These printed helpers omit descriptor initialization and other execution setup. Preserve their original text and semantic operation names.

---

### Slide 12: Eviction follows the shared engine

**Section:** Evidence and attacks. **Suggested time:** 70 seconds.

**On slide**

- Original Figure 5: E0, E1, and E2
- E0: same queue and engine, miss
- E1: different queues but same engine, miss
- E2: different engines, hit

**Speaking script**

The authors now move from one engine's behavior to interference between two virtual machines. They run three configurations shown in the original figure.

In E0, both sides use the same queue and engine. The attacker's primed translation is replaced, so its later probe misses. In E1, they use different queues but still reach the same engine. The probe still misses. Queue separation alone hasn't separated the translation-cache state.

E2 changes the engine as well. This time, the primed translation survives and the probe hits. That's the control that ties the observed interference to the shared engine. It supports a concrete boundary in the tested configuration; it isn't a guarantee about every accelerator or every deployment.

These characterization experiments explain what is shared. The next question is whether an attacker can recognize a hit or miss using a signal available from its own code.

**Source:** Paper Figure 5 and Section IV-B, p. 6.

**Context and accuracy notes**

- E0 and E1 report cross-VM eviction; E2 is the separate-engine control.
- Engine sharing is a requirement of the measured DevTLB channel. Sharing alone does not guarantee that every probe will detect a victim operation.
- Separate queues can still share engine-local replacement capacity.

---

### Slide 13: How a probe distinguishes a hit from a miss

**Section:** Evidence and attacks. **Suggested time:** 70 seconds.

**On slide**

- Original Figure 4: completion-latency distributions
- Hits around 500 cycles; misses above 1,000 cycles
- Reported threshold range: 600-900 cycles
- Timing is an inferred cache-state observation

**Speaking script**

The attacker doesn't get a message saying which cache entry the victim touched. It measures the time taken by its own request. In the paper's measurements, requests whose translations hit cluster around five hundred cycles. Misses take more than a thousand cycles.

That separation lets the attacker choose a threshold and classify a probe as likely hit or likely miss. The authors report thresholds between six hundred and nine hundred cycles in these experiments. Those are measured values for their setup, not universal constants to copy onto any machine.

The figures also include local and cloud runs with background load. The distributions move, but remain distinguishable in those tests. Performance counters help the researchers characterize the hardware; the attack's observation is its own completion timing. A single slow request still has possible competing explanations. Repeated, calibrated measurements are what make the next attack sequence useful.

**Source:** Paper Figure 4 and Section IV-B, pp. 5-6.

**Context and accuracy notes**

- The injected stressors include approximately 2 GB/s of NVMe/PCIe traffic and 10 GB/s of CPU memory-copy traffic.
- A miss classification is inferred from completion latency. It is not direct access to victim addresses or to a hardware victim-hit log.
- The paper uses privileged characterization counters to investigate structure; those counters are not the attacker-facing timing signal.

---

### Slide 14: DevTLB attack: prime, wait, probe

**Section:** Evidence and attacks. **Suggested time:** 80 seconds.

**On slide**

- Prime the attacker's own completion page, wait for activity, and time the next probe
- Editable Listing 1 timing excerpt, lines 7-12
- ENQCMD returns before RDTSC starts the completion-polling interval
- Listing 1 times a compare helper; the NOOP attack reuses the timing pattern

**Speaking script**

Now we can put the attack together. First, I submit a completion-enabled NOOP using my own completion page. That primes the completion slot. Then I wait while the victim may run on the same engine. Finally, I submit another probe using my page and time its completion.

The code excerpt shows the timing pattern. ENQCMD submits the descriptor first. The first timestamp comes after that submission. The loop waits for the completion status to change, and the second timestamp ends the measurement. Subtracting the two gives the polling interval shown here.

There's an important source detail: this excerpt comes from the paper's compare helper. The attack uses NOOP with this timing approach; the slide isn't claiming that the displayed excerpt is its complete implementation. A fast probe suggests retention, while a slow probe suggests replacement. We now have an activity signal. The other channel uses queue admission feedback instead of a duration.

**Code walkthrough for preparation**

1. enqcmd(wq_portal, &desc): submit the descriptor.
2. start = rdtsc(): start timing after submission returns.
3. while (comp.status == 0): poll the completion record.
4. end = rdtsc(); return end - start: measure the shown completion-polling interval.

**Source:** Paper Listing 1, lines 7-12, p. 4; DevTLB attack in Section V-B, p. 8.

**Context and accuracy notes**

- Listing 1's complete helper prints DSA_OPCODE_COMPVAL while using two source-address fields. The displayed timing excerpt avoids presenting that inconsistent initialization as a verified recipe.
- The timer begins after ENQCMD and therefore does not measure the whole interval from before submission.
- Completion-record association, flags, initial status, alignment, mapping, and ordering/error-handling details are not provided by this excerpt.
- A slow sample alone does not identify who caused a delay. Co-location, preparation, calibration, and the observation window support the inference.

---

### Slide 15: Why use a long ordinary copy?

**Section:** Evidence and attacks. **Suggested time:** 70 seconds.

**On slide**

- Editable Listing 5: batch/work arbitration experiment
- Swap the two submissions and measure ordinary-work completion latency
- Observed preference: ordinary work over batch work
- A long ordinary copy anchors the congestion attack

**Speaking script**

To observe queue contention, the attacker needs to keep work outstanding long enough to create an observation window. A batch might seem like an easy way to do that, but its scheduling priority matters.

In this experiment, the authors submit a batch descriptor and an ordinary work descriptor to the same queue. The fence separates the submissions, and the code times completion of the ordinary work. They repeat the experiment after swapping the two submission positions.

The ordinary work's completion latency stays nearly unchanged. Together with the other tested cases, that supports a preference for ordinary work over batch-buffer work. A batch therefore isn't a reliable way to hold up the ordinary requests the attacker wants to observe.

This listing is a scheduling experiment, not the congestion attack itself. Its result explains the next design choice: use one long ordinary copy to keep the queue busy during the probe window.

**Code walkthrough for preparation**

1. Submit batch_desc, execute _mm_sfence(), then submit desc and start timing.
2. Poll desc_comp.status and compute the elapsed duration.
3. Swap the positions of the batch and ordinary-work submissions and compare ordinary-work completion latency.

**Source:** Paper Listing 5 and Section IV-C, pp. 6-7.

**Context and accuracy notes**

- The comparison includes ordinary work alone, alongside batch work, and with the two submissions reordered.
- The fence and timestamps belong to this microbenchmark. Do not describe Listing 5 as the Listing 6 congestion loop.
- The measured work-over-batch preference is an observation about the tested implementation, not a universal DSA scheduling specification.

---

### Slide 16: SWQ attack: fill, wait, probe

**Section:** Evidence and attacks. **Suggested time:** 85 seconds.

**On slide**

- Editable Listing 6: congestion and submission-probe helpers
- One long copy plus N minus 2 fillers
- Aim for N minus 1 occupied positions during the window
- ZF=0: accepted; ZF=1: retry/full in this experiment

**Speaking script**

Here is the second attack. The first submission is the long copy. The loop then submits queue-size minus two additional descriptors. The aim is to keep the queue near full while leaving one admission opportunity during the observation window.

The attacker waits, giving the victim a chance to submit. Then the probe helper tries to submit one more descriptor. This time the observation is the submission result. A zero ZF means the request was accepted. A set ZF means retry, corresponding to a full queue in this experiment.

Under the prepared conditions, a retry is evidence that another submission consumed the remaining capacity. It isn't proof of a particular victim operation by itself. Work can drain, and other activity can interfere, so the window must stay controlled and shorter than the anchor copy's execution.

The paper observed contention with copies of at least thirty-two mebibytes. The signal needs no duration measurement, but it actively congests a resource the victim also uses.

**Code walkthrough for preparation**

1. congest(wq_size) first enqueues mass_desc, the long ordinary copy.
2. The loop starts at 1 and stops before wq_size - 1, adding wq_size - 2 filler descriptors.
3. probe() returns the result of its own ENQCMD submission, which exposes acceptance or retry feedback.

**Source:** Paper Listing 6, p. 7; Sections IV-C and V-C, pp. 6-8.

**Context and accuracy notes**

- One anchor descriptor plus wq_size - 2 fillers targets N - 1 outstanding positions. Treat this as a controlled observation model, not a guarantee that occupancy stays fixed while the queue drains.
- The printed helper's nonzero return corresponds to retry/full feedback in this experiment. An accepted request is not a completed request.
- The 32 MiB value is the paper's characterized threshold, not a universal hardware requirement.
- Descriptor setup, alignment, initial completion state, error handling, and retry policy are omitted from the short listing.
- The victim-performance cost and detectability of active congestion are not fully evaluated.

---

### Slide 17: From a probe result to an inference

**Section:** From signals to inference. **Suggested time:** 70 seconds.

**On slide**

- Own measurement: completion duration or submission result
- Calibrate likely misses or contention events
- Aggregate observations over time
- Infer task-specific activity using labeled examples or event analysis

**Speaking script**

At this point, neither channel has produced a website name or a character. The raw data is much simpler: a duration from my request, or an accepted-or-retry result from my submission.

The next step is to turn those measurements into a time series. For the timing channel, a calibrated threshold marks likely misses. The attacker can count those events within fixed windows and record how the counts change over time. Queue feedback can likewise reveal when contention appears.

The meaning comes from the workload and the analysis. In a classification experiment, the attacker first collects examples with known labels and trains a model to recognize their patterns. Keystroke timing instead looks for candidate events and their timestamps.

So the hardware never tells the attacker, 'This is a browser.' The experiment supplies that context, and the analysis supplies the inferred label. We'll first see a cooperative communication test, then the application cases.

**Source:** Presenter explanation connecting paper Sections V-B/C and VI-A/D, pp. 8-11.

**Context and accuracy notes**

- Distinguish raw observation, event classification, feature aggregation, and application inference.
- Website and LLM classification require known labeled workloads in the evaluated datasets. A single hit or miss does not identify a website or model.
- Keystroke-event detection and timestamp estimation are different tasks from identifying the typed symbols.

---

### Slide 18: Covert communication through shared state

**Section:** From signals to inference. **Suggested time:** 60 seconds.

**On slide**

- Original Figure 9: capacity and error tradeoff
- DevTLB: 17.19 kbps, 4.63% bit error
- SWQ: 4.02 kbps, 13.11% bit error

**Speaking script**

A covert channel is a controlled communication experiment. Here, the sender cooperates with the receiver: it creates activity to represent one bit value and stays idle to represent the other. The receiver uses its probes to decode those changes.

The reported DevTLB channel reaches seventeen point one nine kilobits per second, with four point six three percent bit error. The SWQ channel reaches four point zero two kilobits per second, with a higher error rate.

The plot shows why increasing the raw signaling rate doesn't always help. Faster signaling can create more errors and reduce useful capacity. This establishes a communication channel under coordinated conditions. Next, the sender stops cooperating: ordinary website traffic becomes the source of activity.

**Source:** Paper Figure 9 and Section VI-A, p. 9; comparison values in Table IV, p. 12.

**Context and accuracy notes**

- These are reported true-capacity values, distinct from raw attempted signaling rate.
- Use 4.63% as in Section VI-A and Table IV. The abstract/contribution text also contains 4.64%, a reporting inconsistency.
- The covert channel uses cooperating sender and receiver roles, unlike the non-cooperative application side-channel cases.
- The approximately fivefold capacity comparison is against the IPI covert channel; cross-paper values are not matched reruns.

---

### Slide 19: Why website traffic reaches DSA

**Section:** From signals to inference. **Suggested time:** 65 seconds.

**On slide**

- Original Figure 8: host, VPP/memif, victim VM, and spy VM
- Packet movement generates DSA work
- The spy observes effects on shared-engine translation state

**Speaking script**

This figure connects the hardware channel to the website experiment. The victim application runs in one VM, and the spy runs in another. The network path uses VPP and memif, with DSA accelerating packet movement.

Loading a website creates a sequence of network transfers. Those transfers generate accelerator work, and that work can replace translations in the engine the spy shares. The spy continues to measure its own probes, so the resulting trace reflects changes in accelerator activity over time.

There is no packet payload, URL, or browser-process name in that observation. The attacker knows the experimental task is browsing and has collected examples from known websites. That context is what lets a later classifier associate a trace with a site.

Now let's look at how the paper builds those features and what its accuracy numbers actually describe.

**Source:** Paper Figure 8, p. 8, and Section VI-B, pp. 9-10.

**Context and accuracy notes**

- Figure 8 places the DSA spy in VM2 and victim applications in VM1. The setup uses DSA-accelerated VPP/memif packet movement.
- The diagram is the evaluated network configuration, not a claim that every browser or network stack uses DSA.
- Website identity is a trained label assigned from activity traces. The attacker does not read packet contents or directly discover the browser from the DevTLB.

---

### Slide 20: How a trace becomes a website label

**Section:** From signals to inference. **Suggested time:** 85 seconds.

**On slide**

- Original Figure 11: selected 15-site confusion matrix, 96.5% accuracy
- 85.73% full-dataset accuracy across 100 sites; 20,000 traces and an 80/20 split
- 10 microsecond samples, 400 samples per 4 ms bin, 250 bins per trace
- Attention-BiLSTM classifier

**Speaking script**

The spy samples every ten microseconds and groups four hundred samples into a four-millisecond slot. Each slot records a miss count. About two hundred and fifty slots form a trace, so the feature is the pattern of activity across roughly a second.

The dataset contains one hundred websites with two hundred traces per site, giving twenty thousand traces. The authors use an eighty-twenty training and test split and an attention-based bidirectional LSTM to map those traces to website labels.

The headline result is eighty-five point seven three percent on all one hundred sites. The confusion matrix shown here covers only fifteen selected sites, where the reported accuracy is ninety-six point five percent. Those are different evaluation scopes.

This is a closed-world task: training and testing use the same known set of website labels. It doesn't establish recognition of arbitrary unseen websites. The next application uses the timing of individual events rather than a whole-page loading pattern.

**Source:** Paper Figures 10 and 11 and Section VI-B, pp. 9-10.

**Context and accuracy notes**

- A random top-1 guess over 100 equally weighted labels has a 1% baseline; do not call it a coin flip.
- 20,000 traces and the 16,000/4,000 split are arithmetic from the stated dataset and split ratio.
- The displayed confusion matrix is the 15-site subset, not a visualization of the full-100-site headline accuracy.
- The evaluated split does not establish cross-day, cross-host, or open-world generalization.

---

### Slide 21: Keystrokes reveal events and timing

**Section:** Workload results. **Suggested time:** 85 seconds.

**On slide**

- Original Figure 12: filtered DevTLB and SWQ traces
- Visible workload chain: SSH packets, DTO offload, DSA activity
- DevTLB: 92.0% F1 and 5.29 ms timestamp deviation
- SWQ: 98.4% F1 and 1.21 ms timestamp deviation
- The letters are known input labels, not characters decoded from the probe
- Headline F1 values are reported as printed; event counts in the paper are inconsistent

**Speaking script**

For the SSH experiment, the victim uses DSA Transparent Offload, or DTO. It redirects eligible memory operations to DSA, so handling interactive SSH traffic can generate accelerator activity. The attacker looks for that activity and estimates when candidate keystroke events occurred.

The plots are filtered traces. The letters shown on them are known input labels used to evaluate the experiment. They are not characters decoded from the cache. The demonstrated result is event detection and timing, not recovery of the command text.

The paper reports an F1 score of ninety-two percent for DevTLB and ninety-eight point four percent for SWQ. The standard deviations of timestamp differences are five point two nine milliseconds and one point two one milliseconds, respectively.

There is a reporting caveat: the printed detection, false-positive, and false-negative counts don't fully reconcile with those metrics. We therefore keep the headline scores labeled as reported. The final application asks which model configuration produced an activity pattern.

**Source:** Paper Figure 12 and Section VI-C, p. 10; headline F1 values in Tables III and IV, pp. 11-12.

**Context and accuracy notes**

- Figure 12 labels the known command 'ssh root'. Those labels are ground truth, not recovered characters.
- The paper applies size- and latency-related filtering before evaluating event traces. Exact counts depend on that processing.
- For 512 ground-truth events, the printed DevTLB counts are 515 detections, 15 false positives, 61 false negatives, and 500 true positives. Those totals are inconsistent.
- The printed SWQ counts are 511 detections, 7 false positives, 9 false negatives, and 507 true positives. Those totals are also inconsistent.
- F1 and timestamp deviation answer different questions. Neither alone establishes text recovery.

---

### Slide 22: Fingerprinting model configurations

**Section:** Workload results. **Suggested time:** 75 seconds.

**On slide**

- Original Figure 13: model activity traces
- 98.6% reported validation accuracy across eight tested configurations
- Four named groups: TinyStories, LLaMA 2, Gemma 3, and Qwen3
- Fixed prompts and 50 traces per configuration
- The inferred configuration does not reveal weights or prompts

**Speaking script**

Model inference also moves substantial amounts of data. With the evaluated offload setup, those memory operations create DSA activity. Different model configurations can therefore produce different patterns in the probe trace.

The paper tests eight configurations across four groups: TinyStories, LLaMA 2, Gemma 3, and Qwen3. It collects fifty traces per configuration, uses identical prompts, and splits the data eighty-twenty for training and validation. The aggregation window is eight milliseconds.

Within that task, the reported validation accuracy is ninety-eight point six percent. The inferred label is one of the known model configurations. The attacker doesn't recover model weights or read the prompt.

The fixed prompts and evaluated runtimes matter when interpreting that number. The result shows that the configurations are distinguishable within this dataset; it doesn't establish identification across arbitrary prompts, hosts, or unseen models. We can now ask how these results change under the tested background load.

**Source:** Paper Table II, Figure 13, and Section VI-D, pp. 10-11.

**Context and accuracy notes**

- The eight configurations are TinyStories 15M, 42M, and 110M; LLaMA 2 7B; Gemma 3 1B and 4B; and Qwen3 1.7B and 4B. That is four named model groups, not three.
- The paper uses llama.c and ollama in its CPU and CPU-GPU evaluation paths. Runtime and model choices are part of the experimental setup.
- 50 traces per configuration gives 400 traces; the stated split corresponds to 320 training and 80 validation traces.
- An 8 ms slot groups 800 samples at the stated 10 microsecond interval.

---

### Slide 23: Robustness within the tested setup

**Section:** Workload results. **Suggested time:** 60 seconds.

**On slide**

- All six rows of Table III
- Local and cloud settings, with and without injected noise
- Most metrics change modestly; DevTLB keystroke F1 varies more
- Broader multi-tenant interference is not established

**Speaking script**

This table brings the results together across local and cloud settings, with and without injected background load. Most reported metrics change modestly across those conditions. The DevTLB keystroke F1 varies more, ranging from ninety point five to ninety-three point four percent.

The useful conclusion is that the channels remained effective under these tested stressors. The experiments include PCIe and memory pressure, so the results aren't limited to an entirely idle system.

But that isn't the same as testing every source of interference on a busy shared host. Many independent tenants, changing workloads, or different provisioning could create additional challenges. With that scope in mind, let's look at what the paper proposes to reduce the leakage.

**Source:** Paper Table III and Section VI-E, p. 11.

**Context and accuracy notes**

- Keep all six reported rows: DevTLB covert, SWQ covert, website classification, DevTLB keystroke F1, SWQ keystroke F1, and LLM classification.
- The noise study uses specified synthetic PCIe and host-memory stressors. It does not establish general resilience to arbitrary contention from many DSA tenants.
- The listed values are reported results, not a new experimental reproduction.

---

### Slide 24: Mitigations and what remains unmeasured

**Section:** Mitigations and conclusions. **Suggested time:** 70 seconds.

**On slide**

- Separate engines across trust boundaries for the DevTLB channel
- Avoid sharing an SWQ across trust boundaries
- Hardware proposals: partition replacement state and restrict queue-state feedback
- Random-entry overhead: 15.7% native and 17.9% DTO at 256-byte transfers
- Residual leakage after mitigation was not quantified

**Speaking script**

The practical boundary follows directly from the experiments. Separate queues can still share an engine's translation state, so protecting against this DevTLB channel requires attention to engine assignment. For the SWQ channel, avoid sharing the same queue across trust boundaries. Disabling offload on a sensitive path is another possible tradeoff.

The paper also proposes hardware changes, including partitioning translation-cache replacement state by address-space context and restricting queue-state feedback. Those are proposals, not evaluated deployed fixes, and they come with performance or interface costs.

For a software mitigation based on inserting random translations, the authors measure throughput loss. The maximum reported losses are fifteen point seven percent for native DSA and seventeen point nine percent with DTO, at 256-byte transfers. What they don't quantify is the leakage that remains after mitigation. So we have a cost measurement, but not a complete security-performance result. Let's close with what the experiments do establish.

**Source:** Paper Figure 14 and Section VII, pp. 11-12.

**Context and accuracy notes**

- Engine and queue allocation guidance concerns the observed sharing boundaries. It is not a universal guarantee against all accelerator side channels.
- Restricting admission feedback must account for legitimate software that needs to handle retry responses.
- The 15.7% and 17.9% values are measured throughput losses for the random-translation experiment at its smallest tested transfer size, not the cost of every proposed defense.
- The paper reports mitigation overhead without quantifying residual leakage.

---

### Slide 25: What the experiments establish

**Section:** Mitigations and conclusions. **Suggested time:** 45 seconds.

**On slide**

- Shared-engine translation replacement exposes timing
- Shared-queue admission exposes contention
- Application inference needs workload context and analysis
- Isolation must consider observable shared state as well as address permissions

**Speaking script**

The paper establishes two observable channels in shared DSA resources: translation replacement affects completion timing, and shared-queue admission reveals contention. Controlled experiments connect those observations to the engine and queue boundaries.

The application results then show how repeated observations can support communication, website classification, keystroke timing, and model-configuration classification under the evaluated conditions. The hardware supplies an activity signal; the workload and analysis give it meaning.

The broader lesson is that protecting addresses doesn't automatically hide activity in shared accelerator state. Both need to be considered when defining isolation. Thank you. We're happy to take questions.

**Source:** Synthesis of paper Sections IV-VII and IX, pp. 4-12.

**Context and accuracy notes**

- This is a conclusion from the reported evidence and stated scope, not a separate personal-verdict section.
- The deck does not claim recovery of victim memory contents, typed characters, model weights, or prompts.

---
## Source map

| Slide | Original paper material | Paper pages |
| --- | --- | --- |
| 3 | Section II-A plus Intel DSA operation and performance documentation | 2-3 and official Intel sources |
| 5 | Figure 1, DSA and translation architecture | 3 |
| 6 | Section II-B plus Intel VT-d and Shared Virtual Memory documentation | 2-3 and official Intel sources |
| 7 | Figure 2, reconstructed engine structure | 4 |
| 8 | Figure 3, descriptor layout | 4 |
| 9 | Figure 7, cross-VM sharing setup | 8 |
| 10 | Listing 2, capacity probe | 5 |
| 11 | Listings 3 and 4, field independence | 5 |
| 12 | Figure 5, engine and queue controls | 6 |
| 13 | Figure 4, timing distributions | 6 |
| 14 | Listing 1, timing excerpt from lines 7-12; NOOP attack from Section V-B | 4, 8 |
| 15 | Listing 5, arbitration experiment | 6 |
| 16 | Listing 6, congestion and probe helpers | 7 |
| 18 | Figure 9, covert capacity | 9 |
| 19 | Figure 8, VPP/memif path | 8 |
| 20 | Figure 11, 15-site confusion matrix; Section VI-B for full-dataset result | 9-10 |
| 21 | Figure 12, keystroke traces; Tables III-IV for headline metrics | 10-12 |
| 22 | Figure 13 and Table II, model configurations | 11 |
| 23 | Table III, noisy/local/cloud results | 11 |
| 24 | Section VII and Figure 14, mitigation proposals and measured cost | 11-12 |

The diagrams and code excerpts retain the paper content. Annotations, the memory-mapping primer, agenda, and inference flow are presenter explanations. Figure and listing extraction provenance is recorded in `../deck_v2/paper_assets/figure_manifest.json` and `../deck_v2/paper_assets/code_listings.json`.

## Reference notes for questions

### The short code excerpts are not complete runnable programs

All six numbered paper listings are represented in the main talk: Listing 2 on slide 10, Listings 3 and 4 on slide 11, the timing portion of Listing 1 on slide 14, Listing 5 on slide 15, and Listing 6 on slide 16. Their omitted setup is essential for execution: descriptor initialization and flags, completion-record association and reset, alignment, memory mapping, provisioned device access, ordering, and error or retry handling. The presentation explains what the experiments measure; it does not supply a complete implementation.

The printed full Listing 1 names a two-buffer comparison helper but assigns `DSA_OPCODE_COMPVAL` and supplies a second source address. That inconsistency must not be silently presented as a verified two-buffer compare recipe. The slide therefore shows only the enqueue, timestamp, polling, and subtraction lines. The NOOP-based attack uses the timing approach described in Section V-B.

### Keystroke count arithmetic

Keep the headline F1 values attributed to the paper. Its printed event totals do not reconcile:

| Reported quantity | DevTLB | SWQ |
| --- | --- | --- |
| Ground-truth events | 512 | 512 |
| Detected events | 515 | 511 |
| False positives | 15 | 7 |
| Printed true positives | 500 | 507 |
| Printed false negatives | 61 | 9 |
| TP implied by detections minus FP | 500 | 504 |
| FN implied by 512 minus that TP | 12 | 8 |
| Diagnostic F1 from those implied totals | 97.37% | 98.53% |

The last three rows are presenter calculations that expose the mismatch. They do not repair the experiment or establish corrected performance. The slide retains the reported headline F1 values, 92.0% and 98.4%, and states the reporting caveat. Timestamp deviations of 5.29 ms and 1.21 ms are distinct timing metrics. The labels in Figure 12 are known inputs, not decoded characters.

### What a physical page and a DevTLB entry mean

A physical frame is ordinary RAM backing a virtual page. It can hold instructions, a source or destination buffer, or a completion record. The DevTLB caches the address mapping, relevant context, and permissions needed to access memory. Its entries do not carry browser names, website labels, typed symbols, or an application history. The IOMMU translates and authorizes device accesses; Intel VT-d is Intel's architecture for that I/O translation and isolation. PASID identifies an address space within the relevant device/translation context. On a DevTLB miss, ATS requests a translation from the host Translation Agent. Its IOTLB may answer without a page-table walk. The diagram shows a successful authorized request and simplifies any virtualized translation stages.

### Assumptions and interpretation

- The paper explicitly requires provisioned DSA access and `CAP_SYS_RAWIO` for descriptor submission. Queue/engine configuration is privileged; co-location on the required resource is assumed. Avoid saying that any ordinary user can perform the attack without preparation.
- The DevTLB channel needs a shared engine. The SWQ channel needs the same shared work queue. Separate queues alone do not partition engine-local replacement capacity.
- One slow probe or one retry is not unique attribution to the victim. Preparation, calibration, observation windows, repeated measurements, and workload knowledge support the inference.
- The website and model experiments classify known labels in controlled datasets. They do not establish open-world or cross-host identification.
- The mitigation throughput values do not establish residual security. The random-translation experiment reports cost without quantifying remaining leakage.

### Other quantitative qualifications

- Covert bit error is 4.63% in Section VI-A and Table IV, while the abstract/contributions also print 4.64%. This talk uses the body/table value.
- The 85.73% website result concerns all 100 sites. The 96.5% figure concerns the displayed 15-site subset.
- The LLM task has eight configurations in four named groups: TinyStories, LLaMA 2, Gemma 3, and Qwen3.
- Comparisons with IPI or DEVIOUS are cross-paper reported values, not matched reruns. DevTLB has higher reported covert capacity than IPI, but does not win every metric.
- The noise results cover the paper's specified stressors. Broader contention from many independent DSA users remains outside the demonstrated scope.

### Pronunciation and delivery reminders

DSA can be spoken as "D S A." DevTLB can be introduced as "device T L B." SWQ means "shared work queue." ENQCMD is the enqueue-command instruction, and RDTSC reads the timestamp counter. Introduce each full term once, then use the shorter form. Read only the Speaking script during delivery; use these reference notes when answering questions.

### Changes made for this revision

The revised story adds an agenda with subtopics, a dedicated explanation of why and what to offload, an expanded IOMMU/VT-d and virtual-to-physical translation explanation, the missing field-isolation and arbitration listings, an explicit observation-to-inference sequence, and the original website network-path figure. It removes the dramatic framing and unsupported certainty from the earlier script, makes all 25 slide headings agree with the deck, corrects the four-model-group count, and removes references to nonexistent backup slides. The natural-language text contains no em dashes.
