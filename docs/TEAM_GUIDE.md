# Team guide

Everything you need to record the video and answer questions, in one place. You don't need to read any code for this.

## Before 8:00 a.m. ET on Friday 6 November

- [ ] Add the team's names: cover slide, last slide, and the Team section of the README.
- [ ] Each person fills in their own part on the last slide.
- [ ] Run the hardware job if you can (section 5). The deck is accurate either way.
- [ ] Record the video: 15 minutes or less. Aim for 13. Everyone speaks (section 2).
- [ ] Publish the GitHub repository, and put its link on the last slide and in DeepStation.
- [ ] On DeepStation, submit the video and the GitHub link. It's the only submission platform.
- [ ] 1:30 p.m. Friday, SRHM 114: present at the ceremony. Certificates need both submitting and presenting.

## The project in one minute

**The problem.** The useful events in a quantum system are rare, and rare means expensive. Matching one real 64-step click record from our model takes about 27 million runs, because you throw away every run that doesn't match.

**The idea.** Grover's algorithm makes rare answers common, using about the square root of the work. But it has to run the machine backwards, and our machine resets a qubit every step. You can't Grover what you can't rewind.

**What we did.** We made the machine reversible, then redesigned Grover around noise, in four moves:

1. **Purify.** A fresh qubit replaces every reset. The whole run becomes one reversible circuit, holding every possible history at once.
2. **Steer.** Part of the rarity is just one gate angle. Tune it, and the event gets common for free, with the answer still exact.
3. **Amplify locally.** One iteration, with a reflection on 3 qubits instead of every qubit.
4. **Verify.** The click is measured, so a failed shot shows itself and is dropped.

**The result.** 3 to 5 times fewer two-qubit gates than textbook Grover, and better answers on all five IBM device models we tested. No speedup today, and we say so plainly. The point is the architecture, and where it could matter on future machines.

## Who presents what

This is a suggestion, so swap it around. Everyone speaking helps: the rubric asks whether all members contribute.

| time | slides | suggested speaker |
|---|---|---|
| 0:00 | 1-4: the problem, the model, the wall | Nicholas |
| 2:25 | 5-6: Grover in one minute, why it won't bolt on | Dan |
| 3:55 | 7-8: purify, and it works | Nicholas |
| 5:25 | 9-12: the resilient architecture and its results | Nicholas |
| 8:35 | 13: the physics fingerprint | Nicholas or Tim |
| 9:25 | 14-15: keyword search and the demo | Tim |
| 10:50 | 16-17: hardware and honest limits | fourth teammate |
| 12:15 | 18-19: potential, what we learned | fourth teammate, then all |

The speaker notes on each slide are written to be read aloud. They add up to about 13.5 minutes at a relaxed pace of 140 words a minute, which leaves room under the 15-minute limit. If you run long, cut slide 15 down to the raster clip, or skip the search demo.

## Recording the video

**The easiest way:** open `deck/Rewind_and_Amplify_deck_with_notes.pptx` in PowerPoint. Use Slide Show › Record, read your notes, then File › Export › Create a Video. Each person can record their own slides on their own laptop, and you can join the clips afterwards.

**For the demo slide,** either record your screen running `python demo/demo.py`, or show `results/figures/raster.mp4` and the interactive lab (`demo/index.html`).

**A fallback:** `tools/make_video.py` makes a complete narrated draft with a computer voice. It's useful for checking pace, or if time runs out. Your own voices will score better on communication.

**Submitting:** check the Submission tab on DeepStation, after signing in, to see whether it wants a file or a link. If it wants a link, an unlisted YouTube video or a Google Drive file set to "anyone with the link" both work. Test the link in a private window.

## Questions judges may ask

**Isn't this just known amplitude amplification?**
The core is, and we cite it: Low, Yoder and Chuang did amplified rejection sampling on Bayesian networks in 2014. What's ours is mapping it onto hidden quantum models, solving the reset problem, and the noise-resilient design: steering, the local reflection and its leak diagnostic, and an honest test across five device models.

**Why not just use a classical computer?**
At this size you should. An exact classical sampler gives a sample in about a millisecond. Its cost grew about 6 times per hidden qubit in our tests, and it took 10 minutes just to set up at 11 hidden qubits. So quantum could only matter for large hidden memories, and we can't test that today.

**Then where could quantum help?**
Two places. When the hidden memory is too big to simulate, running the circuit is the only way to sample it, and Grover then cuts the cost of conditioning from 1/p to 1/√p. And our estimate says that regime fits inside IBM's published 2029 target: 50 hidden qubits and 150 steps in 200 logical qubits, where the memory alone would be about 18 petabytes classically. That's an estimate, not a result.

**You can't rewind a real chip, so what's the use?**
Right, and we say so. We rewind a model of the chip, the QRSM, which was learned from its clicks. A physical defect can't be run backwards. So this is for querying a learned model, not the device.

**Doesn't the oracle need to know the answer?**
No. It checks a property of a history you could verify by eye, such as "there's a click at step 3". What you want is the distribution of everything else given that. In the keyword search it's different: the oracle is compiled from the catalogue, so classical code has already read every entry. That's why that demo has no speedup.

**Isn't steering just importance sampling?**
Yes, and it's classical. It gets most of the gain on the 64-step record: 4,400 times, against about 50 times from Grover on top. We count it in the baseline to be fair. It's exact here because a click's operator has a single non-zero singular value, so scaling it scales every matching history equally.

**Why does the local reflection work?**
One iteration gives exactly (1 - 4p)|psi> + 2|g> - 4A|l>, where |l> is the leak: the part of a rewound marked history with the memory back at zero but a light still on. Watching the question's light removes the largest term. What's left needs an earlier click as well, so it's second order. That's why it drifts on long records, where earlier clicks are likely.

**How do you know p, if the event is rare?**
You don't need it precisely. Steering is forgiving: anything from p' = 0.18 to 0.32 gives a hit rate above 0.94. With p unknown altogether, the standard BBHT schedule costs about 2 times more, and it still scales as the square root.

**What about noise, really?**
It's the central problem, and we made it a design constraint. Noise floors can fool you: "any click" at 3 steps scores 87.5% from pure noise, so we report the conditional distribution and hidden-state fidelity too. For very rare events, plain sampling on a noisy device reads about 3 times too high, because false clicks swamp true ones.

**Why do you need a fresh qubit for every step?**
Reversibility needs the history kept somewhere. That costs T extra qubits. A dynamic circuit with reset needs only one light, but it can't be rewound. It's a real trade: qubits for invertibility.

**Why a QRSM, and not any other circuit?**
The recurrent structure is what the design uses. The memory is a bottleneck, so a reflection can watch only that and the question's light. The physics-shaped click operator is what makes steering exact. A free-unitary model has neither, and at about 136 two-qubit gates a step it would be far too deep.

**What would you do next?**
Run more on real hardware, extend steering to learned models, add error detection, and rewind only as far as the memory reaches.

## Running on real IBM hardware

1. In a terminal in this folder, run `python tools/save_ibm_account.py` and paste your API key at the hidden prompt. Your key is stored by Qiskit in your home folder, never in this repository.
2. `python experiments/run_ibm.py --plan` picks a device, compiles everything and estimates QPU time. It uses no QPU time.
3. `python experiments/run_ibm.py --predict` simulates those exact circuits with the device's noise model, one small circuit at a time. It uses no QPU time. Never give a simulator a circuit compiled for the whole device: that appears to have crashed a laptop.
4. `python experiments/run_ibm.py --submit` sends two jobs: one plain, one with dynamical decoupling and twirling.
5. `python experiments/run_ibm.py --fetch` waits and saves the results. IBM's queue can take minutes or hours.
6. `python experiments/analyse_hardware.py`, then `python experiments/make_figures.py`, make the tables and the charts.

Then update the hardware slide with the real numbers and job IDs. Real hardware is worth up to 8 bonus points, and showing the job IDs matters.

## Glossary

- **Amplitude.** A qubit state's weight. Its square is a probability, and it can be negative, which is how interference works.
- **Amplitude amplification.** Grover's algorithm in its general form: any starting state, any marked set.
- **CZ.** The two-qubit gate on IBM Heron chips. Two-qubit gates cause most of the errors, so we count these.
- **Conditioning.** Asking "what is this, given that?" For a sampler, that means keeping only the runs where "that" happened.
- **Dynamic circuit.** A circuit that measures and resets in the middle. Ours did, before purifying.
- **Hit rate.** The chance a shot has the event you asked about.
- **Oracle.** The part of Grover that marks the answers you want, by flipping their sign.
- **Purify.** Replace each reset with a fresh qubit, so the whole run is reversible.
- **QRSM.** Quantum recurrent state machine: a recurrent model whose hidden state is quantum.
- **Reflection.** The second half of a Grover iteration: flip everything about the start state.
- **Steering.** Changing one gate so the event is common, in a way that keeps the conditional answer exact.
- **TVD.** Total variation distance: how far a distribution is from the right one. 0 is perfect, 1 is as wrong as possible.
