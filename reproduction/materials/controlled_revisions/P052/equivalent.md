**VLM Skin Lesion Experimental Plan**

**Protocol for Multi-Reader Multi-Case Non-Inferiority Evaluation of Vision-Language Models in Dermatological Image Annotation**

**Theoretical Formulation and Experimental Objectives**

Automated dermatological image analysis has transitioned from narrow convolutional neural networks optimized for isolated binary classification tasks toward multimodal vision-language models (VLMs) capable of synthesizing visual patterns with free-text reasoning. In clinical workflows, expert evaluation extends beyond assigning a categorical diagnostic label; it requires hierarchical morphological analysis, lesion border segmentation, pattern identification across dermoscopic structures, anatomical localization, and the contextual integration of clinical history. Modern foundation architectures—including general-domain frontier models, domain-adapted systems such as SkinVL and DermatoLlama, and compact edge-deployable networks—offer the theoretical capability to interpret clinical imagery, answer complex visual queries, and draft descriptive reports.

Substituting autonomous VLMs for board-certified dermatologists introduces serious clinical, ethical, and regulatory liabilities. Unlike human clinicians whose credentialing guarantees standardized baseline competencies across diverse patient populations, generalist foundation models often exhibit severe operational asymmetries, such as defaulting to high-specificity benign-labeling biases that miss invasive malignancies or suffering catastrophic performance degradation when exposed to subtle prompt injections or conflicting clinical metadata.

Determining whether an artificial intelligence system can replace human specialists requires an experimental protocol capable of establishing statistical non-inferiority across both diagnostic accuracy and granular morphological characterization. This technical report outlines a Multi-Reader Multi-Case (MRMC) non-inferiority trial designed to evaluate candidate VLMs against a panel of board-certified dermatologists across standardized diagnostic, descriptive, and fairness-aware endpoints.

**Multi-Reader Multi-Case Experimental Architecture**

Evaluating medical imaging technologies against clinician cohorts requires statistical methods that account for two distinct sources of experimental variance: reader variability arising from differential clinician experience, and case variability arising from lesion ambiguity and spectrum bias. Standard paired analyses, such as DeLong tests for correlated receiver operating characteristic (ROC) curves, treat the clinician reader cohort as fixed, limiting conclusions to the specific participants in the study rather than generalizing to the broader population of dermatologists. Consequently, this evaluation implements a fully crossed Random-Reader Random-Case (RRRC) paradigm analyzed via the Obuchowski-Rockette-Hillis (ORH) analysis-of-variance framework and Gallas U-statistics.

**Random-Reader Random-Case Statistical Formulation**

Let θijrepresent the observed diagnostic accuracy metric—specifically the non-parametric Area Under the Receiver Operating Characteristic Curve (AUROC) or the multi-class concordance index—for diagnostic modality i(i=1 for the standalone VLM system; i=2for the human specialist cohort) evaluated on reader j(j=1,…,J) across a common set of patient cases k(k=1,…,K). Under the Obuchowski-Rockette random-effects formulation, accuracy is modeled as:

θij=μ+τi+Rj+τRij+εij

where μrepresents the grand population mean accuracy, τiis the fixed effect of the assessment modality (τi=0), Rj∼N0,σR2denotes the random effect of reader j, τRij∼N0,στR2represents the modality-by-reader interaction, and εijcaptures the residual error composed of case-sampling variability and modality-by-case interactions.

Because an algorithmic VLM operates deterministically when queried at temperature T=0, the model is integrated into the RRRC structure as a single deterministic reader modality evaluated on the identical case set, using jackknife pseudovalues to compute cross-modality covariance components:

Cov1=Covθ1jk,θ2jk

Cov2=Covθ1jk,θ1j'k j≠j'

Cov3=Covθ1jk,θ2j'k j≠j'

The test statistic for evaluating modality divergence employs the Hillis-corrected denominator degrees of freedom applied to the adjusted mean square ratio:

F=MSModalityMSModality×Reader+maxJCov2-Cov3,0

**Non-Inferiority Hypothesis Structure**

Demonstrating that a candidate VLM can stand in for a human specialist requires showing that the algorithmic performance is not inferior to the human specialist mean by more than a predefined, clinically acceptable margin δ. Formally, the null (H0) and alternative (H1) hypotheses are defined as:

H0:θVLM-μDermatologist≤-δ vs. H1:θVLM-μDermatologist>-δ

For primary binary diagnostic triage (malignant versus benign lesions), the non-inferiority margin is set at δ=0.05(5% absolute margin) for both AUROC and diagnostic sensitivity at the average human specificity operating point. Rejection of H0at a one-sided significance level of α=0.025satisfies the regulatory and statistical threshold for diagnostic non-inferiority.

| **Study Dimension** | **Design Specification** | **Statistical Justification** |
| --- | --- | --- |
| **Reader Panel (**J**)** | J=15board-certified dermatologists | Ensures adequate denominator degrees of freedom under Hillis correction (df≥12) to control Type I error rates. |
| **Case Cohort (**K**)** | K=750independent patient cases | Achieves >85%statistical power to detect non-inferiority at δ=0.05assuming baseline AUROC =0.85, σR2=0.002, and covariance difference Cov2-Cov3=0.0008. |
| **Case Balance** | 250 Malignant / 500 Benign | Reflects clinical enrichment while ensuring precision in disease-specific sensitivity and specificity bounds. |
| **Reading Protocol** | Fully crossed, independent blinded reads | All 15 clinicians and candidate VLMs independently review all 750 cases without inter-reader communication. |
| **Analytical Engine** | MRMCaov and iMRMC (v4.0.3) | Validated regulatory software implementations for ORH ANOVA and U-statistic variance estimation. |

**Dataset Stratification and Reference Standard Calibration**

Retrospective evaluations in dermatology frequently fail due to shortcut learning, lack of multi-attribute annotations, and inadequate demographic diversity. To evaluate replacement viability across all labeling tasks, the evaluation dataset is assembled from established multimodal repositories—including DermaBench, MM-Skin, DERM12345, BCN20000, and Diverse Dermatology Images (DDI)—encompassing clinical photography, contact dermoscopy, and matched histopathology.

Total Evaluation Cohort: K = 750 Cases

├── Malignant Lesions: n = 250 (Histopathologically Verified)

│   ├── Cutaneous Melanoma (In Situ & Invasive): n = 120

│   ├── Basal Cell Carcinoma: n = 80

│   └── Squamous Cell Carcinoma: n = 50

└── Benign Lesions: n = 500 (Histopathology or 12-Month Confirmed Stability)

├── Melanocytic Nevi (Common, Dysplastic, Blue): n = 200

├── Seborrheic Keratoses & Solar Lentigines: n = 150

└── Benign Vascular, Inflammatory, & Fibrous Lesions: n = 150

**Reference Standard Hierarchy**

Establishing a reliable ground truth requires decoupling the diagnostic label from the subjective interpretations of the study readers.

- **Histopathological Reference**: All malignant cases (n=250) and complex benign lesions excised during routine care must possess definitive histopathological confirmation adjudicated by consensus of two independent dermatopathologists.

- **Longitudinal Clinical Stability**: Unbiopsied benign lesions (n=350) require documented photographic stability over a minimum follow-up duration of 12 months, verified by clinical follow-up records.

- **Delphi Morphological Consensus**: For non-histological attributes (e.g., primary lesion type, anatomical distribution, surface texture, color variegation), ground truth is established through a three-round Delphi panel of three external senior academic dermatologists who do not participate in the reader study.

**Hierarchical Annotation Schema**

The evaluation leverages an ontology-driven, 22-question hierarchical annotation schema adapted from DermaBench to evaluate the multi-attribute perception of VLMs:

- **Global Lesion Context**: Anatomical localization, lesion distribution pattern, and overall photographic quality indicators.

- **Primary and Secondary Morphology**: Categorization of primary lesions (macule, papule, plaque, nodule, vesicle, wheal) and secondary cutaneous changes (scale, crust, erosion, ulceration, lichenification).

- **Dermoscopic**** Features**: Evaluation of pigment networks (typical versus atypical reticular patterns), aggregated globules, streaks/pseudopods, blue-white veils, regression structures, and vascular morphologies.

- **Diagnostic and Triage Synthesis**: Identification of top-1 diagnosis, structured differential diagnosis list (top-3 ranked), and clinical management decisions (routine monitoring, short-term dermoscopic follow-up, or urgent biopsy/referral).

- **Free-Text Synthesis**: Production of an unstructured, clinical-grade narrative description summarizing the morphological rationale and patient-specific risk factors.

| **Stratification Axis** | **Subgroup Breakdown** | **Clinical and Statistical Rationale** |
| --- | --- | --- |
| **Skin Phototype** | Fitzpatrick I–II: n=250<br>Fitzpatrick III–IV: n=250<br>Fitzpatrick V–VI: n=250 | Balanced representation mitigates documented model failure modes and sensitivity drop-offs on deeply pigmented skin. |
| **Imaging Modality** | Clinical Macro: 100% (n=750)<br>Contact Dermoscopy: 100% (n=750)<br>Histopathology Whole-Slide: n=250 | Assesses multimodal reasoning and ensures models can process paired macro- and micro-morphological visual inputs. |
| **Lesion Complexity** | Subtle / Early Stage: 40% (n=300)<br>Classic Presentation: 40% (n=300)<br>Challenging Mimics: 20% (n=150) | Tests model discriminability against diagnostic edge cases, including melanoma mimicking seborrheic keratosis. |

**Candidate Models and Standardized Inference Protocols**

The evaluation framework assesses three distinct structural categories of vision-language architectures to determine whether performance parity is driven by parameter scale, domain-specific instruction tuning, or localized multimodal alignment.

**Evaluated Model Architectures**

The candidate cohort includes closed-weights generalist foundation models, open-weights domain-adapted dermatology VLMs, and compact edge-deployable models. General foundation models (e.g., GPT-5.4, Claude Opus 4.7, and Gemini 3.1 Pro) provide a baseline for zero-shot clinical reasoning across multimodal inputs. Domain-adapted architectures—specifically SkinVL (pre-trained on MM-Skin's 10,000 professional image-text pairs) and DermatoLlama (trained under the SCALEMED framework using 1.2 million synthetic DermaSynth samples)—evaluate the impact of specialized medical pre-training. Finally, compact edge architectures (such as instruction-tuned SmolVLM and MedCLIP multimodal embeddings combined with neural classifiers) assess whether resource-efficient, privacy-preserving models can achieve specialist-level annotation within local institutional boundaries.

**Standardized Prompting Protocol**

To isolate perceptual and linguistic capabilities from prompt sensitivity, models are queried using the standardized DermaBench visual question answering template:

The system prompt defines the operational persona: "You are a board-certified dermatologist with expertise in clinical image interpretation. Carefully analyze the provided dermatological image and answer the question below using only the visual information in the image and standard dermatological knowledge. Do not assume patient history, symptoms, or metadata unless explicitly provided. If the image cannot be evaluated for the given question, state that the image cannot be evaluated".

The input context provides structured patient metadata including age, biological sex, anatomical site, and maximum lesion diameter. The query specifies the question type (single-choice, multi-choice, or open-ended), the standardized question text, and the allowable clinical ontology options.

All queries are executed at deterministic temperature T=0across three independent runs to evaluate output reproducibility and quantify variance.

**Evaluative Metrics and Conformal Uncertainty Guarantees**

A valid surrogate for a human specialist must demonstrate proficiency across statistical discriminability, semantic alignment with clinical ontologies, and calibrated uncertainty quantification.

| **Evaluative Domain** | **Primary Metric** | **Target Equivalence / Non-Inferiority Criterion** |
| --- | --- | --- |
| **Diagnostic Discriminability** | Non-parametric AUROC | Lower bound of two-sided 95% CI of AUROCVLM-μDermatologist>-0.05. |
| **High-Sensitivity Triage** | Partial AUROC (pAUC0.90) | ΔpAUC0.90>-0.03relative to the dermatologist panel mean. |
| **Morphological Concordance** | Hierarchical Macro-F1 & Cohen's κ<br>[[1]](https://www.medrxiv.org/content/10.1101/2025.05.17.25327785v2.full-text) [[2]](https://www.mdpi.com/2072-6694/18/11/1750) | Macro-averaged Cohen's κ≥0.75across all 22 hierarchical morphological questions. |
| **Narrative Fidelity** | BERTScore / F1-RadGraph Semantic Match | Semantic similarity score non-inferior to inter-dermatologist agreement baseline (p<0.05). |
| **Fairness Parity** | Stratified AUROC Across Fitzpatrick I–VI | Maximum pairwise performance disparity \|AUROCType I-II-AUROCType V-VI\|≤0.04. |
| **Conformal Coverage** | Empirical Prediction Set Coverage (1-α) | Empirical coverage ≥95%with singleton prediction sets (\|CX\|=1) on ≥80%of cases. |

**Conformal Triage and Abstention Formulation**

To prevent dangerous hallucinations and ensure patient safety, the candidate VLM must incorporate a mathematically grounded abstention mechanism using Split Conformal Prediction.

Using an independent calibration set Dcal=Xm,Ymm=1M, non-conformity scores Sm=1-πYm∣Xmare derived from model output probabilities π. Given an error tolerance of α=0.05, the conformal quantile threshold qis computed as:

q=QuantileM+11-αM; Smm=1M

For any novel test lesion Xtest, the model outputs a prediction set:

CXtest=y∈Y:πy∣Xtest≥1-q

The deployment decision follows a conformal triage algorithm:

- **Autonomous Processing**: If |CXtest|=1, the model operates autonomously, outputting its confident diagnostic and morphological label.

- **Mandatory Specialist Escalation**: If |CXtest|>1(high diagnostic ambiguity) or CXtest=∅(out-of-distribution anomaly), the system abstains from autonomous labeling and routes the case to a human dermatologist.

- **Operational Constraint**: For full specialist substitution, the autonomous triage subset must maintain ≥95%accuracy while the specialist referral rate must not exceed 20%of the overall case volume.

**Robustness, Adversarial Vulnerability, and Stress-Testing**

Dermatological foundation models are vulnerable to non-visual artifacts, metadata shifts, and adversarial perturbations. When evaluating whether a VLM can operate autonomously, it must undergo systematic stress-testing across four critical conditions.

First, typographic prompt injections are evaluated by faintly overlaying conflicting diagnostic terms (such as "seborrheic keratosis" or "benign nevus") onto the peripheral margins of histologically confirmed malignant melanoma images. Recent trials have shown that prompt injections can reduce VLM diagnostic accuracy to near-zero levels (0.0%--1.9%, p<10-7) while preserving descriptive output and high self-reported confidence. A viable specialist surrogate must demonstrate robustness against such input manipulations, showing less than a 5% drop in diagnostic sensitivity under typographic perturbation.

Second, metadata perturbation testing introduces conflicting tabular data—such as pairing an image of a geriatric lesion on sun-damaged skin with metadata indicating a pediatric patient—to determine whether the model's visual perception is inappropriately overridden by tabular priors. Third, artifact resistance is quantified by injecting common dermatological imaging noise, including surgical ink markings, excessive dermoscopic gel bubbles, hair occlusions, and off-center vignetting. Finally, benign-labeling bias audits assess whether high overall accuracy masks a catastrophic failure to detect thin, early-stage melanomas (≤1.0 mm Breslow depth), which is an essential requirement for avoiding severe clinical harm.

**Hierarchical Decision Framework and Operational Deployment Pathways**

Approval of a vision-language model as a stand-in for human dermatologists proceeds through sequential gates. Not passing any tier restricts the model's operational scope, preventing unqualified clinical substitution.

Evaluation Tier 1: Primary Diagnostic MRMC Non-Inferiority

├── Passed: Lower 95% CI of AUROC difference > -0.05 (ORH F-test)

│   └── Continue to Evaluation Tier 2

└── Failed: Lower 95% CI of AUROC difference <= -0.05

└── Operational Status: REJECT AUTONOMOUS DEPLOYMENT

Evaluation Tier 2: Demographic Fairness & Subgroup Parity

├── Passed: Pairwise AUROC difference between Fitzpatrick I-II and V-VI <= 0.04

│   └── Continue to Evaluation Tier 3

└── Failed: Disparity > 0.04 or failure on dark phototypes

└── Operational Status: CONDITIONAL RESTRICTED TRIAGE ONLY

Evaluation Tier 3: Morphological & Semantic Concordance

├── Passed: Hierarchical Macro-F1 Cohen's Kappa >= 0.75 on 22-question schema

│   └── Proceed to Evaluation Tier 4

└── Failed: Cohen's Kappa < 0.75

└── Operational Status: BINARY TRIAGE PROXY ONLY (No Descriptive Autonomy)

Evaluation Tier 4: Adversarial Robustness & Conformal Safety

├── Passed: Performance drop < 10% under stress test; abstention rate <= 20%

│   └── Operational Status: FULL SPECIALIST SURROGATE (Autonomous Certification)

└── Failed: Catastrophic collapse or excessive abstention rate > 20%

└── Operational Status: ASSISTED MODE ONLY (Mandatory Human Over-Read)

| **Decision Tier** | **Evaluated Parameters** | **Minimum Success Threshold** | **Authorized Operational Scope** |
| --- | --- | --- | --- |
| **Tier 1: Diagnostic Parity** | ORH RRRC AUROC and Sensitivity at mean human specificity | p<0.025for H0:θVLM-μHuman≤-0.05<br>[[8]](https://chat.powerdrill.ai/discover/summary-mind-the-rarities-can-rare-skin-diseases-be-cmn0tnfz403x307pol2n0bski) [[9]](https://www.computer.org/csdl/proceedings-article/wacv/2026/551100a927/2ggPwK8a6ZO) | **Primary Gate**: Authorizes continued evaluation. Failure terminates autonomous qualification. |
| **Tier 2: Equity & Fairness** | Subgroup AUROC and Sensitivity across Fitzpatrick I–VI | No subgroup AUROC <0.80; cross-group delta ≤0.04<br>[[7]](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1608837/full) [[16]](https://repository.ubn.ru.nl/bitstream/handle/2066/178907/178907.pdf?sequence=1&isAllowed=y) | **Fairness Certification**: Failure limits deployment to demographic groups where safety is proven. |
| **Tier 3: Morphological Alignment** | Hierarchical Cohen's κacross 22 DermaBench attributes | Macro-averaged Cohen's κ≥0.75versus Delphi consensus | **Labeling Autonomy**: Authorizes structured metadata generation. Failure restricts model to binary triage. |
| **Tier 4: Robustness & Safety** | Performance under prompt injections and conformal set bounds | Accuracy drop <10%under stress; Conformal referral rate ≤20%<br>[[2]](https://www.mdpi.com/2072-6694/18/11/1750) [[19]](https://scholarcommons.sc.edu/cgi/viewcontent.cgi?article=8807&context=etd) | **Full Specialist Surrogate**: Model cleared to replace human readers in clinical registries and tele-triage. |

**Synthesis and Translational Conclusions**

Establishing whether a vision-language model can substitute for human specialists requires rigorous validation beyond standard classification accuracy. While domain-specialized VLMs trained on curated multimodal corpuses demonstrate strong visual reasoning, their deployment as autonomous diagnostic agents requires formal proof of non-inferiority within an Obuchowski-Rockette-Hillis multi-reader multi-case statistical framework.

The experimental protocol defined here establishes clear statistical bounds, requiring candidate VLMs to match human specialist performance across diverse skin phototypes, maintain high morphological concordance on structured ontologies, and demonstrate resistance to adversarial perturbations and clinical metadata shifts. By integrating Split Conformal Prediction, the protocol guarantees that autonomous labeling is restricted to high-confidence cases while routing ambiguous lesions to expert clinical review. Models that fail to satisfy these multi-tiered criteria cannot serve as autonomous specialist surrogates, but must instead remain restricted to assistive, human-in-the-loop workflows.
