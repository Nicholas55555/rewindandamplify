# Speaker script

Generated from the slides by `tools/render_deck.py`. Times assume 140 words a minute with a short pause per slide.

## 1. Rewind & Amplify  (0:00)

Hi, we’re presenting Rewind and Amplify. In the next thirteen minutes: how we fused Grover’s algorithm with a quantum recurrent model, what broke when we tried, and the noise-resilient design that came out of it. The orange tick in this click record is the kind of rare event this talk is about.

## 2. Rare events hold the answers, and cost the most to see  (0:24)

Quantum chips are held back by tiny hidden defects. You can’t put a probe on one. What engineers get is one qubit’s readout: click or no click, step after step, and the defect’s fingerprint is hiding in rare patterns of those clicks. Rare means expensive. Matching one real 64-step record from our model takes about 27 million runs. To learn what a chip does around a rare event, you pay for all the runs where it didn’t happen. That hits the people who calibrate chips, and anyone paying for quantum time.

## 3. Our model: a quantum recurrent state machine  (1:05)

Here’s the model. A QRSM is a recurrent network whose hidden state is quantum. Each step, an emitter is driven, a hidden defect turns, the two swap energy, and the emitter may give off light. We read the light, click or no click, then reset it. Earlier this week we showed this model can find a hidden defect from clicks alone, leaving under a tenth of a percent of the error, where a tuned LSTM leaves seventeen percent. But a model like this only generates. To ask it a question, all you can do is run it and throw runs away.

## 4. Asking it a question means throwing runs away  (1:50)

This is the wall. Conditioning on a record means keeping only the runs that match. That costs one over p runs, and every extra step multiplies it. The grey line is plain sampling, climbing into the tens of millions by 64 steps. The blue line is what Grover’s algorithm promises: the square root of that. So our team’s idea was simple to say: use Grover to search the machine’s own histories. The question was whether that could work at all.

## 5. Grover’s algorithm in one minute  (2:26)

Here’s Grover’s algorithm for anyone who hasn’t met it. A quantum computer can hold every possible answer at once, each with a weight. Step two: flip the sign of the answers you want. That changes nothing you could measure yet. Step three is the clever part: flip every weight around the average. The one you marked jumps up, and the others shrink. That’s interference doing the work. Repeat a few times, and a ten percent chance becomes nearly certain in just two rounds. Searching N things takes about the square root of N rounds. One warning: go too far and it overshoots.

## 6. You can’t Grover what you can’t rewind.  (3:12)

So can we just bolt Grover on? No, and our own research note said why. First, every Grover round runs the machine backwards, and our machine resets a qubit every step. A reset throws information away, so it has no inverse. You can’t Grover what you can’t rewind. Second, a hidden quantum state is not a database. It’s a compressed memory, with no records to look up. Third, fewer queries doesn’t mean less time, because rewinding and reflecting cost gates, and on real chips gates cost errors. Each of these needs a real answer.

## 7. Move 1: Purify. A fresh qubit replaces every reset  (3:54)

Here’s the first move, and the key to everything else. Instead of reusing one light qubit and resetting it, we give every step a fresh light, and measure nothing until the end. By the deferred measurement principle the click statistics can’t change. But now the whole run is one reversible circuit, and that state holds every possible click history at once, each with an amplitude equal to the square root of its probability. So Grover’s search space is the machine’s own past. We checked: amplitudes match the exact model to ten to the minus sixteen, and the two circuits click alike over a million shots each.

## 8. Grover now searches the machine’s histories  (4:42)

And it works. These dots are real Qiskit circuits, using Qiskit’s grover operator on the purified machine, and they sit right on Grover’s curve for all six questions we tried. The more important thing is on the right. Amplification doesn’t just find an answer, it reweights. Inside the matching histories, the relative odds never change. So every shot is an honest sample of the conditional distribution, with the hidden qubits right too. That’s conditioning. And it scales: at a one in a million event, it takes 725 times fewer machine calls, counting every rewind.

## 9. Noise punishes depth, so we redesigned around it  (5:24)

Now the honest problem. Grover is famously fragile, because every iteration rewinds the whole history and checks every qubit. Compiled for an IBM chip, the textbook version at five steps needs 456 two-qubit gates. At today’s error rates, most of those runs have a mistake in them. We don’t need this to be practical on today’s chips. But it made us ask a better question: what would a version built around noise look like? We ended up with four moves. Purify you’ve seen. Steer, and amplify locally, are new, and they’re the next two slides.

## 10. Move 2: Steer. Part of the rarity is free to remove  (6:07)

We found this one by accident, chasing why a crude approximation gave an exact answer. A click is rare for two reasons. Was the emitter excited? And did it emit? The second is just one gate angle. Turn it up, and every history that clicks there scales by the same number, so the conditional answer stays exactly right. For a real 64-step record, that takes 27 million runs down to about six thousand. Then Grover takes what’s left down to 125 calls. To be clear on the credit: steering is classical importance sampling. And if you tune the chance to exactly a quarter, a single Grover iteration gives certainty.

## 11. Move 3: Reflect only where the question looks  (6:56)

Move three attacks the most expensive gate in Grover: the reflection, which has to check every qubit. So we asked how much it really needs to look at. Watching only the two memory qubits looked great. The hit rate held up. Then a harder test showed the hidden state was scrambled, on the right here in yellow. Hit rate alone would never have shown that. The maths said why: what’s missed is the light the question marks. So watch that too. That’s the green line: three qubits, whatever the record length, and almost exact on short records. It does drift on long ones, and we’ll say so.

## 12. Across five IBM device models: fewer gates, better answers  (7:43)

Here’s the test, on five IBM device snapshots, none of them the one we developed the idea on, with circuits compiled for each device and simulated with its noise model. Left: two-qubit gates, with textbook Grover in blue and the resilient build in orange, three to five times fewer. Middle: the chance of getting the event. Right: how far the distribution is from the exact answer. In all 20 combinations of device and length, orange beat textbook on both. So a cheaper, slightly approximate circuit beats the exact one, because the error it adds is smaller than the noise it avoids. Grey has the least distortion, but it throws away over 90 percent of its shots.

## 13. Now it can answer a physics question  (8:35)

So what can you do with this? Here’s a real physics question: what happens right after a rare click? This curve is g-two, the correlation optics labs measure. With no defect, a click wipes the machine clean, so what follows simply restarts the run. With a hidden defect the curve differs from the very first step, because the defect remembers across the click. That’s a fingerprint of hidden memory, and you can only read it by conditioning. So we amplify the click and keep running: Grover inside the recurrent loop. On noisy device models, at the same 4,096 shots, that lifts the separation between defect and no defect from 2.4 to 7 standard errors.

## 14. The other slot: a QRSM as the oracle  (9:26)

Tim’s idea fits the other half of the architecture. Grover has two slots: what to search over, and what counts as a match. So far a QRSM has filled the first. Here a reader QRSM fills the second. It reads a vague request one token at a time, and each token turns the phase of every table that contains it. A full match gets a normal Grover mark, and a partial match gets a partial boost, which is what makes a vague search possible. It found the right table for 19 of 20 requests. The honest part: the oracle is compiled from the catalogue, so this shows the architecture, not a speedup.

## 15. Demo: real circuits, about a minute, no account needed  (10:16)

Here’s all of that running: one script, real Qiskit circuits, about a minute, no account needed. First, a rare click: plain sampling gets 8 percent usable shots, and steering plus one Grover iteration gets all of them. Second, what follows the click: the amplified answers match the exact filter, with and without a defect. Third, Tim’s search lands on the right table. The repository also has an interactive lab, where you can watch runs change as you switch builds.

## 16. Built for real IBM hardware, in proper Qiskit  (10:52)

On hardware, here’s exactly where we stand. Everything so far is simulation, including the IBM device noise models. The job is built and rehearsed: 39 circuits, with readout calibration and echo circuits that measure the noise directly. It runs twice, plain and with dynamical decoupling and Pauli twirling, to see what error suppression buys. It’s proper Qiskit throughout: the library’s Grover operator, preset pass managers, layouts chosen by the device’s own error rates, and SamplerV2. There are 110 automated tests, and the same code path has run end to end on a local device snapshot.

## 17. What we don’t claim  (11:35)

We want to be straight about the limits. No speedup today: a classical sampler gives an exact answer in about a millisecond. We rewind a model of the chip, never the chip, because a physical defect can’t run backwards. Steering is classical, and exact only for clicks at known steps. The local reflection is an approximation that drifts on long records. And the core idea isn’t new: amplified rejection sampling was published in 2014. What’s ours is applying it to hidden quantum models, and the design work to make it survive noise.

## 18. Why it has potential: where the classical baseline runs out  (12:16)

So why does this have potential, when today it loses to a laptop? Because of where each side runs out. Conditioning on a 64-step record takes about 2.7 million gates as textbook Grover, and about 40,000 once steered. Not today’s hardware. But IBM’s published target for 2029 is 200 logical qubits and 100 million gates. That would fit a machine with 50 hidden qubits and a 150-step record, and just holding that memory classically takes about 18 petabytes. That’s a rough estimate, not a result, but it’s where our classical baseline stops working.

## 19. What we learned, and who did what  (12:58)

Three things we’ll take away. Reversibility is a design choice: one reset decides whether Grover is possible at all. Exact isn’t always best: on noisy hardware, a cheaper, slightly wrong circuit beat the exact one. And test what you can’t see: our hit rate looked perfect while the hidden state was scrambled. To be open: the QRSM model existed before the event, the Grover fusion is new this week, and we built this with AI assistance from Claude. The code, tests and every result are in the repository. Thanks for listening.

**Total: about 13.7 minutes.**
