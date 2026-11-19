# PREDICT-E: A Biologically Plausible Predictive-Coding Network with Engram Allocation for Classification

*Assumptions stated up front (per the task's defaults): (1) learning uses local, biologically plausible rules rather than end-to-end backpropagation; (2) the model is specified concretely enough to implement — populations, equations, update rules, and pseudocode are given; (3) classification is discussed against standard benchmarks (MNIST/Fashion-MNIST/CIFAR-10) and few-shot/continual-learning settings where engram-like memory matters most.*

## TL;DR

- **We propose PREDICT-E**, a hierarchical predictive-coding network (Rao & Ballard 1999; Whittington & Bogacz 2017) whose top layer is not a dense representation but a **sparse, competitively allocated engram store** (Josselyn & Tonegawa 2020), trained with local Hebbian/delta-rule plasticity and no backpropagation — combining the *generalization* strength of predictive coding with the *one-shot, interference-resistant* memory of engram ensembles.
- The core novelty: **classification is read out from which engram ensemble is reactivated by prediction-error minimization**, and new classes/examples are written by CREB-style excitability-based allocation (Han et al. 2007; Yiu et al. 2014; Cai et al. 2016) into previously silent units — giving native few-shot and continual-learning behavior that standard predictive-coding networks (PCNs) and backprop CNNs lack.
- **Honest expectation**: on standard benchmarks the model should roughly match other biologically plausible learners — the Whittington & Bogacz (2017) PCN (784-600-600-10) reaches ~98.2% on MNIST (sub-2% error), and the strongest equilibrium-propagation / difference-target-propagation variants reach ~88–90% on CIFAR-10 — i.e. below strong backprop CNNs, but PREDICT-E should *outperform* all of them on one-shot writing, class-incremental continual learning, and calibrated uncertainty, which is where the proposal earns its keep.

## Key Findings (the literature that motivates the design)

1. 1. **Engrams are sparse, competitively allocated ensembles.** Liu et al. (2012, *Nature* 484:381–385) state verbatim that "sparse populations of DG granule cells (2–4%) are activated in a given context," [PubMed Central][ref-01] whereas the lateral amygdala recruits a higher fraction — Kim et al. (2024, *Nat. Neurosci.*) note the LA "recruits 10–30% of its neurons per fear memory engram." [Nature][ref-02] Allocation is biased toward transiently more-excitable neurons via CREB (Han et al. 2007; Zhou et al. 2009); Yiu et al. (2014) showed neurons with artificially elevated excitability "are preferentially recruited into the... memory trace." [PubMed Central][ref-03] This is a *winner-take-all with an excitability prior* — directly implementable.
2. 2. **Silent engrams and systems consolidation.** Kitamura et al. (2017, *Science* 356:73–78) showed a rapid write of an *immature, silent* prefrontal engram at day 1 alongside a hippocampal engram that becomes silent over ~2 weeks — a fast sparse write plus slow maturation. Complementary learning systems (CLS) theory (McClelland, McNaughton & O'Reilly 1995; Kumaran, Hassabis & McClelland 2016) explains why a fast sparse store plus a slow interleaved store avoids catastrophic forgetting.
3. 3. **Predictive coding maps cleanly onto cortical microcircuitry.** Bastos et al. (2012, *Neuron* 76:695–711) [NCBI][ref-04] assign error units to superficial layers 2/3 (feedforward, gamma) and representation/prediction units to deep layers 5/6 (feedback, alpha/beta). Positive and negative prediction-error neurons are observed experimentally in mouse V1 (Keller & Mrsic-Flogel 2018; Jordan & Keller 2020; Attinger et al. 2017). [bioRxiv][ref-05]
4. 4. **Predictive coding can learn by local rules that approximate backprop.** Whittington & Bogacz (2017) proved PC with local Hebbian plasticity approximates backprop in MLPs; [Ox][ref-06] [OpenReview][ref-07] Millidge, Tschantz & Buckley (2022) extended this to arbitrary computation graphs; [IJCAI][ref-08] [PLOS][ref-09] Song et al. (2020, Z-IL) gave an exact-backprop variant. PCNs can simultaneously act as classifiers, generators, and associative memories, even on arbitrary graph topologies [arXiv][ref-10] (Salvatori et al. 2021, 2022).
5. 5. **Prior art gets close but stops short.** Barron, Auksztulewicz & Friston (2020, *Prog. Neurobiol.* 192:101821) unify memory recall and prediction in one hippocampal-neocortical predictive-coding circuit (recall as "fictive prediction error"); [Ovid][ref-11] Tang, Salvatori et al. (2023, *PLOS Comput. Biol.*) build recurrent covariance PCNs as hippocampal associative memories; [PLOS][ref-12] the Tolman-Eichenbaum Machine (Whittington et al. 2020, *Cell* 183:1249–1263) is a predictive generative hippocampal model; [nih][ref-13] Rao, Gklezakos & Sathish (2022/2024) propose Active Predictive Coding. [eScholarship][ref-14] **None couples competitive, excitability-based engram allocation to a predictive-coding classifier as the read-out mechanism.** That is the gap PREDICT-E fills.

## Details

### 1. Motivation and the gap

Standard PCNs (Whittington & Bogacz 2017) are trained discriminatively and behave like MLPs: their top layer is a dense code, and learning a new class or example perturbs shared weights, causing catastrophic forgetting. Engram neuroscience offers a different memory substrate — a sparse ensemble, competitively allocated, whose reactivation *is* the memory. CLS theory (Kumaran et al. 2016) tells us these two systems are complementary, not competing. PREDICT-E fuses them: a predictive-coding "neocortex" that learns slow, generalizable features, capped by an engram "hippocampus" layer that writes fast, sparse, one-shot memories and provides the classification read-out. The model is meant to be concrete enough to implement, using only local plasticity.

### 2. Architecture (populations, layers, connectivity)

PREDICT-E is an *L*-level hierarchy. Levels 0…*L*–1 are a standard predictive-coding stack; level *L* is the **engram store**.

**Per predictive-coding level ℓ (following the Bastos et al. 2012 laminar assignment):**

- **Representation/prediction units** rℓ (deep-layer 5/6 analog): hold the current estimate of causes; project *top-down* predictions to level ℓ–1.
- **Error units** εℓ, split into **positive** (ε⁺) and **negative** (ε⁻) populations (superficial layer 2/3 analog; Keller & Mrsic-Flogel 2018), because firing rates are non-negative. [ResearchGate][ref-15] They compute the mismatch between rℓ and the top-down prediction from rℓ₊₁ and pass it *feedforward*.
- **Precision interneurons** πℓ: gain-control units that weight error signals (precision = inverse variance), implemented as divisive/lateral inhibition and modulated by a neuromodulatory signal (dopamine/acetylcholine as uncertainty/precision signals; Yu & Dayan 2005).

**Engram store (level L):**

- A large population of *M* engram units e (M ≫ number of classes), each with an **intrinsic excitability variable** bⱼ (CREB analog).
- **k-winners-take-all (k-WTA)** lateral inhibition enforces sparsity: only the top-k units (k/M ≈ 2–5%, matching the 2–4% DG statistic from Liu et al. 2012) are active for any input.
- Bottom-up weights W\_up (feature → engram) and top-down generative weights W\_down (engram → features). W\_down lets an active engram *predict* the feature representation r\_{L-1}, closing the predictive-coding loop.
- Each engram unit carries a **class tag** vector (a small set of label-associated synapses), so a reactivated ensemble votes for a class.

### 3. Mathematical formulation

**Free-energy / objective.** As in variational predictive coding, the network minimizes a sum of precision-weighted squared prediction errors plus a sparsity/allocation penalty:

F = Σℓ (1/2) εℓᵀ Πℓ εℓ + λ·S(e) , with εℓ = rℓ − f(W\_{ℓ+1} r\_{ℓ+1})

where f is a nonlinearity, Πℓ the precision (gain) matrix, and S(e) a sparsity penalty (e.g., an L1/entropy term or the hard k-WTA constraint). This is the Rao–Ballard/Friston energy augmented with an engram-sparsity term.

**Inference dynamics (fast, within-example).** Representation units descend the energy gradient:

τ ṙ ℓ = −∂F/∂rℓ = −Πℓ εℓ + (∂f/∂rℓ)ᵀ Π\_{ℓ−1} ε\_{ℓ−1}

i.e. each unit is driven by its *own* error minus the top-down-weighted error it explains away — a purely local rule. Error units follow εℓ ← rℓ − f(W\_{ℓ+1}r\_{ℓ+1}), with ε⁺ = \[εℓ\]₊ and ε⁻ = \[−εℓ\]₊.

**Engram activation and allocation.** The engram pre-activation is aⱼ = wⱼᵀ r\_{L-1} + bⱼ (excitability bias). The active ensemble is E = k-WTA(a). During *learning of a new pattern*, allocation is biased by excitability exactly as in Han et al. (2007) / Yiu et al. (2014): units with transiently high bⱼ win the competition. After allocation, winners undergo homeostatic excitability reset (bⱼ decays), implementing the transient excitability window that produces memory co-allocation "within 5 hours but not 7 days" [biorxiv][ref-16] (Cai et al. 2016, *Nature* 534:115–118) [PubMed Central][ref-03] — in-model, a decaying counter that links temporally adjacent examples into overlapping ensembles.

**Plasticity (local, three-factor).** All weights update by a delta/Hebbian rule using the *locally available* error:

- ΔW\_ℓ ∝ Πℓ εℓ · f(r\_{ℓ+1})ᵀ (predictive-coding delta rule; Whittington & Bogacz 2017)
- ΔW\_up ∝ (e − ⟨e⟩) r\_{L-1}ᵀ (Hebbian, gated to active winners)
- ΔW\_down ∝ Π\_{L-1} ε\_{L-1} eᵀ (generative, so engrams learn to predict features)
- Δ(class tag) ∝ eⱼ · (label − prediction) (local delta; the supervised label acts as a somatic teaching signal, à la Urbanczik & Senn 2014, dendritic prediction of somatic spiking) [Neuron][ref-17]

Anti-Hebbian lateral weights among engram units and homeostatic threshold adaptation maintain the target sparsity.

### 4. Training and inference algorithm (pseudocode)

# ---- TRAINING (per example (x, y)) ----clamp r\_0 = x initialize r\_ℓ by a fast feedforward pass (Whittington-Bogacz init) for t in 1..T\_infer:                       # inference relaxation    for each level ℓ: ε\_ℓ = r\_ℓ - f(W\_{ℓ+1} r\_{ℓ+1})    a = W\_up·r\_{L-1} + b                    # engram drive + excitability    E = kWTA(a, k)                          # sparse ensemble (2–5%)    for each level ℓ: r\_ℓ += (η/τ)·(-Π\_ℓ ε\_ℓ + (∂f)ᵀ Π\_{ℓ-1} ε\_{ℓ-1})    if supervised: clamp class-tag error using label y until ΔF < tol  (typically T\_infer ≈ 20–100 iterations, per PCN practice) # ---- ALLOCATION (write) ----if example is novel (high residual error / new label):    select winners among high-excitability units b    strengthen W\_up, W\_down, class-tags for winners (Hebbian/delta)    reset excitability b of winners; leave a decaying trace for co-allocation # ---- WEIGHT UPDATE (local) ----for each level ℓ: W\_ℓ += α·Π\_ℓ ε\_ℓ f(r\_{ℓ+1})ᵀ update W\_up, W\_down, class-tags as above homeostatic update of thresholds/precision to keep sparsity ≈ target # ---- INFERENCE / CLASSIFICATION (test) ----clamp r\_0 = x; relax r\_ℓ for T\_infer steps (labels free) E = kWTA(a, k)                              # reactivated engram ensemble ŷ = softmax( Σ\_{j∈E} class\_tag\_j )         # ensemble votes confidence = 1 / (Σ\_ℓ ε\_ℓᵀ Π\_ℓ ε\_ℓ)       # residual free energy = uncertainty

Practical hyperparameters (from PCN practice; Whittington & Bogacz 2017; Millidge et al. 2022): MLP such as 784-600-600-10 for MNIST; [ResearchGate][ref-18] T\_infer ≈ 20–100 relaxation steps; inference step η/τ ≈ 0.1; learning rate α ≈ 1e-3 with Adam; [PubMed][ref-19] engram sparsity k/M ≈ 2–5%.

### 5. How classification is read out

Classification is **not** a final linear layer trained by backprop. Instead, an input is explained by relaxing the predictive-coding hierarchy; this reactivates a sparse engram ensemble by pattern completion (CA3-style attractor dynamics; Rolls 2013). The reactivated ensemble's class-tag synapses vote for a label. Because the read-out is the *identity of the reactivated ensemble*, adding a new class = allocating new engram units, not reshaping a shared softmax — the mechanism that gives continual-learning robustness.

### 6. Predicted advantages and how to test them

- **One-shot / few-shot learning**: a single presentation can allocate a dedicated ensemble (like a single fear-conditioning trial). *Test*: Omniglot/miniImageNet few-shot; compare to a matched PCN without allocation.
- **Continual / class-incremental learning**: sparse non-overlapping allocation + generative replay from W\_down (deep generative replay; Shin et al. 2017; CLS, Kumaran et al. 2016) should sharply reduce forgetting. *Test*: Split-MNIST / Split-CIFAR class-incremental; report average accuracy and backward transfer vs EWC, standard PCN, backprop.
- **Uncertainty estimation**: residual free energy is a native confidence/OOD score. *Test*: OOD detection (e.g., MNIST-vs-Fashion) using residual energy; compare AUROC to max-softmax baselines.
- **Associative recall/robustness**: partial or noisy inputs should complete to the right ensemble (Salvatori et al. 2021 show PCNs are strong associative memories). *Test*: occluded-image classification.

### 7. Falsifiable neuroscience predictions

1. 1. In laminar recordings, the *engram-tagged* neurons should behave like deep-layer representation/prediction units (L5/6), while their reactivation should be *preceded* by transient superficial-layer prediction-error bursts (testable with layer-resolved imaging during recall; extends Bastos et al. 2012 and Keller & Mrsic-Flogel 2018).
2. 2. Engram allocation should be predicted by a *precision/excitability* signal: raising neuromodulatory gain (ACh/DA) at encoding should widen the allocated ensemble and reduce pattern separation — a quantitative dose–response prediction beyond Cai et al. (2016).
3. 3. Selectively silencing the top-down generative (W\_down) pathway should abolish *pattern completion* (recall from partial cues) while sparing feedforward recognition — a dissociation testable with pathway-specific optogenetics, echoing the synapse-specific manipulations of Abdou et al. (2018, *Science* 360:1227–1231), who showed synapse-specific plasticity gives each memory its identity within a shared engram [PubMed][ref-20] and permits selective erasure of one memory.
4. 4. Co-allocation (shared ensembles) should occur only within the model's excitability-decay window, predicting a specific temporal-overlap curve matching the ~5-hour linking window (Cai et al. 2016; and the CCR5/CCL5 window-closing mechanism of Shen et al. 2022, *Nature* 606).

### 8. Comparison table

| Model | Bio-plausibility | Classification (MNIST / CIFAR-10) | One-shot | Continual learning | Known weakness |
| --- | --- | --- | --- | --- | --- |
| Backprop CNN | Low: weight transport and global loss | ~99.7% / ~95%+ | Poor | Poor: catastrophic forgetting | Not biological; requires many labels |
| Standard PCN (Whittington & Bogacz 2017; Salvatori 2022) | High: local Hebbian/delta learning | ~98.2% (sub-2% error) / "indistinguishable from backprop", with ~100× compute (Millidge et al. 2022) | Poor | Poor | Iterative inference is slow; difficult scaling to deep nets |
| CLS / hippocampal replay models (Kumaran et al. 2016) | Medium-high | good when replay is used | Medium | Strong | Requires complex two-system machinery |
| Hopfield / Modern Hopfield (Ramsauer et al. 2020) | Medium | through a read-out layer | Strong: one-shot storage | Medium | Attractors are isolated, without structure between memories |
| HTM (Hawkins & Ahmad 2016) | High: dendritic and sparse | not competitive on benchmarks | Strong for sequences | Strong | Weak on standard supervised benchmarks |
| **PREDICT-E (proposed)** | High: local + laminar + engram | expected ~98% / ~85–90%, by extrapolation | **Strong** | **Strong** | Unproven; possible fragmentation from allocation; scaling not tested |

*Benchmark anchors for "biologically plausible" context: equilibrium propagation — naive ~86% error on CIFAR-10, improved to 11.7% error [nih][ref-21] (~88%, Laborieux et al. 2021); difference target propagation — 89.38% CIFAR-10 within <1% of backprop (Ernoult et al. 2022); [Proceedings of Mac…][ref-22] feedback alignment — ~63% CIFAR-10 (Bartunov et al. 2018), collapses on ImageNet (6.6% vs 50.9% BP); [arxiv][ref-23] Forward-Forward (Hinton 2022) — ~1.4% error MNIST (~98.6%), [University of Toronto][ref-24] ~59–60% CIFAR-10.*

### 9. Well-supported vs. speculative

- **Well-supported by evidence**: excitability-biased, sparse competitive engram allocation (Han et al. 2007; Yiu et al. 2014; Liu et al. 2012); the superficial-error/deep-prediction laminar division (Bastos et al. 2012; Keller & Mrsic-Flogel 2018); local delta-rule PC learning that approximates backprop (Whittington & Bogacz 2017; Millidge et al. 2022); continual learning through CLS/replay (Kumaran et al. 2016).
- **Plausible extrapolation**: reading uncertainty from residual free energy; obtaining class predictions by ensemble voting; using co-allocation as an in-model mechanism for temporal linking.
- **Frank speculation**: the particular numerical benchmark expectations for PREDICT-E, which nobody has built; whether competitive allocation will scale smoothly to CIFAR-scale features; and whether the excitability window will provide a useful curriculum/temporal-linking signal for classification.

## Recommendations

1. 1. **Stage 1 — MNIST/Fashion-MNIST proof of concept.** Implement the *L*-level PCN with a k-WTA engram top layer and ensemble read-out (e.g., 784-600-600-M with M large, k/M ≈ 2–5%). Benchmark against a matched standard PCN. *Success threshold*: within ~1% of the PCN's ~98.2% MNIST accuracy while using a sparse top layer. If it fails to reach ~96–97%, the allocation/read-out is fragmenting the code — revisit k and the class-tag rule.
2. 2. **Stage 2 — Continual learning.** Run Split-MNIST class-incremental. *Threshold that would justify continuing*: average accuracy meaningfully above EWC and standard PCN with no task boundaries provided. This is the model's main selling point; if it does not beat replay-free baselines here, the engram premise is not paying off.
3. 3. **Stage 3 — Few-shot + uncertainty.** Test one-shot allocation (Omniglot) and residual-energy OOD detection. *Threshold*: one-shot allocation should exceed a nearest-neighbor-on-features baseline; OOD AUROC should beat max-softmax.
4. 4. **Stage 4 — Scale to CIFAR-10** with a convolutional predictive-coding front end (Millidge et al. 2022). *Threshold*: ~85%+ would be a strong result for a biologically plausible allocation model; below ~75% indicates the sparse engram bottleneck is throttling capacity — consider multiple ensembles per class or larger k. Budget for the ~100× inference-compute overhead of convolutional PCNs.
5. 5. **Throughout**, keep every learning rule local and log the falsifiable predictions (Section 7) as analyses a neuroscientist could later test.

## Caveats

- **No one has built PREDICT-E**; all performance figures for it are extrapolations from adjacent models, not measurements.
- **PCN inference is iterative and slow** (~20–100 relaxation steps per example; Millidge et al. 2022 report "roughly a 100× greater computational cost than the backprop network" [arxiv][ref-25] for convolutional PCNs), so training cost is a real obstacle.
- **Engram sparsity is region-dependent**: the 2–4% figure is DG-specific (Liu et al. 2012); the lateral amygdala is 10–30% (Kim et al. 2024; Han et al. 2007), so "2–5%" should not be treated as universal — treat k/M as a tunable hyperparameter.
- **Predictive coding as a brain theory is contested** — laminar evidence is debated (Kogo & Trengove 2015), and the free energy principle's falsifiability is questioned (Gershman 2019); [ResearchGate][ref-26] the biological framing is motivation, not proof.
- **Discrete allocation vs. continuous inference** is an unresolved engineering tension; making k-WTA compatible with gradient-like inference may require straight-through estimators or Gumbel-softmax, which are engineering conveniences, not biological mechanisms.
- Some cited empirical numbers are qualitative rather than a single audited percentage: Millidge et al. (2022) report PCN CIFAR-10 performance as "largely indistinguishable" [arxiv][ref-25] from backprop [arxiv][ref-25] rather than one headline figure, and the strongest FF/PCN CIFAR-10 numbers (>80%) generally come from post-2022 *improved* variants, not the original algorithms. The Whittington & Bogacz (2017) MNIST accuracy (~98.2%) is from a faithful reproduction; the original paper reports it as "less than 2% error." [PubMed][ref-19]

[ref-01]: <https://pmc.ncbi.nlm.nih.gov/articles/PMC3331914/>
[ref-02]: <https://www.nature.com/articles/s41593-024-01676-6>
[ref-03]: <https://pmc.ncbi.nlm.nih.gov/articles/PMC6064663/>
[ref-04]: <https://www.ncbi.nlm.nih.gov/pubmed/23177956>
[ref-05]: <https://www.biorxiv.org/content/10.1101/2022.07.20.500837v1.full>
[ref-06]: <https://www.bndu.ox.ac.uk/sites/default/files/pdf_files/Whittington%20Bogacz%202017_Neural%20Comput.pdf>
[ref-07]: <https://openreview.net/pdf/cf265d888b10e6a8f351a7945c93545f5dfa3048.pdf>
[ref-08]: <https://www.ijcai.org/proceedings/2022/0774.pdf>
[ref-09]: <https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0266102>
[ref-10]: <https://arxiv.org/pdf/2202.09467>
[ref-11]: <https://www.ovid.com/journals/proneu/abstract/10.1016/j.pneurobio.2020.101821~prediction-and-memory-a-predictive-coding-account>
[ref-12]: <https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1010719>
[ref-13]: <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7707106/>
[ref-14]: <https://escholarship.org/uc/item/6g85953g>
[ref-15]: <https://www.researchgate.net/publication/328507272_Predictive_Processing_A_Canonical_Cortical_Computation>
[ref-16]: <https://www.biorxiv.org/content/10.1101/2025.08.17.670544.full.pdf>
[ref-17]: <https://www.cell.com/neuron/fulltext/S0896-6273(13)01127-6>
[ref-18]: <https://www.researchgate.net/publication/315593322_An_Approximation_of_the_Error_Backpropagation_Algorithm_in_a_Predictive_Coding_Network_with_Local_Hebbian_Synaptic_Plasticity>
[ref-19]: <https://pubmed.ncbi.nlm.nih.gov/28333583/>
[ref-20]: <https://pubmed.ncbi.nlm.nih.gov/29903972/?dopt=Abstract>
[ref-21]: <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7930909/>
[ref-22]: <https://proceedings.mlr.press/v162/ernoult22a/ernoult22a.pdf>
[ref-23]: <https://arxiv.org/pdf/1812.11446>
[ref-24]: <https://www.cs.toronto.edu/~hinton/FFA13.pdf>
[ref-25]: <https://arxiv.org/pdf/2006.04182>
[ref-26]: <https://www.researchgate.net/publication/365481195_What_does_the_free_energy_principle_tell_us_about_the_brain>
