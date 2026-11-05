# Design log: QRSM x Grover

Newest entries at the bottom. Expectations are written before the runs they predict. This continues the habit of the hidden-defect project, whose own log is in `prior_work/`.

## 5 Nov 2026, 14:00: the brief

From the team's Discord: "Probe and experiment with QRSM architecture fusion with Grovers algorithm ... Try to get something ready to test on ibm or another quantum compute cloud provider, and have a MVP for our quantum hackathon. Additionally a slide deck and digestible reports of our results with visuals."

Submission: a video of 15 minutes or less and a GitHub link, by 8:00 a.m. ET on 6 Nov, on DeepStation.

**The rubric** (from the event page): problem 15, why quantum and honest limits 20, working code and Qiskit use 20, results and baselines 10, originality 10, communication 15, Q&A and teamwork 10. Bonus: simulator 1, real hardware 3, hardware plus noise analysis or mitigation 5.

**What the research note warned** (`QRSM_Grover_Memory_Access_Analysis`):
- a QRSM state is not addressable memory;
- resets stop you inverting the machine, so Grover cannot run on it directly;
- a query speedup is not a time speedup, and the oracle or the reflection can dominate.

## 14:15: the idea

**Purify, then amplify.** Replace each reset with a fresh light qubit. By the deferred-measurement principle the click statistics do not change, and the whole T-step run becomes one unitary A. Then

    A|0> = sum over histories y of |m_y>|y>,   with <m_y|m_y> = P(y).

The state holds every click history at once, each with amplitude sqrt(P(y)). So Grover's search space is the machine's own **histories**. This answers the wall in the circuit diagrams note (figure 4): fitting or conditioning on hardware "keeps only the runs whose outputs match the record", which costs 1/p runs. Amplitude amplification costs about 1/sqrt(p) calls of A and A-dagger.

Amplification has two slots, and a recurrent machine can fill either one:
- **the state-preparation slot:** an emitter QRSM. Grover searches its histories.
- **the oracle slot:** a coherent reader QRSM. It reads a sequence and marks what matches. It may never forget, which is why the coherent QRSM that failed as a learner fits here.

**This is not a new algorithm, and we will not claim it is.** A literature check found:
- amplitude-amplified rejection sampling on Bayesian networks: Low, Yoder and Chuang, PRA 89, 062315 (2014);
- discrete stochastic processes run in superposition, with amplitude estimation, on IBM hardware: Blank, Park and Petruccione, npj QI 7, 126 (2021);
- superpositions of all future trajectories in a photonic experiment: Ghafari et al., Nat. Commun. 10, 1630 (2019);
- local or partial diffusion for shallower search: Zhang and Korepin, PRA 101, 032346 (2020).

What we add: the mapping onto hidden quantum models (QRSM emitters and readers), the reset problem and its fix, the memory reflection below, and a hardware-honest evaluation.

## 14:25: pilots, logged before the official runs

All of these used the default machine (theta 0.6, gamma 0.2, phi 0.45, zeta 0.3) and the FakeMarrakesh noise snapshot.

- **The purified state equals the Kraus branches** to 1e-16, for T up to 7.
- **The first metric was a trap.** "Any click" at T = 3 scores 87.5% from pure noise, since 7 of 8 random bitstrings count. So the hit rate alone proves little. The honest measure is whether the conditional distribution survives, so every noisy result now reports both, and the true overshoot (hit rate falling at r past the peak) is the coherence check.
- **Rare events hide under the noise floor.** At p = 0.00105 the noisy device reports 0.0029: plain sampling is 2.8 times too high, from readout and gate errors.
- **The reflection dominates the cost.** A 5-qubit multi-controlled Z costs 49 CZ on heavy-hex, or 27 with clean ancillas.
- **An unplanned finding: the memory reflection.** Reflecting on only the hidden memory (1 CZ for one defect), not on every qubit:
  - keeps most of the amplification for single-event questions at small r: T = 3 any click, r = 1, 2, 3 gives 0.544, 0.953, 0.861, against the exact 0.609, 0.994, 0.754;
  - bends the conditional distribution a little (TVD about 0.02);
  - fails for rare multi-click questions: at p = 0.001 the peak is 0.28, not 1.0.
- **Why it can work.** One iteration of Q' from A|0> gives exactly

      Q'|psi> = (1 - 4p)|psi> + 2|g> - 4A|l>

  where |g> is the marked part of |psi> and |l> is the leak: the part of the rewound marked state with the memory back at |0> but some light still on. With the full reflection |l> = 0. So the shortcut is exact to the extent that a rewound marked history leaves its trace in the memory.
- **Under noise the pilot favours the shortcut.** T = 3, click at step 3, r = 3: full reflection 213 CZ, hit rate 0.734, TVD 0.130; memory reflection 82 CZ, 0.826, 0.067. At T = 5: 456 CZ, 0.613, 0.331 against 180 CZ, 0.806, 0.159.

Because the idea came from these FakeMarrakesh pilots, the test below uses other device snapshots.

## 14:35: the official experiments, and expectations

**E1, the same machine, now rewindable** (`experiments/e1_purify.py`). Pass marks fixed now:
- amplitudes of A|0> equal the Kraus branches within 1e-12, for k = 0, 1, 2 and T up to 12;
- the dynamic circuit (measure and reset) and the purified circuit, each sampled 1,000,000 times on Aer at T = 6, agree: chi-square p above 0.001.

**E2, Grover on histories** (`e2_amplify.py`), T = 6, real Qiskit circuits, six predicates, r up to past the peak. Pass marks:
- |P_r - sin^2((2r+1) theta)| below 1e-9;
- conditional TVD below 1e-9;
- the hidden-qubit populations read from the amplified state equal the exact ones within 1e-9.

**E3, the post-selection wall** (`e3_scaling.py`).
- Exact records at T = 18, p from 0.1 to about 1e-6. Expected log-log slopes of calls per conditioned sample against p: rejection -1.00; amplification with known p -0.50 +- 0.02; BBHT (unknown p) -0.5 +- 0.1, at 2 to 6 times the known-p cost.
- Held-out 64-step records from the hidden-defect project: median 1/P(record) between 1e6 and 1e8 (the training loss of 0.266 nats per step implies about 2e7). Amplification would need about 1/sqrt of that, and we will state what that means in gates, which is far beyond today's hardware.
- The exact classical backward sampler: build time growing about 8 times per hidden qubit, and far faster than anything quantum at n = 2. This baseline should win everywhere we can test. That is the honest headline for this scale.

**E4, the memory reflection** (`e4_reflection.py`).
- Noiseless grid, T = 3 to 10, five predicates, reflections full, memory, emitter, lights, and windows. Expected: at r up to 3, memory reflection keeps at least 80% of the hit-rate gain for "any click" and "click at T" at T up to 6, with TVD below 0.1 (80% confident). It should lose most of the gain for "at least 2 clicks" and "contains 11" (85%).
- The leak predicts the damage: Spearman correlation between the leak fraction and the hit-rate loss at r = 1 is at least 0.7 (70%).
- Noisy Aer on five fresh snapshots (FakeFez, FakeTorino, FakeKingston, FakePittsburgh, FakeMiami), T = 3, 4, 5, "any click" and "click at T", r = 0 to 3:
  - at r >= 2, memory reflection has the higher hit rate in at least 80% of cells (70%), and the lower conditional TVD in at least 80% of cells (75%);
  - at r = 1 the hit rates split about evenly (no strong view);
  - the margin shrinks on the best devices, but survives at T = 5, r = 3 (60%).

**E5, Grover inside the recurrent loop** (`e5_inside_loop.py`). The note's experiment C asks to insert retrieval at selected timesteps. So: amplify "a click at step t", then keep running the machine on fresh lights. That reads the click-click correlation g2 after a rare event, which is the classic optics fingerprint: a two-level emitter cannot click twice at once (antibunching), and a defect that stores energy should bring clicks back later.
- Noiseless: exact against the filter within 1e-9, with post-selection on the verifiable bit.
- Noisy: at equal shots (4,096), the amplified estimate of P(click at t + tau | click at t) has lower total error than the plain-sampling one for most tau (65%). Over a large shot budget plain sampling should win, because it has lower bias.

**E6, the reader oracle: keyword search** (`e6_catalog.py`). Tim's idea: find a table in an unsorted catalogue from a vague request. Classical tokenising first, then a phase-layer QRSM reads the query one token at a time and Grover amplifies.
- Soft phases rank partial matches, not only exact ones. Expected top-1 agreement with the classical score on clear queries (80%).
- Oracle cost is reported apart from the search. Honest expectation: the oracle is compiled from the catalogue, so classical code has already read every entry, and there is no real speedup.

**Hardware** (`experiments/run_ibm.py`), only with the user's own account. Expected on a real Heron device, based on the fresh noisy snapshots: T = 3, click at step 3, memory reflection, r = 3: hit rate between 0.5 and 0.85, against 0.04 ideal at r = 0. To be updated when a device is chosen.

**Not planned:** the note's beat_20 benchmark, and large-scale retrieval. Neither fits the time, and we will say so.

## 15:05: E1 to E3 pass, and E5 finds a flaw in the memory reflection

**E1 and E2 passed their marks.** Largest amplitude error 3.9e-16; dynamic against purified chi-square p = 0.61 at 1,000,000 shots each; Grover curve, conditional TVD and hidden populations all within 8e-15 across six questions.

**E5's noiseless run exposed a real flaw.** With the full reflection, the amplified "click, then keep running" circuit gives the filter's conditional click rates to 1e-17. With the memory reflection it does not. With no defect it gives [0.091, 0.029, 0.009] where the truth is [0.018, 0.058, 0.101]. So the memory reflection keeps roughly the right histories but scrambles the hidden state they leave behind: the mean fidelity of the memory given the history is only 0.70 to 0.89. Hit rate and history TVD alone would never have shown this, so memory fidelity is now reported too.

**The diagnosis and the fix, found after seeing that result.** The leak is the rewound marked state with memory at |0> but a light still on. For "click at step t0" the biggest term is the very light the question marks. So watch that light too. Call this the **question-local reflection**: the memory plus the lights the question reads. For one step that is 3 qubits however long the record is. Pilot, T = 3 and 4 (`memory+last-1`):
- hit rates 0.319, 0.705, 0.968, against the exact 0.319, 0.709, 0.972;
- conditional click rates within 1e-4 (t0 = 3) and 5e-4 (t0 = 4);
- memory fidelity 0.9999, 0.9992, 0.9975 at r = 1, 2, 3.

The likely reason: the remaining leak needs an earlier click as well, so it is second order in the click rate. That predicts it degrades as T grows, since earlier clicks become likely.

**Limits to expect.** The saving exists only when a question reads few lights. "Any click" reads them all, so its question-local reflection is the full one.

**Expectations for the question-local reflection, written before these runs** (`e4b_local.py`; same five fresh snapshots):
- noiseless, click at step T, T = 3 to 12: hit rate within 0.03 of exact at r up to 3 for T up to 6, and history TVD below 0.05 for T up to 8 (60%). Degrades with T.
- noisy, T = 3, 4, 5, 6, r >= 2: beats the full reflection on hit rate and on TVD in at least 80% of cells (75%).
- noisy, against memory only: lower TVD in at least 60% of cells (65%), with a similar hit rate.
- E5 noisy, at 4,096 shots: amplification with this reflection has lower RMSE than plain sampling for tau = 2 and 3 (70%).

## 15:20: a steer from the user, and the rarity splits in two

**The user's note, mid-run:** "noise is a significant issue when it comes to grovers algorithm but luckily what we are doing for the hackathon doesn't have to be practical now or on current hardware but rather in the future, plus maybe it will lead to finding a more resilient architecture of what we are building, it just has to have potential."

So the goal shifts from "does it beat sampling on today's device?" to **"what architecture makes this as resilient as it can be, and what does that buy in future?"** Noise becomes a design constraint. Honest limits stay in.

**The time-local test.** If a machine forgets, an iteration may only need to rewind its last w steps. Pilot, click at step T, reflection on the lights in the window:
- **w = 1 gave TVD 0.000 and memory fidelity 1.000 at every T,** with a hit-rate boost of 4.8. An exact result from a crude cut needs an explanation, and it has one. A click's Kraus operator is K_1 = sin(alpha) |0><1| on the emitter, with one non-zero singular value, so amplifying it is perfectly uniform. It is the same as turning up the last emission: r iterations turn alpha into (2r + 1) alpha. **No Grover is needed for that part.**
- So the rarity of a click splits in two: the **emission factor** (gamma per click), which one gate angle removes exactly and for free, and the **population factor** (how likely the memory is to be excited), which is Grover's real job.

**Steering.** Set the emission of the clicked step to gamma'. Every history that clicks there scales by the same constant, so conditional distributions and hidden states stay exact, and p rises to p gamma' / gamma. This is what section 07 of the research note hoped for: concentrate the useful probability first, and use interference only for the rest. It is also a classical importance-sampling trick, so a fair baseline must use it too.

**Steer, then amplify.** Tune gamma' so p' = 1/4, and one iteration gives certainty. Pilot, T = 5 to 14: hit 1.000, TVD 0, fidelity 1.000, in one iteration where textbook needs 2 to 3. At T = 3 and 4, gamma' = 1 cannot reach 1/4, and one iteration gives 0.965 and 0.972.
- With the question-local reflection: hit 0.96 to 0.99 for T up to 6, 0.93 at T = 8, 0.76 at T = 12; TVD 0.035 to 0.12. It degrades at long T, as expected. There, watching all the lights does better (0.945 at T = 12), but that gate grows with T.

**The horizon.** With rewinding limited to 8 steps, at r = 2, the hit rate is 0.83, 0.87, 0.87 at T = 10, 12, 14. That hints that the cost per iteration can stop growing with T. It needs a real test.

**What this means for the claim.** The resilient architecture is four moves: **purify, steer, amplify locally, verify.**

**Expectations for E7, written before it ran** (`e7_resilience.py`; the five fresh snapshots; T = 3 to 6; click at step T):
- noiseless: steer + full, r = 1: hit within 1e-9 of 1 wherever gamma' < 1, and conditional TVD below 1e-9 (a theorem, so 99%).
- two-qubit gates: textbook at its peak r against steer + local at r = 1: at least 3 times fewer in every cell (85%).
- noisy: steer + local has a higher hit rate than textbook in at least 80% of cells (75%), and a lower conditional TVD in at least 70% (70%).
- the question after the click (E5): steer + local at 4,096 shots has lower RMSE than plain sampling at tau = 2 and 3 on at least 4 of 5 snapshots (65%).
- the horizon (T = 10 to 18, w = 4 to 10, r = 1 and 2): at fixed w the hit rate stays within 0.05 as T grows (60%).
- the wall: steering every clicked step cuts the median 64-step record from about 1e7 runs to about 1e3 to 1e5 (70%), and amplification takes the square root of what is left.

## 15:55: results, and the changes made along the way

**Changes to the plan, in order:**
- E5's noisy run was extended to include the steered build, before it ran on most devices. FakeMiami's first copy, which lacked it, was rerun.
- E4b's cells at T = 6 with the full reflection were dropped. 13-qubit trajectories at 32,768 shots were taking over an hour, and E7 already measures textbook at T = 6. So the comparison with textbook in E4b covers T up to 5.
- E7 on FakeFez and FakePittsburgh stalled at T = 6, and FakeTorino's process died. All three were restarted with the same seeds. Torino then finished in minutes. Fez and Pittsburgh stalled again on the full-reflection cells at T = 6, where a wider layout makes Aer fall back to one trajectory per shot, so those cells on those two devices use 8,192 shots in place of 32,768. Each row in the results records its shots.
- The hardware job's calibration went from one pair per layout (48 circuits) to one pair over every qubit used (2 circuits), which halved the estimated QPU time. Its echo circuits were compiling to nothing, because the transpiler rightly cancelled A against its inverse, so they now have barriers.

**E3.** Slopes -1.000, -0.500, -0.521. The median 64-step record costs 27,495,891 runs, and steering every clicked step (median 5 clicks) takes that to 6,240. The classical sampler's set-up grew about 5.7 times per hidden qubit, under load and with parallel linear algebra, where theory says 8.

**E4.** Mixed. The leak predicted the damage (Spearman 0.82). The memory reflection won TVD in 100% of cells at r >= 2, but hit rate in only 73%, under the 80% expected, and it lost hit rate almost everywhere at r = 1, where an even split was expected. Gain kept for single-event questions: median 88%, worst 63%, so the logged "at least 80%" failed. Multi-click questions were less clear-cut than expected: at larger T they are not rare, and the memory reflection does better on them.

**E5.** With the full reflection the circuit matches the filter to 7e-17. At 4,096 noisy shots, the steered, local build keeps about 3,600 shots where plain sampling keeps about 270. RMSE is lower at tau = 2 and 3 on 4 of 5 devices with a defect, and 5 of 5 without, as expected. Telling defect from no defect at tau = 3 goes from 2.4 to 7.0 standard errors.

**Wrong, and worth saying:** we expected plain sampling to win over a large shot budget, because it should have lower bias. It didn't. Its bias was the larger one, because false clicks swamp a rare click: at tau = 1 it reads about 0.07 where the truth is 0.01. Amplifying lifts true clicks above that floor.

**E6.** 19 of 20 vague requests found the right table, matching the classical score on all 20. The one miss is the tokeniser mapping "month" to "monthly". Ranking by score at r = 1 held for all 20. On 8 entries under noise, the target reaches 0.74 to 0.86, against 0.945 ideal. Cost: 32,800 gates at N = 1,024, against a 1,024-step scan. The recurrent reader undercuts a lookup table from about T = 10.

**E7.** Steer + local beat textbook on both hit rate and TVD in all 20 cells (5 snapshots, T = 3 to 6). Averaged over T, its median hit rate is 0.88 against 0.71, and its TVD 0.12 against 0.21. It used 2.9 to 5.3 times fewer two-qubit gates, a median of 5.2. The logged "at least 3 times in every cell" narrowly missed: the 2.9 is at T = 6, where textbook needs only r = 2. So "3 to 5 times" is the honest wording, not "5 times".

**Better hardware.** At T = 5 the hit-rate lead is 0.25 on the noisiest snapshot (FakeTorino, 0.42% two-qubit error) and 0.19 on the best (FakePittsburgh, 0.15%). It shrinks and survives, as expected.

**Another miss.** On noisy history TVD, the memory reflection beat the local reflection in 62% of cells: it has fewer gates. The logged "local wins at least 60%" failed. But history TVD can't see what the memory reflection breaks, which is the hidden state, so this result is a reminder of what that metric misses, and not a reason to prefer it.

**Scorecard:** 15 held, 5 partly, 5 missed, scored by calculation in `tools/build_docs.py`.

**The horizon.** At a fixed rewind of 8 steps the hit rate is 0.83, 0.87, 0.87, 0.84, 0.80 at T = 10 to 18: a span of 0.06, a little over the 0.05 expected. Memory fidelity stays above 0.98. TVD grows from 0.06 to 0.15, since older history isn't reweighted.
