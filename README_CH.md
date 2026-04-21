<p align="center">
  <img src="docs/assets/logo.png" alt="OneResearchClaw Header" width="95%">
</p>

<h2 align="center"><b>Start Any Research in One Claw. 🦞</b></h2>

<p align="center">
  <strong>From real materials to reports with a fully autonomous & skill-driven researcher.</strong>
</p>

---

<p align="center">
  <img src="docs/assets/framework-v6.png" alt="OneResearchClaw Framework" width="100%">
</p>

OneResearchClaw 是一套面向真实工作流的 **多格式输入 → 研究报告生成流水线**。  
它支持从会议音频/视频、文档、表格、PPT、ZIP 混合包，以及 arXiv / YouTube / Bilibili 链接出发，逐步完成内容整理、文献 research、质量 review、技能演化与多格式导出。

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="https://github.com/gaotiexinqu/OneResearchClaw"><img src="https://img.shields.io/badge/GitHub-OneResearchClaw-181717?logo=github" alt="GitHub"></a>
  <a href="https://github.com/gaotiexinqu/OneResearchClaw#-citation"><img src="https://img.shields.io/badge/Cite-OneResearchClaw-orange?logo=readme&logoColor=white" alt="Citation"></a>
  <a href="https://github.com/gaotiexinqu/OneResearchClaw#-star-history"><img src="https://img.shields.io/badge/Star_History-⭐-blue?logo=github" alt="⭐ Star History"></a>
</p>

<p align="center">
  <a href="./README.md"><b>🌐 English README</b></a> ·
  <a href="https://weiyang209.github.io/OneResearchClaw/index_zh.html"><b>🖥️ Project Page</b></a> ·
  <a href="#-showcase"><b>🎬 Showcase</b></a> ·
  <a href="#-快速开始"><b>🚀 Quick Start</b></a> ·
  <a href="#-skills-catalog"><b>🧩 Skills Catalog</b></a>
</p>

<p align="center">
  <a href="./docs/assets/wechat.jpg"><b>💬 WeChat</b></a> ·
  <a href="./docs/assets/rednote.jpg"><b>📕 RedNote</b></a> ·
  <a href="https://discord.gg/D53kdpX9"><b>🤖 Discord</b></a>
</p>

---

## 🎬 Showcase

<table>
  <tr>
    <td width="180" align="center">
      <img src="docs/assets/showcase-cover.png" alt="OneResearchClaw Showcase" width="140">
    </td>
    <td>
      <h3>生成报告展示</h3>
      <p>
        5 个具有代表性的案例，覆盖会议、文档、混合归档包、链接输入与审阅工作流 —— 
        展示了<b>多主题拆分</b>、<b>可控研究深度</b>、
        <b>Review-Rewrite 质量提升</b>以及<b>多格式交付</b>。
      </p>
      <p>
        <a href="docs/showcase/SHOWCASE_ZH.md"><img alt="View Full Showcase" src="https://img.shields.io/badge/View%20Full%20Showcase-%E2%86%92-3b82f6?style=for-the-badge"></a>
        <a href="docs/showcase/SHOWCASE_ZH.md#case-overview"><img alt="All Cases" src="https://img.shields.io/badge/All%205%20Cases-ef4444?style=for-the-badge"></a>
      </p>
    </td>
  </tr>
</table>

---
## 🔥 News


- **[2026/04/21] Skill-Evolve 正式上线**：现在支持基于用户反馈持续演化 skills 集，沉淀个性化偏好并保存为可指定的派生版本，让自动化流水线越用越懂你。

- **[2026/04/20] 云端链接一键接入**：无论是 arXiv 论文、YouTube 视频还是 Bilibili 内容，只需粘贴链接，系统自动下载到本地并启动研究流程，零门槛开启探索。

- **[2026/04/19]多模型 Review机制**：Review → Rewrite 闭环设计，支持有限轮迭代修订，显著提升报告交付质量。

- **[2026/04/17] 可控 Research 深度**：simple / medium / complex 三档可选，快速摸底还是深度调研，由你一手把控，资源消耗清晰可见。

- **[2026/04/16] 多 Topic 并行执行**：自动识别会议中的多个主题并独立生成报告，一场组会的讨论再密集，也能被完整、结构化地保留下来。

- **[2026/04/13] OneResearchClaw 发布**：从会议录音到 PDF，从表格到 ZIP ，材料散落在各处、格式各异，你需要手动串联提取关键词、做调研、写总结：整个Workflow 需要人工来衔接来各个环节。 OneResearchClaw 解决了这个问题：输入任意格式的文件，自动完成结构化、关键词提取、深度调研和内容总结，多格式报告直接导出。报告现在一键可达，无需人工干预。

---

## ✨ 核心亮点

| 核心能力 | 说明 |
|---|---|
| 🧭 **多输入源统一接入** | 支持从会议录音到 PDF、从表格到 ZIP 的多类型材料输入。系统会自动识别材料类型，并路由到对应的 grounding skill，减少手动整理、转换和预处理成本。 |
| 🧠 **多 Topic 会议拆分** | 对长会议、复杂讨论或多议题材料，系统可以自动拆分出多个 topic，并分别生成独立的研究分支。每个 topic 都可以单独完成 grounding、research、summary 和 export，适合从一场复杂会议中产出多个聚焦 report。 |
| 🎚️ **可控 Research 深度** | 支持 `simple / medium / complex` 三档 research 模式，用于控制文献搜索、资料打开、证据整理和报告分析深度。既可以快速生成 briefing，也可以产出更完整的研究报告。 |
| 🔎 **Query 确认与定向检索** | 在正式检索前，系统会先基于 grounded note 生成候选 query，并支持用户确认、增删或修改。这样可以让文献搜索更贴合用户真正需要的调研方向，减少无关检索和 token 浪费。 |
| 🧪 **多模型 Review 机制** | 报告生成后进入 review → rewrite 闭环，可通过不同模型或审查视角检查内容完整性、证据一致性、逻辑连贯性和过度推断问题，再对报告进行有限轮修订。 |
| ☁️ **云端链接一键接入** | 支持对云端链接材料进行接入与处理，例如 arXiv、YouTube、Bilibili 等来源，让线上材料可以直接进入同一套研究流水线。 |
| 📦 **多格式导出** | 支持将最终结果导出为 `md / docx / pdf / pptx / audio`，覆盖阅读、归档、汇报和复用等不同交付场景，并支持中文 / 英文导出。 |
| 🧬 **Skill-Evolve 技能演化** | 支持基于用户反馈演化 skill 子集，通过反馈收集、补丁生成、回归检查和版本提升，让系统能力可以持续迭代，而不是固定在一次性的手写流程中。 |

---

## 🎯 典型使用场景

- 🎙️ 将会议录音 / 视频整理为分主题报告
- 📄 将论文、文档、表格、PPT 等已有材料整合成统一研究报告
- 🗂️ 将 ZIP 混合材料包自动拆解并汇总为综合报告
- 🔗 从 arXiv / YouTube / Bilibili 链接启动内容获取与分析
- 📚 在 grounded 内容基础上补充文献检索与相关工作梳理
- 🧪 通过 review loop 提升报告质量
- 🧬 通过 skill-evolve 将个性化偏好沉淀为新的 skill 子集
- 📦 将结果导出为 Markdown / DOCX / PDF / PPTX / Audio

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone <your-repo-url>
cd OneResearchClaw
```

### 2. 安装依赖

```bash
pip install -e .
```

如需安装可选能力，可按模块启用：

```bash
pip install -e ".[audio]"
pip install -e ".[document]"
pip install -e ".[export]"
pip install -e ".[table]"
pip install -e ".[api]"
pip install -e ".[full]"
```

### 3. 在 Cursor 中运行

从入口 skill 开始使用，例如读取：

```text
.cursor/skills/one-report/SKILL.md
```

一个最小示例可以是：

```text
Please use the existing `.cursor/skills/one-report/` skill to generate a full report from one input file.

First read:
- `.cursor/skills/one-report/SKILL.md`

Input:
- input_path: docs/showcase/inputs/case5/HER2-case5.zip
- output_formats: pdf
- research_mode: complex

Search settings:
- search_backend: cursor
- require_open_link: true
- download_opened_literature: true

Optional:
- output_lang: zh
- transcription_language: zh
```

<details>
<summary><b>📂 展开查看：Case 5 完整执行链路与关键中间产物</b></summary>


下面以 Showcase 中的 **Case 5 · 综合材料 → 双语最终交付** 为例，展示一次 `one-report` pipeline 从 ZIP 混合材料输入到最终 PDF 的主要阶段。  
为了方便复核，关键中间产物已放在 `docs/showcase/reports/readme_case/` 目录下。下面提到的文件名都可以点击跳转查看。

---

### Case 配置

| 配置项             | 当前值                                      |
| ------------------ | ------------------------------------------- |
| 输入材料           | `docs/showcase/inputs/case5/HER2-case5.zip` |
| 输入类型           | ZIP mixed-material package                  |
| Research 模式      | `complex`                                   |
| Search backend     | `cursor`                                    |
| 是否要求打开来源   | `require_open_link: true`                   |
| 是否下载已打开文献 | `download_opened_literature: true`          |
| 输出语言           | `zh`                                        |
| 输出格式           | `pdf`                                       |
| Showcase ground id | `archive-HER2-case5_20260415130231`         |

---

### 1. Input Routing：识别输入类型

`one-report` 首先读取 `input_path`，判断输入是 ZIP 混合材料包，然后将任务路由到 archive grounding 流程。

这一阶段会解压材料包、枚举内部文件，并记录每个文件被分发到哪个 grounding skill。  
可以查看 [`manifest.json`](docs/showcase/reports/readme_case/grounded_notes/archive-HER2-case5_20260415130231/manifest.json) 和 [`routed_items.json`](docs/showcase/reports/readme_case/grounded_notes/archive-HER2-case5_20260415130231/routed_items.json) 了解输入材料如何被识别和路由。

---

### 2. Grounding：混合材料结构化

Grounding 阶段会把 ZIP 内部的不同材料转换为后续 `research`、`summary` 和 `review` 阶段可使用的结构化内容。

其中最重要的产物是 [`grounded.md`](docs/showcase/reports/readme_case/grounded_notes/archive-HER2-case5_20260415130231/grounded.md)。  
它汇总了输入材料的主题、关键信息、可研究问题和后续报告生成需要的上下文。

如果想进一步查看 ZIP 内每个子文件的处理结果，可以打开 [`child_outputs/`](docs/showcase/reports/readme_case/grounded_notes/archive-HER2-case5_20260415130231/child_outputs/) 目录。  
README 展示里不需要逐个展开这些 child outputs；它们主要用于说明混合材料包中的不同文件确实被分别 grounding，再汇总到主 `grounded.md`。

> **Tip：Pipeline 行为可以通过入口参数控制。**  
> 在 `one-report` prompt 中添加 `key: value`，即可控制输入、research 深度、检索方式、review 方式和最终导出格式。

---

### 3. Query Generation：生成并确认检索 Query

Research 阶段不会直接开始搜索，而是先基于 `grounded.md` 生成候选 query。  
用户可以在正式检索前确认、增删或修改 query，从而减少无关检索和 token 浪费。

这一阶段可以重点查看两个文件：

- [`queries.json`](docs/showcase/reports/readme_case/lit_inputs/archive-HER2-case5_20260415130231/queries.json)：系统基于 grounded note 生成的候选 query；
- [`queries_confirmed.json`](docs/showcase/reports/readme_case/lit_inputs/archive-HER2-case5_20260415130231/queries_confirmed.json)：确认后真正进入检索阶段的 query。

这一步体现的是 OneResearchClaw 的 **定向 research** 能力：先校准搜索方向，再消耗检索、打开来源和阅读成本。

---

### 4. Literature Research：检索、打开来源与整理证据

在 `complex` research mode 下，系统会执行更深入的文献调研。  
由于当前设置了：

```text
require_open_link: true
download_opened_literature: true
```

因此系统不会只依赖搜索摘要，而是会尽量打开来源、保存证据，并下载已打开文献用于后续复核。

这一阶段可以查看：

- [`search_results.json`](docs/showcase/reports/readme_case/lit_inputs/archive-HER2-case5_20260415130231/search_results.json)：记录检索结果；
- [`opened_sources/`](docs/showcase/reports/readme_case/lit_inputs/archive-HER2-case5_20260415130231/opened_sources/)：保存实际打开过的来源内容；
- [`opened_paper_notes.jsonl`](docs/showcase/reports/readme_case/lit_inputs/archive-HER2-case5_20260415130231/opened_paper_notes.jsonl)：汇总 paper-level notes；
- [`lit_initial.md`](docs/showcase/reports/readme_case/lit_inputs/archive-HER2-case5_20260415130231/lit_initial.md)：初步文献调研结果；
- [`manifest.json`](docs/showcase/reports/readme_case/lit_downloads/archive-HER2-case5_20260415130231/manifest.json)：文献下载记录与下载状态。

最终，research 阶段会生成 [`lit.md`](docs/showcase/reports/readme_case/lit_results/archive-HER2-case5_20260415130231/lit.md)。  
这是后续 summary 阶段最重要的外部文献依据，包含 query、打开来源、paper notes 和调研结论的综合结果。

---

### 5. Summary：整合 grounded note 与 literature result

Summary 阶段会读取 [`grounded.md`](docs/showcase/reports/readme_case/grounded_notes/archive-HER2-case5_20260415130231/grounded.md) 和 [`lit.md`](docs/showcase/reports/readme_case/lit_results/archive-HER2-case5_20260415130231/lit.md)，并生成初版报告。

这一阶段的目标不是把材料压缩成几条摘要，而是把原始材料和文献调研结果整合为结构化 research report。  
对应产物可以查看 [`summary.md`](docs/showcase/reports/readme_case/report_inputs/archive-HER2-case5_20260415130231/summary.md)。

---

### 6. Review → Rewrite：质量检查与有限轮修订

初版报告生成后，可以进入 review → rewrite loop。  
Reviewer 会检查 topic alignment、coverage、evidence specificity、analytical depth、structure coherence 和 deliverability；Writer 根据 reviewer 的 repair actions 对报告进行修订。

这一阶段可以查看：

- [`review_history.json`](docs/showcase/reports/readme_case/review_outputs/archive-HER2-case5_20260415130231/review_history.json)：记录多轮 review / rewrite 历史；
- [`review_report.md`](docs/showcase/reports/readme_case/review_outputs/archive-HER2-case5_20260415130231/review_report.md)：最终 review 报告；
- [`review_state.json`](docs/showcase/reports/readme_case/review_outputs/archive-HER2-case5_20260415130231/review_state.json)：最终 review 状态；
- [`round_0/`](docs/showcase/reports/readme_case/review_outputs/archive-HER2-case5_20260415130231/round_0/)、[`round_1/`](docs/showcase/reports/readme_case/review_outputs/archive-HER2-case5_20260415130231/round_1/)、[`round_2/`](docs/showcase/reports/readme_case/review_outputs/archive-HER2-case5_20260415130231/round_2/)：每一轮 review 的详细记录。

当 review 达到通过条件后，系统会生成最终报告 [`research_report.md`](docs/showcase/reports/readme_case/reports/archive-HER2-case5_20260415130231/research_report.md)。  
后续所有导出格式都会基于这份 review 后的最终报告，而不是基于初版 summary。

---

### 7. Export：导出最终 PDF

Export 阶段读取 [`research_report.md`](docs/showcase/reports/readme_case/reports/archive-HER2-case5_20260415130231/research_report.md)，并根据 `output_formats` 和 `output_lang` 导出对应格式。

当前示例配置为：

```text
output_formats: pdf
output_lang: zh
```

因此会生成中文 PDF 报告：[`zh/report.pdf`](docs/showcase/reports/readme_case/final_outputs/archive-HER2-case5_20260415130231/zh/report.pdf)。  
Showcase 中也保留了英文版本：[`en/report.pdf`](docs/showcase/reports/readme_case/final_outputs/archive-HER2-case5_20260415130231/en/report.pdf)。

</details>



> **Tip：Pipeline 行为可以通过入口参数控制。**  
> 在 `one-report` prompt 中添加 `key: value`，即可控制输入、research 深度、检索方式、review 方式和最终导出格式。
>
> | Parameter | Default | What it does |
> |---|---|---|
> | `input_path` | 必填 | 输入材料路径。支持本地文件、ZIP 混合材料包，以及云端链接下载后的本地路径。 |
> | `output_formats` | 必填 | 最终导出格式，支持 `md / docx / pdf / pptx / audio`，可用逗号组合，例如 `md,pdf,pptx`。 |
> | `research_mode` | `medium` | 控制 research 深度，支持 `simple / medium / complex`。这是影响文献打开数量、检索覆盖和 token 成本的核心参数。 |
> | `research_requirements` | — | 额外调研要求，例如强调技术贡献、工程风险、benchmark、局限性或应用场景。 |
> | `search_backend` | `cursor` | 文献检索后端，支持 `cursor / external / auto`。 |
> | `require_open_link` | `true` | 是否要求打开并读取来源，而不是只依赖搜索结果摘要。 |
> | `download_opened_literature` | `true` | 是否下载已打开文献，便于后续复核和 refine paper notes。 |
> | `transcription_language` | `en` | 音频 / 视频输入的转写语言提示，只影响 ASR 阶段。 |
> | `output_lang` | `en` | 最终报告语言，例如 `zh` 表示导出中文报告。 |
> | `reviewer_api_config` | 未启用 | 可选外部 reviewer 配置。提供后，review → rewrite loop 的每一轮都会使用指定外部模型作为 reviewer。 |
>
> `research_mode` 会自动映射到 `config/research_pipeline.env` 中的 runtime 参数。  
> 下表是当前默认 preset，用于控制文献目标范围、最低打开文献数和近期文献要求；这些数值不是固定规则，可以根据具体任务需求在 config 中调整。
>
> | Mode | 文献目标范围 | `MIN_OPENED_PAPERS` | `OPEN_TOP_K` | `MIN_RECENT_PAPERS` |
> |---|---:|---:|---:|---:|
> | `simple` | 3–5 篇 | 3 | 2 | 2 |
> | `medium` | 6–10 篇 | 6 | 3 | 4 |
> | `complex` | 10–15 篇 | 10 | 5 | 6 |

---

## 🌟 核心能力

### 1. 🧭 多输入源统一接入

OneResearchClaw 可以从不同形态的本地材料中启动研究流程：会议录音、论文 PDF、实验表格、PPT 汇报材料，甚至包含多种文件的 ZIP 材料包，都可以进入同一条自动化 pipeline。

系统会自动识别输入类型，并路由到对应的 grounding skill，将原始材料转换为后续 research、summary、review 和 export 阶段可使用的结构化内容。

| 输入类别 | 支持格式 | 典型内容 |
|---|---|---|
| 音频 | `.mp3`, `.wav`, `.m4a` | 会议录音、访谈、语音记录 |
| 视频 | `.mp4`, `.mov`, `.mkv` | 会议视频、讲座录像、演示录屏 |
| 文档 | `.pdf`, `.docx`, `.md`, `.txt` | 论文、报告、笔记、说明文档 |
| 表格 | `.xlsx`, `.csv` | 数据表、实验结果、统计表格 |
| 演示文稿 | `.pptx` | 汇报材料、课程讲义、项目 deck |
| 压缩包 | `.zip` | 多文件混合材料包 |

---

### 2. 🧠 多 Topic 会议拆分

在真实研究与项目讨论中，一场会议往往包含多个相对独立的主题：例如不同论文方向、实验进展、问题排查、任务规划或后续行动项。  
如果所有内容都被合并到同一个上下文中，后续生成报告时容易出现主题边界不清、信息互相干扰、报告结构臃肿等问题。

OneResearchClaw 针对这类长会议与多议题讨论，支持自动识别会议中的多个 topic，并将每个 topic 拆分为独立的 `grounded unit`。  
每个 `grounded unit` 都保留对应主题的上下文、关键信息和证据边界，后续可以分别进入 research、summary、review 和 export 流程。

```text
Meeting Input
audio / video / transcript
        │
        ▼
Meeting Grounding
topic detection + segmentation
        │
        ▼
┌────────────┬────────────┬────────────┐
│ Topic A    │ Topic B    │ Topic C    │
└─────┬──────┴─────┬──────┴─────┬──────┘
      ▼            ▼            ▼
Grounded Unit  Grounded Unit  Grounded Unit
      │            │            │
      ▼            ▼            ▼
Report A      Report B      Report C
```

| 应用需求                | 处理方式                 |
| ------------------- | ------------------------------------- |
| 一场会议包含多个研究方向        | 自动识别 topic，并按主题拆分为多个 grounded unit    |
| 不同主题需要独立调研          | 每个 topic 可单独进入 research 阶段，生成对应文献调研结果 |
| 组会 / 访谈 / 讨论会需要多份输出 | 同一场会议可以按主题产出多个聚焦报告                    |

---

### 3. 🎚️ 可控 Research 深度

不同任务对调研深度的需求并不相同：  
有些场景只需要快速补充背景，有些场景需要覆盖核心相关工作，而复杂研究问题则需要更系统的文献映射。

OneResearchClaw 通过 `research_mode` 提供 `simple / medium / complex` 三档 research 深度。  
该参数会在运行前映射到 `config/research_pipeline.env` 中的 runtime 配置，从而影响后续的检索范围、来源打开数量、近期文献要求和调研成本。具体 preset 可在 Quick Start 的参数表中查看，也可以根据任务需求自行调整。

| Research Mode | 适用场景                                                     |
| ------------- | ------------------------------------------------------------ |
| `simple`      | 快速了解背景，补充少量核心相关工作，适合轻量 briefing 或初步探索。 |
| `medium`      | 平衡覆盖范围、成本和报告深度，适合作为默认 research 模式。   |
| `complex`     | 面向跨方向、复杂问题或需要系统性 literature mapping 的任务，适合生成更深入的研究报告。 |

在执行 research 时，系统会根据当前模式控制检索、来源打开、近期文献要求和 evidence 整理强度。  
对于 Cursor-native backend，只有真正被打开、读取并保存为本地证据的来源，才会计入有效 opened literature。这样可以避免只依赖 snippet-only 搜索结果生成调研报告。

如果开启文献下载，系统还会进一步下载已打开文献，并使用下载后的 PDF 内容 refine paper notes。  
因此最终的 `lit.md` 不只是搜索结果摘要，而是结合 query、打开来源、文献笔记和可复核材料形成的调研结果。

---

### 4. 🔎 Query 确认与定向检索

高质量 research 不只取决于搜索得多深，也取决于一开始搜索方向是否准确。  
在真实使用中，自动生成的 query 可能过宽、过窄，或者没有命中用户真正关心的文献类型。例如，用户可能更需要 benchmark paper、survey paper、method paper、system paper，或者某一类 failure mode / limitation 相关工作。

因此，OneResearchClaw 在正式执行文献检索前加入 query confirmation 步骤：系统会先基于 `grounded note` 生成候选 query，再支持用户确认、增删或修改。  
只有确认后的 query 才会进入后续 search、open source、paper notes 和 `lit.md` 生成流程。

这一机制的核心价值是：让用户在 research 成本真正发生前，就可以校准调研方向，把预算集中在真正需要的文献类型上。

| Query 类型           | 主要用途                                           |
| -------------------- | -------------------------------------------------- |
| `problem_queries`    | 补充问题背景、领域上下文、benchmark、任务定义。    |
| `method_queries`     | 检索方法、baseline、解决方案和相关技术路线。       |
| `constraint_queries` | 检索风险、约束、失败模式、数据质量问题和开放问题。 |

通过 query confirmation，用户可以更直接地指定自己需要的调研重点，例如：

```text
更关注近两年的方法论文
增加 benchmark / dataset 相关 query
减少泛泛的 survey query
补充 failure mode / limitation 方向
聚焦某个应用场景或模型架构
```

这可以带来两个直接收益：

- **减少无效检索**：避免生成的 query 偏离用户需求，减少无关 search result 和无用 source opening；
- **降低 token 与时间成本**：尤其在 `medium / complex` research 模式下，提前校准 query 可以显著减少后续无效阅读与整理。

确认后的 query 会作为后续 research stage 的执行依据。  
因此，OneResearchClaw 的文献调研是一个可以在检索前进行人工校准的定向 research 流程。

---

### 5. 🧪 多模型 Review 机制

自动生成的研究报告通常还需要进一步检查：  
材料是否覆盖完整、证据是否具体、分析是否足够深入、结论是否存在过度推断、最终内容是否适合交付。  
OneResearchClaw 在 summary 之后加入 `review → rewrite` 质量闭环，用于在导出前对报告进行结构化诊断和有限轮修订。

这一阶段会把报告作为可审查对象，结合 `grounded.md`、`lit.md`、`summary.md` 以及可选的 paper notes / download manifest，对报告进行基于证据的质量检查。

| Review 维度                         | 检查重点                                                     |
| ----------------------------------- | ------------------------------------------------------------ |
| `topic_alignment`                   | 报告是否保持与 grounded topic 和原始材料需求一致。           |
| `coverage_completeness`             | 是否覆盖 `lit.md` 中的重要主题、关键论文和主要问题。         |
| `evidence_specificity`              | 关键结论是否有 grounded note、literature result 或 opened evidence 支撑。 |
| `analytical_depth`                  | 是否解释问题为什么重要、证据支持到什么程度、仍有哪些不确定性。 |
| `structure_and_narrative_coherence` | 报告结构是否清晰，是否存在重复、跳跃或主题混杂。             |
| `deliverability`                    | 是否已经适合进入后续 `md / docx / pdf / pptx / audio` 导出阶段。 |

Review 阶段支持两类 reviewer：

| Reviewer 模式            | 说明                                                         |
| ------------------------ | ------------------------------------------------------------ |
| **Cursor 本地 reviewer** | 使用 `.cursor/agents/reviewer.md` 中定义的 reviewer subagent，对报告进行本地审查。 |
| **外部 reviewer API**    | 当提供 `reviewer_api_config` 时，可调用 OpenAI、Gemini 等外部模型作为 reviewer，并在每一轮 review 中保持同一个外部 reviewer 后端。 |

修订过程由独立 writer 角色完成。Reviewer 负责评分、诊断和给出 repair actions；Writer 负责根据 reviewer 指定的修订动作改写报告。  
这种角色拆分便于接入不同模型进行交叉审查，也让每轮修改都有明确的诊断来源和修订依据。

每一轮 review 都会被记录下来，便于复核报告是如何被修改和通过质量门控的，当得分>=90后，即可导出最终report：

```text
data/review_outputs/<ground_id>/
├── round_0/
│   ├── review_report.md
│   └── review_state.json
├── round_1/
│   ├── review_report.md
│   └── review_state.json
├── review_history.json
├── review_report.md
└── review_state.json

data/reports/<ground_id>/
└── research_report.md
```

---

### 6. ☁️ 云端链接一键接入

除了本地文件，OneResearchClaw 也支持从远程链接直接启动报告生成流程。  
当 `input_path` 是 URL 时，系统会先调用 `remote-input` skill，将远程材料下载或解析为本地文件，再交给 `input-router` 按文件类型进入后续 grounding pipeline。

这样，用户可以直接从 arXiv 论文、YouTube 视频或 Bilibili 视频开始，而不需要手动下载、改名、移动文件或重新指定下游处理流程。远程材料会先被标准化为本地输入，因此后续仍然复用同一套 `grounding → research → summary → review → export` 流程。

| 远程来源 | 支持形式 | 标准化结果 |
|---|---|---|
| 📄 **[arXiv](https://arxiv.org/)** | `arxiv.org/abs/...`、`arxiv.org/pdf/...` | 下载为 PDF 文件 |
| 🎬 **[YouTube](https://www.youtube.com/)** | `youtube.com/watch`、`youtu.be`、`youtube.com/shorts` | 下载为视频文件 |
| 🎬 **[Bilibili](https://www.bilibili.com/)** | `bilibili.com/video/BV...`、`av...`、`b23.tv/...` | 下载为视频文件 |

---

### 7. 📦 多格式导出

OneResearchClaw 支持将 review 后的最终报告导出为多种交付形态，覆盖编辑、归档、汇报和语音浏览等不同使用场景。  
导出阶段基于同一份最终报告生成不同格式，避免每种格式各自重新生成内容，从而保持版本一致性。

目前支持的导出格式包括：

```text
md / docx / pdf / pptx / audio
```

其中，`md` 适合继续编辑和版本管理，`docx` 适合正式文档交付和人工修改，`pdf` 适合稳定阅读与归档，`pptx` 适合汇报展示，`audio` 适合语音播报式交付。

同时，OneResearchClaw 支持通过 `output_lang` 控制最终交付语言：

```text
output_lang: zh
output_lang: en
```

也就是说，同一条 pipeline 可以根据需要导出中文或英文版本的最终报告

---

### 8. 🧬 Skill-Evolve

OneResearchClaw 的主流程负责生成报告，而 `Skill-Evolve` 负责让这套流程在使用过程中逐步贴合用户偏好。

在实际使用中，不同用户对报告风格、调研深度、结构组织、引用方式和导出偏好往往并不相同。  
如果每次都靠临时 prompt 说明偏好，这些修改很难沉淀下来，也容易在后续任务中丢失。`Skill-Evolve` 的目标就是把这类重复出现的反馈转化为可审查、可验证、可复用的 skill 修改建议。

它不会直接覆盖稳定的主 skill 集，而是先基于用户反馈生成 patch proposal，再经过验证后产出新的派生 skill 子集。这样既能保留原始流程的稳定性，也能让用户根据自己的使用习惯维护定制版本。

```text
user feedback → patch proposal → validation gate → derived skill set
```

`Skill-Evolve` 主要支持：

- 根据用户反馈分析当前 skill 的不足，例如报告不够深入、结构不符合偏好、review 维度需要调整、导出格式需要加强等；
- 生成面向具体 skill 的 patch proposal，而不是只给一段临时 prompt；
- 通过 regression / validation gate 检查修改是否会破坏原有流程；
- 产出可指定使用的派生 skill 子集，便于后续任务继续复用；
- 将个性化偏好沉淀到技能层，而不是停留在单次对话中。

---

## 🧩 Skills Catalog

下面列出当前仓库中的主要 skill 集，按功能分组展示。

| Skill | Description |
|---|---|
| `one-report` | 主入口 skill，组织完整的报告生成流水线 |
| `input-router` | 识别输入类型，并将任务路由到合适的 skill |
| `remote-input` | 处理 arXiv / YouTube / Bilibili 等远程链接输入 |
| `archive-grounding` | 处理 ZIP / archive 混合材料包，并聚合内部多种内容 |
| `document-grounding` | 处理 PDF / DOCX / Markdown / TXT 等文档输入 |
| `table-grounding` | 处理 XLSX / CSV 等表格输入 |
| `pptx-grounding` | 处理演示文稿输入 |
| `meeting-grounding` | 会议类 grounding 总入口 |
| `meeting-audio-grounding` | 音频会议 grounding |
| `meeting-video-grounding` | 视频会议 grounding |
| `audio_structuring` | 音频内容结构化、转写与分段相关能力 |
| `grounded-research-lit` | 基于 grounded note 执行 research、打开来源并生成 `lit.md` |
| `grounded-summary` | 整合 grounded 内容与 research evidence，生成综合报告 |
| `grounded-review` | 执行 review → rewrite loop，提升报告质量 |
| `report-export` | 导出 md / docx / pdf / pptx / audio 等最终格式 |
| `skill-evolve` | 基于用户反馈生成 patch proposal，并构建新的 skill 子集 |

---

## ⭐ Star History

<a href="https://www.star-history.com/?repos=gaotiexinqu%2FOneResearchClaw&type=date&legend=top-left">

 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=gaotiexinqu/OneResearchClaw&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=gaotiexinqu/OneResearchClaw&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=gaotiexinqu/OneResearchClaw&type=date&legend=top-left" />
 </picture>

</a>

---

## 🙏 Acknowledgements

OneResearchClaw 的灵感来源于多个优秀的开源项目以及基于技能的工作流实践，包括：

- [AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw)
- [Auto-claude-code-research-in-sleep](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)
- [A-Evolve](https://github.com/A-EVO-Lab/a-evolve)
- [awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)

我们感谢这些项目的作者和维护者与开源社区分享他们的成果。

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

## 📌 Citation

如果你觉得 OneResearchClaw 对你有帮助，欢迎引用我们的工作：

```bibtex
@misc{OneResearchClaw2026,
  author       = {Yang, Wei* and Zhao, Yiming* and Zeng, Yu* and Fang, Zhen* and Huang, Wenxuan and Zhang, Ziao and Shi, Kou and Miao, Qing and Zhao, Jiawei and Chen, Lin and Chen, Zehui and Bao, Xikun},
  title        = {OneResearchClaw: Fully Autonomous, Skill-Driven Research Synthesis from Heterogeneous Inputs},
  year         = {2026},
  organization = {GitHub},
  url          = {https://github.com/gaotiexinqu/OneResearchClaw},
}
```

<p align="center">
  <sub>Built with <a href="https://cursor.com/cn/get-started?cc_platform=google&cc_campaignid=23639215328&cc_adgroupid=194817004980&cc_adid=799754797082&cc_keyword=cursor&cc_matchtype=b&cc_device=c&cc_network=g&cc_placement=&cc_location=2702&cc_adposition=&gad_source=1&gad_campaignid=23639215328&gbraid=0AAAABAkdGgSYLK4tfnXaSFHBrYgrb-ttX">Cursor</a> by the OneResearchClaw Team</sub>
</p>
