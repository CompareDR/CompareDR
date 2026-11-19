# LiDAR vs. Vision: Why Autonomous-Vehicle Programs Diverge on Sensing — A Technical Report (August 2026)

## TL;DR

- The split is not primarily about which sensor "sees better" — it is about **business model and the burden of proof for safety**: robotaxi operators (Waymo, Zoox, Baidu, Aurora) amortize expensive multi-modal suites over high-utilization fleets and use LiDAR's deterministic depth to build a bounded, auditable safety case, while mass-market consumer programs (Tesla, and increasingly XPeng) treat bill-of-materials cost and scalable data-driven learning as decisive and bet that cameras + neural networks will reach adequate safety.
- As of 2026 the empirical record favors the multi-modal camp on *demonstrated* driverless safety at scale (Waymo's peer-reviewed crash-rate studies over 56.7M+ rider-only miles; 500,000 paid rides/week across 10 US cities) while the vision-only camp's flagship — Tesla — remains supervised or lightly-supervised with a ~20-car unsupervised robotaxi fleet and an open NHTSA engineering-analysis probe into camera-blinding failures covering ~3.2M vehicles.
- The two camps are **converging**: Chinese suppliers collapsed automotive LiDAR to ~$200/unit, imaging radar is eating LiDAR's adverse-weather niche, everyone is moving to end-to-end learning, and — crucially — even vision-only inference stacks (Tesla, Wayve) rely on LiDAR/radar as *training-time ground truth* and auto-labeling. LiDAR is migrating from a runtime necessity toward a training-and-validation tool.

## Key Findings

1. 1. **Physics gives each modality a non-overlapping strength.** LiDAR directly measures metric range (deterministic depth, works in darkness); cameras carry the only semantic content that matters for a human-designed road (traffic lights, brake lights, signs, gestures); radar owns velocity and adverse weather. No single modality dominates on all axes, which is why the disagreement is real rather than a simple engineering error by one side.
2. 2. **The cost argument that anchored vision-only has largely collapsed.** The Velodyne HDL-64E that defined early AV cost ~$75,000; Hesai's ATX ADAS LiDAR reached $200/unit in mass production in Q1 2025. This removes the strongest historical reason to avoid LiDAR on consumer cars — yet Tesla and XPeng are moving *away* from LiDAR anyway, which shows the debate is now about architecture and data philosophy, not just unit price.
3. 3. **Waymo (LiDAR + camera + imaging radar) has the only large body of peer-reviewed driverless safety evidence.** Its 6th-gen Driver keeps all three modalities while cutting sensor count 42%, explicitly framing redundancy as a requirement: "demonstrably safe AI requires equally resilient inputs."
4. 4. **Tesla's vision-only bet is intact but under regulatory pressure.** NHTSA escalated its FSD probe to an Engineering Analysis (EA26002, opened March 18, 2026) over camera performance in glare/fog/dust across ~3.2M vehicles — the specific failure mode LiDAR/radar redundancy is meant to cover.
5. 5. **On benchmarks, LiDAR still wins on 3D localization but the camera gap has narrowed ~3×.** Fusion methods (BEVFusion) top nuScenes/Waymo leaderboards; camera-only methods improved dramatically but still trail LiDAR on precise localization/velocity, which is exactly the safety-relevant metric.
6. 6. **Convergence point (important): LiDAR as training supervision.** Tesla's own patents describe training vehicles with LiDAR/radar to auto-label depth/velocity, then deploying vision-only networks — LiDAR is used to *teach* cameras.

## Details

### 1. Technical fundamentals

**LiDAR.** LiDAR emits laser pulses and times their return (time-of-flight, ToF) to measure range directly, producing a 3D point cloud with reflectivity/intensity per point. Frequency-modulated continuous-wave (FMCW) LiDAR instead measures a frequency shift, adding per-point radial velocity (Doppler) and better interference rejection at the cost of complexity. Architectures span legacy spinning-mechanical units (e.g., Velodyne's 64-laser HDL-64E, 360° horizontal, ~26.8° vertical, ~1.3M points/s) to solid-state / MEMS / optical-phased-array (OPA) designs that are cheaper and more automotive-robust but often trade field-of-view and resolution. Wavelength matters: 905 nm silicon detectors are cheap but eye-safety limits power and thus range; 1550 nm (InGaAs) permits far higher power for long range (Aurora's FirstLight FMCW cites >450 m in darkness, next-gen 1,000 m) at higher cost. **Intrinsic advantages:** direct metric depth independent of learned inference; operation in total darkness; geometric ground truth; low-latency obstacle detection that does not depend on having seen an object class before.

**Cameras + neural networks.** Passive imagers capture dense color/texture at high angular resolution but no direct depth. Depth is *inferred*: stereo/multi-camera triangulation, structure-from-motion, self-supervised monocular depth networks (e.g., Monodepth2, Godard et al., ICCV 2019), or learned "pseudo-LiDAR" that lifts predicted depth into a point cloud (Wang et al., CVPR 2019, which raised KITTI within-30 m accuracy from 22% to 74%). Modern stacks build a bird's-eye-view (BEV) representation via transformers (BEVFormer, BEVDet) and increasingly occupancy networks and end-to-end learned policies. **Intrinsic advantages:** unmatched information density and the only source of the semantic cues roads are literally designed to convey.

**Radar and 4D imaging radar.** Radar directly measures range and Doppler velocity, works through fog/rain/snow/dust, and is cheap. Conventional 3D radar lacks elevation resolution (the classic overhead-sign "phantom braking" problem). 4D imaging radar adds elevation via massive-MIMO arrays, producing sparse point clouds with velocity that approach low-end LiDAR in some tasks. [Aminext][ref-01] Its rise is central to the debate: a camera + 4D-radar stack can claim much of LiDAR's adverse-weather and depth value at lower cost, which is why Mobileye and Waymo both invest heavily in in-house imaging radar. Caveat: 4D radar point clouds remain roughly two orders of magnitude sparser than LiDAR, with multipath ghosts.

**Thermal/IR.** Long-wave IR cameras add pedestrian/animal detection in darkness and glare and are used by some ADAS suppliers, but remain niche in current L4 stacks.

*Sensor capability matrix (qualitative):*

| Capability | Camera | LiDAR | Radar (4D) | Thermal |
| --- | --- | --- | --- | --- |
| Metric depth (direct) | ✗ (inferred) | ✓✓✓ | ✓✓ | ✗ |
| Angular resolution | ✓✓✓ | ✓✓ | ✓ | ✓ |
| Semantics (signs/lights/color) | ✓✓✓ | ✗ | ✗ | ~ |
| Darkness | ✗ | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| Fog / rain / snow / dust | ✗ | ✗/~ | ✓✓✓ | ✓ |
| Direct velocity | ✗ | ~ (FMCW) | ✓✓✓ | ✗ |
| Unit cost (2026) | very low | low–moderate | low | moderate |

### 2. The engineering case for LiDAR-first

- **Diversity of failure modes / redundancy.** Independent physical modalities fail differently; a camera blinded by glare is backstopped by LiDAR/radar. Waymo's framing: three complementary modalities give overlapping fields of view "up to 500 meters away, day and night."
- **Deterministic depth, no learned inference required.** A LiDAR return is a geometric fact; obstacle presence does not depend on whether the object's class was in the training set — crucial for the long tail (debris, overturned trucks, unusual shapes).
- **Long-tail / edge cases.** Unclassified stationary obstacles, tunnel-exit HDR, low sun, dust — precisely the conditions implicated in Tesla's NHTSA probe.
- **Mapping & localization.** LiDAR point clouds enable centimeter HD-map matching for precise localization, the backbone of geofenced robotaxi ODDs.
- **Safety case / V&V.** LiDAR lets engineers *bound* perception error and build auditable arguments under ISO 26262 (functional safety), ISO 21448 SOTIF (safety of the intended function, i.e., performance limitations without a fault), and UL 4600 (safety case for autonomous products). Bounding the error of a deep network from camera pixels alone is far harder to argue to a regulator.
- **Known LiDAR limitations:** degradation in fog/heavy rain/snow/dust (scattering); sparse returns at long range; near-zero semantic content; [arxiv][ref-02] poor returns from low-albedo or specular surfaces; inter-unit interference; cost, packaging, thermal, and automotive-grade reliability challenges.

### 3. The engineering case for vision + neural networks

- **Cost, packaging, manufacturability.** Cameras are cheap, small, aerodynamic, and mass-manufacturable. A 2024 estimate put Tesla's sensor suite at ~$400/vehicle vs. ~$12,700 for Waymo's 5th-gen Jaguar suite — decisive when BOM cost dominates a consumer product sold at scale.
- **Semantic density.** Cameras read what LiDAR fundamentally cannot: traffic-light state, brake lights, turn signals, hand gestures, text on signs, lane markings, road texture. "Roads are designed for human vision."
- **Data flywheel & scaling.** A large camera fleet supplies petabyte-scale, diverse data; proponents apply scaling laws / foundation-model logic and end-to-end learning (Tesla FSD v12–v14; Wayve's AV2.0 "GPT for driving"; world-model simulation) to argue learned perception will keep improving.
- **"Fusion is hard."** Combining heterogeneous sensors introduces calibration burden, time-alignment, and contradictory-measurement arbitration; vision-only advocates argue a single modality with a unified network avoids fusion failure modes.
- **Known vision limitations:** metric-scale/depth ambiguity; degradation in low light, glare, and weather; occlusion; reliance on statistical generalization (hallucination / failure on out-of-distribution objects); difficulty of formal validation of deep networks; long-tail brittleness.

### 4. Who does what (2026)

| Program | Sensing approach | Status (2026) |
| --- | --- | --- |
| **Waymo** | LiDAR + camera + imaging radar (6th-gen: 13 cameras, 4 LiDAR, 6 radar, audio) + HD maps | Market leader; 500,000 paid rides/week; 10 US cities; 200M+ autonomous miles; London/Tokyo/Germany planned |
| **Tesla** | Camera-only ("Tesla Vision"); radar & ultrasonics removed | FSD v14 (AI4); supervised for consumers; ~20-car unsupervised robotaxi fleet in Austin; NHTSA EA26002 open |
| **Zoox (Amazon)** | LiDAR + camera + radar, purpose-built vehicle | Commercial launch in Las Vegas; testing SF |
| **Cruise (GM)** | Was LiDAR + camera + radar | Robotaxi shut down Dec 2024; [Smart Cities Dive][ref-03] tech folded into GM consumer ADAS |
| **Baidu Apollo Go** | LiDAR + camera + radar (Hesai) | ~250,000+ rides/week; [CNBC][ref-04] ~20 China cities; 6th-gen ~$28,500 vehicle [Seeking Alpha][ref-05] |
| **Pony.ai / WeRide** | LiDAR + camera + radar | Scaling in China + Middle East; ~1,000-vehicle targets |
| **Aurora / Kodiak (trucking)** | LiDAR-first (Aurora FirstLight FMCW 1550 nm) + camera + radar | Aurora driverless Dallas–Houston + Fort Worth–El Paso; 100k+ driverless miles [ACT News][ref-06] |
| **Wayve** | Camera-first, end-to-end; radar added; hardware-agnostic | $1.2B Series D (2026), $8.6B valuation; [Wayve][ref-07] Uber robotaxi London from 2026 [Wayve][ref-08] |
| **Mobileye** | Two-track: SuperVision (camera-only) + True Redundancy (camera+radar+LiDAR) for eyes-off | Ended internal FMCW LiDAR R&D (Sept 2024); imaging radar now strategic priority |
| **XPeng** | Moved to pure vision (dropped LiDAR on new models) | P7+, G6/G9/G7/GX vision-only; CEO says LiDAR "no longer necessary" for cars |
| **Huawei ADS 4** | Multi-modal: LiDAR + radar + camera + HD map | 1M+ vehicles; 1M+ LiDAR units shipped; L3 highway pilot; first China L3 permits Dec 2025 |
| **Comma.ai / openpilot** | Camera-only, retrofit L2 | Consumer driver-assist |

**Notable position shifts:** Mobileye killed internal FMCW LiDAR development (Sept 2024), citing EyeQ6 vision progress, imaging-radar confidence, and cheaper third-party ToF LiDAR [Silicon UK][ref-09] — but keeps LiDAR in its redundant eyes-off stack. XPeng publicly abandoned LiDAR for pure vision across new models. [CnEVPost][ref-10] Tesla removed radar (2021) and ultrasonics (2022); NHTSA is now demanding Tesla's internal "Radar Saves Us" document. [Electrek][ref-11] Meanwhile Chinese consumer LiDAR adoption is *rising* (Huawei, Li Auto, Xiaomi), the opposite direction. There is no single industry trend — the field is genuinely bifurcating by use case.

### 5. The economics

- **LiDAR cost curve:** ~$75,000 (HDL-64E, 2009) → ~$8,000 (VLP-16) → ~$4,000 (2018) → $200 (Hesai ATX, entering mass production in Q1 2025). Hesai puts the total reduction at ~99.5% over eight years; blended ASP fell from ~82,000 yuan (2020) to ~3,900 yuan (2024). China installed 3.386M LiDAR units in 2025 (penetration ~11%); RoboSense/Hesai/Huawei roughly split the passenger-vehicle market.
- **Compute cost:** vision-heavy stacks push compute/energy/thermal budgets; Tesla's AI5 targets ~2,000–2,500 TOPS (~10× HW4), taped out April 2026, volume mid-2027. [TeslAnt][ref-12]
- **Business model determines architecture.** *Robotaxi*: small fleet, high per-vehicle revenue over high utilization → sensor cost amortized → maximize safety with redundancy + HD maps within a tight geofenced ODD. *Consumer at scale*: BOM cost dominates, ODD is "everywhere" → favors cheap, uniform sensing + learned generalization + no HD-map dependency. *Trucking*: high-speed highway ODD with long stopping distances → long-range LiDAR's early, far detection is a strong safety argument (Aurora quantifies an ~11-second detection advantage over a human driver in darkness). [Aurora][ref-13]
- **ODD & geofencing** are the hidden variable: the tighter and better-mapped the ODD, the more LiDAR + maps pays off; the broader the ODD, the more the vision-only camp's generalization bet is forced.

### 6. Evidence / empirical state of play

- **Waymo safety studies (peer-reviewed).** Kusano, Scanlon, Chen, McMurry, Gode & Victor (2025), *Traffic Injury Prevention* 26(sup1):S8–S20 (DOI 10.1080/15389588.2025.2499887, published 16 May 2025) analyzed 56.7M rider-only miles through January 2025: aggregate any-injury-reported crashes down 79% \[71%,85%\] and airbag-deployment crashes down 81% \[69%,90%\] vs. human benchmarks, with the largest single reduction in V2V intersection crashes — a 96% reduction in any-injury-reported (87%–99% CI) and 91% in airbag deployment (76%–98% CI). An earlier 7.1M-mile study reported 85% fewer any-injury and 57% fewer police-reported crashes. IIHS independently found Waymo involved in 85% fewer single-vehicle and 81% fewer injury crashes per mile. [IIHS-HLDI][ref-14] These are the strongest existing data and they come from a LiDAR-multimodal system — though they cannot isolate *which* sensor drives the result, and benchmarks/underreporting corrections are contested.
- **Tesla safety reporting** is self-published quarterly (miles-per-collision with Autopilot engaged) and widely criticized for not normalizing road type/driver demographics; it is not peer-reviewed and does not isolate FSD driverless performance.
- **Regulatory.** NHTSA's Office of Defects Investigation opened Engineering Analysis EA26002 on March 18, 2026 (upgraded from PE24031, opened Oct 2024), covering ~3,203,754 Tesla vehicles (2016–2026 Model S/X, 2017–2026 Model 3, 2020–2026 Model Y, 2023–2026 Cybertruck), tied to nine FSD reduced-visibility crashes including one pedestrian fatality and at least one injury; per the filing FSD may fail "to detect a degraded state and to warn the driver appropriately" in glare/fog/airborne-obscurant conditions. Tesla was ordered to respond by August 12, 2026. This is a direct empirical stress on the no-redundancy architecture. Separately, Cruise's 2023 pedestrian-dragging incident (permit revoked; DOJ/SEC probes) shows multi-modal sensing is necessary but not sufficient — behavior/operations matter too.
- **Benchmarks.** On nuScenes/Waymo Open, LiDAR and LiDAR-camera fusion (e.g., BEVFusion) lead 3D detection; camera-only NDS/mAP improved sharply (the camera-vs-LiDAR NDS gap shrank ~3× in three years) but still trails on translation and velocity error [arXiv][ref-15] — the metrics most tied to collision avoidance. Academic consensus: cameras have closed much of the semantic/detection gap but not the precise-localization gap.
- **Disengagement data** (CA DMV) is widely regarded as a weak cross-company metric: definitions vary, ODDs differ, and it is gameable; useful only as a coarse trend within one program.

### 7. Synthesis — why reasonable engineers disagree

The disagreement traces to different **priors**, not different physics:

- **(a) Speed of learned-perception improvement.** Vision-only requires believing neural depth/semantics will keep scaling to superhuman reliability; LiDAR-first hedges against that bet not paying off in time.
- **(b) Burden of proof for safety.** If you must *demonstrate and bound* safety to a regulator today (robotaxi, eyes-off), deterministic LiDAR makes the safety case tractable. If you believe fleet statistics will eventually suffice, cameras are enough.
- **(c) Business model & scale economics** (robotaxi vs. consumer vs. trucking), as above — the single best predictor of architecture.
- **(d) Tolerance for the long tail.** LiDAR-first weights rare catastrophic edge cases heavily; vision-first weights average-case scalability.
- **(e) Whether fusion helps or hurts.** One camp sees redundancy as safety; the other sees fusion complexity as a new failure source.

**Convergence is real and accelerating:**

- **Cheap LiDAR** (~$200) removes cost as a blocker; consumer LiDAR adoption is rising in China even as Tesla/XPeng exit it.
- **Imaging radar** increasingly delivers LiDAR-like depth/velocity in bad weather at low cost, blurring the "need LiDAR" line (Mobileye, Waymo, camera+4D-radar stacks).
- **End-to-end learning on multimodal input** is now universal — even LiDAR users run learned BEV/occupancy/policy nets; the "rules vs. learning" axis is collapsing separately from the sensor axis.
- **LiDAR as training-time supervision (the key convergence).** Even vision-only *inference* stacks depend on LiDAR at *training* time. Tesla's patent family — "Estimating object properties using visual image data" (granted US10956755B2, 2021-03-23; continuations through US20250182498A1, filed 2025-01-27; assignee Tesla, Inc.; inventors incl. Ashok Elluswamy) — describes equipping "training vehicles ... with auxiliary sensors, including expensive and/or difficult to operate sensors" (radar, LiDAR) to generate ground-truth depth/velocity, then deploying "to vehicles, such as production vehicles, that only require vision sensors." Andrej Karpathy (Tesla, CVPR 2021) described offline auto-labeling fusing "radar, lidar, camera" to supervise the vision network, while asserting vision alone could recover depth/velocity ("an unequivocal yes"). Academic pseudo-LiDAR (Wang et al., CVPR 2019) and NVIDIA's radar nets similarly use LiDAR labels as ground truth; Wayve, which deploys camera-first, evaluates against LiDAR-based ground truth (Waymo Open). In effect, both camps use LiDAR — the question is increasingly *whether it must be on the car at runtime*, not whether it is needed at all.

## Recommendations

1. 1. **If you are building a robotaxi / eyes-off L4 in a geofenced ODD:** keep the multi-modal (camera + LiDAR + imaging radar) suite now. The safety-case tractability under ISO 21448/UL 4600 and the only extant peer-reviewed driverless safety data both favor it. Exploit the ~$200 LiDAR cost collapse; invest in in-house imaging radar to reduce LiDAR count over time (as Waymo's 6th-gen did, −42% sensors). *Threshold to revisit:* if camera+4D-radar stacks demonstrate bounded, validated depth parity with LiDAR on your ODD's edge cases, begin removing LiDAR channels.
2. 2. **If you are building consumer ADAS/L2–L3 at scale:** a camera-forward stack is economically rational, but do **not** remove all independent-modality redundancy given the NHTSA glare/fog/dust findings. Retain at least 4D imaging radar as a cheap, weather-robust backstop; the "camera-only" purity of Tesla's approach is the single most regulatorily exposed choice in the industry.
3. 3. **If you are in trucking:** prioritize long-range LiDAR (1550 nm FMCW). High-speed stopping distances make early, deterministic long-range detection the dominant safety lever; Aurora's approach is the reference.
4. 4. **Everyone:** use LiDAR at training/validation time regardless of runtime choice — as auto-labeling ground truth and as a validation oracle to bound your vision system's error. This is low-cost, de-risks the perception stack, and is already standard practice.
5. 5. **Investors/analysts:** treat "LiDAR vs. vision" as a proxy for business model, not technical merit. Track three benchmarks that would move the debate: (i) camera-only 3D-detection velocity/translation error reaching LiDAR parity on nuScenes/Waymo Open; (ii) a peer-reviewed vision-only driverless safety study at >10M unsupervised miles; (iii) resolution of NHTSA EA26002.

## Caveats

- **Fast-moving facts.** Fleet sizes, city counts, ride volumes, software versions (FSD v14/v15, AI5), and regulatory status change monthly; figures here are as of mid-2026 and several (Tesla robotaxi counts, Waymo weekly rides) come from company statements or third-party trackers of varying reliability.
- **Attribution problem.** Waymo's strong safety data cannot causally isolate LiDAR's contribution from Waymo's maps, ODD restriction, operations, and remote assistance; likewise Tesla's incidents cannot prove vision-only is inherently unsafe rather than immature.
- **Marketing vs. fact.** Claims like "cameras beat LiDAR," "LiDAR is a crutch," "fusion is hard," and supplier accident-reduction percentages are advocacy; they are labeled as such above and should not be read as established fact. Company blogs (Waymo, Wayve, Mobileye) are technically informative but promotional.
- **Benchmark ≠ road.** nuScenes/KITTI/Waymo Open leaderboard gaps are informative but do not directly translate to on-road safety, which depends on the whole stack.
- **Speculative items flagged:** Tesla AI5 timing/performance, Wayve/Baidu/Pony expansion targets, and analyst market projections are forward-looking statements, not results.

[ref-01]: <https://www.aminext.blog/en/post/4d-imaging-radar-autonomous-driving-lidar-alternative>
[ref-02]: <https://arxiv.org/pdf/2306.09304>
[ref-03]: <https://www.smartcitiesdive.com/news/general-motors-shuts-cruise-robotaxi-unit-mary-barra/735205/>
[ref-04]: <https://www.cnbc.com/2025/11/03/china-baidu-robotaxis-alphabet-waymo-.html>
[ref-05]: <https://seekingalpha.com/pr/19789981-baidu-selects-hesai-as-exclusive-long-range-lidar-provider-for-next-generation-robotaxis>
[ref-06]: <https://www.act-news.com/news/aurora-expands-driverless-operations/>
[ref-07]: <https://wayve.ai/press/series-d/>
[ref-08]: <https://wayve.ai/company/investors/>
[ref-09]: <https://www.silicon.co.uk/press-release/mobileye-to-end-internal-lidar-development>
[ref-10]: <https://cnevpost.com/2026/05/21/xpeng-defends-pure-vision-strategy-says-lidar-no-longer-necessary/>
[ref-11]: <https://electrek.co/2026/07/21/nhtsa-tesla-radar-saves-us-document-fsd-probe/>
[ref-12]: <https://teslant.com/en/guides/tesla-fsd-hardware-generations-reference-2026>
[ref-13]: <https://ir.aurora.tech/news-events/press-releases/detail/122/aurora-begins-driverless-operations-at-night-and-opens-phoenix-terminal>
[ref-14]: <https://www.iihs.org/news/detail/waymos-driverless-cars-crash-less-often-than-people>
[ref-15]: <https://arxiv.org/html/2512.02448v1>
