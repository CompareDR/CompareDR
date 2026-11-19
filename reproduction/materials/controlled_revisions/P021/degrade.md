# Energy Recovery in Urban Water Supply/Distribution Systems: Conventional Micro-Hydroturbines vs. Pump-as-Turbine (PAT) Technology

## TL;DR

- For the micro/pico scale typical of urban water networks (<100–200 kW), **PATs are the more economically compelling choice**: purchase price is roughly 5–15× lower per kW than a purpose-built turbine (Novara et al., 2019), with documented payback periods often under ~2–4 years, but they pay for this with lower peak efficiency (~60–80% vs ~85–92%) and poor part-load behaviour because they lack adjustable guide vanes.
- **Conventional micro-hydroturbines (Pelton, Turgo, Crossflow, Francis, Kaplan) win on efficiency, flow-regulation flexibility and part-load performance** thanks to adjustable geometry (spear jets, guide vanes, adjustable blades), and remain preferable above roughly 200–300 kW where their cost premium narrows and their higher efficiency dominates lifetime economics.
- The dominant barriers to deployment are not the machines themselves but **highly variable daily/seasonal flow and head, low available head, lack of manufacturer PAT performance data, civil-works and control-system costs, and regulatory/utility-ownership hurdles** — meaning site selection, sizing and control strategy matter more than turbine type.

## PART 1 — Narrative Comparison: Conventional Micro-Hydroturbines vs. Pump-as-Turbine (PAT)

### 1.1 Operational efficiency (BEP and off-design behaviour)

**Conventional turbines.** Purpose-built hydro turbines are individually designed to hit a high best-efficiency point (BEP). Large Francis and Kaplan machines routinely exceed 90% peak efficiency (Wikipedia/Kaplan; [Wikipedia][ref-01] hydraulic-turbine reference notes cite "typically over 90%" for both Francis and Kaplan). At micro scale the achievable peak is lower but still high: small Pelton wheels reach ~90% mechanical efficiency and small Francis ~92% (Mecaflux). [Mecaflux][ref-02] Crossflow (Banki-Michell) turbines are the lowest of the conventional family, typically ~80% (measured ~80% in lab per one review), but they retain a signature flat efficiency curve.

The decisive advantage of conventional turbines is **part-load behaviour governed by adjustable geometry**. Pelton (via spear-jet/nozzle) and Kaplan (via adjustable runner blades plus guide vanes) "retain very high efficiencies when running below design flow," whereas "the efficiency of Crossflow and Francis turbines falls away more rapidly if run at below half their normal flow" [GreenBug Energy][ref-03] (GreenBug Energy). A double-regulated Kaplan maintains high efficiency across roughly 15–100% of discharge; a single-regulated Kaplan across ~30–100% (ScienceDirect, Kaplan Turbines overview). [ScienceDirect][ref-04]

**PATs.** A pump run in reverse has no movable guide vanes, so it is a fixed-geometry machine optimised for a single operating point. Two consequences follow (Frontiers, "Performance Prediction and Geometry Optimization for Application of Pump as Turbine"): (1) "when pump operates as turbines, the BEP will shift toward a larger flow rate," [Frontiers][ref-05] and (2) "the maximum efficiency under the turbine mode is somewhat lower than that under pump mode." [Frontiers][ref-05] Reported PAT peak efficiencies are commonly in the **70–80% range** (Carravetta et al., 2013), with field/WDN installations often lower — the Antalya full-scale plant averaged 60% (Muhammetoglu, Nursen, Karadirek & Muhammetoglu, *Water Supply* 18(1):130–141, 2018: the PAT "works efficiently in a wide range of inflows (130–300 m³/h) and the produced energy varies between 0.7 and 8.4 kWh for a reduction of approximately one bar pressure head with an average efficiency of 60%"), and a variable-speed WDN PAT held best efficiencies of only 0.62–0.64 (Souza et al., 2023, *Water Resources Management*). Semi-axial submersible PATs can reach 70–75%+ (REDAWN database, per *Water* 2022, 14, 1526).

Crucially, off-design losses are severe: "If PATs are operated at other than the design flow, i.e. below their best efficiency point (bep), a relatively rapid drop of efficiency will occur" [NZDL][ref-06] (Chapallaz et al. / NZDL manual). This is the core efficiency penalty of PATs in networks with variable flow.

### 1.2 Costs (capital, installation, O&M; €/kW and $/kW)

**Capital / procurement.** PATs are dramatically cheaper because they are mass-produced. The definitive study (Novara, Carravetta, McNabola & Ramos, *J. Water Resources Planning & Management*, 2019, compiling 343 pumps and 286 generators) concluded the PAT+generator unit cost "may vary from 130 to 5,400 €/kW according to the machine rated power," [Wikipedia][ref-07] and that "PAT + generator unit cost proved to be between 5 and 15 times lower than generating sets based on conventional hydro turbines." At 3 kW their model gave 500–1,000 €/kW; at 20 kW, 200–500 €/kW. Earlier figures they reconcile: Ramos et al. (2009) 200–400 €/kW for P<40 kW; Carravetta et al. (2013) 230 €/kW (turbine) + 115 €/kW (generator); De Marchis et al. (2014) a flat 2,000 €/kW.

For context, IRENA ("Renewable Energy Technologies: Cost Analysis Series – Hydropower," 2012) puts small-hydro total installed costs "between USD 1 300/kW and USD 8 000/kW. Adding additional capacity at existing hydropower schemes or existing dams that don't have a hydropower plant can be significantly cheaper, and can cost as little as USD 500/kW." Micro-hydro literature separately cites 1,500–3,000 €/kW (up to 3,000–6,000 €/kW in some African programs; energypedia).

**Installation & balance-of-plant.** For small schemes the turbogenerator is only 30–40% of total cost (Chapallaz et al.; Ogayar & Vidal, 2009), rising to ~70% for a few-kW plant (Gallagher et al., 2015). Civil works, grid connection and engineering are "highly site-specific and independent of the chosen turbine technology" (Novara et al., 2019). A key nuance: because a PAT machine is cheaper, the **control system becomes a proportionally larger share**. Ogayar & Vidal found control systems average 22% of total investment for conventional sub-2-MW schemes (nearly 2/3 of turbogenerator cost); for PAT plants requiring backpressure control (e.g. Cartuja/Conejeras twin plants near Granada, Spain — 278 L/s, ~36–39 m head, 90 kW each) "the reported cost of the control system was 1.2 times the purchase cost of the PAT and generator."

**O&M.** Annual O&M for hydropower is "typically 1% to 4%" of investment cost/kW, with large hydro averaging "around 2% to 2.5%" (IRENA, 2012). PATs benefit from low O&M owing to mechanical simplicity, standard parts and global service networks.

### 1.3 Pressure-regulation capability

In WDNs the machine must often replace a **pressure-reducing valve (PRV)** and hold a target downstream backpressure despite varying flow. Conventional turbines regulate hydraulically via adjustable guide vanes/nozzles/blades — the same mechanism that preserves part-load efficiency.

PATs, lacking these, achieve regulation by three schemes (Carravetta et al., 2012/2013; Novara et al., 2019):

- **Hydraulic Regulation (HR):** a series control valve plus a parallel bypass modulate flow/head around the PAT.
- **Electric Regulation (ER):** a four-quadrant inverter varies PAT shaft speed (VFD).
- **Hydraulic + Electric Regulation (HER):** both combined.

Fecarotta et al. (2015) and Carravetta's work using the Variable Operating Strategy (VOS) generally find HR gives higher overall efficiency across a range of backpressures, while ER avoids bypass leakage but often operates far from BEP at low efficiency. Variable-speed operation is the most effective for tracking demand: Souza et al. (2023) showed a variable-speed PAT maintained pressure "according to the values required by the PCVs" [Springer][ref-08] whereas at constant speed it only acted as a valve near the BEP. García/Novara/McNabola (2019) found the NPV of PAT operation 6–29% higher than a PRV across scenarios. [ResearchGate][ref-09] Overall, PATs *can* regulate pressure but only with added control hardware and some efficiency/energy penalty; PRVs regulate perfectly but recover zero energy.

### 1.4 Design and operational complexity

**Conventional turbines** come with manufacturer-supplied characteristic/hill charts, standardized selection procedures, guide-vane/blade regulation and mature governor/control systems. Their complexity is mechanical (movable parts, spiral casings, draft tubes) and cost, not informational.

**PATs** invert this. Their key complexity is the **lack of published turbine-mode performance data**: "manufacturers of pumps will not provide their characteristics under the turbine mode, which requires performance prediction methods" [Frontiers][ref-05] (Frontiers review). Designers must predict the turbine-mode BEP from pump data via semi-empirical correlations (e.g. Yang et al., 2012: h = 1.2/η^1.1, q = 1.2/η^0.55), CFD, or lab testing — none universally accurate (Singh, 2005). The machine itself is mechanically simpler (fixed geometry, no guide vanes), but achieving flexibility comparable to a conventional turbine "would require the installation of a relatively sophisticated and expensive control system" (Novara & McNabola, 2018).

### 1.5 Expected service life / lifespan

Well-built micro-hydro systems are long-lived: turbines "20 to 30 years or more" [Suneco Hydro][ref-10] and often 20–50 years for the overall system [Suneco Hydro][ref-10] (Suneco Hydro), with hydropower systems "often 40 years or more" [Renewable Energy Hub][ref-11] (Renewable Energy Hub). Mechanical equipment (turbines, pumps, generators) generally needs major refurbishment/replacement every 20–40 years, and electrical/control systems every 10–25 years. [Sustainability-directory][ref-12] PATs, being standard industrial pumps in stainless/cast iron, share this durability, though running a pump in reverse at off-design and under transients can accelerate wear on bearings/seals if poorly selected. No source indicates a materially shorter design life for correctly selected PATs versus conventional micro-turbines; both are multi-decade assets when protected from sediment and cavitation.

### 1.6 Market availability

This is the strongest PAT advantage. Pumps are "easily available industrial equipment in most countries," [researchgate][ref-13] highly standardized, with "off-the-shelf availability … up to a nominal power of around 250 kW," [researchgate][ref-13] short delivery times, easy installation, and abundant spare parts (Novara et al., 2019; Alatorre-Frenk, 1994). Above ~250 kW–1 MW, dedicated manufacturing is needed, restricting PATs to mini/micro/pico hydro. Conventional micro-turbines (especially Crossflow, small Pelton) are also commercially available but are semi-custom, longer-lead, and — for spiral-case Francis — "rare … on sites of less than 100 kW output" [greenbugenergy][ref-03] (GreenBug). Purpose-built low-head/in-pipe turbines (spherical, inline axial) are still largely at prototype/early-commercial stage (e.g. LucidPipe).

## PART 2 — Comparison of Conventional Micro-hydroturbines and PATs

| Dimension | Conventional Micro-hydroturbines — Advantages | Conventional Micro-hydroturbines — Disadvantages | PATs — Advantages | PATs — Disadvantages |
| --- | --- | --- | --- | --- |
| **Peak (BEP) efficiency** | High: Francis/Kaplan >90%; small Pelton ~90%, small Francis ~92%; Crossflow ~80% | Crossflow lower (~80%) | Typical BEP ~70–80%; semi-axial up to 70–75%+ | Lower peak than purpose-built; below pump-mode. Field WDN average, not BEP: ~60% |
| **Part-load / off-design** | Pelton & Kaplan excellent at low flow | Francis & Crossflow drop off below ~50% flow | Variable-speed (ER) can improve performance | Rapid off-BEP loss; BEP shifts to higher flow; flow instabilities |
| **Capital cost (€/kW)** | Predictable equipment cost; competitive at larger sizes (>200–300 kW) | Micro-scale equipment costs 5–15× more per kW than PAT | PAT+generator equipment: 130–5,400 €/kW; 5–15× cheaper than conventional turbines | Cost advantage shrinks above ~200–300 kW |
| **Installation cost** | Standard practices | Turbogenerator: 30–70% of small-scheme cost | Compact; easy installation; short delivery | Backpressure-control system can reach 1.2× PAT+generator cost |
| **O&M cost** | Mature service ecosystem | Movable parts add maintenance | Low O&M; standard parts; global service | Reverse-mode wear if mis-selected |
| **Pressure regulation** | Native hydraulic regulation | — | Achievable with HR, ER (VFD) or HER; NPV 6–29% higher than PRV | Additional valves/bypass or inverter; ER can operate far from BEP |
| **Design complexity** | Manufacturer hill charts; standardized selection | Mechanically complex | Mechanically simple; fixed geometry | No manufacturer turbine-mode curves; BEP prediction required; no universally accurate method |
| **Service life** | 20–50 yr; refurb every 20–40 yr | Electrical/controls 10–25 yr | Comparable multi-decade life; robust materials | Off-design/transient wear risk |
| **Market availability** | Commercially available | Semi-custom; Francis rare <100 kW; longer lead | Off-the-shelf ≤~250 kW; mass-produced; abundant spares | Limited to <~250 kW–1 MW; dedicated build needed above that |

Row notes:

- **Part-load / off-design:** the conventional Pelton/Kaplan entry refers to adjustable geometry holding efficiency at low flow.
- **Capital cost / Installation cost:** the €/kW entry concerns equipment procurement; the control-system figure is a separate cost conditional on backpressure control.
- **O&M cost:** guide vanes and blades are the movable parts named in the conventional entry.
- **Pressure regulation:** the conventional hydraulic mechanisms are guide vanes, nozzles and blades.
- **Design complexity:** the conventional mechanical examples are casings, draft tubes and governors. PAT prediction uses correlations, CFD or testing; absent turbine-mode curves necessitate that prediction.

## PART 3 — Technical Parameters and Applicability of Various Turbine Types

Ranges are approximate and manufacturer/design-dependent; sources disagree at the margins (see notes). Efficiencies are design-point unless stated. Hydrokinetic/lift-based devices (spherical, Gorlov, Darrieus) are quoted as power-coefficient / exergy efficiency, which is not directly comparable to water-to-wire turbine efficiency.

| Turbine | Type (Impulse/Reaction) | Head range (m) | Flow rate (m³/s) | Design-point efficiency (%) | Pressure-regulation capability |
| --- | --- | --- | --- | --- | --- |
| **Pelton** | Impulse | ~20 – >1,000 (high head) | ~0.005 – 1 (low) | ~90 (small units); up to ~92 | Excellent — adjustable spear-jet/nozzle regulates flow; flat efficiency curve at part load |
| **Turgo** | Impulse | ~15 – 300 (med– high; overlaps Francis/Pelton) | ~0.01 – 0.15+ (higher than Pelton per diameter) | ~80–90 | Good — nozzle/jet regulation; broad flow range |
| **Crossflow (Banki-Michell)** | Impulse | ~2 – 200 (low– medium) | ~0.02 – 10 | ~75–85 (often ~80) | Good — adjustable guide vanes/splitter; two-cell partial admission gives discharge regulation; efficiency falls below ~50% flow |
| **Francis** | Reaction | ~20 – 700 (medium; 45–250 typical) | ~0.5 – hundreds | >90 (large); ~92 small | Moderate — adjustable guide vanes; efficiency falls off rapidly below ~50% flow |
| **Kaplan** | Reaction | ~2 – 70 (low; ~10–70 typical) | high (tens– hundreds) | >90 | Excellent — double-regulated (blades + guide vanes) holds efficiency 15–100% discharge |
| **Semi-Kaplan / Propeller** | Reaction | ~1.5 – 30 (low; propeller most efficient <10) | variable, high | ~74 (guide-vane-free bulb) to >90 (regulated) | Single-regulated (30–100% discharge) or fixed propeller (narrow range) |
| **Pump-as-Turbine (PAT)** | Reaction | ~3 – 350 (radial); 10 – 311 (multistage) | ~0.001 – 0.32 | ~70–80 (field ~60) | Only via HR (valve+bypass), ER (VFD/inverter) or HER; no built-in guide vanes |
| **Spherical / sphere (in-pipe, lift-based)** | Reaction / lift-based | Extracts small head; head loss ~1.6 m (2.7%) to ~9.7% of pipe head | governed by pipe velocity 0.8–6.5 m/s (urban ~1.2–2.0 m/s); ~1 m³/s in 1 m pipe | ~22–27 (Cp basis); up to 43 exergy (free-flow LST) | Minimal head extraction — well suited to sit in-line without disturbing supply |
| **Archimedes screw** | Gravity / quasi-static pressure machine | ~0.1 – 10 (single screw ≤~8) | ~0.01 – 14.5 | ~60–80 practical (lab peaks 55–89) | Variable-speed screw adjusts to available flow; tolerant of debris/variable flow |
| **In-line axial / tubular / bulb (e.g. LucidPipe)** | Reaction | ~1 – 5 (academic low-head); LucidPipe extracts ~0.7–4 m (1–5 psi)/unit | 0.05–0.15 (academic); LucidPipe rated 14/50/100 kW at ~27–32 m head, 3 m/s | ~74 (ultra-low-head bulb) to >90 (regulated bulb/Kaplan) | Very low head extraction per unit; units can be staged in series; deactivate at low flow |
| **Deriaz (diagonal, adjustable-blade)** | Reaction | ~20 – 100 (some sources 20–200) | high | High over wide range (double-regulated; Kaplan-like part-load) | Excellent — adjustable diagonal blades regulate over wide head/flow window |
| **Water wheel (overshot/undershot)** | Gravity | <6 (undershot <0.5–2.5) | few m³/s (~0.15–0.2 per m width overshot) | ~85 overshot; ~75 undershot; 75–80 breastshot | Tolerates highly variable flow (0.2<Q/Qmax<1); inherently slow-running |
| **Gorlov helical (hydrokinetic)** | Reaction / lift-based (VAWT) | Ultra-low / free-flow (<2 m with nozzle) | velocity-driven (<1–3 m/s) | ~35 (Cp); ~70 exergy (free-flow) | Free-flow/in-pipe with blockage; no defined head regulation |
| **Darrieus (cross-flow VAWT, hydrokinetic)** | Reaction / lift-based | Ultra-low head (<2 m); in-pipe via high blockage | velocity-driven 0.5–3 m/s | Cp ~0.25–0.29 (up to ~0.45 with diffuser) | Free-flow/in-pipe; ultra-low head niche |

**Notes on disagreement:** Kaplan head upper bound is given variously as ~30 m (flashcards) up to ~70 m (ScienceDirect); Pelton lower bound 15–20 m. Crossflow efficiency cited 55% (one experiment, 8–10.5 m head) to 85% (5.5 m, 100 L/s). Archimedes-screw upper head varies 5/8/10/15 m depending on single vs multiple screws. Deriaz head range 20–100 m (peer-reviewed/encyclopedia) vs 20–200 m (course notes). Spherical/Gorlov/Darrieus efficiencies are Cp/exergy from CFD or tank tests, not water-to-wire.

## PART 4 — Main Economic and Technical Challenges to Installing Energy-Recovery Equipment in Urban Water Networks

**Variable, unpredictable flow and pressure; daily/seasonal demand.** Urban WDN flows swing widely over the day and season (e.g. Souza et al. varied speed 2,400 rpm at 11 am to 3,000 rpm at 6 pm to track demand). [Springer][ref-08] Because fixed-geometry machines (especially PATs) lose efficiency sharply off-BEP, the network's variability — not the peak potential — usually dictates recovered energy. Studies repeatedly find that variable/highly-variable flow "remains a key challenge" and that real-time control is needed to maximise recovery.

**Low and fluctuating head.** Available head in distribution mains is often small and limited; utility PRV data indicate typical pressure drops on the order of ~3.5 bar (~35 m) with ~8 kW dissipated, but many sites offer far less. Low head pushes designs toward reaction/low-head machines (Kaplan, bulb, screw, spherical) that are either costly or immature.

**Part-load efficiency losses.** As above — the central technical penalty. PATs and Francis/Crossflow lose efficiency below ~50% flow; only variable-speed drives, multiple parallel units, or adjustable-geometry (conventional) turbines mitigate this, each adding cost/complexity.

**Site selection, placement and sizing optimisation.** Choosing the DMA/branch, machine type and operating hours is an optimisation problem (EPANET-based simulation-optimisation, particle swarm, simulated annealing in the literature). Muhammetoglu et al.'s Antalya (Konyaalti) study of 18 DMAs found "DMA-6 was the best site for implementation of PAT with a payback period of 0.85 year," illustrating how strongly site choice drives economics. A widely cited practical threshold: ~2 kW is the minimum economically viable recovery potential, and payback ≤10 years typically requires generation potential above a 3–25 kW threshold band.

**Water-quality and leakage/pressure-management trade-offs.** Pressure reduction reduces leakage and pipe bursts, which is often worth more than the electricity; energy recovery must not compromise minimum service pressure or water quality. Devices inserted in potable mains require materials/precautions "to ensure the essential reliability of water supply" [researchgate][ref-13] (Novara et al., 2019).

**Cavitation and mechanical wear.** Low-head reaction machines elevated above tailwater, or PATs pushed off-design, risk cavitation and vibration; sediment erodes nozzles, runners, guide vanes and seals, shortening life. Axial PATs at part load show "significant pressure fluctuations and vibration noise" [ScienceDirect][ref-14] that "greatly shorten the service life." [ScienceDirect][ref-14]

**Water hammer / transients.** Sudden PAT/turbine shutdown or load rejection generates pressure transients that can damage pipes; dynamic behaviour "during the groups' shut-off" is a recognised design constraint (Fontana/Ramos), and electro-hydraulic transients with self-excited induction generators are an active research topic.

**Grid connection and electrical integration.** Interconnection is frequently the "weak link": queues, network-upgrade costs and utility procedures delay and burden small distributed generators. Lawrence Berkeley National Laboratory's 2024 analysis (a >2,000-project dataset spanning 2000–2024) found average interconnection costs for "complete" projects reaching $194/kW between 2018 and 2024, with active-queue and withdrawn projects incurring substantially higher costs primarily due to rising network-upgrade costs, and most requests ultimately withdrawn. Variable-speed PATs need four-quadrant inverters and control to deliver "flexible grid-connected power generation" (Mercier et al., 2019); self-excited induction generators raise voltage/frequency-stability issues off-grid.

**Payback, NPV, IRR.** Documented WDN/irrigation PAT economics are attractive but scattered: Antalya DMA-6 payback 0.85 yr; a PAT design-strategy case 2.1 yr; a variable-speed WDN case with 27-month payback, NPV US$64,476.18 and IRR 63% recovering 270,192.19 kWh/year (Souza et al., 2023); an irrigation case with feasibility-index/IRR 0.79, B/C 8.2 and 2-yr payback (485 MWh/yr); a PAT-PV hybrid with 8-yr payback. A speed-controlled micro-pumped-storage case reached LCOE ~29.2 €cents/kWh [MDPI][ref-15] with WDN PAT payback ~6 yr (*Sustainability* 2022, 14, 653). Conventional-turbine comparison: a Francis turbine produced more energy but a PAT delivered ~4% higher NPV (*Energy* 2025). An irrigation PSO study spanned paybacks 0.88–12.92 yr depending on energy price and site.

**Regulatory and utility-ownership barriers.** Water utilities are not traditional generators; integrating distributed energy resources strains their planning models, and regulatory/utility incentive structures are often misaligned (US DOE Grid Modernization Strategy, 2024; WaterWorld "Backing the Grid"). Ownership, permitting and revenue-model questions (who owns/operates the generation, how power is sold or self-consumed) slow adoption.

**Lack of standardized PAT performance data.** Pump makers do not publish turbine-mode curves, forcing prediction and creating selection risk — the discordant, outdated cost/performance figures in the literature are "a severe barrier to a more widespread PAT implementation" [researchgate][ref-13] (Novara et al., 2019).

**Maintenance access and civil works.** PRVs typically sit in confined manholes/chambers; retrofitting a machine plus bypass, control and grid tie often demands new civil works — "a great barrier to the diffusion of a small hydro power plant in water distribution is represented by the necessity of additional civil works to host the whole plant" [DOI][ref-16] (*Water* 2022, 14, 1526). Axial/inline turbines need straight pipe runs and horizontal alignment, "posing installation constraints in compact water networks." [ScienceDirect][ref-17]

## Recommendations

1. **Default to PATs for sub-100 kW in-pipe/PRV-replacement sites.** The 5–15× capital advantage and off-the-shelf availability dominate at this scale; documented paybacks of ~1–4 years are achievable at well-chosen sites. Benchmark to change this decision: if computed installed power exceeds ~200–300 kW, re-evaluate against a conventional turbine, whose higher efficiency and narrowing cost gap then favour it.
2. **Screen sites before selecting a machine.** Require ≥~2 kW recoverable potential as a minimum viability floor and target sites in the 3–25 kW+ band for ≤10-year payback. Use EPANET-based simulation-optimisation to fix location, size and operating hours using at least a year of flow/pressure data.
3. **Match the regulation strategy to variability.** For modest variability, hydraulic regulation (valve + bypass) usually gives higher overall efficiency; for highly variable branches, use electric (variable-speed) regulation or multiple parallel units. Budget the control system explicitly — it can reach 1.2× the PAT+generator cost when strict backpressure control is required.
4. **Value leakage/pressure benefits alongside energy.** Justify projects on combined NPV (energy + water-loss + burst reduction), where PATs have shown 6–29% higher NPV than PRVs; do not judge on kWh alone.
5. **De-risk the two biggest technical unknowns early:** (a) obtain or predict turbine-mode curves (Yang et al. 2012 correlations, CFD, or lab test) since manufacturers won't supply them; (b) run a transient/water-hammer analysis and specify controlled shutdown to protect mains.
6. **Engage the grid operator and regulator at concept stage** to resolve interconnection, ownership and revenue-model questions, which are frequently the schedule-critical path.

**Thresholds that would change the recommendation:** installed power >200–300 kW (favour conventional turbine); available head so low that only immature in-pipe devices (spherical/inline axial) apply (pilot-only until commercially proven); or a site where pressure reduction alone (a PRV) already captures most of the value and generation payback exceeds ~10 years (defer generation).

## Caveats

- Numeric ranges vary between sources; where they conflict (Kaplan/Pelton head bounds, Crossflow and Archimedes-screw efficiency, Deriaz head range) both bounds are reported and flagged.
- Lift-based/hydrokinetic device "efficiencies" (spherical, Gorlov, Darrieus) are power-coefficient or exergy values from CFD/tank tests, not directly comparable to conventional water-to-wire turbine efficiency, and these devices remain largely pre-commercial for potable networks.
- Economic figures (payback/NPV/IRR) are strongly site-, tariff- and year-specific; the cited cases are illustrative, not universal, and older €/kW figures should be inflation-adjusted.
- LucidPipe and similar commercial in-pipe figures trace ultimately to manufacturer data.
- This report deliberately excludes and does not rely on one specific 2024 review article per the research scope; all figures here are drawn from independent peer-reviewed papers, technical manuals, manufacturer data and agency reports.

[ref-01]: <https://en.wikipedia.org/wiki/Kaplan_turbine>
[ref-02]: <https://www.mecaflux.com/en/turbines.htm>
[ref-03]: <https://greenbugenergy.com/get-educated-knowledge/types-of-turbines>
[ref-04]: <https://www.sciencedirect.com/topics/engineering/kaplan-turbines>
[ref-05]: <https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2021.818118/full>
[ref-06]: <https://www.nzdl.org/cgi-bin/library?e=d-00000-00---off-0hdl--00-0----0-10-0---0---0direct-10---4-------0-1l--11-en-50---20-about---00-0-1-00-0-0-11-1-0utfZz-8-00-0-0-11-10-0utfZz-8-00&cl=CL1.11&d=HASH011f05bf8734d88d1a080257.6.2&gt=1>
[ref-07]: <https://en.wikipedia.org/wiki/Pump_as_turbine>
[ref-08]: <https://link.springer.com/article/10.1007/s11269-022-03421-9>
[ref-09]: <https://www.researchgate.net/publication/317358497_Full-Scale_PAT_Application_for_Energy_Production_and_Pressure_Reduction_in_a_Water_Distribution_Network>
[ref-10]: <https://www.sunecohydro.com/how-long-does-a-micro-hydro-system-last/>
[ref-11]: <https://www.renewableenergyhub.co.uk/main/hydroelectricity-information/maintenance-and-warranties-for-hydroelectricity-systems>
[ref-12]: <https://energy.sustainability-directory.com/question/what-is-the-lifespan-of-pumped-hydro/>
[ref-13]: <https://www.researchgate.net/publication/331699316_Cost_Model_for_Pumps_as_Turbines_in_Run-of-River_and_In-Pipe_Microhydropower_Applications>
[ref-14]: <https://www.sciencedirect.com/science/article/abs/pii/S0196890424006253>
[ref-15]: <https://www.mdpi.com/2071-1050/14/2/653>
[ref-16]: <https://doi.org/10.3390/w14101526>
[ref-17]: <https://www.sciencedirect.com/science/article/abs/pii/S0020740326000147>
