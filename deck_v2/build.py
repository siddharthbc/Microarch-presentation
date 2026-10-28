"""Build the DSASSASSIN v2 deck — Apple-inspired, static (no animations).

    python build.py            # layout + PDF/PNG export via PowerPoint COM
    python build.py --no-com   # layout only

The final editorial pass produces 36 main slides and 7 backup slides, matching
SLIDE_PLAN.md. Full narration lives in each slide's speaker notes.
"""
import sys
import json
from kit import *  # noqa: F401,F403
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE


# ============================================================================= ACT I
def act1():
    # ---- 1 Title (dark, cinematic)
    s = slide('', '', '', notes(
        "Datacenters race to move memory work off the CPU. Intel's DSA ships in every recent Xeon. This is the first "
        "public security analysis of it. Seed the thesis: VT-d isolates addresses, not the accelerator's shared "
        "heartbeat."), 40, dark=True)
    tx(s, 'HPCA 2026', M, 1.5, CW, .4, 14, 'gray_dark', semi=True)
    tx(s, 'DSASSASSIN', M, 2.0, CW, 1.3, 72, 'white', semi=True)
    tx(s, 'Cross-VM side-channel attacks by exploiting\nIntel’s Data Streaming Accelerator', M, 3.5, CW, 1.4, 30,
       'gray_dark', line_spacing=1.1)
    tx(s, 'Ben Chen · Kunlin Li · Shuwen Deng · Dongsheng Wang · Yun Chen', M, 5.4, CW, .4, 18, 'white')
    tx(s, 'HKUST (Guangzhou) · Tsinghua University', M, 5.85, CW, .4, 15, 'gray_dark')
    tx(s, 'Presented by Siddharth Banakar and Dinesh Samala · 29 October 2026', M, 6.5, CW, .4, 15, 'gray_dark')

    # ---- 2 The crack, in one picture
    s = slide('Address isolation still leaves the shared activity visible', 'The wall has a crack',
              'Paper §§ I, IV–V · pp. 1–8', notes(
        "The thesis in one picture. Two VMs, each its own PASID, cannot read each other's memory — VT-d works. But both "
        "use the SAME physical accelerator, whose internal state is NOT split. DSASSASSIN never reads victim memory; it "
        "watches the accelerator twitch. Confidentiality of addresses is not confidentiality of activity."), 70)
    card(s, 'VM A — victim', 'Private address space\nPASID A', M, TOP + .1, 4.55, 1.7, title_color='accent')
    card(s, 'VM B — observer', 'Private address space\nPASID B', SW - M - 4.55, TOP + .1, 4.55, 1.7, title_color='redtext')
    tx(s, 'VT-d / PASID\nisolates translation', M + 4.75, TOP + .5, CW - 9.5, .9, 15, 'gray', align=PP_ALIGN.CENTER)
    arrow(s, M + 2.2, TOP + 1.95, M + 2.2, TOP + 2.45)
    arrow(s, SW - M - 2.3, TOP + 1.95, SW - M - 2.3, TOP + 2.45)
    sh = rect(s, M, TOP + 2.5, CW, 1.1, 'black', radius=.2)
    tx(s, 'Shared engine state   ·   shared queue occupancy', M, TOP + 2.5, CW, 1.1, 26, 'white', semi=True,
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    key(s, 'The leakage is about resource use — not access to victim memory.', y=6.25)

    # ---- 3 Results at a glance
    s = slide('Four demonstrations, one humble signal', 'The wall has a crack',
              'Paper § VI, Tables III–IV · pp. 9–12 · reported results', notes(
        "The twitch is enough for: a 17.19 kbps covert channel (5x faster, 4x cleaner than prior IPI); website "
        "fingerprinting 85.73% over 100 sites vs 1% baseline; SSH keystroke timing 98.4% F1; LLM fingerprinting 98.6%. "
        "Same 'accelerator is busy' signal, four different secrets. I'll flag which are rock-solid vs caveated."), 70)
    stats(s, [('17.19 kbps', 'Covert channel', 'DevTLB · 4.63% bit error', 'accent'),
              ('85.73%', 'Website fingerprinting', '100 sites · 1% baseline', 'black'),
              ('98.4%', 'Keystroke timing F1', 'SWQ · 1.21 ms deviation', 'black'),
              ('98.6%', 'LLM fingerprinting', 'Validation · 8 models', 'black')],
          y=TOP + .15, cols=2, rowgap=2.15)
    key(s, 'None of these reads a byte of victim memory.', y=6.35)

    # ---- 4 Roadmap
    s = slide('The route — from shared state to application leakage', 'The wall has a crack',
              'Six acts + backup', notes(
        "The map. Machine, then the detective story of reverse engineering, then the four attacks, then defenses and "
        "comparison, then my own critique. Hold mechanism questions until after Act III."), 55)
    table(s, ['', 'Theme', 'Covers', 'Time'],
          [['I', 'The wall has a crack', 'thesis + payoff', '4 min'],
           ['II', 'Meet the machine', 'architecture + threat model', '8 min'],
           ['III', 'The detective story', 'reverse engineering + two primitives', '16 min'],
           ['IV', 'What it steals', 'covert channel + three attacks', '12 min'],
           ['V', 'Does it hold up?', 'robustness, comparison, defenses', '6 min'],
           ['VI', 'My verdict', 'strengths, limits, open questions', '5 min']],
          y=TOP, colfracs=[.07, .3, .48, .15], rowh=.62, size=18, muted_cols=(2, 3))
    key(s, 'A running theme: VT-d guards addresses, not the accelerator’s shared heartbeat.', y=6.35)


# ============================================================================= ACT II
def act2():
    divider(2, 'Meet the machine', ['What DSA is and how a job flows through it',
                                     'The device-side translation cache (DevTLB)',
                                     'The honest threat model — and two kinds of sharing'])

    # ---- 5 offloading moves the secret
    s = slide('Memory offload creates a new place to observe', 'Meet the machine', 'Paper §§ I–II-A · pp. 1–2', notes(
        "DSA is a data mover: software hands it copy/compare/checksum jobs, done asynchronously. For years we studied "
        "how these ops leak on the CPU; the fix was partly to move them. The premise: 'somewhere else' is a new, "
        "unstudied, shared place to watch. We relocated the side channel to a building with no cameras."), 65)
    flow(s, [('Common operations', 'memcpy · memset\ncompare · checksums'),
             ('DSA offload', 'descriptor submission\nasynchronous execution'),
             ('Observable state', 'translation cache\nqueue occupancy')],
         y=TOP + .5, h=2.2, last_color='accent')
    key(s, 'Moving work off the CPU moves the side-channel surface with it.')

    # ---- 6 pipeline
    s = slide('A DSA operation is a descriptor-driven pipeline', 'Meet the machine',
              'Paper § II-A, Fig. 1 · pp. 2–3', notes(
        "Follow one job: software fills a descriptor, writes it to an MMIO portal, it lands in a work queue, an engine "
        "executes and writes a completion record. Remember two observation handles: did my submission get in? and how "
        "long until my completion? Everything later is one of those two."), 75)
    flow(s, [('Application', 'prepare descriptor'), ('Portal + WQ', 'submit / buffer'),
             ('DSA engine', 'decode → write'), ('Completion', 'notify CPU')],
         y=TOP + .3, h=1.7, title_size=20)
    tx(s, 'The attacker owns two handles —\n“was my submission accepted?”   ·   “how long did my completion take?”',
       M, TOP + 2.3, CW, .9, 18, 'black', semi=True, align=PP_ALIGN.CENTER, line_spacing=1.2)
    key(s, 'Observe request acceptance, or observe how long completion takes.', y=5.7)

    # ---- 7 DevTLB
    s = slide('The device keeps its own translation cache', 'Meet the machine', 'Paper § II-B, Fig. 1 · pp. 2–3', notes(
        "DSA caches address translations on the device in the DevTLB. The translation request's address-space "
        "context controls authorization, but does not give every VM separate replacement capacity. A conflicting "
        "request can replace my entry, making my own probe slower without revealing the victim's address or data. "
        "A DevTLB miss consults the Translation Agent; its IOTLB may answer without a page-table walk."), 75)
    flow(s, [('Device request', 'virtual address + PASID'), ('DevTLB / ATC', 'hit → reuse translation'),
             ('Host memory', 'physical transaction')],
         y=TOP + .3, h=1.7)
    tx(s, 'Miss  →  Translation Agent / IOTLB  →  page-table walk if needed', M, TOP + 2.4, CW, .5, 18, 'redtext', semi=True,
       align=PP_ALIGN.CENTER)
    key(s, 'Shared replacement capacity can leak activity without exposing page contents.', y=5.6)

    # ---- 8 threat model
    s = slide('The attacker needs DSA access and co-location', 'Meet the machine', 'Paper § V-A · pp. 7–8', notes(
        "Be scrupulous. Unprivileged in the way that matters: no root, no host reconfiguration, no reading victim "
        "memory, and NOT sharing a CPU core — genuinely cross-VM, cross-core. But it still assumes provisioned device "
        "access and co-location on the same engine/queue. An assumption; I revisit it in the critique. Note a tension "
        "in §V-A: it first says configuring engine affinity / WQ settings needs root, then says setting affinity to an "
        "engine or queue does NOT need root — read this as: creating/configuring queues is root (accel-config), but "
        "binding to an existing portal is not. Kernel 6.11.0-25, IDXD driver."), 75)
    xw = (CW - .6) / 2
    tx(s, 'Assumed', M, TOP, xw, .4, 16, 'accent', semi=True)
    hline(s, M, TOP + .42, xw)
    for i, t in enumerate(['DSA-enabled Xeon + IDXD + VT-d scalable mode', 'Victim actually uses DSA',
                           'Attacker may submit descriptors (CAP_SYS_RAWIO)', 'Shares the engine (DevTLB) or the SWQ',
                           'May set its own engine / queue affinity']):
        tx(s, t, M, TOP + .65 + i * .72, xw, .6, 17, 'black', line_spacing=1.0)
    tx(s, 'Not needed', M + xw + .6, TOP, xw, .4, 16, 'redtext', semi=True)
    hline(s, M + xw + .6, TOP + .42, xw)
    for i, t in enumerate(['A shared CPU core', 'Shared victim memory', 'Permission to read victim addresses',
                           'Root / authority to reconfigure host DSA']):
        tx(s, t, M + xw + .6, TOP + .65 + i * .72, xw, .6, 17, 'gray', line_spacing=1.0)
    key(s, '“Unprivileged” still depends on pre-provisioned device access and co-location.')

    # ---- 9 two doors (CRITICAL)
    s = slide('Two channels cross two different boundaries', 'Meet the machine', 'Paper §§ IV-A, V · pp. 3–8', notes(
        "The slide I'd tattoo on an operator. DevTLB channel needs only the same ENGINE — different queues still leak. "
        "SWQ channel needs the same QUEUE. So separate queues, which operators call isolation, do NOT stop the DevTLB "
        "channel because the cache lives below the queues, at the engine. Remember this one fact."), 80)
    card(s, 'DevTLB timing channel', 'Victim and attacker may use\ndifferent work queues —\nif they share one engine.\n\nDifferent queues can still interfere.',
         M, TOP, 5.7, 3.7, title_color='accent')
    card(s, 'SWQ contention channel', 'Victim and attacker must\nshare the same work queue.\n\n\nThe same queue must be shared.',
         SW - M - 5.7, TOP, 5.7, 3.7, title_color='redtext')
    key(s, 'Separate work queues are not enough if the engine is shared.', y=6.1, color='redtext')

    # ---- 10 how to reverse engineer
    s = slide('Reverse engineering answers three questions', 'Meet the machine', 'Paper §§ III–IV · pp. 3–7', notes(
        "No datasheet exists. So: form a hypothesis about structure, design a probe that gives a visibly different "
        "result under each hypothesis, keep the survivor. The next ten minutes are a chain of these, each eliminating "
        "a possibility until the scary truth is all that's left."), 60)
    columns(s, [('What is shared?', 'Capacity, indexing,\nreplacement policy,\nPASID behaviour'),
                ('What is visible?', 'Privileged counters\nvs. user-observed\nlatency and flags'),
                ('What can it reveal?', 'Eviction → activity\nAdmission → occupancy')],
            numbered=True, title_size=24)
    key(s, 'Each microbenchmark links an implementation behaviour to an observable signal.')

    # ---- 11 tools vs weapon
    s = slide('Characterization counters ≠ attack signals', 'Meet the machine', 'Paper § IV-B, Table I · pp. 4–6', notes(
        "Fair challenge: aren't you using privileged counters? To UNDERSTAND the hardware, yes — Perfmon, for ground "
        "truth. But the ATTACK reads only what any user can: its own completion time, or whether its own submission "
        "succeeded. Counters are the microscope in the lab, not part of the weapon. Done on local and a real cloud "
        "instance."), 70)
    xw = (CW - .6) / 2
    tx(s, 'Reverse engineering · privileged PMU', M, TOP, xw, .4, 16, 'gray', semi=True)
    hline(s, M, TOP + .42, xw)
    for i, t in enumerate(['EV_ATC_ALLOC', 'EV_ATC_NO_ALLOC', 'EV_ATC_HIT_PREV']):
        tx(s, t, M, TOP + .65 + i * .55, xw, .5, 18, 'black', font=FONT)
    tx(s, 'Attack signal · unprivileged', M + xw + .6, TOP, xw, .4, 16, 'accent', semi=True)
    hline(s, M + xw + .6, TOP + .42, xw)
    for i, t in enumerate(['DevTLB · own completion time (rdtsc)', 'SWQ · ENQCMD result via EFLAGS.ZF']):
        tx(s, t, M + xw + .6, TOP + .65 + i * .55, xw, .5, 18, 'black')
    tx(s, 'Platforms: Xeon Platinum 8468V (local) · 8475B (Alibaba cloud) · Linux 6.11 · IDXD · VT-d scalable mode · SR-IOV (DevTLB setup) / Scalable IOV (shared SWQ)',
       M, TOP + 2.6, CW, .4, 14, 'gray')
    key(s, 'PMU access supports the explanation; it is not needed for the attack loop.', y=5.6)


# ============================================================================= ACT III
def act3():
    divider(3, 'The detective story', ['Each microbenchmark rules out an alternative',
                                        'Five one-entry slots — indexed by engine and field, not PASID',
                                        'Prime → Idle → Probe   and   Congest → Idle → Probe'])

    # ---- 12 opcode chooses the drawer
    s = slide('Clue #1 — the opcode chooses which slot you touch', 'The detective story',
              'Paper § IV-B, Fig. 3 · pp. 4–5', notes(
        "First clue. The cache is indexed by a field's ROLE — src, src2, dst, dst2, comp — not by address. The authors "
        "pick which roles to exercise by picking the opcode. noop is the scalpel: touches only the completion slot, "
        "cheapest, cleanest timing. dualcast lights four slots. Surgical control."), 70)
    table(s, ['Operation', 'Address fields', 'Completion', 'Why useful'],
          [['noop', 'none', 'comp', 'Minimal timing probe — the scalpel'],
           ['memcmp / compare', 'src + src2', 'comp', 'Two independent reads'],
           ['memcpy', 'src + dst', 'comp', 'Read / write separation'],
           ['dualcast', 'src + dst + dst2', 'comp', 'Multiple destination slots']],
          y=TOP, colfracs=[.22, .26, .16, .36], rowh=.68, size=18, muted_cols=(1, 2, 3))
    tx(s, 'Byte 24 is src2 for compare but dst for copy — same bits, different meaning.', M, TOP + 3.35, CW, .4, 16,
       'gray', italic=True)
    key(s, 'The opcode changes field meaning; field meaning changes which slot is used.')

    # ---- 13 five slots (anchor diagram)
    s = slide('The reveal — five drawers, one translation each', 'The detective story',
              'Paper §§ IV-A–B, Fig. 2 · pp. 3–6 · empirical model', notes(
        "Spoiler so the experiments make sense: each engine's DevTLB has exactly five entries, one per field role, each "
        "holding ONE translation. Direct-mapped to the extreme. Why catastrophic? No eviction set needed — any single "
        "different page in that role evicts the occupant. The drawer only fits one sock."), 75)
    tx(s, 'Engine 0', M, TOP + .1, 3, .4, 17, 'gray', semi=True)
    fields = ['src', 'src2', 'dst', 'dst2', 'comp']
    sw = (CW - 4 * .35) / 5
    for i, f in enumerate(fields):
        x = M + i * (sw + .35)
        rect(s, x, TOP + .6, sw, 1.5, 'fill' if f != 'comp' else 'black', radius=.18)
        tx(s, f, x, TOP + .95, sw, .4, 22, 'white' if f == 'comp' else 'black', semi=True, align=PP_ALIGN.CENTER)
        tx(s, 'one page\ntranslation', x, TOP + 1.4, sw, .6, 13, 'gray_dark' if f == 'comp' else 'gray',
           align=PP_ALIGN.CENTER, line_spacing=1.0)
    tx(s, 'A single different page in a field’s role replaces the one translation in that slot — no eviction set required.',
       M, TOP + 2.5, CW, .5, 17, 'gray', align=PP_ALIGN.CENTER)
    key(s, 'One-slot replacement makes a neighbour’s activity trivial to detect.', y=6.05)

    # ---- 14 base-offset-base
    s = slide('Proof of “one slot” — base → offset → base', 'The detective story',
              'Paper § IV-B, Listing 2 · pp. 4–5', notes(
        "Load base. Touch an address 'offset' away. Re-check base. Inside the same 4KB page, base survives → page "
        "granularity. Cross a page boundary → base is gone → only ONE slot (two would survive). They even evict a 4KB "
        "entry with a 2MB huge-page address — no separate drawers per page size."), 70)
    steps(s, [('Probe base', 'Load one page translation'),
              ('Probe base + offset', 'Keep or replace it'),
              ('Probe base again', 'Did it survive?')],
          y=TOP, h=2.0)
    table(s, ['Offset', 'Final base observation', 'Interpretation'],
          [['< 4 KiB', 'Hit', 'Same page retained'],
           ['≥ 4 KiB', 'Miss', 'A different page replaced it']],
          y=TOP + 2.55, colfracs=[.2, .32, .48], rowh=.55, size=18, highlight=1, hl_color='redtext', muted_cols=(2,))
    key(s, 'A single different page is enough to evict the tested field’s translation.')

    # ---- 15 fields independent
    s = slide('The drawers are independent — even sharing bits', 'The detective story',
              'Paper § IV-B, Listings 3–4 · p. 5', notes(
        "Change the source, keep the destination → destination survives: independent drawers. Then the elegant one: "
        "src2 and dst are encoded in the SAME bytes, told apart only by opcode. If indexed by raw bytes they'd collide. "
        "They don't — routed by MEANING, not bit position. This is what makes the reverse engineering credible."), 75)
    card(s, 'Independent fields', 'copy(src A, dst D)\ncopy(src B, dst D)\n\nSource replaced; destination retained\n→ separate slots.',
         M, TOP, 5.7, 3.4, title_color='accent')
    card(s, 'Shared encoding, distinct slots', 'compare(src A, src2 X)\ncopy(src A, dst X)\n\nOnly the src reuse\nproduces the shared hit.',
         SW - M - 5.7, TOP, 5.7, 3.4, title_color='black')
    key(s, 'The organisation follows field semantics, including src2 versus dst.', y=6.0)

    # ---- 16 long transfers
    s = slide('A slot remembers the last page, not the history', 'The detective story', 'Paper § IV-B · pp. 5–6', notes(
        "Big transfers split per-page; the drawer keeps only the FINAL page's translation — a snapshot, not a "
        "replayable log. Also: batch-fetcher reads and completion writes bypass the cache. For the attacker that's a "
        "note: use ordinary work descriptors for reliable interference, not batch tricks."), 60)
    tx(s, 'One descriptor crossing several source pages', M, TOP, CW, .4, 18, 'gray')
    pw = (CW - 3 * .5) / 4
    for i, lab in enumerate(['Page A', 'Page B', 'Page C', 'Page D']):
        x = M + i * (pw + .5)
        rect(s, x, TOP + .55, pw, 1.0, 'black' if i == 3 else 'fill', radius=.18)
        tx(s, lab, x, TOP + .55, pw, 1.0, 20, 'white' if i == 3 else 'black', semi=True, align=PP_ALIGN.CENTER,
           anchor=MSO_ANCHOR.MIDDLE)
        if i < 3:
            arrow(s, x + pw + .1, TOP + 1.05, x + pw + .4, TOP + 1.05)
    tx(s, 'Retained in the src slot:  Page D', M, TOP + 1.85, CW, .5, 20, 'black', semi=True)
    tx(s, 'The batch fetcher’s own descriptor reads and completion-record writes did not populate these slots — a separate translation path.',
       M, TOP + 2.6, CW, .4, 16, 'gray', italic=True)
    key(s, 'A slot records recent field-specific state, not a page-access history.')

    # ---- 17 THE MONEY SHOT
    s = slide('The money shot — eviction follows the engine, not the queue', 'The detective story',
              'Paper § IV-B, Fig. 5 · p. 6', notes(
        "Three experiments, two VMs. E0: same queue + engine → miss, expected. E1 (the dangerous one): DIFFERENT "
        "queues, same engine → still miss. So the leak isn't about the queue, and PASID isn't partitioning this cache. "
        "E2 is the negative control: separate ENGINES → hit. Separate engines prevented this eviction in the tested "
        "configuration; separate queues did not. The control identifies the observed sharing boundary, not a "
        "universal security guarantee."), 85, title_size=24)
    cards = [('E0', 'same WQ · same engine', 'Miss', 'Cross-VM interference', 'redtext'),
             ('E1', 'different WQ · same engine', 'Miss', 'Queue separation insufficient', 'redtext'),
             ('E2', 'different WQ · different engine', 'Hit', 'No cross-engine eviction', 'green')]
    cw = (CW - 2 * .5) / 3
    for i, (nm, cfg, res, impl, col) in enumerate(cards):
        x = M + i * (cw + .5)
        rect(s, x, TOP, cw, 3.4, 'fill', radius=.22)
        tx(s, nm, x + .35, TOP + .3, cw - .7, .5, 24, 'black', semi=True)
        tx(s, cfg, x + .35, TOP + .9, cw - .7, .6, 15, 'gray', line_spacing=1.0)
        tx(s, res, x + .35, TOP + 1.65, cw - .7, .7, 34, col, semi=True)
        tx(s, impl, x + .35, TOP + 2.5, cw - .7, .6, 15, 'gray', line_spacing=1.0)
    key(s, 'E2 is the control: eviction followed the shared engine in these experiments.', y=6.05)

    # ---- 18 latency distinguishable
    s = slide('The clock still works — even under noise', 'The detective story',
              'Paper § IV-B, Fig. 4 · pp. 5–6 · original distributions', notes(
        "The attacker's real view: just rdtsc on its own completion. Hits ~500 cycles, misses >1000 — two clean humps, "
        "threshold 600-900. They deliberately stress PCIe (2 GB/s NVMe) and memory (10 GB/s). Humps shift ~89 cycles in "
        "the cloud but never merge. Lab result survives reality."), 70)
    picture(s, 'latency', M, TOP, 7.7, 4.1)
    xx = M + 8.1
    tx(s, 'Measured signal', xx, TOP + .2, 3.4, .4, 16, 'accent', semi=True)
    hline(s, xx, TOP + .62, 3.4)
    for i, (a, b) in enumerate([('Hit', '≈ 500 cycles'), ('Miss', '≈ > 1000 cycles'), ('Threshold', '600 – 900')]):
        tx(s, a, xx, TOP + .85 + i * .62, 1.5, .4, 18, 'black', semi=True)
        tx(s, b, xx + 1.4, TOP + .85 + i * .62, 2.0, .4, 18, 'gray')
    tx(s, 'Noise shifts latency; the separation survives in every tested environment.', xx, TOP + 2.9, 3.4, 1.0, 15,
       'gray', line_spacing=1.15)
    key(s, 'An unprivileged clock cleanly tells a hit from a miss.', y=6.3)

    # ---- 19 Weapon 1
    s = slide('Weapon #1 — Prime → Idle → Probe', 'The detective story', 'Paper § V-B · p. 8', notes(
        "Prime+Probe with a twist. I prime a slot with MY OWN completion-record address — never need the victim's. Go "
        "quiet. A victim completion write through the same engine can replace that slot. Probe = re-run noop and "
        "time its completion. A fast probe suggests retention; a slow probe suggests replacement. Calibration, "
        "co-location, and the observation window support an activity inference. One sample does not prove who "
        "caused the delay or reveal their data."), 75)
    steps(s, [('Prime', 'Submit noop → cache my own\ncompletion-record page'),
              ('Idle', 'Wait > one DSA op; a victim\non this engine may evict it'),
              ('Probe', 'Submit noop again,\ntime it with rdtsc')],
          y=TOP + .3, h=2.2, colors=['accent', 'redtext', 'black'])
    key(s, 'Fast probe suggests retention.   Slow probe suggests replacement.')

    # ---- 20 why powerful / limit
    s = slide('Why it’s powerful — and what it cannot do', 'The detective story',
              'Paper §§ IV-B, V-B · pp. 4–8 · interpretation', notes(
        "Versus LLC Prime+Probe, half the battle is eviction sets and alignment. Here the one-slot design hands you the "
        "eviction for free — that's the power. The limit, honestly: the signal is coarse, just 'the engine was busy'. "
        "So every real attack is a pattern-recognition problem on top of this heartbeat. That framing is where my "
        "critique bites."), 60)
    bullets(s, [('No address guessing', 'the attacker primes its own completion-record page'),
                ('No eviction-set search', 'one slot — a single different page evicts it'),
                ('A broad activity signal', 'meaning comes later, from timing patterns and a classifier')],
            y=TOP + .3, gap=1.25)
    key(s, 'The primitive yields a heartbeat; the application supplies its meaning.')

    # ---- 21 SWQ dead end
    s = slide('The dead end that wasn’t — a flag talks', 'The detective story',
              'Paper § IV-C, Fig. 6 · pp. 6–7 · original latency plot', notes(
        "You'd expect a shared queue to leak via submission timing. They measure it — submission time is FLAT. Timing "
        "is a dead end. The save: submission is a Deferrable Memory Write, and when the queue is full the hardware "
        "refuses and sets EFLAGS.ZF. Fullness leaks through yes/no, not how-long. Timer-free — better, no clock "
        "noise."), 70)
    picture(s, 'submit', M, TOP, 7.7, 4.1)
    xx = M + 8.1
    tx(s, 'Two observables', xx, TOP + .2, 3.4, .4, 16, 'accent', semi=True)
    hline(s, xx, TOP + .62, 3.4)
    for i, (a, b) in enumerate([('Submission', 'flat ≈ 700 cycles'), ('Completion', 'grows with size'),
                                ('Queue-full', 'a visible flag')]):
        tx(s, a, xx, TOP + .85 + i * .62, 1.6, .4, 18, 'black', semi=True)
        tx(s, b, xx + 1.5, TOP + .85 + i * .62, 1.9, .4, 18, 'gray')
    key(s, 'The SWQ channel uses ENQCMD / EFLAGS.ZF — no timing threshold at all.', y=6.3)

    # ---- 22 arbiter
    s = slide('Learning to hold the queue hostage', 'The detective story', 'Paper §§ IV-A, IV-C · pp. 3–4, 6–7', notes(
        "Two facts to pin down. One: the fullness check happens at enqueue against config registers in constant time — "
        "that's why the flag is timer-free. Two: the arbiter always prefers WORK descriptors over BATCH (race them, "
        "latency unchanged). So to hold the queue hostage reliably, use one long ordinary memcpy, not a batch trick."), 65)
    card(s, 'Admission path', 'Portal → per-queue metadata check\nFixed-time occupancy test\nSuccess or retry stays visible',
         M, TOP, 5.7, 3.0, title_color='accent')
    card(s, 'Execution path', 'Work queue + batch buffer → arbiter\nArbiter prefers work over batch\nSo: use a long ordinary copy',
         SW - M - 5.7, TOP, 5.7, 3.0, title_color='black')
    key(s, 'The attacker holds the engine with a long ordinary copy, not batch priority.', y=5.6)

    # ---- 23 the trap
    s = slide('The trap — leave exactly one seat open', 'The detective story',
              'Paper §§ IV-C, V-C, Listing 6 · pp. 7–8', notes(
        "A theater with N seats. The attacker buys all but one — a long copy holds the front row so the queue drains "
        "slowly, fillers take the rest. One seat left. If the victim submits, it takes that seat and the house is "
        "full. Queue size readable without root. A stopwatch-free race against the long copy finishing."), 70)
    tx(s, 'Target state: effective occupancy  N − 1', M, TOP, CW, .5, 20, 'black', semi=True)
    seats = [('LONG\nCOPY', 'redtext', 'white'), ('WORK', 'black', 'white'), ('WORK', 'black', 'white'),
             ('WORK', 'black', 'white'), ('WORK', 'black', 'white'), ('WORK', 'black', 'white'),
             ('FREE', 'fill', 'gray')]
    sw = (CW - 6 * .2) / 7
    for i, (lab, fill, col) in enumerate(seats):
        x = M + i * (sw + .2)
        rect(s, x, TOP + .7, sw, 1.2, fill, radius=.16, line='hair' if fill == 'fill' else None)
        tx(s, lab, x, TOP + .7, sw, 1.2, 15, col, semi=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
           line_spacing=1.0)
    tx(s, 'If the victim submits during the hold window, it consumes the last seat — the queue goes full.',
       M, TOP + 2.3, CW, .5, 18, 'black', semi=True)
    tx(s, 'The anchor must be large: contention only appeared for transfers ≥ 2²⁵ bytes (32 MiB). Queue size is readable via accel-config without root.',
       M, TOP + 2.95, CW, .4, 15, 'gray', italic=True)
    key(s, 'Probe before the long copy completes and the queue starts draining.')

    # ---- 24 Weapon 2
    s = slide('Weapon #2 — Congest → Idle → Probe', 'The detective story', 'Paper § V-C · p. 8', notes(
        "Same three-beat rhythm as DevTLB. Congest to one-from-full. Hold it there. Try to submit one job and read the "
        "flag. ZF=0 means accepted; ZF=1 means retry, a full queue in this experiment. With the queue prepared and "
        "the window controlled, retry is evidence that the victim consumed remaining admission capacity. The "
        "signal uses no duration measurement; the observation window still needs control. The cost is active "
        "congestion of a shared resource the victim needs."), 75)
    steps(s, [('Congest', 'Long memcpy + fillers →\nnear-full SWQ'),
              ('Idle', 'Hold the window;\nthe victim may enqueue'),
              ('Probe', 'Submit once,\nread EFLAGS.ZF')],
          y=TOP, h=1.8, colors=['redtext', 'accent', 'black'])
    hline(s, M, TOP + 2.7, CW, 'hair')
    xw = (CW - .6) / 2
    tx(s, 'ZF = 0   →   accepted (capacity available)', M, TOP + 2.95, xw, .5, 19, 'green', semi=True, align=PP_ALIGN.CENTER)
    tx(s, 'ZF = 1   →   retry (full in this experiment)', M + xw + .6, TOP + 2.95, xw, .5, 19, 'redtext', semi=True,
       align=PP_ALIGN.CENTER)
    key(s, '“Timer-free” describes the signal; the window still needs control.')

    # ---- 25 two weapons
    s = slide('Two weapons, two personalities', 'The detective story',
              'Paper §§ V–VI · pp. 7–12 · footprint row = presenter reading', notes(
        "DevTLB: quiet sniper — tiny noops, reaches anyone on the engine, needs a clock. SWQ: blunt instrument — must "
        "actively jam a shared queue, reaches only queue-mates, no clock, gorgeous timing. You'll see DevTLB win covert "
        "bandwidth, SWQ win keystroke timing. The 'footprint' row is my interpretation — flagged as such."), 70)
    table(s, ['Property', 'DevTLB', 'SWQ'],
          [['Shared resource', 'same engine (queues may differ)', 'same shared work queue'],
           ['Observed signal', 'completion latency', 'submission success / retry'],
           ['Preparation', 'prime comp translation', 'hold queue near-full'],
           ['Timer', 'rdtsc required', 'none'],
           ['Footprint', 'light noop probes', 'heavy active congestion'],
           ['Best at', 'covert bandwidth', 'keystroke timing']],
          y=TOP, colfracs=[.26, .4, .34], rowh=.58, size=17, muted_cols=())
    key(s, 'Both infer activity through the attacker’s own requests.', y=6.35)


# ============================================================================= ACT IV
def act4():
    divider(4, 'What it steals', ['A covert channel proves the channel carries bits',
                                   'Websites, SSH keystrokes, and the LLM next door',
                                   'Strong numbers — quoted honestly, caveats and all'])

    # ---- 26 covert protocol
    s = slide('Can it even carry a message?', 'What it steals', 'Paper § VI-A · p. 9 · simplified protocol', notes(
        "A covert channel is the controlled test: make the 'victim' a cooperative SENDER and see how cleanly bits move. "
        "Sender encodes 1 by causing activity, 0 by idling; receiver reads the heartbeat. A preamble of 1s syncs the "
        "clocks. This proves capacity under clean conditions — real victims are messier."), 65)
    table(s, ['Phase', 'Receiver', 'Sender'],
          [['Synchronize', 'detect preamble', 'transmit consecutive 1 bits'],
           ['Prepare', 'prime DevTLB / congest SWQ', 'wait for data slot'],
           ['Encode', 'open observation window', '1 → submit · 0 → idle'],
           ['Decode', 'time completion / read ZF', 'advance to next slot']],
          y=TOP, colfracs=[.2, .4, .4], rowh=.66, size=18, muted_cols=())
    key(s, 'Covert-channel feasibility is a separate claim from inference accuracy.')

    # ---- 27 covert results
    s = slide('17.19 kbps — and a bandwidth / error tradeoff', 'What it steals',
              'Paper § VI-A, Fig. 9, Table IV · pp. 9, 12', notes(
        "DevTLB hits 17.19 kbps under 5% error — quiet sniper packs probes tightly, beats SWQ. Curve shape: crank the "
        "RAW rate and errors climb until USEFUL throughput peaks then collapses — hence a best point. That 17-and-change "
        "is 5x faster, 4x cleaner than the prior IPI channel. Capacity: proven."), 70)
    picture(s, 'capacity', M, TOP, 7.7, 4.1)
    xx = M + 8.1
    stat(s, '17.19 kbps', 'DevTLB', '4.63% bit error', xx, TOP + .2, 3.4, 'accent', num_size=40)
    stat(s, '4.02 kbps', 'SWQ', '13.11% bit error', xx, TOP + 2.2, 3.4, 'black', num_size=40)
    key(s, 'Faster raw signalling loses useful throughput as the error rate climbs.', y=6.3)

    # ---- 28 website path
    s = slide('Attack #1 — websites leak through the stack', 'What it steals',
              'Paper § VI-B, Fig. 8 · pp. 8–10 · simplified path', notes(
        "A realistic victim: a VM running VPP, a DPDK userspace network stack that uses DSA to move packets through "
        "memif. Every burst of traffic becomes a burst of DSA activity on the shared engine. The attacker runs the "
        "quiet DevTLB probe and counts evictions over time. Never sees a packet — only the rhythm."), 70)
    flow(s, [('Website visit', 'victim browser'), ('Packet movement', 'VPP / memif + DSA'),
             ('Engine activity', 'completion-slot eviction'), ('Observer trace', 'DevTLB miss counts')],
         y=TOP + .3, h=1.7, title_size=19, size=16, last_color='accent')
    key(s, 'A fingerprint is learned from traffic-induced accelerator activity.', y=5.4)

    # ---- 29 pipeline closed-world
    s = slide('The pipeline, laid bare — and it is closed-world', 'What it steals',
              'Paper § VI-B · pp. 9–10 · dataset arithmetic from stated split', notes(
        "Each site → a ~250-slot time series, each slot a count of evictions. Feed an attention-BiLSTM, standard here. "
        "Notice one honest word: closed-world. 100 KNOWN sites, train and test from the same 100. Legitimate and "
        "strong, but not open-world detection of arbitrary pages. I hold them to that in the critique."), 65)
    columns(s, [('Sampling', 'probe every 10 µs\n400 probes / slot\n≈ 4 ms per slot'),
                ('Model', '2 × BiLSTM\nattention + dropout\nsoftmax classes'),
                ('Dataset', '100 sites × 200 traces\n80 / 20 split\n≈ 16,000 / 4,000')],
            title_size=24)
    tx(s, 'One feature per slot = the number of classified DevTLB misses.', M, TOP + 3.7, CW, .4, 17, 'gray', italic=True)
    key(s, 'The evaluated problem is closed-world classification over known labels.')

    # ---- 30 website traces
    s = slide('The traces really are different', 'What it steals',
              'Paper § VI-B, Fig. 10 · p. 9 · original example traces', notes(
        "Three sites, three visibly different signatures — different burst timing and height. That's what the model "
        "keys on. No URLs, no content — just the silhouette of the accelerator working as the page loads. Striking "
        "that something this coarse separates sites at all."), 55)
    picture(s, 'website_traces', M + 1.0, TOP, CW - 2.0, 4.0)
    key(s, 'Temporal shape is the feature; miss count is a proxy for DSA activity.')

    # ---- 31 website results
    s = slide('85.73% — the number you must not misquote', 'What it steals',
              'Paper § VI-B, Fig. 11 · pp. 9–10 · original 15-site matrix', notes(
        "On all 100 sites: 85.73% vs a 1% coin-flip. Strong. CAREFUL: the pretty confusion matrix is a 15-site SUBSET "
        "at 96.5% — not the headline. Don't let anyone quote 96.5% as the result. Misses are sensible — sites with "
        "similar traffic shapes (canva, notion) blur; authors call it future work."), 70)
    picture(s, 'confusion', M, TOP, 7.7, 4.1)
    xx = M + 8.1
    stat(s, '85.73%', 'Full dataset', '100 websites · 1% baseline', xx, TOP + .2, 3.4, 'accent', num_size=44)
    stat(s, '96.5%', 'Displayed subset', '15 selected websites only', xx, TOP + 2.2, 3.4, 'black', num_size=44)
    key(s, 'The headline is 85.73% on 100 sites; 96.5% is the 15-site subset.', y=6.3)

    # ---- 32 keystroke path
    s = slide('Attack #2 — keystrokes, via transparent offload', 'What it steals',
              'Paper § VI-C · p. 10 · no end-to-end text recovery', notes(
        "DTO silently redirects ordinary memcpy-style calls to DSA, no code changes. So unmodified OpenSSH, handling "
        "each interactive keystroke packet, generates DSA activity per keypress. The attacker times those. The line I "
        "won't blur: the paper recovers keystroke TIMING, and notes it could feed a text model — it does NOT recover "
        "what you typed."), 70)
    flow(s, [('User input', 'interactive SSH event'), ('Packet handling', 'OpenSSH mem* calls'),
             ('DTO offload', 'eligible calls → DSA'), ('DSA observation', 'eviction or congestion')],
         y=TOP + .3, h=1.7, title_size=19, size=16, last_color='redtext')
    key(s, 'The demonstrated output is keystroke timing — not recovered command text.', y=5.4, color='redtext')

    # ---- 33 keystroke evidence
    s = slide('You can see the typing', 'What it steals',
              'Paper § VI-C, Fig. 12 · p. 10 · original filtered traces', notes(
        "Top: DevTLB attack; bottom: SWQ attack — both resolving 'ssh root' keystroke by keystroke. SWQ gives crisper "
        "spikes, foreshadowing its better timing. Honesty note for Q&A: events are filtered by byte-size and latency "
        "thresholds, so exact counts depend on those knobs — which matters for the next slide."), 60)
    picture(s, 'keystrokes', M, TOP, 7.9, 4.1)
    xx = M + 8.3
    tx(s, 'Read the panels', xx, TOP + .2, 3.2, .4, 16, 'accent', semi=True)
    hline(s, xx, TOP + .62, 3.2)
    for i, t in enumerate(['Top: completion latency', 'Bottom: queue contention', 'Labels: ground-truth input']):
        tx(s, t, xx, TOP + .85 + i * .55, 3.2, .5, 17, 'black')
    tx(s, 'Filtering affects event metrics; thresholds matter.', xx, TOP + 2.7, 3.2, .9, 15, 'gray', line_spacing=1.15)
    key(s, 'Both primitives reveal candidate keystroke events.', y=6.3)

    # ---- 34 keystroke results + caveat
    s = slide('SWQ wins timing — and a caveat I owe you', 'What it steals',
              'Paper § VI-C, Tables III–IV · pp. 10–12 · headline metrics as reported', notes(
        "SWQ wins keystroke timing cleanly — 98.4% F1, 1.21 ms spread vs 5.29 for DevTLB, exactly what timer-free "
        "predicts. Use these headlines. But full disclosure: the paper's own detection/FP/FN counts don't perfectly "
        "reconcile with the printed F1 (backup). Doesn't overturn the conclusion, but a careful reader should know."), 70)
    table(s, ['Primitive', 'Reported F1', 'Timestamp deviation (σ)'],
          [['DevTLB', '92.0%', '5.29 ms'], ['SWQ', '98.4%', '1.21 ms']],
          y=TOP, colfracs=[.33, .33, .34], rowh=.7, size=20, highlight=1, muted_cols=())
    tx(s, 'Reporting caveat: the detection / FP / FN counts in § VI-C do not fully reconcile with the printed F1 (see backup).',
       M, TOP + 2.3, CW, .5, 16, 'redtext', italic=True)
    key(s, 'Use the headline values with attribution; disclose the arithmetic gap.')

    # ---- 35 LLM setup
    s = slide('Attack #3 — fingerprinting the LLM next door', 'What it steals', 'Paper § VI-D, Table II · pp. 10–11', notes(
        "LLM inference shuffles weights around memory; with DTO those moves hit DSA. Different sizes/architectures move "
        "memory in different rhythms. A slightly longer 8ms window becomes a model fingerprint. Be precise: which of 8 "
        "KNOWN configs, under IDENTICAL prompts. Not stealing weights, not reading prompts, not open-world."), 65)
    table(s, ['Family', 'Parameter counts', 'Choices'],
          [['TinyStories', '15M / 42M / 110M', '3'], ['LLaMA 2', '7B', '1'],
           ['Gemma 3', '1B / 4B', '2'], ['Qwen3', '1.7B / 4B', '2']],
          y=TOP, colfracs=[.34, .44, .22], rowh=.6, size=18, muted_cols=(1, 2))
    tx(s, '50 traces per model · identical prompts · 80 / 20 split · 8 ms slots', M, TOP + 3.1, CW, .4, 17, 'gray',
       italic=True)
    key(s, 'The label is a model configuration — no weights or prompts are recovered.')

    # ---- 36 LLM results
    s = slide('98.6% — impressive, and bounded', 'What it steals',
              'Paper § VI-D, Fig. 13 · p. 11 · original model traces', notes(
        "98.6%. Traces differ across sizes within a family and across families at a size — the model gets both. "
        "Striking that an accelerator twitch distinguishes LLMs through two VM walls. But keep the fence: fixed "
        "prompts, fixed runtimes, same host. Proves separability, not open-world identification."), 65)
    picture(s, 'llm_traces', M, TOP, 7.9, 4.1)
    xx = M + 8.3
    stat(s, '98.6%', 'Validation accuracy', '8 model choices', xx, TOP + .3, 3.2, 'accent', num_size=48)
    tx(s, 'Generality beyond identical prompts and fixed runtimes remains open.', xx, TOP + 2.3, 3.2, 1.2, 16, 'gray',
       line_spacing=1.2)
    key(s, 'Distinguishable configurations within a controlled dataset.', y=6.3)


# ============================================================================= ACT V
def act5():
    divider(5, 'Does it hold up?', ['Robust across quiet / noisy and local / cloud',
                                     'Better than prior work on capacity and timing — not every axis',
                                     'The clean fix costs the thing DSA is for'])

    # ---- 37 robustness
    s = slide('It barely flinches under stress', 'Does it hold up?',
              'Paper § VI-E, Table III · p. 11 · all six reported rows', notes(
        "Full Table III, all six rows. Most numbers barely move — tight CIs, no collapse. The one row worth naming: the "
        "DevTLB keystroke F1 varies a few points (90.5-93.4%), and cloud / noise can even raise it; the covert, website, "
        "SWQ-keystroke and LLM numbers stay within a point. Synthetic PCIe and memory pressure don't save you. Precise "
        "language: they stressed background NOISE, not a dozen real tenants fighting the same engine. 'Robust to noise' "
        "is proven; 'robust to a busy multi-tenant host' is not — open question. (Local column = the paper's geometric-"
        "mean baseline; other columns are the reported noisy / cloud runs.)"), 70)
    table(s, ['Metric', 'Local', 'Noisy local', 'Cloud', 'Noisy cloud'],
          [['DevTLB covert (kbps)', '17.19', '16.81', '16.97', '16.52'],
           ['SWQ covert (kbps)', '4.02', '4.08', '3.96', '3.80'],
           ['Website accuracy', '85.7%', '86.0%', '85.5%', '85.1%'],
           ['DevTLB keystroke F1', '92.0%', '90.5%', '93.4%', '93.0%'],
           ['SWQ keystroke F1', '98.4%', '98.2%', '99.1%', '98.9%'],
           ['LLM accuracy', '98.6%', '98.6%', '97.7%', '98.0%']],
          y=TOP, colfracs=[.32, .17, .17, .17, .17], rowh=.55, size=16, muted_cols=())
    key(s, 'Robustness covers these stressors; broader tenant interference remains open.')

    # ---- 38 comparison
    s = slide('Better on two axes — honestly, not all', 'Does it hold up?',
              'Paper § VI-F, Table IV · pp. 11–12 · cross-paper values, not matched re-runs', notes(
        "Vs the prior IPI channel, DevTLB is ~5x capacity at a quarter of the error. SWQ has the best keystroke timing "
        "here. Fair referee: DEVIOUS actually has LOWER bit error than DevTLB. DSASSASSIN wins throughput and timing, "
        "not every axis. And these are cross-paper numbers, not a head-to-head — multipliers are indicative."), 70)
    table(s, ['Work / mechanism', 'Capacity', 'Bit error', 'Keystroke F1', 'Keystroke σ', 'Website acc.'],
          [['IPI', '3.45 kbps', '18.9%', '97.9%', '6.15 ms', '— (F1 80.4%)'],
           ['DEVIOUS / IOTLB', '2.16 kbps', '2.18%', '—', '10.08 ms', '98.9% ¹'],
           ['This work / DevTLB', '17.19 kbps', '4.63%', '92.0%', '5.29 ms', '85.7%'],
           ['This work / SWQ', '4.02 kbps', '13.11%', '98.4%', '1.21 ms', '—']],
          y=TOP, colfracs=[.26, .15, .13, .15, .15, .16], rowh=.6, size=16, highlight=(2, 3), muted_cols=())
    tx(s, '¹ DEVIOUS traces include GPU fingerprints; its IOTLB channel is since mitigated by PASID.   IPI’s keystroke F1 beats DevTLB; DEVIOUS’s bit error beats both.',
       M, TOP + 3.2, CW, .4, 14, 'gray', italic=True)
    key(s, 'Best on capacity (DevTLB) and keystroke timing (SWQ) — not on every axis.')

    # ---- 39 hardware mitigation
    s = slide('The clean hardware fix costs the thing DSA is for', 'Does it hold up?',
              'Paper § VII · pp. 11–12 · proposals, not shipped fixes', notes(
        "Root cause is structural: PASID TAGS entries but doesn't PARTITION the structure, and queue-full is a visible "
        "flag. Clean fix: partition the DevTLB by PASID like the IOTLB. Irony: that costs the capacity/perf DSA exists "
        "to provide. Hiding the queue flag collides with honest submitters needing retry info. Sketches, not deployed."), 65)
    card(s, 'DevTLB', 'Partition replacement state by PASID\n\nCost: capacity · area · utilization\nGoal: block cross-tenant eviction',
         M, TOP, 5.7, 3.0, title_color='accent')
    card(s, 'SWQ', 'Make queue-state feedback privileged\n\nChallenge: legit submission retries\nGoal: block occupancy inference',
         SW - M - 5.7, TOP, 5.7, 3.0, title_color='redtext')
    key(s, 'A defense must constrain interference and feedback, not just permissions.', y=5.6)

    # ---- 40 software mitigation
    s = slide('What an operator can do right now', 'Does it hold up?', 'Paper § VII · p. 12 · deployment guidance', notes(
        "Via accel-config: give sensitive tenants their own ENGINE — not just queue, callback to slide 10, because "
        "separate queues leave the DevTLB channel open. Don't share SWQs across trust boundaries. For crown-jewel "
        "paths, turn DSA off. This is the misconception most likely to bite an operator, so I say it twice."), 65)
    table(s, ['Exposure', 'Boundary', 'Software response'],
          [['DevTLB eviction', 'DSA engine', 'Allocate engines by trust domain'],
           ['SWQ admission feedback', 'shared work queue', 'Avoid cross-tenant SWQ sharing'],
           ['Sensitive-op offload', 'application path', 'Disable DSA on critical paths if needed']],
          y=TOP, colfracs=[.3, .28, .42], rowh=.72, size=18, muted_cols=(1,))
    key(s, 'Separate queues do not close the shared-engine DevTLB channel.', y=6.0, color='redtext')

    # ---- 41 mitigation cost
    s = slide('They measured the cost — not the leftover leak', 'Does it hold up?',
              'Paper § VII, Fig. 14 · p. 12 · original throughput chart', notes(
        "Their defense sprinkles random translations to confuse the attacker, and they honestly measure cost — up to "
        "~16-18% at small transfers, shrinking as transfers grow. The gap, and the perfect transition to critique: "
        "they measured what it COSTS, never how much leakage it LEAVES. Overhead study, not a proven fix."), 65)
    picture(s, 'mitigation', M, TOP, 7.9, 4.1)
    xx = M + 8.3
    tx(s, 'Maximum reported loss', xx, TOP + .2, 3.2, .4, 16, 'redtext', semi=True)
    hline(s, xx, TOP + .62, 3.2)
    for i, (a, b) in enumerate([('Native DSA', '15.7%'), ('DTO', '17.9%'), ('At', '256-byte transfers')]):
        tx(s, a, xx, TOP + .85 + i * .62, 1.6, .4, 18, 'black', semi=True)
        tx(s, b, xx + 1.5, TOP + .85 + i * .62, 1.7, .4, 18, 'gray')
    key(s, 'The plot measures throughput overhead; residual leakage is not quantified.', y=6.3)


# ============================================================================= ACT VI
def act6():
    divider(6, 'My verdict', ['The lasting contribution is the causal hardware analysis',
                              'Scope and reporting gaps qualify the headline claims',
                              'An isolation contract for shared accelerator state'])

    # ---- 42 strengths
    s = slide('What’s genuinely excellent', 'My verdict', 'Presenter assessment · paper §§ IV–VI', notes(
        "My honest take: the lasting contribution is NOT the kbps number — it's the reverse engineering. Disciplined, "
        "falsifiable, with a real negative control in E2, which most exploit papers skip. First public look inside DSA, "
        "and it reframes accelerator internal state as part of the isolation boundary. Credit — disclosed to Intel."), 65)
    bullets(s, [('Controlled reconstruction', 'page, field, queue, engine — each test is falsifiable'),
                ('A real negative control', 'E2: separate engines eliminate the cross-VM DevTLB eviction'),
                ('Two complementary interfaces', 'completion latency + admission feedback → distinct channels')],
            y=TOP + .3, gap=1.25)
    key(s, 'The work turns an implementation detail into an isolation question.')

    # ---- 43 limits
    s = slide('What I’d push back on', 'My verdict', 'Presenter assessment · paper §§ V–VII, esp. § VI-C', notes(
        "Four pushbacks. One: it rests on CO-LOCATION, assumed more than demonstrated. Two: classifiers are "
        "closed-world, fixed-prompt — generality unproven. Three: the SWQ attack is ACTIVE — jamming a queue the victim "
        "needs — so perf and detectability costs aren't really evaluated. Four: keystroke metrics don't reconcile. None "
        "breaks the core finding; they mean the shouting numbers need more evidence."), 70)
    table(s, ['Limit', 'What it changes'],
          [['Provisioning and co-location', 'who can reach the target — SWQ discovery is sketched; engine binding is assumed'],
           ['Closed-world / fixed-prompt datasets', 'how far classification accuracy generalizes'],
           ['Active congestion and probing', 'victim impact and possible detectability'],
           ['Metric inconsistencies / missing detail', 'confidence in exact quantitative claims']],
          y=TOP, colfracs=[.4, .6], rowh=.74, size=17, muted_cols=(1,))
    key(s, 'The shared-state leakage is well-supported; deployment reach needs more evidence.')

    # ---- 44 future work
    s = slide('The experiments I’d want to see', 'My verdict', 'Presenter-proposed · not reported in the paper', notes(
        "If I supervised the follow-up: close the loop on the defense — leakage AND throughput in one config, for the "
        "real security-performance curve. Break the closed world — train one day, test another; train some sites, test "
        "unseen. Study it under a crowd — many tenants, how loud and detectable the attacker is. My proposed "
        "experiments."), 65)
    columns(s, [('Isolation study', 'Residual leakage +\nthroughput\nPASID-aware replacement'),
                ('Generality study', 'Cross-day / cross-host\nUnseen sites / prompts\nMatched runtimes'),
                ('Deployment study', 'Many concurrent tenants\nVictim latency / retries\nProbe detectability')],
            title_size=24, title_colors=['accent', 'black', 'redtext'])
    key(s, 'Measure security and performance together, under the same configuration.')

    # ---- 45 takeaways (dark close)
    s = slide('Shared accelerator state belongs in the isolation model', 'My verdict',
              'Based on Chen et al., HPCA 2026 · main talk ends here', notes(
        "Where we landed — the sentence I opened with, now earned. VT-d guards addresses and works. But the accelerator "
        "behind that wall has a shared heartbeat — in its translation cache and its queue — and offloaded apps give it "
        "meaning. As we offload more, the isolation model must cover internal state, not just addresses. Open question: "
        "when a cloud sells an 'isolated' accelerator, what must that contract guarantee? Thank you."), 70, dark=True)
    for i, (num, t) in enumerate([('01', 'Engine sharing exposes DevTLB replacement.'),
                                  ('02', 'Queue sharing exposes admission feedback.'),
                                  ('03', 'Application offload gives those signals meaning.')]):
        tx(s, num, M, TOP + .15 + i * .95, 1.0, .6, 22, 'gray_dark', semi=True)
        tx(s, t, M + 1.1, TOP + .1 + i * .95, CW - 1.1, .6, 26, 'white', semi=True)
    rect(s, M, TOP + 3.35, .55, .045, 'accent')
    tx(s, 'Discussion: what should an accelerator isolation contract guarantee?', M, TOP + 3.55, CW, .6, 22,
       'gray_dark', semi=True)


# ============================================================================= BACKUP
def backup():
    def b(title, src, note, cat='Reference', secs=45):
        return slide(title, cat, src, note, secs, backup=True)

    s = b('Glossary', 'Paper §§ II–V · pp. 2–8', 'Reference for acronyms.', 'Glossary')
    table(s, ['Term', 'Meaning in this paper'],
          [['DSA', 'Intel Data Streaming Accelerator'], ['ATS / TA', 'Address Translation Services / Translation Agent'],
           ['ATC / DevTLB', 'device-side cache of address translations'], ['PASID', 'process address-space ID; translation context'],
           ['WQ / SWQ / DWQ', 'work queue / shared / dedicated work queue'],
           ['DMWr / ENQCMD', 'deferrable memory write / descriptor submission'], ['DTO', 'DSA Transparent Offload library']],
          y=TOP, colfracs=[.25, .75], rowh=.54, size=16, muted_cols=(1,))

    s = b('Descriptor layout — field meaning depends on opcode', 'Paper Fig. 3 · p. 4', 'Note the offset-24 overlap.',
          'Descriptor detail')
    picture(s, 'descriptor', M, TOP, 7.4, 4.1)
    table(s, ['Offset', 'Field', 'Slot'],
          [['0', 'opcode / flags / PASID', 'header'], ['8', 'completion record', 'comp'], ['16', 'source', 'src'],
           ['24', 'dest OR source2', 'dst / src2'], ['40', 'second dest', 'dst2']],
          x=M + 7.8, y=TOP, w=CW - 7.8, colfracs=[.22, .5, .28], rowh=.6, size=15, muted_cols=(1, 2))

    s = b('Observation windows have different constraints', 'Paper §§ IV-B–C, V-B–C · pp. 5–8',
          'Calibration / timing.', 'Timing & calibration')
    table(s, ['Aspect', 'DevTLB', 'SWQ'],
          [['Prepare', 'own comp-page cached', 'effective occupancy ≈ N−1'],
           ['Idle window', 'permit victim execution', 'shorter than holding copy'],
           ['Probe', 'time own completion', 'read acceptance / retry'],
           ['Calibration', 'hit / miss distributions', 'queue depth + drain'],
           ['Confounder', 'other users of the slot', 'other submissions / completions']],
          y=TOP, colfracs=[.2, .4, .4], rowh=.6, size=16, muted_cols=())

    s = b('Keystroke count arithmetic needs clarification', 'Paper § VI-C · p. 10 · diagnostic only',
          'Reported detection / FP / FN do not match the printed F1.', 'Reporting audit')
    table(s, ['For 512 ground-truth events', 'DevTLB', 'SWQ'],
          [['Reported detections / FP', '515 / 15', '511 / 7'], ['Implied TP = det − FP', '500', '504'],
           ['Implied FN = 512 − TP', '12', '8'], ['Printed FN / TP', '61 / 500', '9 / 507'],
           ['Diagnostic F1 (fixed totals)', '97.37%', '98.53%']],
          y=TOP, colfracs=[.5, .25, .25], rowh=.58, size=16, highlight=3, hl_color='redtext', muted_cols=())
    tx(s, 'These calculations expose the inconsistency; they do not repair the experiment.  Also: the abstract/contributions say 4.64% covert bit error; §VI-A and Table IV say 4.63%.',
       M, TOP + 3.5, CW, .6, 15, 'redtext', italic=True)

    s = b('Sampling and dataset sizes', 'Paper §§ VI-B, VI-D · pp. 9–11', 'Reproducibility.', 'Evaluation detail')
    table(s, ['Setting', 'Website task', 'LLM task'],
          [['Sample interval', '10 µs', '10 µs'], ['Samples per slot', '400', '800'], ['Slot duration', '4 ms', '8 ms'],
           ['Classes × traces', '100 × 200', '8 × 50'], ['Total traces', '20,000', '400'],
           ['80 / 20 split', '16,000 / 4,000', '320 / 80']],
          y=TOP, colfracs=[.4, .3, .3], rowh=.56, size=16, muted_cols=())

    s = b('Different metrics answer different questions', 'Paper §§ VI-A–F · pp. 9–12', 'What each metric means.',
          'Metric interpretation')
    table(s, ['Metric', 'Question it answers'],
          [['Raw rate / true capacity', 'how fast are attempts / useful bits reported?'],
           ['Bit error rate', 'how often does a decoded bit differ?'], ['Top-1 accuracy', 'how often is the class correct?'],
           ['Precision / recall', 'how many detections correct / events found?'],
           ['F1 = 2TP / (2TP+FP+FN)', 'balance of precision and recall'],
           ['Timestamp σ', 'how dispersed are timing differences?']],
          y=TOP, colfracs=[.35, .65], rowh=.56, size=16, muted_cols=(1,))

    s = b('The original cross-paper comparison table', 'Paper Table IV · p. 12 · blank cells = not reported',
          'DEVIOUS trace includes GPU fingerprints.', 'Prior-work detail')
    picture(s, 'comparison', M + .8, TOP, CW - 1.6, 4.0)

    s = b('Reproduction requires a configured DSA platform', 'Paper Appendix, p. 15 · authors’ artifact',
          'Hardware, victim software, artifact layout.', 'Artifact & reproducibility')
    bullets(s, [('Hardware & provisioning', 'DSA-capable Xeon; VT-d / IDXD; admin configuration + device access'),
                ('Victim-specific software', 'VPP / DPDK for websites; DTO-enabled SSH and inference workloads'),
                ('Artifact organization', 'playground → characterization; attack → traces; evaluate → metrics')],
            y=TOP + .1, gap=1.15, size=22)
    tx(s, 'github.com/hkustgz-secarch/dsassassin   ·   DOI 10.5281/zenodo.17799273', M, 6.2, CW, .4, 15, 'gray')

    s = b('Likely questions and concise answers', 'Answers from paper §§ IV–VII + presenter assessment',
          'Prepared Q&A.', 'Q&A preparation')
    table(s, ['Question', 'Answer'],
          [['Does encryption stop it?', 'content protection does not remove activity patterns'],
           ['Do separate CPU cores help?', 'the observations arise in shared DSA resources'],
           ['Do separate queues help?', 'SWQ: yes; DevTLB: also separate the engines'],
           ['Are typed characters recovered?', 'it evaluates event timing, not full text recovery'],
           ['Would timer removal solve it?', 'SWQ reads admission feedback without a duration'],
           ['Is random insertion a proven fix?', 'overhead is measured; residual leakage is not']],
          y=TOP, colfracs=[.36, .64], rowh=.58, size=16, muted_cols=(1,))

    s = b('Sources and provenance', 'Primary source: user-supplied hpca26dsassassin.pdf', 'Citation and links.',
          'References')
    bullets(s, [('Primary paper', 'Chen, Li, Deng, Wang, Chen. DSASSASSIN. HPCA 2026'),
                ('Author-hosted PDF', 'i.benx.dev/assets/hpca26dsassassin.pdf'),
                ('Artifact', 'github.com/hkustgz-secarch/dsassassin'),
                ('Archive + record', 'doi.org/10.5281/zenodo.17799273 · 2026.hpca-conf.org')],
            y=TOP + .1, gap=1.1, size=22)


# ============================================================================= build
act1(); act2(); act3(); act4(); act5(); act6(); backup()

from paper_visuals import apply as apply_paper_visuals
visual_changes = apply_paper_visuals(P)
for change in visual_changes:
    MANIFEST[change['slide'] - 1]['source'] = change['source']

from trim_deck import apply as trim_deck, remap_visuals
trim_report = trim_deck(P, MANIFEST)
visual_changes = remap_visuals(visual_changes)

PPTX = Path(sys.argv[sys.argv.index('--output') + 1]).resolve() if '--output' in sys.argv else OUT / 'DSASSASSIN_v2.pptx'
PPTX.parent.mkdir(parents=True, exist_ok=True)
save(PPTX)
(PPTX.parent / 'paper_visuals_manifest.json').write_text(json.dumps(visual_changes, ensure_ascii=False, indent=2), encoding='utf-8')
(PPTX.parent / 'trim_manifest.json').write_text(json.dumps(trim_report, ensure_ascii=False, indent=2), encoding='utf-8')
n_main = sum(1 for m in MANIFEST if not m['backup'])
print(json.dumps(dict(slides=len(MANIFEST), main=n_main, backup=len(MANIFEST) - n_main), indent=2))

if '--no-com' not in sys.argv:
    import subprocess
    PDF = PPTX.with_suffix('.pdf'); PNG = PPTX.parent / 'rendered'
    cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(HERE / 'export.ps1'),
           '-Pptx', str(PPTX), '-Pdf', str(PDF), '-PngDir', str(PNG)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout.strip())
    if r.stderr.strip():
        print('STDERR:', r.stderr.strip()[:2000], file=sys.stderr)
