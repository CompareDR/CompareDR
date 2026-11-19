# 低代码开发（Low-Code Development）市场与技术调 研报告（截至2021年底）

## TL;DR

- 截至2021年底，低代码已从"快速开发工具"演进为主流企业应用交付范式：Gartner 预测2021年全球低代码开发技 术市场规模达138亿美元（同比增⻓22.6%），并预言到2025年70%的新企业应用将使用低代码/无代码技术（2020 年不足25%）。
- 其技术内核是**模型驱动开发（MDD/MDE）+ 可视化拖拽 + 声明式配置 + 代码/元数据自动生成**，叠加云原生多租 户、流程引擎（BPMN）、API集成（iPaaS）与RPA；平台按"模型驱动 vs. 表单/数据驱动 vs. 流程驱动"分化，直接 决定了各自的目标客户与适用场景。
- 主流格局呈"国际六强 + 中国新势力"：Gartner 2021 LCAP魔力象限领导者为 Mendix、Microsoft、OutSystems、 ServiceNow、Salesforce 五家；中国市场由钉钉宜搭、简道云、氚云、明道云、iVX 等领跑，2021年市场规模约 27.5亿元人⺠币。核心优势（提速、降本、赋能业务、缓解人才短缺）直接源自底层抽象技术，但厂商锁定、可扩展 性与治理⻛险是公认局限。

## Key Findings

**1. 市场规模与增⻓（数据来源明确）**

- Gartner（2021年2月15日发布）：2021年全球低代码开发技术市场约138亿美元，同比增⻓22.6%。该新闻稿引用研 究副总裁 Fabrizio Biscotti 的预测："低代码应用平台（LCAP）预计将持续为该市场最大细分，2021年较2020年增 ⻓近30%，达到57.5亿美元。"（原文："low-code application platforms (LCAP) are expected to remain the largest component of the low-code development technology market through 2022, increasing nearly 30% from 2020 to reach $5.8 billion in 2021"）
- Gartner 反复引用的标志性预测："到2025年，企业开发的新应用中70%将使用低代码或无代码技术，高于2020年 的不足25%"。
- 中国市场：艾瑞咨询数据显示2020年约15.9亿元人⺠币（增速80.2%），2021年约27.5亿元（增速72.4%），预计未 来四年复合增速44.1%、2025年达约118.4亿元。

**2. Gartner 2021 LCAP 魔力象限（2021年9月20日发布，分析师 Jason Wong 等）共12家厂商**

- 领导者（Leaders）：Mendix（排名最高、远⻅维度最远）、Microsoft（Power Apps）、OutSystems、 ServiceNow、Salesforce。
- 挑战者（Challengers）：Appian（由上年领导者降级）、Pega（由远⻅者移入）、Oracle（APEX）。
- 利基厂商（Niche Players）：Creatio、Newgen、Quickbase、Kintone。
- （注：AgilePoint、AuraQuantic、Betty Blocks、Oracle Visual Builder、ProntoForms、TrackVia、Zoho 因 2021年更新的准入⻔槛不再入选。）

**3. Forrester Wave（2021年两份）**

- 面向专业开发者（Q2 2021，2021年5月11日发布，分析师 John Bratincevic 与 Rob Koplowitz，评估14家）：领导者 为 **Mendix、OutSystems、Microsoft、ServiceNow**；强劲表现者为 Salesforce、Pegasystems、Appian、 HCL Software；竞争者为 AgilePoint、Unqork、Oracle、Thinkwise；挑战者为 WaveMaker、GeneXus。报告 称 **Unqork 为"rookie of the year（年度新秀）"**。
- 面向业务开发者（Q4 2021，2021年10月28日发布，评估9家：Betty Blocks、Caspio、Claris、Creatio、 Google、Kintone、Quickbase、TrackVia、Zoho）：领导者包括 **Betty Blocks、Google AppSheet、 Quickbase**。

## Details

### 第一部分 核心技术基础

低代码平台并非单一技术，而是一组成熟技术范式的工程化集成。关键技术与设计范式包括：

1. **模型驱动开发/模型驱动工程（MDD/MDE/MDA）**：被普遍视为低代码的理论根基。通过计算无关模型（CIM）、平 台无关模型（PIM）、平台相关模型（PSM）等抽象层，将数据模型、业务逻辑、UI、工作流抽象为可处理的模型， 再自动映射为可运行系统。SoSyM [Emergent Mind][ref-01] 期刊论文《Low-code development and model-driven engineering: Two sides of the same coin?》（Softw. Syst. Model. 21(2):437–446, 2022；作者 Davide Di Ruscio、Dimitris Kolovos、Juan de Lara、Alfonso Pierantonio、 Massimo Tisi、Manuel Wimmer，受欧盟 Horizon 2020 Lowcomote 项目资助，编号 813884）指出：低代码与 MDE "都致力于通过提升抽象层次、隐藏实现级细节来改进软件开发"，但"两种实践并不完全等同"。
2. **可视化/图形化建模与拖拽式界面（WYSIWYG）**：以图形画布、区块、节点取代文本代码，是最直观的技术表征。 [Kissflow][ref-02]
3. **声明式编程（Declarative）**：聚焦"做什么"而非"怎么做"，用户描述期望结果，平台负责生成实现；无代码平台尤其 依赖此范式。 [Microsoft][ref-03]
4. **领域特定语言（DSL）与元建模（Metamodeling）**：部分平台使用自定义建模符号/DSL，简化抽象模型到目标代码 的映射。 [Emergent Mind][ref-01]
5. **代码生成与模型转换**：将可视化模型自动转换为前后端代码、配置文件；这是"低代码"区别于纯声明式黑盒的关键 ——部分平台（如 OutSystems）可生成可被第三方工具扫描的标准代码。
6. **组件化与可复用构件**：预制模块、模板、连接器像"乐高积木"一样拼装，是复用性的核心。 [Clickatell][ref-04]
7. **表单驱动与数据驱动开发**：中国技术社区将设计思想分为"表单驱动"（表单与数据存储结构合一，源自传统 BPM/Excel 服务器）与"模型驱动"（数据与表现分离，接近纯代码架构）两条路线。 [Alibaba Cloud][ref-05]
8. **工作流/BPM引擎与流程建模（BPMN 2.0）、规则引擎（DMN）**：流程型平台的技术核心，支持审批流、案件管理、 ⻓流程编排。
9. **云原生与多租户 SaaS 架构、容器化与微服务**：如 Pega Infinity 采用云原生、多租户、微服务架构，支持弹性伸 缩；Betty Blocks 采用微服务架构。
10. **API 优先与集成中间件（iPaaS/ESB/ETL）**：连接器生态（如得帆 200+ 连接器）打通遗留系统与外部服务。 [CSDN][ref-06]
11. **RPA 集成**：低代码与 RPA 融合为"超自动化"的一部分（Gartner 将 RPA 列为低代码技术市场的一个细分，2021年约 21.9亿美元）。
12. **AI 辅助开发（2021年前后新兴）**：2021年6月 GitHub 发布 Copilot 技术预览（基于 OpenAI Codex），标志 AI 代码 生成进入主流视野；同期 [GitHub][ref-07] Mendix、OutSystems、Microsoft 均在平台中嵌入 AI 辅助建模能力。

**总结分析（第一部分）**：这些技术并非并列，而是分层协作的"技术栈"。底层是**抽象与自动化**（MDD + 代码生成 + 声 明式），中层是**表现与复用**（可视化拖拽 + 组件化 + 表单/模型驱动），上层是**连接与运行**（云原生多租户 + API/iPaaS + BPM引擎 + RPA）。这一栈的核心矛盾决定了平台的技术路线选择：**表单驱动**路线上手快、适合业务人员，但数据 与表现耦合限制了复杂场景；**模型驱动**路线架构接近专业开发、可扩展性强，但学习⻔槛更高。这也解释了为何 Gartner 将"模型驱动或图形化编程"作为 LCAP 的最低⻔槛。2021年最重要的趋势是 **AI 辅助开发的萌芽**与**低代 码/MDE 的学术合流**——研究者指出，几乎可以把 MDE 的开放挑战直接"改名"为低代码的研究路线图，低代码本质 上降低了进入建模技术空间的⻔槛。 [Modeling Languages][ref-08]

### 第二部分 主要应用领域

低代码平台在2021年的主要应用类型与业务问题：

1. **企业内部业务应用/部⻔级应用**：审批工作流、入职流程、内容管理、工单队列、请求处理、预算管理、资产追踪 ——多用于替换 [InfoWorld][ref-09] Excel、邮件、Access 等"临时拼凑"的流程。
2. **表单与审批流、工作流自动化**：最常⻅用例，拖拽映射审批、路由数据、减少人工错误（发票、HR、采购）。 [Agilepoint][ref-10]
3. **遗留系统现代化与集成**：在老旧数据库之上叠加现代 UI、API 与工作流；如 PostNL 用 Mendix 重建核心订单管理系 统（微服务架构，日处理超100万包裹，99.95%可用性，两年积压需求六个月清空）。
4. **客户参与/CRM类应用**：Salesforce、Creatio、Pega 等围绕 CRM/客户流程扩展。
5. **⻔户与 Web 应用、移动应用**：多端（PC/移动）一键发布。
6. **数据可视化与报表仪表盘（CADP场景）**：Gartner 的"公⺠自动化与开发平台"典型用例。 [theregister][ref-11]
7. **公⺠开发者（Citizen Developer）场景**：赋能非 IT 业务人员；据 SegmentFault/JEECG《2021盘点：国内外10大 低代码开发平台》，"过去3年，阿里巴巴集团通过低代码开发平台，构建了12700个应用，其中绝大部分是由HR、财 务等不具备开发经验的岗位员工搭建"。
8. **行业垂直应用**：金融/保险（Unqork 面向银行、保险、资产管理，约50%业务来自该领域）、政府（纽约市72小时内 用无代码搭建疫情追踪⻔户）、医疗、制造（Siemens/Mendix [Sacra][ref-12] [Alpha Software][ref-13] 面向工业 IoT、数字孪生）、零售、教育。
9. **疫情期间快速交付**：美国国务院用 ServiceNow 数周内部署近十个关键应用；纽约、华盛顿等政府用低代码快速搭 建疫情⻔户；这被 [Alpha Software][ref-14] Gartner 称为"新冠疫情的经济后果验证了低代码的价值主张"。 [Computer Weekly][ref-15]

**总结分析（第二部分）**：应用领域的边界由**底层技术路线**直接圈定——流程型平台（Appian、Pega）天然适配审批 流与复杂案件管理；数据库/表单型平台（Quickbase、简道云、氚云）适配数据管理与轻量业务应用；通用型平台 （Mendix、OutSystems、Power Apps）覆盖从"电子表格替代"到"核心系统现代化"的宽谱。艾瑞数据揭示了一条 清晰的**复杂度梯度**：低代码可覆盖中小企业约95%的应用场景，中大型企业约70%，而音视频、即时通信等垂直深 水区仅约50%。2021年最强的需求驱动力是**疫情催化的数字化加速**——远程办公所需的数字表单与流程自动化成 为"保持业务运转"的刚需，使低代码从"锦上添花"变为"雪中送炭"。 [The Paper][ref-16]

### 第三部分 主流平台与工具

**国际厂商（按 Gartner 2021 LCAP 魔力象限 + Forrester 2021 定位）**

*领导者/企业级通用型*：

- **Mendix**（⻄⻔子子公司）：象限排名最高、远⻅维度最远，支持多云/本地、融合团队、IoT/数字孪生，面向大中型 企业。 [Kissflow][ref-17]
- **Microsoft Power Apps/Power Platform**：内含 Dataverse + Power Automate， [Microsoft][ref-18] 用户基数最大，AI 驱动开发，深度绑定 Microsoft 365/Azure；据微软，财富500强中92%每月使用 Power Apps。
- **OutSystems**：面向专业开发者，AI 增强、原生 CI/CD、企业级敏捷规划， [Scribd][ref-19] 擅⻓核心系统现代化，可生成可扫描代码。
- **ServiceNow**（App Engine/Creator Workflows）：基于 Now Platform， [q4cdn][ref-20] 流程自动化⻅⻓，连续两年领导者。
- **Salesforce**（Lightning Platform）：十余个行业云均用 LCAP 扩展，生态与市场庞大。

*流程驱动型（Gartner挑战者）*：

- **Appian**：全栈低代码自动化，专注复杂案件管理与业务流程（BPM），2021年从领导者降为挑战者。 [BPI][ref-21]
- **Pega**（Pega Infinity）：iBPMS + MXDP + RPA + CRM，云原生多租户微服务。
- **Oracle APEX**：内嵌 Oracle 数据库，入⻔成本低（含免费选项），数据库能力强。

*利基/公⺠开发者/数据库型*：

- **Creatio**：无代码 + 流程自动化 + CRM。 [Creatio][ref-22]
- **Quickbase**：无代码运营敏捷平台，治理与安全⻅⻓（Forrester [Quickbase][ref-23] [Quickbase][ref-23] Q4 2021业务开发者领导者，安全与治理获最高分之一）。
- **Kintone**（日本）、**Newgen**（复杂流程自动化）。
- **Google AppSheet**（Forrester Q4 2021领导者）、**Betty Blocks**（微服务架构、公⺠开发）、**Zoho [Solutions Review][ref-24] Creator**、**Airtable**（2021年12月完成7.35亿美元 F 轮融资，估值110亿美元，由 XN 领投，Salesforce Ventures 与 Michael Dell 的 MSD Capital 参投）、**Unqork**（无代码、金融保险、Forrester"年度新秀"）、**Bubble**、**Retool**（内 部工具）。

**中国厂商**

- **阿里/钉钉宜搭**：2019年3月上线，拖拽配置、一键发布 PC/移动端； [Juejin][ref-25] 背靠阿里云，2021年钉钉6.0发布会再度点燃低代码市场。
- **腾讯微搭**、**百度爱速搭**、**华为 AppCube（应用魔方）**：云厂商入场代表。
- **氚云（奥哲）**、**简道云（帆软）**：中国最早一批零代码/表单驱动平台（2015年前后），主打表单、流程、数据管理与可 视化，被视为无代码赛道明星。
- **明道云**、**iVX**、**织信 Informat**、**轻流**、**得帆（DefinePaaS）**（组件化+元数据驱动，多次入选 Gartner/IDC）、**炎⻩ 盈动 [CSDN][ref-06] AWS PaaS**（流程驱动+BPMN 2.0+iPaaS）、**葡萄城活字格**（模型驱动）、 [SegmentFault][ref-26] **用友 YonBuilder**、**金蝶**、**ClickPaaS**。

**总结分析（第三部分）**：平台定位可用两个维度切分。其一是**目标用户**：专业开发者（OutSystems、Mendix、 WaveMaker）vs. 公⺠开发者/业务人员（Quickbase、AppSheet、Betty Blocks、简道云、氚云）——Forrester 正是据此在2021年拆分为"专业开发者"（Q2）与"业务开发者"（Q4）两份 Wave。其二是**技术路线**：通用型 （Mendix、Power Apps）、流程型（Appian、Pega、炎⻩盈动）、数据库/表单型（Quickbase、Airtable、简道 云）。技术路线直接映射目标客户与场景——流程型厂商多来自 BPM 血统、主攻金融政府大客户的复杂流程；表单/ 数据库型主攻中小企业与部⻔级应用。2021年三大结构性趋势：**（1）云厂商入场**——微软、谷歌、阿里、腾讯、百 度、华为全面下场，凭生态与云资源改变格局；**（2）大厂并购整合**——⻄⻔子2018年以7.3亿美元收购 [NetEase][ref-27] Mendix、2021年4月再收购其合作伙伴 TimeSeries（面向垂直行业 app），ServiceNow 2021年3月收购印度 RPA 厂商 Intellibot，Forrester 称"六强正从数十家厂商中脱颖而出"；**（3）资本追捧头部**——Unqork（2020年 [forrester][ref-28] C 轮 2.07亿美元，估值达20亿美元，投资方含 BlackRock、Goldman Sachs、CapitalG）、Airtable（2021年12月 估值110亿美元）等估值飙升。

### 第四部分 公认的业务优势与局限

**公认优势**

1. **开发提速、缩短上市时间**：抽象并自动化整个 SDLC，Unqork [Mendix][ref-29] 案例显示可比传统开发提前数月交付。 [Unqork][ref-30]
2. **降低开发成本**。
3. **缓解专业开发人才短缺**：全球专业开发者供给不足，低代码是直接对策。 [Mendix][ref-31]
4. **赋能业务人员（公⺠开发）**：Gartner 称平均41%的非 IT 员工（业务技术人员）在定制或构建数据/技术方案；预测 到2025年一半新低代码客户来自 IT 部⻔之外，到2026年 IT 部⻔之外的开发者将占低代码工具用户的至少 80%（2021年为60%）。
5. **促进业务与 IT 协作（融合团队 fusion teams）**：可视化模型成为业务与 IT 的"共同语言"。Forrester [Mendix][ref-32] 一项开发经理调查中，39%受访者称其组织采用低代码的目标是赋能 IT 之外的员工交付应用。
6. **提高一致性与可维护性**：可视化环境强制一定质量标准，标准化代码结构便于维护。 [ShiftAsia][ref-33] [Mendix][ref-32]
7. **快速迭代与敏捷响应**：疫情期间的快速交付验证。
8. **统一治理、降低影子 IT ⻛险**：如 Quickbase 强调访问控制、可配置策略、应用组合监控。 [businesswire][ref-34]

**公认局限与批评**

1. **厂商锁定（Vendor Lock-in）**：专有架构使迁移、扩展、复用困难； [Emergent Mind][ref-01] 无源码访问意味着实现无法脱离平台使用。 [ScienceDirect][ref-35]
2. **可扩展性与性能瓶颈**：难以承载大规模、高并发、高性能关键系统；抽象层引入额外开销。 [ShiftAsia][ref-33]
3. **定制化能力受限**：高度定制的 UI 或复杂算法/深度集成可能超出平台能力。 [LogRocket][ref-36]
4. **治理与安全挑战**：受监管行业中平台级安全可能不满足合规要求； [LogRocket][ref-36] 第三方服务依赖引入漏洞⻛险。
5. **技术债务**：快速开发可能积累低效设计与捷径。 [Pointury][ref-37]
6. **集成挑战**：预定义集成点未必契合既有基础设施，自定义集成又需公⺠开发者不具备的技术能力。 [Baytech Consulting][ref-38]

**总结分析（第四部分）**：优势与局限是同一枚硬币的两面，均源自"抽象"这一核心技术特性。**抽象带来的红利**——提 速、降本、赋能业务、一致性——正是把底层技术细节隐藏后的直接产物；而**抽象带来的代价**——厂商锁定、性能天 花板、定制受限——则是隐藏细节后失去的控制力。因此2021年业界形成的务实共识是：低代码不是替代传统编 码，而是**互补**——推荐"混合开发"策略（低代码 + 自定义微服务）、建立健全治理体系、采用厂商中立 API 以降低锁 定。从趋势看，低代码正与 Gartner 三大主题融合——**超自动化（hyperautomation）**、**可组合企业 （composable business）**、**⺠主化（democratization）**——这三者恰好分别对应流程/RPA 集成、微服务/API 组 件化、公⺠开发三条技术与业务主线，构成2021年低代码叙事的完整闭环。

## Recommendations

**分阶段落地建议：**

1. **试点阶段（0–3个月）**：选择部⻔级、低复杂度、高频手工流程（审批流、数据收集、报表）作为首个用例。中小企 业可直接选表单/数据库型（简道云、氚云、Quickbase）；已在特定生态中的企业优先选原生平台（微软生态选 Power Apps，Salesforce 生态选 Lightning，钉钉生态选宜搭）。**阈值**：若单个应用需求超过平台声明式能力的边界 （需大量自定义代码/复杂算法），应回退到专业开发或通用型平台。
2. **扩展阶段（3–12个月）**：建立融合团队与治理框架（访问控制、应用组合监控、安全扫描），复杂流程/案件管理选流 程型（Appian、Pega、炎⻩盈动），核心系统现代化选可生成标准代码的通用型（OutSystems、Mendix）。**阈值**： 当应用进入高并发、任务关键、强合规场景时，须评估性能压测与合规认证（如中国等保三级）。
3. **规模化阶段（12个月以上）**：以厂商中立 API 与微服务架构缓解锁定⻛险， [Ijetcsit][ref-39] 制定退出策略（源码导出能力是关键采购指标），将低代码纳入 DevOps/CI-CD 管线与超自动化战略。

**改变建议的基准/阈值**：若目标是"赋能 IT 之外的业务人员交付应用"（Forrester 调查中39%受访开发经理的首要目 标），优先业务开发者型平台；若目标是替代重型 [Quickbase][ref-23] BPM 套件，优先流程型；若需承载对外客户级、高性能应用，则应审慎评估低代码适用性并保留高代码退路。

## Caveats

- **市场规模数据的口径差异**：Gartner 138亿美元为"低代码开发技术"总市场（含 LCAP 约57.5亿、iBPMS 约28.9亿、 MXDP 约23.3亿、RPA 约21.9亿、CADP 约5.8亿美元等多个细分），并非仅指狭义低代码平台；引用时须注意口径。 同一 Gartner 新闻稿的 meta 描述曾出现"113亿美元/增⻓23.2%"的早期数字，正文最终定稿为"138亿美元/增⻓ 22.6%"，本报告采用正文定稿值。
- **中国市场数据**来自艾瑞咨询，2020年15.9亿元、2021年27.5亿元为该机构口径，与国际数据不可直接横向相加。
- **Unqork 估值时点**：20亿美元估值来自其2020年10月宣布的2.07亿美元 C 轮融资，而非2021年；2021年 Unqork 在 Forrester Q2 报告中被评为竞争者兼"年度新秀"，并被媒体估算当年营收约1.3亿美元。
- **魔力象限/Wave 的时点性**：厂商象限位置逐年变动（如 Appian、Pega 在2021年被降级），本报告严格锁定2021年 版本；请勿与后续年份混用。Gartner/Forrester 明确声明其研究不构成对特定厂商的背书。 [Microsoft][ref-40]
- **厂商自述来源**：部分平台能力描述来自厂商官网/新闻稿（Mendix、Quickbase、Appian、得帆等），可能含营销色 彩，已尽量与第三方（Gartner、Forrester、Solutions Review、TechTarget 等）交叉印证。
- **前瞻性预测**："2025年70%""2026年80%"等均为 Gartner 的预测（predict/forecast），非既成事实，本报告已标注 其预测属性。
- 本调研全程未使用亦未引用任何被限制的文献来源，相关技术论述改由 SoSyM 期刊论文（Di Ruscio 等著）、 Forrester、Gartner、厂商文档及中国技术社区（艾瑞、葡萄城、阿里云开发者社区、SegmentFault 等）等独立来 源支撑。

[ref-01]: <https://www.emergentmind.com/topics/low-code-development-platforms>
[ref-02]: <https://kissflow.com/low-code/visual-programming-overview/>
[ref-03]: <https://www.microsoft.com/en-us/power-platform/products/power-apps/topics/low-code-no-code/low-code-platform>
[ref-04]: <https://www.clickatell.com/articles/technology/about-low-code-development-platforms/>
[ref-05]: <https://developer.aliyun.com/article/1085168>
[ref-06]: <https://www.cnblogs.com/worktile/articles/18931683>
[ref-07]: <https://github.blog/news-insights/product-news/introducing-github-copilot-ai-pair-programmer/>
[ref-08]: <https://modeling-languages.com/low-code-vs-model-driven/>
[ref-09]: <https://www.infoworld.com/article/2338656/when-low-code-and-no-code-can-accelerate-app-modernization.html>
[ref-10]: <https://www.agilepoint.com/blog-post/low-code-application-examples>
[ref-11]: <https://www.theregister.com/2022/12/13/lowcode_tools_2023_rise/>
[ref-12]: <https://sacra.com/c/unqork/>
[ref-13]: <https://www.alphasoftware.com/blog/low-code-helps-battle-the-coronavirus-and-it-can-help-your-enterprise-as-well>
[ref-14]: <https://www.alphasoftware.com/how-to-create-a-government-app-with-low-code>
[ref-15]: <https://www.computerweekly.com/news/252496408/Covid-19-drives-growth-in-low-code-development-tools>
[ref-16]: <https://m.thepaper.cn/baijiahao_11837622>
[ref-17]: <https://kissflow.com/low-code/gartner-magic-quadrant-for-enterprise-low-code/>
[ref-18]: <https://www.microsoft.com/en-us/power-platform/blog/power-apps/microsoft-is-a-leader-in-the-forrester-wave-low-code-development-platforms-q2-2021/>
[ref-19]: <https://www.scribd.com/document/563406544/Gartner-Magic-Quadrant-Enterprise-Low-code-Application-Platforms-2021>
[ref-20]: <https://s205.q4cdn.com/537566246/files/doc_news/ServiceNow-Named-a-Leader-in-the-2021-Gartner-Magic-Quadrant-for-Enterprise-Low-Code-Application-Platforms-for-Second-Consecutive-Yea-LR2A4.pdf>
[ref-21]: <https://www.businessprocessincubator.com/content/key-takeaways-2021-gartner-magic-quadrant-for-enterprise-low-code-application-platforms/>
[ref-22]: <https://www.creatio.com/company/news/20377>
[ref-23]: <https://www.quickbase.com/about-us/media/quickbase-named-a-leader-in-low-code-platforms-for-business-developers-analyst-report>
[ref-24]: <https://solutionsreview.com/business-process-management/key-takeaways-forrester-wave-for-low-code-platforms-for-business-developers-q4-2021/>
[ref-25]: <https://juejin.cn/post/7106390799637561381>
[ref-26]: <https://segmentfault.com/a/1190000046722671>
[ref-27]: <https://www.163.com/dy/article/H1CTPI5905383QFT.html>
[ref-28]: <https://www.forrester.com/blogs/siemens-snaps-up-mendix-low-code-platforms-enter-new-phase/>
[ref-29]: <https://www.mendix.com/low-code-guide/>
[ref-30]: <https://unqork.com/resource-center/blogs/calculating-the-business-value-of-no-code-applications/>
[ref-31]: <https://www.mendix.com/press/pandemic-drove-dramatically-accelerated-digitalization-in-2020/>
[ref-32]: <https://www.mendix.com/blog/low-code-principle-1-model-driven-development/>
[ref-33]: <https://shiftasia.com/column/dead-or-transformed-the-future-of-low-code-development-platforms-in-an-ai-driven-world/>
[ref-34]: <https://www.businesswire.com/news/home/20211110005847/en/Quickbase-Named-a-Leader-in-Low-Code-Platforms-for-Business-Developers-Analyst-Report>
[ref-35]: <https://www.sciencedirect.com/science/article/pii/S0164121226001263>
[ref-36]: <https://blog.logrocket.com/low-code-decision-guide/>
[ref-37]: <https://www.pointury.com/publications/low-code>
[ref-38]: <https://www.baytechconsulting.com/blog/why-most-low-code-platforms-eventually-face-limitations-and-strategic-considerations-for-the-future>
[ref-39]: <https://www.ijetcsit.org/index.php/ijetcsit/article/download/368/319>
[ref-40]: <https://www.microsoft.com/en-us/power-platform/blog/power-apps/microsoft-is-a-leader-in-the-2021-gartner-magic-quadrant-for-enterprise-low-code-application-platforms/>
