# 液压成形技术材料选用与制造缺陷控制深度研究报告

液压成形（Hydroforming）作为一种利用高压流体作为传力介质使金属管材或板材在模具型腔内发生塑性变形的先进制造成形技术，在现代汽车轻量化底盘、车身骨架以及航空航天复杂异形导管构件制造中确立了关键地位[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。相比于传统冲压拼焊工艺，液压成形具备减少零部件与焊缝数量、提高结构刚度与疲劳寿命、减轻构件重量以及提升材料利用率等多重优势[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。然而，随着高强度钢、轻质铝镁合金及难变形钛合金的规模化应用，材料力学性能差异与成形工艺窗口的窄化对材料选型与缺陷控制提出了更高的技术要求[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。本报告针对液压成形中的代表性材料体系及其力学行为进行系统分析，并对成形过程中五大典型制造缺陷的产生机理与工程对策展开深度剖析。

## 常用材料分析

材料的微观组织、力学本构关系以及硬化行为直接决定了液压成形过程中的压力加载轨迹、模具工装寿命与最终构件的尺寸精度[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。

### 高强度钢（HSS / AHSS）

高强度钢及先进高强钢（AHSS）主要包括双相钢（DP，如 DP600、DP780）、相变诱发塑性钢（TRIP，如 TRIP780）、复相钢（CP）以及热成形硼钢（如 22MnB5）等牌号[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/)。此类材料具备优异的屈服强度（$\sigma_y \approx 300 \sim 1200\text{ MPa}$）与抗拉强度，其弹性模量高（$E \approx 210\text{ GPa}$），在特定强度级别下保持了良好的加工硬化指数（$n$ 值），赋予零件极高的抗冲击吸能能力与优良的抗疲劳服役性能[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/)。

然而，在高强度钢的成形过程中，材料强度的提高直接导致室温断后伸长率急剧衰减，成形极限图（FLD）整体下移[[2]](https://mfr.edp-open.org/articles/mfreview/pdf/2014/01/mfreview140008.pdf)。这使得初始屈服起胀压力 $P_{yield}$ 与模具微小圆角贴模整形所需的校形压力 $P_{calibration}$ 异常高昂，常规管材液压成形内压往往需达到 $150 \sim 350\text{ MPa}$[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)：

$$P_{yield} = \frac{2 t_0}{D_0 - t_0} \sigma_y$$

$$P_{calibration} = \frac{2}{\sqrt{3}} \sigma_f \ln\left(\frac{r_b}{r_b - t}\right)$$

式中 $t_0$ 为初始壁厚，$D_0$ 为管材外径，$\sigma_f$ 为流动应力，$r_b$ 为模具圆角半径[[8]](https://repository.lib.ncsu.edu/bitstreams/46bf68b3-dd34-44ce-bd51-f67741a5ad84/download)。超高内压不仅对压机的闭合吨位与合模力设计提出了严峻挑战，加剧了模具型腔表面的磨损，且其较高的屈模比（$\sigma_y / E$）会在开模卸载后引发强烈的弹性回弹，极难保证复杂截面的尺寸稳定性[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。

在实际工业应用中，高强度钢液压成形技术主要集中于对抗扭刚度与碰撞安全性要求极高的汽车闭口承载件[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。典型应用包括乘用车前副车架横梁（Front Subframe Crossmember）、发动机悬置支架与后扭力梁总成，通过整体液压胀形替代传统的冲压双半焊接壳体结构，实现单件减重 $15\% \sim 25\%$ 并显著减少焊缝疲劳源[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。此外，在 A 柱/B 柱加强嵌管、车顶纵梁（Roof Rail）以及基于内外差压液压成形工艺（HIEP）制造的高强钢轻量化车轮轮辋中也得到了成熟应用[[4]](https://www.mdpi.com/1996-1944/15/19/6820)。

### 高强度铝合金

用于液压成形的高强度铝合金涵盖不可热处理强化的 5xxx 系（如 5083、5182、5754，Al-Mg 系）以及可热处理强化的 6xxx 系（如 6061、6082、6111，Al-Mg-Si 系）和 7xxx 系（如 7075，Al-Zn-Mg-Cu 系）[[6]](https://mfr.edp-open.org/en/component/article?access=doi&doi=10.1051%2Fmfreview%2F2014007&mb=0)。铝合金的密度约为 $2.7\text{ g/cm}^3$，仅为钢材的三分之一，具备出色的比强度和优异的耐腐蚀性能，但其弹性模量较低（$E \approx 70\text{ GPa}$），且具有相对明显的平面各向异性[[6]](https://mfr.edp-open.org/en/component/article?access=doi&doi=10.1051%2Fmfreview%2F2014007&mb=0)。

高强度铝合金在室温下的主要成形挑战在于其塑性变形范围窄、成形极限低，在大胀形率及深腔圆角充填时极易过早出现局部缩颈并破裂[[2]](https://mfr.edp-open.org/articles/mfreview/pdf/2014/01/mfreview140008.pdf)。同时，铝合金在超高法向接触应力下极易与钢模具表面发生微观焊合，产生粘模划伤（Galling）缺陷[[13]](https://grokipedia.com/page/Hydroforming)。此外，由于弹性模量仅为钢的 $1/3$，其成形后的回弹量通常是同级别强度钢制构件的 2 到 3 倍，尺寸公差极难控制[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。为突破室温成形极限，行业目前广泛采用温热液压成形技术（Warm Hydroforming），在 $150^\circ\text{C} \sim 250^\circ\text{C}$ 温度区间内软化基体金属、激发滑移系，以兼顾延伸率提升与成形精度[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/)。

高强度铝合金在汽车底盘轻量化与航空管路系统中应用广泛[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。在汽车领域，典型应用为底盘轻量化副车架、后悬架纵臂及仪表板横梁支架，常采用 6061-T4 态挤压管进行内高压成形并在成形后实施 T6 人工时效热处理，实现力学性能与轻量化指标的最优平衡[[2]](https://mfr.edp-open.org/articles/mfreview/pdf/2014/01/mfreview140008.pdf)。在航空航天领域，5083 和 6061 铝合金管材被广泛应用于飞机环境控制系统的大直径变截面通风导管与燃油输送管路，通过整体液压胀形成形消除了传统多段拼焊带来的密封失效隐患[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。

### 镁合金

代表性变形镁合金包括 AZ31B、AZ61、AZ80 以及 ZM21 等牌号[[4]](https://www.mdpi.com/1996-1944/15/19/6820)。镁合金具有工程结构金属中最低的密度（约 $1.74 \sim 1.81\text{ g/cm}^3$），比铝轻 $33\%$、比钢轻 $77\%$，展现出极高的比强度与比刚度，且具备优良的抗震阻尼能力和电磁屏蔽性能[[12]](https://pdfs.semanticscholar.org/ab90/6ecb5a7589367c50062f6dfdcca004f8c434.pdf)。

由于镁合金具备密排六方（HCP）晶体结构，在室温条件下其独立的基面滑移系数量不足以满足冯·米塞斯连续塑性变形准则，室温断后伸长率通常不足 $10\%$，室温冷态液压成形极易发生早期脆断[[4]](https://www.mdpi.com/1996-1944/15/19/6820)。因此，镁合金必须依托温热液压成形技术（成形温区通常在 $150^\circ\text{C} \sim 300^\circ\text{C}$），通过热激活启动非基面（柱面与锥面）滑移并引发动态再结晶来提升塑性极限[[16]](https://www.mdpi.com/2075-4701/11/6/901)。在温热成形过程中，液体介质（通常为特种耐高温合成硅油）的蒸发与热裂解限制了工艺上限温度（通常控制在 $300^\circ\text{C}$ 以内）[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/)。此外，高温下镁合金材料在补料进给区的抗变形抗力急剧下降，在轴向进给推力作用下极易产生材料镦粗失稳与壁厚不均，需要对模具施加高精度的非均匀温场梯度控制[[16]](https://www.mdpi.com/2075-4701/11/6/901)。

在应用方面，镁合金主要用于对结构减重与减震有极致要求的汽车骨架零件及高端构件[[12]](https://pdfs.semanticscholar.org/ab90/6ecb5a7589367c50062f6dfdcca004f8c434.pdf)。典型实例包括汽车一体化仪表板横梁（Cross Car Beam, CCB）与转向系统骨架件，利用 AZ31B 挤压管在 $220^\circ\text{C} \sim 250^\circ\text{C}$ 下进行温热内高压成形，实现单件减重 $40\%$ 以上并提升驾舱结构刚度[[16]](https://www.mdpi.com/2075-4701/11/6/901)。此外，在高端赛车与摩托车锻造空心轮辐件中，采用 AZ80 锻造管坯经温态内压扩张成形，能够有效规避铸造镁合金轮毂常见的内部缩松与微气孔缺陷[[4]](https://www.mdpi.com/1996-1944/15/19/6820)。

### 钛合金

液压成形涉及的钛合金涵盖工业纯钛（如 TA1、TA2）及高强双相钛合金（如 TA15、TC4 / Ti-6Al-4V 等）[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。钛合金兼具出色的比强度、优异的高温蠕变抗力（可在 $400^\circ\text{C} \sim 550^\circ\text{C}$ 下长期稳定服役）以及卓越的耐腐蚀性能，是航空航天领域极端工况构件的首选材料[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。

钛合金在室温下的变形抗力巨大、加工硬化显著，且屈强比（$\sigma_y / \sigma_u$）极高，塑性加工窗口极为狭窄，冷态液压成形极易发生开裂，卸载回弹量巨大且难以预测[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。对于 TC4、TA15 等高强钛合金，常温液压胀形基本无法实现，必须依赖高温高压气动成形（High Pressure Pneumatic Forming, HPPF / HMGF）或超塑成形工艺，在 $700^\circ\text{C} \sim 850^\circ\text{C}$ 的高温以及 $10 \sim 70\text{ MPa}$ 的高纯氩气压力下进行[[18]](https://www.mdpi.com/2504-4494/4/2/56)。在高温环境下，钛合金极易与环境中的氧、氮等气体发生剧烈反应生成脆硬的 $\alpha$ 表面污染层，成形过程必须保持全程惰性气氛保护；同时，极端高温对模具材料的抗高温蠕变性提出了苛刻要求，通常需使用昂贵的高温镍基合金模具，大幅推高了制造成本[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。

在主要应用领域，钛合金主要服役于航空发动机高温区管路与航天飞行器流体控制系统[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。典型应用包括航空发动机复杂引气歧管、排气喷口异形流道组件及机匣双壁导管，采用 TA15 或 TC4 管材在 $800^\circ\text{C} \sim 850^\circ\text{C}$ 下实现一次气压成形，消除传统焊接结构的多道环焊缝，提升疲劳寿命并大幅削减推重比瓶颈[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。在航天推进系统高压耐腐蚀波纹管及异形钛合金高压管路中，该技术也是确保高可靠无泄漏连接的核心制造手段[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。

### 代表性材料液压成形工艺特性与典型应用对比

表中温区与压力覆盖不同工况，不把一行解释为同一组可直接联用的参数。密度与屈服强度的具体测量温度、材料状态原稿未说明；下列补注仅区分已有数据的工况身份。

| 材料体系 | 代表性牌号 | 密度 ($\text{g/cm}^3$) | 典型屈服强度 $\sigma_y$ ($\text{MPa}$) | 典型成形工艺温区 | 适用成形压力区间 ($\text{MPa}$) | 核心成形瓶颈 | 典型应用部件实例 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **高强度钢 (AHSS)** | DP780, TRIP780, 22MnB5 | $\approx 7.85$ | $450 \sim 1200$ | 室温 $\sim 1000^\circ\text{C}$ （此栏跨室温与热气胀工况，具体牌号/状态对应原稿未说明）[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/) | $150 \sim 350$ （冷态液压成形，具体牌号/材料状态原稿未说明；不与左栏热气胀温度配成参数组）[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/) | 贴模校形压力极高、设备吨位大、卸载弹性回弹严重[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/) | 汽车前/后副车架横梁、车身 A/B 柱加强嵌管、轻量化轮辋[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/) |
| **高强度铝合金** | 5083, 6061, 7075 | $\approx 2.70$ | $120 \sim 480$ | 室温 $\sim 250^\circ\text{C}$ （室温至温态液压成形，具体数值对应介质/材料状态原稿未说明）[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/) | $50 \sim 180$（对应冷态或温态、介质及材料状态原稿未说明） | 室温塑性变形裕量小、模具表面易发生粘着划伤、回弹量大[[2]](https://mfr.edp-open.org/articles/mfreview/pdf/2014/01/mfreview140008.pdf) | 底盘控制臂纵梁、仪表板横梁支架、航空变径通风导管[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/) |
| **镁合金** | AZ31B, AZ61, ZM21 | $\approx 1.78$ | $140 \sim 260$ | $150^\circ\text{C} \sim 300^\circ\text{C}$ （温态液压；前文所述液体介质通常为特种耐高温合成硅油，各温度点对应材料状态原稿未说明）[[16]](https://www.mdpi.com/2075-4701/11/6/901) | $10 \sim 60$（温态液压相关压力；该区间的具体温度点、介质及材料状态原稿未说明）[[16]](https://www.mdpi.com/2075-4701/11/6/901)[[17]](https://www.researchgate.net/profile/Gang-Liu-68/publication/257444199_Warm_hydroforming_of_magnesium_alloy_tube_with_large_expansion_ratio_within_non-uniform_temperature_field/links/5a954ea0aca272140567f48e/Warm-hydroforming-of-magnesium-alloy-tube-with-large-expansion-ratio-within-non-uniform-temperature-field.pdf) | HCP 晶体室温脆性高、进给区材料易失稳镦粗、需控温介质[[4]](https://www.mdpi.com/1996-1944/15/19/6820) | 汽车一体化仪表板横梁（CCB）、转向柱骨架、赛车锻造空心轮辐[[4]](https://www.mdpi.com/1996-1944/15/19/6820) |
| **钛合金** | TA2, TA15, TC4 | $\approx 4.50$ | $350 \sim 950$ | $700^\circ\text{C} \sim 850^\circ\text{C}$ （高温气胀，前文所述为高纯氩气保护；各牌号/状态对应原稿未说明）[[20]](https://pmc.ncbi.nlm.nih.gov/articles/PMC5456185/) | $10 \sim 70$ （高温气动成形；具体温度点及材料状态原稿未说明）[[20]](https://pmc.ncbi.nlm.nih.gov/articles/PMC5456185/) | 变形抗力极大、高温氧化吸收气体脆化、工装模具成本昂贵[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/) | 航空发动机高温引气导管、机匣异形排气流道、航天高压波纹管[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/) |

## 常见缺陷、成因及对策

在液压成形中，内压加载路径（Pressure Path）、轴向补料位移（Axial Feed）、界面摩擦与模具几何边界构成高度耦合的动力学系统[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/)。参数的微小失配往往引起变形失稳和制造缺陷[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/)。

### 表面缺陷（Surface Defects）

- **粘模拉伤（Galling）—界面摩擦机制及对应措施**：大位移轴向补料时，局部极高接触正应力可破坏润滑油膜，金属微观接触副发生固相冷焊撕剥，铝、钛合金表面尤其容易划伤[[13]](https://grokipedia.com/page/Hydroforming)。对应的模具型面措施是物理气相沉积（PVD）表面改性，以及母本所列氮化钛铝（TiAlN）、类金刚石碳膜（DLC）或渗氮硬化层，目标是降低摩擦、阻断粘着[[14]](https://www.ispatguru.com/glossary-of-technical-terms-for-the-use-of-metallurgical-engineers-terms-starting-with-alphabet-f/)。润滑方面，母本列出高承载微乳化高压专用聚合物润滑剂，或用于温热条件的固态纳米二硫化钼（$\text{MoS}_2$）涂层；二者应按其原有液压/温热语境理解，现文未给出各牌号和温区的完整适配条件[[17]](https://www.researchgate.net/profile/Gang-Liu-68/publication/257444199_Warm_hydroforming_of_magnesium_alloy_tube_with_large_expansion_ratio_within_non-uniform_temperature_field/links/5a954ea0aca272140567f48e/Warm-hydroforming-of-magnesium-alloy-tube-with-large-expansion-ratio-within-non-uniform-temperature-field.pdf)。
- **桔皮（Orange Peel）—晶粒不均与冶金质量控制**：粗大且不均匀的晶粒在双向拉伸大变形中呈现不同取向滑移的各向异性，形成自由表面微观凹凸。相应对策是控制原料冶金质量和退火工艺、细化晶粒；母本提出 ASTM 8 级以上，但现文未给出这一数值对各材料、状态及工况普遍适用的依据。
- **流体侵蚀/硬质颗粒压痕—循环液压介质污染与清洁控制**：残留微米级氧化皮、金属切屑等，在高压注入和闭合加压时压入表层形成点状或凹坑。母本对应措施是在液压系统高压管路设置 $5\ \mu\text{m}$ 精度的高效反冲洗过滤装置，并对进模管坯进行严格表面酸洗去毛刺和高压清洗；该过滤精度保留为母本数值，现文未说明其普遍适用依据，此处液体循环过滤也不等同于气胀介质控制。

### 回弹（Springback）

- **主要成因与工况**：卸载后弹性应变能各向异性、不均匀释放是回弹来源[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。在弯曲预成形及后续非轴对称截面液压胀形中，壁厚内外存在显著拉压残余应力梯度[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)；卸内压、开模分离后，内部弯矩及残余应力失去外力约束，使截面张开、型面翘曲或轴线角度偏移[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。母本指出幅度与屈强比及屈模比（$\sigma_y / E$）成正比，高强钢和低模量铝合金尤为明显[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。
- **应力梯度—终端校形**：针对上述液压成形语境，母本的核心措施是充分的超高整形校形压力（Calibration Pressure），使终端阶段整个壁厚屈服、进入完全塑性流动，强制消除厚度方向应力反向梯度[[8]](https://repository.lib.ncsu.edu/bitstreams/46bf68b3-dd34-44ce-bd51-f67741a5ad84/download)。现文未给具体设备压力设定，也未给将此措施推广到所有高温气胀工艺的依据。
- **卸载形状变化—模具预补偿**：采用高精度有限元（FEA）弹塑性逆向反演，依据 Barlat 或 Hill 等先进各向异性屈服准则，对型腔曲率和截面角度作反向预补偿[[8]](https://repository.lib.ncsu.edu/bitstreams/46bf68b3-dd34-44ce-bd51-f67741a5ad84/download)。
- **难控制构件—温热液压路径**：母本列出的另一措施是温热液压成形，借助高温应力松弛和动态回复显著削减回弹[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)；这里保持温热液压的工况范围，不将其自动等同于高温气胀。

### 起皱（Wrinkling）

- **主要成因**：起皱本质上是材料在轴向或周向压应力作用下超过临界屈曲载荷所诱发的失稳现象[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/)。在管材液压成形中，主要成因是轴向进给补料量（Axial feed $s$）过大而内部液压支撑力（Internal pressure $p$）偏低或建压滞后，导致轴向压缩主应力占主导并引发管壁波浪状局部屈曲[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/)。在板材充液成形中，若压边圈提供的压边力（BHF）不足，板料在向凹模流动过程中切向压应力失稳也会导致凸缘起皱[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。起皱初期若波幅过大且波峰曲率陡峭，在后续高压贴模阶段无法被有效压平，就会相互挤压折叠形成不可消除的“死皱”，造成工件报废[[17]](https://www.researchgate.net/profile/Gang-Liu-68/publication/257444199_Warm_hydroforming_of_magnesium_alloy_tube_with_large_expansion_ratio_within_non-uniform_temperature_field/links/5a954ea0aca272140567f48e/Warm-hydroforming-of-magnesium-alloy-tube-with-large-expansion-ratio-within-non-uniform-temperature-field.pdf)。
- **建议的解决方法**：建立精密的闭环自适应压力-补料位移协同控制系统，通过仿真成形窗口严格优化动态加载曲线（$p-s$ 路径），确保内压始终处于起皱临界边界之上[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/)。在需要极高膨胀率的局部特征区，可主动采用“有益活皱”（Useful Wrinkling）控制策略，即在成形初期利用可控的浅波幅活皱汇聚金属体积，随后施加超高压将其平整贴模，兼顾防破与大变形要求[[17]](https://www.researchgate.net/profile/Gang-Liu-68/publication/257444199_Warm_hydroforming_of_magnesium_alloy_tube_with_large_expansion_ratio_within_non-uniform_temperature_field/links/5a954ea0aca272140567f48e/Warm-hydroforming-of-magnesium-alloy-tube-with-large-expansion-ratio-within-non-uniform-temperature-field.pdf)。在板料液压成形中，应引入多段差动可调压边力控制或液压背压腔体，防止凸缘区切向失稳[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)。

### 变薄（Thinning）

- **主要成因**：过度变薄是指成形区局部壁厚减薄率超过了工程技术规范阈值（通常为 $>15\% \sim 20\%$），其直接力学原因是变形区处于纯双向拉应力状态且材料补给受阻[[4]](https://www.mdpi.com/1996-1944/15/19/6820)。在工艺操作中，若轴向推杆补料行程不足或推进速度滞后于胀形升压速度，膨胀区表面积的增加将完全消耗原始壁厚[[4]](https://www.mdpi.com/1996-1944/15/19/6820)。若在成形早期过快施加高内压，管壁过早紧贴模具型腔，摩擦阻力会将材料流动在进给通道处“锁死”，导致材料无法向膨胀区转移[[4]](https://www.mdpi.com/1996-1944/15/19/6820)。此外，模具过渡圆角半径 $r_b$ 过小引发的局部应力集中也会加剧平面应变状态下的集中拉薄[[8]](https://repository.lib.ncsu.edu/bitstreams/46bf68b3-dd34-44ce-bd51-f67741a5ad84/download)。
- **建议的解决方法**：合理提高轴向补料比例与进给速率，使材料处于“一向受压、两向受拉”的有利三向应力状态，以连续的轴向材料流入补偿横向周向扩张引起的截面收缩[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/)。在模具设计中，针对复杂截面与小圆角区域可集成可动滑块或活动模套（Movable Die / Bushes），在成形过程中通过滑块主动推挤材料，将局部拉伸应力转为压应力，实现小圆角区域的低减薄或等厚贴模成形[[4]](https://www.mdpi.com/1996-1944/15/19/6820)。在温成形条件下，可构建“非均匀温场”，通过保持胀形区低温以维持较高抗力、加热补料区以降低流动剪切应力，从而引导材料均匀向变形区流动[[16]](https://www.mdpi.com/2075-4701/11/6/901)。

### 撕裂与破裂（Tearing / Bursting）

- **主要成因**：撕裂是液压成形中最严重的破坏性失稳缺陷。其根本成因是局部区域的主应变组合超过了材料在当前应力状态下的成形极限曲线（FLC/FLSD）或内压超过了极限破裂压力 $P_{bursting}$，致使微孔洞迅速形核、汇合演变为局部宏观缩颈并瞬间爆裂[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/)： $$P_{bursting} = \frac{4 t_0}{D_p - t_0} \sigma_u$$ 式中 $D_p$ 为膨胀区外径，$\sigma_u$ 为抗拉强度[[8]](https://repository.lib.ncsu.edu/bitstreams/46bf68b3-dd34-44ce-bd51-f67741a5ad84/download)。工艺上若内压过早飙升而补料受阻，局部过度减薄会迅速转变为拉伸撕裂[[4]](https://www.mdpi.com/1996-1944/15/19/6820)。前期产生的严重死皱在被高压强行压平折叠时，折叠根部的剪切应力集中也极易诱发沿晶撕裂[[17]](https://www.researchgate.net/profile/Gang-Liu-68/publication/257444199_Warm_hydroforming_of_magnesium_alloy_tube_with_large_expansion_ratio_within_non-uniform_temperature_field/links/5a954ea0aca272140567f48e/Warm-hydroforming-of-magnesium-alloy-tube-with-large-expansion-ratio-within-non-uniform-temperature-field.pdf)。此外，对于高频焊管（ERW）或激光拼焊管，若焊缝区热影响区（HAZ）存在硬化脆化相、微裂纹或未焊透缺陷，在高压胀形下会沿焊缝熔合线发生脆性撕裂[[7]](https://www.researchgate.net/publication/351300490_Predictions_of_formability_parameters_in_tube_hydroforming_process)。
- **建议的解决方法**：必须通过有限元数值模拟确定安全的成形极限裕度，精确优化内压随时间及位移的上升斜率，严禁在材料补料未充分进入型腔前盲目加压[[8]](https://repository.lib.ncsu.edu/bitstreams/46bf68b3-dd34-44ce-bd51-f67741a5ad84/download)。对于难变形材料，可采用双面液压成形（Double-Sided Hydroforming），通过在型腔外部施加可控液体背压（Back Pressure）显著提升变形区的全向静水压应力，抑制微观空洞扩展，成倍提升宏观破裂极限[[4]](https://www.mdpi.com/1996-1944/15/19/6820)。在原材料质量控制方面，应优先采用高洁净度无缝管材，或对焊接管坯实施焊后在线高频感应正火及全管退火处理，消除焊缝残余应力与粗大马氏体组织，使焊缝韧性与母材实现等延展性匹配[[2]](https://mfr.edp-open.org/articles/mfreview/pdf/2014/01/mfreview140008.pdf)。

### 常见制造缺陷机理与防治矩阵

| 缺陷类型 | 宏观外观特征 | 关键物理成因 | 核心力学判定机理 | 关键工程对策 |
| --- | --- | --- | --- | --- |
| **表面缺陷** (Surface Defects) | 模具咬死拉伤、微观桔皮凹凸、表层杂质压坑[[13]](https://grokipedia.com/page/Hydroforming) | 界面润滑油膜破裂、原材料晶粒粗大、高压流体介质污染[[13]](https://grokipedia.com/page/Hydroforming) | 金属微凸体界面微焊合剪切、自由表面晶粒各向异性滑移[[13]](https://grokipedia.com/page/Hydroforming) | 模具 PVD/DLC 镀膜、涂覆专用高压微乳润滑剂、原材料晶粒细化至 ASTM 8 级、系统增设 $5\ \mu\text{m}$ 过滤[[14]](https://www.ispatguru.com/glossary-of-technical-terms-for-the-use-of-metallurgical-engineers-terms-starting-with-alphabet-f/) |
| **回弹** (Springback) | 制件开模后截面张口、弯曲角度偏移、轮廓扭曲[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/) | 壁厚内外层拉压残余应力不均、材料屈模比 ($\sigma_y/E$) 过高[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/) | 截面弹性弯矩卸载释放 $\Delta \theta \propto \frac{\sigma_y}{E}$[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/)[[8]](https://repository.lib.ncsu.edu/bitstreams/46bf68b3-dd34-44ce-bd51-f67741a5ad84/download) | 施加超高全塑性校形压力 $P_{calibration}$、模具型面 FEA 逆向反弹预补偿、温热成形应力松弛[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/) |
| **起皱** (Wrinkling) | 管壁轴向/周向波浪纹、板件凸缘多层折叠死皱[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/) | 补料过多而内压支撑不足、板材成形压边力偏低[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/) | 局部压应力超过壳体临界屈曲极限 $\sigma_{comp} > \sigma_{critical}$[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/)[[17]](https://www.researchgate.net/profile/Gang-Liu-68/publication/257444199_Warm_hydroforming_of_magnesium_alloy_tube_with_large_expansion_ratio_within_non-uniform_temperature_field/links/5a954ea0aca272140567f48e/Warm-hydroforming-of-magnesium-alloy-tube-with-large-expansion-ratio-within-non-uniform-temperature-field.pdf) | 优化 $p-s$ 加载曲线提升动态支撑内压、采用“有益活皱”平整工艺、配置多段动态可调压边力[[1]](https://www.meetyoucarbide.com/sheet-metal-forming/) |
| **变薄** (Thinning) | 局部膨胀区壁厚急剧削薄、严重缩颈[[4]](https://www.mdpi.com/1996-1944/15/19/6820) | 补料量滞后、高内压导致管料被摩擦锁定、小圆角应力集中[[4]](https://www.mdpi.com/1996-1944/15/19/6820) | 双向主拉应力主导、厚向真应变 $\vert\varepsilon_t\vert$ 超过工程阈值[[8]](https://repository.lib.ncsu.edu/bitstreams/46bf68b3-dd34-44ce-bd51-f67741a5ad84/download) | 协同提升轴向补料量与速率、集成活动滑块/镶块模具结构、构建非均匀梯度温场引导金属流动[[4]](https://www.mdpi.com/1996-1944/15/19/6820) |
| **撕裂与破裂** (Tearing / Bursting) | 侧壁爆裂开缝、死皱处剪切断裂、焊缝开裂[[5]](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/) | 局部应变超限、加载内压超过爆破压力 $P_{bursting}$、焊缝脆性[[7]](https://www.researchgate.net/publication/351300490_Predictions_of_formability_parameters_in_tube_hydroforming_process) | 应变状态跨越成形极限图 (FLD/FLSD)、$P > P_{bursting}$[[8]](https://repository.lib.ncsu.edu/bitstreams/46bf68b3-dd34-44ce-bd51-f67741a5ad84/download)[[10]](https://www.thefabricator.com/tubepipejournal/article/hydroforming/turning-up-the-heat-on-tube-hydroforming) | 闭环加载路径防过压控制、应用双面液压背压技术提高静水压力、对焊接管坯实施焊缝在线退火[[4]](https://www.mdpi.com/1996-1944/15/19/6820) |

## Sources

1. [meetyoucarbide.com — Sheet Metal Forming: Mechanisms, Processes, Advanced Technologies, and Industrial Applications - Meetyou Carbide](https://www.meetyoucarbide.com/sheet-metal-forming/)
2. [mfr.edp-open.org — A critical review on special forming processes and associated research for lightweight components based on sheet and tube materi](https://mfr.edp-open.org/articles/mfreview/pdf/2014/01/mfreview140008.pdf)
3. [mdpi.com — Special Issue : Latest Hydroforming Technology of Metallic Tubes and Sheets - MDPI](https://www.mdpi.com/journal/metals/special_issues/hydroforming_tubes_sheets)
4. [mdpi.com — A Novel Hydroforming Process by Combining Internal and External Pressures for High-Strength Steel Wheel Rims - MDPI](https://www.mdpi.com/1996-1944/15/19/6820)
5. [pmc.ncbi.nlm.nih.gov — Integration of Hot Tube Gas Forming and Die Quenching of Ultra-High Strength Steel Hollow Parts Using Low Pressure Sealed-Air - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8874987/)
6. [mfr.edp-open.org — A critical review on special forming processes and associated research for lightweight components based on sheet and tube materials](https://mfr.edp-open.org/en/component/article?access=doi&doi=10.1051%2Fmfreview%2F2014007&mb=0)
7. [researchgate.net — (PDF) Predictions of formability parameters in tube hydroforming process - ResearchGate](https://www.researchgate.net/publication/351300490_Predictions_of_formability_parameters_in_tube_hydroforming_process)
8. [repository.lib.ncsu.edu — Optimizing tube hydroforming using process simulation and experimental verification](https://repository.lib.ncsu.edu/bitstreams/46bf68b3-dd34-44ce-bd51-f67741a5ad84/download)
9. [researchgate.net — (PDF) A novel approach in manufacturing two-stepped tubes using a multi-stage die in tube hydroforming process - ResearchGate](https://www.researchgate.net/publication/265336894_A_novel_approach_in_manufacturing_two-stepped_tubes_using_a_multi-stage_die_in_tube_hydroforming_process)
10. [thefabricator.com — Turning up the heat on tube hydroforming - The Fabricator](https://www.thefabricator.com/tubepipejournal/article/hydroforming/turning-up-the-heat-on-tube-hydroforming)
11. [nationalacademies.org — Application of Lightweighting Technology to Military Aircraft, Vessels, and Vehicles (2012)](https://www.nationalacademies.org/read/13277/chapter/6)
12. [pdfs.semanticscholar.org — Latest Hydroforming Technology of Metallic Tubes and Sheets - Semantic Scholar](https://pdfs.semanticscholar.org/ab90/6ecb5a7589367c50062f6dfdcca004f8c434.pdf)
13. [grokipedia.com — Hydroforming — Grokipedia](https://grokipedia.com/page/Hydroforming)
14. [ispatguru.com — Glossary of technical terms for the use of metallurgical engineers Terms starting with alphabet 'F' - IspatGuru](https://www.ispatguru.com/glossary-of-technical-terms-for-the-use-of-metallurgical-engineers-terms-starting-with-alphabet-f/)
15. [thefabricator.com — Warm forming of aluminum alloys - The Fabricator](https://www.thefabricator.com/thefabricator/article/bending/warm-forming-of-aluminum-alloys)
16. [mdpi.com — Warm Hydroforming Process under Non-Uniform Temperature Field for Magnesium Alloy Tubes - MDPI](https://www.mdpi.com/2075-4701/11/6/901)
17. [researchgate.net — Warm hydroforming of magnesium alloy tube with large expansion ratio within non-uniform temperature field - ResearchGate](https://www.researchgate.net/profile/Gang-Liu-68/publication/257444199_Warm_hydroforming_of_magnesium_alloy_tube_with_large_expansion_ratio_within_non-uniform_temperature_field/links/5a954ea0aca272140567f48e/Warm-hydroforming-of-magnesium-alloy-tube-with-large-expansion-ratio-within-non-uniform-temperature-field.pdf)
18. [mdpi.com — Hot Gas Forming of Aluminum Alloy Tubes Using Flame Heating - MDPI](https://www.mdpi.com/2504-4494/4/2/56)
19. [researchgate.net — Formability testing of AZ31B magnesium alloy tube at elevated temperature - ResearchGate](https://www.researchgate.net/publication/223650352_Formability_testing_of_AZ31B_magnesium_alloy_tube_at_elevated_temperature)
20. [pmc.ncbi.nlm.nih.gov — High Pressure Pneumatic Forming of Ti-3Al-2.5V Titanium Tubes in a Square Cross-Sectional Die - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5456185/)
21. [sid.ir — Analysis of Bursting in Tube Hydroforming - SID](https://sid.ir/fileserver/se/531e20141350.pdf)
22. [mdpi.com — Movable Die and Loading Path Design in Tube Hydroforming of Irregular Bellows - MDPI](https://www.mdpi.com/2075-4701/10/11/1518)
23. [scribd.com — Overview of Hydroforming Processes | PDF | Sheet Metal | Strength Of Materials - Scribd](https://www.scribd.com/document/694724879/lecture-9-Hydroforming-2)
24. [researchgate.net — Wrinkling Study in Tube Hydroforming Process | Request PDF](https://www.researchgate.net/publication/260814621_Wrinkling_Study_in_Tube_Hydroforming_Process)
25. [researchgate.net — Hydro-Forming of U-Shaped Parts with Branches - ResearchGate](https://www.researchgate.net/publication/397707798_Hydro-Forming_of_U-Shaped_Parts_with_Branches)
26. [https://www.lsrpf.com/hydroforming](https://www.lsrpf.com/hydroforming)
27. [https://eureka.patsnap.com/triz-case/hybrid-tube-forming-composite-beams](https://eureka.patsnap.com/triz-case/hybrid-tube-forming-composite-beams)
28. [https://asmedigitalcollection.asme.org/manufacturingscience/article/142/11/110813/1085053/Opportunities-and-Challenges-in-Metal-Forming-for](https://asmedigitalcollection.asme.org/manufacturingscience/article/142/11/110813/1085053/Opportunities-and-Challenges-in-Metal-Forming-for)
29. [https://www.researchgate.net/figure/Influence-of-the-pressure-rate-on-the-microstructure-a-1-Microstructure-of-an-initial_fig5_327659045](https://www.researchgate.net/figure/Influence-of-the-pressure-rate-on-the-microstructure-a-1-Microstructure-of-an-initial_fig5_327659045)
30. [https://re.public.polimi.it/bitstream/11311/978780/7/0The%20influence%20of%20process%20variables%20on%20the%20gas%20forming%20and%20press%20hardening%20of%20steel%20tubes%20%281%29.pdf](https://re.public.polimi.it/bitstream/11311/978780/7/0The%20influence%20of%20process%20variables%20on%20the%20gas%20forming%20and%20press%20hardening%20of%20steel%20tubes%20%281%29.pdf)
