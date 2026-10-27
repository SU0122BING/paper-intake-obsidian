# Paper Intake · Obsidian 文献阅读工作台 / Literature Reading Workbench

[简体中文](#chinese) | [English](#english)

<a id="chinese"></a>

## 简体中文

把一篇论文的 **PDF、AI 精读和个人阅读笔记** 放进同一个可持续使用的阅读流程。

将论文链接或 PDF 发给 AI，它调用 DeepPaperNote 精读，再把结果整理进 Obsidian：建立阅读主页、保留原图、关联原文、核对编号，并更新文献总目录和标签索引。

本项目是 **Agent Skill + 空白 Obsidian 工作台 + 本地文献助手**。精读能力来自独立项目 [DeepPaperNote](https://github.com/917Dhj/DeepPaperNote)；本项目负责组织与入库联动。

> 当前版本：0.1.0，供本地试用。以 macOS、Codex 和 Obsidian 桌面端为验证环境。Python helper 使用 POSIX 文件锁，暂不支持 Windows 原生 Python；Linux 尚未完成实际桌面验证。
>
> 本 README 提供中英文说明；工作台模板、插件界面和目录名称目前仍为中文。请保留示例中的实际路径，不要按英文释义重命名文件夹。

## 适合什么场景

- 每次读论文都要分别创建 PDF、AI 笔记和个人笔记，希望减少整理工作。
- 希望 AI 提供阅读参考，同时保留自己的理解、批注与质疑。
- 希望有一份持续更新的论文总列表，并按主题、方法等标签检索。
- 有时手动导入文件，希望下一次 AI 入库能识别现有记录并续接编号。

## 能完成什么

| 操作 | 执行者 | 结果 |
| --- | --- | --- |
| 把论文链接或 PDF 发给 AI，并要求精读入库 | paper-intake + DeepPaperNote | 精读、图片检查、正式保存及入库关联 |
| 手动将 PDF 放进 `10 文献/PDF` | Obsidian 文献助手，需启用 | 补建个人阅读主页、刷新目录；不调用 AI |
| 添加或修改阅读主页的 tags/status | Obsidian 文献助手 | 刷新论文标签和阅读状态 |
| 核对与补齐论文编号 | 执行 skill 的 agent | 同一论文的 PDF、主页和 AI 归档沿用编号 |
| Obsidian 关闭时刷新目录 | `intake.py refresh` | 更新已有阅读主页的关联区、目录与标签 |

**尚未实现**：EndNote 自动同步、后台无人值守精读、插件独立编号、跨设备自动同步。`intake.py` 是关联工具，不是“一条命令自动生成论文笔记”的模型程序。

## 工作台长什么样

```text
文献阅读工作台/
├── 00 收件箱/
│   └── 随手记.md
├── 10 文献/
│   ├── 文献入口.md
│   ├── 文献目录.md
│   ├── 标签索引.md
│   ├── PDF/
│   ├── 阅读笔记/
│   ├── AI辅助阅读/          # 每篇论文保留自己的 images/
│   └── 阅读工具/
│       ├── 使用说明.md
│       ├── 模板/
│       ├── 附件/
│       └── 论文入库登记.json
└── .obsidian/               # 隐藏的设置和本地文献助手
```

每篇论文以个人阅读主页为入口：从这里打开原文、查看 AI 精读，并写下自己的判断。AI 原稿保持独立，便于区分来源和复核。

## 直接下载现成工作台

不需要手动创建文件夹，也不需要先运行 Python。下载本仓库 [现成的文献阅读工作台 ZIP](downloads/文献阅读工作台.zip)，解压后在 Obsidian 中选择「打开文件夹作为仓库」，选择解压得到的 **文献阅读工作台** 文件夹，然后进入 `10 文献/文献入口`。

首次打开时启用附带的「学术文献助手」。ZIP 已保留 `.obsidian` 配置，文件夹布局、个人笔记模板、目录和标签索引均已准备好。里面不包含真实论文与私人记录。不要将它覆盖到已有同名工作台中。

这份 ZIP 提供本地阅读与整理环境。需要 **AI 精读并入库** 时，还须按下面步骤安装 `paper-intake`、DeepPaperNote 和相应 Python 依赖；PDF++ 可另行安装。已经通过 ZIP 创建工作台的用户可以跳过第 3 步初始化命令。

## 安装与开始使用

### 1. 准备环境

- Obsidian 桌面端。
- 支持本地 Agent Skills、能读写文件与运行 Python 的 AI 工具。本项目在 Codex 中验证。
- Python 3.10 或更新版本。以下终端命令适用于 macOS / Linux。
- 已安装 `deeppapernote` skill；请遵循 [DeepPaperNote 上游安装说明](https://github.com/917Dhj/DeepPaperNote#-quick-start)。它独立维护，不随本仓库再分发。

将本仓库下载并解压，在仓库根目录打开终端：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install PyMuPDF
```

PyYAML 用于本项目的属性读写，PyMuPDF 用于 DeepPaperNote 的 PDF 处理。请让 agent 使用这套已安装依赖的解释器，并按上游说明补齐具体论文所需的依赖。

### 2. 安装 paper-intake skill

将完整的 `skills/paper-intake` 文件夹复制到你的技能目录，不能只复制 `SKILL.md`。

Codex 的用户技能目录可使用 `~/.agents/skills/`；项目内也可使用 `.agents/skills/`。位置与发现规则见 [OpenAI 官方技能文档](https://learn.chatgpt.com/docs/build-skills)。其他宿主请按各自支持的路径安装。

下面的复制命令遇到已存在的同名目录会停止，避免覆盖你的自定义版本：

```bash
python - <<'PY'
from pathlib import Path
import shutil
target = Path.home() / '.agents/skills/paper-intake'
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree('skills/paper-intake', target)
print(target)
PY
```

如果另一技能目录已安装同名版本，先选定保留哪份，避免重复发现。安装后确认宿主技能列表中同时能找到 `paper-intake` 和 `deeppapernote`。

### 3. 创建空白工作台（已解压 ZIP 的用户跳过）

仍在仓库根目录运行。目标父目录须已存在；将路径改为你希望保存的位置：

```bash
python skills/paper-intake/scripts/init_vault.py --vault "$HOME/Desktop/文献阅读工作台"
```

脚本只创建新目录，已有同名目录时停止，不合并或覆盖。然后在 Obsidian 中选择「打开文件夹作为仓库」，打开该目录；启用附带的「学术文献助手」，进入 `10 文献/文献入口`。

PDF++ 是可选项，需要时在 Obsidian 社区插件中单独安装，用于更方便地复制原文定位链接；未安装时仍可打开 PDF、写笔记和浏览目录。

### 4. 配置精读保存位置

可以直接对 agent 说：

> 请将 DeepPaperNote 的默认保存方式设为 Obsidian，输出语言设为中文，Vault 设为我刚创建的「文献阅读工作台」的绝对路径，AI 笔记子目录设为 `10 文献/AI辅助阅读`。使用上游官方配置脚本保存，并检查配置是否 ready。

配置脚本在已安装的 DeepPaperNote 技能目录下：

```text
python <deeppapernote目录>/scripts/user_configuration.py --set-output-language zh-CN --set-save-mode obsidian --set-vault <你的Vault绝对路径> --set-papers-dir "10 文献/AI辅助阅读"
```

如需英文 AI 笔记，可明确要求英文输出，将语言参数改为 `en`；这不会改变工作台目录名称或界面语言。

尖括号是需要替换的说明，不是可原样执行的路径。含空格的实际路径需加引号。`init_vault.py` 不会自行改变任何现有默认库；多库使用时，在每次请求中写明目标路径。

### 5. 导入第一篇论文

把论文链接或 PDF 发给 agent：

> 使用 $paper-intake 精读并导入这篇论文到我的文献阅读工作台。关联 PDF、个人阅读主页和 AI 图文笔记，按现有编号继续，并更新文献目录和标签索引。

首次空库编号从 `001` 开始。若已有手动导入的文件，agent 会先核对身份与已有编号，再补齐变化。

## 阅读、编号和标签约定

- **个人内容写在阅读主页**：摘录链接、疑问、质疑和研究联想由你逐步补充，不让 AI 冒充个人判断。
- **AI 精读与图片保留独立归档**：图表检查不通过时可保留说明性占位；并非所有论文都能提取出全部图片。
- **编号稳定**：采用 `001`、`002` 等前缀；同一论文跨文件保持一致，删除论文不回收编号，新论文取现存最大编号加一。编号由 agent 按技能规则维护。
- **标签集中在阅读主页**：如 `主题/人机交互`、`方法/用户研究`；阅读进度写在 `status`。AI 笔记的标签不会自行并入论文总索引。
- **同一论文多份 AI 笔记只计一篇**：依赖稳定 `reference_id` 去重；标题相同不是判定同一论文的充分依据。
- **自动区之外可自由记录**：目录和 AI 引用区使用 HTML 注释标记，刷新只替换标记内内容。自己的文字不要写在自动区内。

详细编号与归档迁移规则见 [numbering.md](skills/paper-intake/references/numbering.md)。

## 常见问题

**拖入 PDF 后为什么没有 AI 笔记？** 本地插件只建档。需要另外发起精读请求，并确保 agent 能取得全文和使用 DeepPaperNote。

**目录没有自动更新？** 检查「学术文献助手」是否启用、PDF 是否在规定目录，再执行命令「刷新文献目录并补建阅读笔记」。关闭 Obsidian 时可运行 `intake.py --vault <路径> refresh`，但这个命令不补建缺失主页。

**AI 笔记为什么显示“待核对”？** 脚本结构与哈希校验通过不等于人已阅读确认。个人核对状态独立保留。

**如何接入已有 Obsidian 库？** 当前初始化脚本只服务于新库。已有库需要先备份，再由 agent 对照本模板调整路径与关联；不要把模板直接覆盖到原库。

**一篇论文花多少 token？** 没有固定值。篇幅、图表数量、模型、修订轮次、上下文长度和缓存都会影响消耗；本项目不提供可靠的统一价格或用量保证。

**是否必须使用 EndNote / Zotero？** 不需要。本版本未实现 EndNote 自动同步；直接提供链接或 PDF 即可。

## 仓库内容与验证

```text
README.md                     中英文项目介绍、安装与使用
skills/paper-intake/SKILL.md    Agent 工作流入口
skills/paper-intake/scripts/    新建工作台、关联与刷新脚本
skills/paper-intake/references/ 编号迁移规则
skills/paper-intake/assets/    空白内容模板、可见的 obsidian-config 与插件源码
downloads/文献阅读工作台.zip   可直接解压打开的完整空白工作台
tests/                        隔离环境下的行为测试
docs/发布到GitHub.md           发布操作与版本说明
THIRD_PARTY.md                依赖来源与署名
LICENSE                       本项目自有代码与文档的 MIT 许可
```

运行测试：

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

Python 测试覆盖新库初始化、入库校验、重复关联、个人内容保留、多版本计数、阅读版目录布局、工作台 ZIP 和忽略隐藏文件时的源码分发；安装 Node.js 后还会运行插件的模拟 Obsidian API 测试。模拟测试不等同于真实桌面 UI 测试，也不重新运行一次真实论文的模型精读。上游升级后应重新验证归档和配置接口。

发布源码中的配置位于普通文件夹 `assets/obsidian-config`，初始化脚本会将其复制为工作台实际需要的 `.obsidian`，并补建空目录。这可以避免网页上传漏掉隐藏文件。直接下载的工作台 ZIP 已包含最终目录结构。

## 来源与许可

本项目自有代码、模板与文档采用 MIT 许可。DeepPaperNote、Obsidian、PDF++ 及 Python 依赖分别遵循其自身条款，不随本发布包附带。来源见 [THIRD_PARTY.md](THIRD_PARTY.md)。

仓库仅包含空白模板与测试用合成文本，不包含个人文献库、真实论文 PDF、论文图片、私人笔记或聊天记录。

---

<a id="english"></a>

## English

[返回中文 / Back to Chinese](#chinese)

Keep a paper’s **PDF, AI reading notes, and your own notes** connected in one Obsidian reading workflow.

Give your agent a paper link or PDF. It uses DeepPaperNote to read the paper, then organizes the results in Obsidian: creates a personal reading page, retains extracted figures, links the original PDF, reconciles paper numbers, and updates the paper catalog and tag index.

This project includes an **Agent Skill, a blank Obsidian vault, and a local library helper plugin**. Deep reading is provided by the independent [DeepPaperNote project](https://github.com/917Dhj/DeepPaperNote); this project coordinates the intake and organization of its results.

> Version 0.1.0 — available for local trial use. Validated with macOS, Codex, and Obsidian desktop. The Python helper uses POSIX file locking and does not support native Windows Python. The desktop workflow has not been validated on Linux.
>
> This README is bilingual. The bundled vault, templates, plugin labels, and folder names remain in Chinese. Keep the directory names shown in the commands so that the scripts and plugin can find the expected files.

### Who is this for?

- Readers who want to spend less time organizing PDFs, AI notes, and personal notes separately.
- Researchers who want AI assistance while retaining their own interpretations, annotations, and questions.
- Anyone who wants a maintained paper catalog with topic and method tags.
- Users who sometimes import files manually and want the next agent-assisted intake to reconcile existing records and numbering.

### What it does

| Action | Responsible component | Result |
| --- | --- | --- |
| Give the agent a paper link or PDF and request deep reading and intake | paper-intake + DeepPaperNote | Deep reading, figure inspection, formal save, and linked library records |
| Manually place a PDF in `10 文献/PDF` | Obsidian library helper, when enabled | Creates a missing personal reading page and refreshes the catalog; does not call an AI model |
| Edit a reading page’s `tags` or `status` | Obsidian library helper | Updates the tag index and reading status |
| Reconcile and assign paper numbers | The agent executing this skill | Keeps the PDF, personal page, and AI archive under the same paper number |
| Refresh indexes while Obsidian is closed | `intake.py refresh` | Updates AI reference sections on existing reading pages, the catalog, and the tag index |

**Not implemented:** automatic EndNote synchronization, unattended background deep reading, numbering performed independently by the plugin, or automatic cross-device synchronization. `intake.py` manages associations; it is not a standalone program that generates AI notes with one command.

### Vault structure

The paths below are the actual paths used by the bundled vault. English comments explain their purpose.

```text
文献阅读工作台/
├── 00 收件箱/                    # Inbox
│   └── 随手记.md                 # Quick notes
├── 10 文献/                      # Literature
│   ├── 文献入口.md               # Start here
│   ├── 文献目录.md               # Paper catalog
│   ├── 标签索引.md               # Tag index
│   ├── PDF/
│   ├── 阅读笔记/                 # Personal reading pages
│   ├── AI辅助阅读/               # AI notes; each paper keeps its own images/
│   └── 阅读工具/                 # Reading tools and configuration
│       ├── 使用说明.md           # Usage guide
│       ├── 模板/                 # Templates
│       ├── 附件/                 # Attachments
│       └── 论文入库登记.json     # Intake registry
└── .obsidian/                    # Obsidian settings and the local helper plugin
```

Each paper’s personal reading page is the main entry point. Open the PDF, consult the AI analysis, and record your own judgment there. AI originals remain separate so that their source and review status stay clear.

### Download a ready-to-open vault

You do not need to create the folders manually or run Python first. Download the [ready-to-open reading vault ZIP](downloads/文献阅读工作台.zip), extract it, and choose **Open folder as vault** in Obsidian. Select the extracted **文献阅读工作台** folder, then open `10 文献/文献入口`.

Enable the bundled **学术文献助手** (“Academic Library Helper”) plugin when opening the vault for the first time. The ZIP includes the hidden `.obsidian` settings, folder layout, personal note template, catalog, and tag index. It contains no real papers or private records. Extract it into a new location rather than overwriting an existing vault with the same name.

The ZIP provides a local reading and organization environment. **AI deep reading and intake** additionally require `paper-intake`, DeepPaperNote, and the Python dependencies below. PDF++ is optional and installed separately. If you use the ZIP, skip the vault initialization command in step 3.

### Installation and first use

#### 1. Prepare your environment

- Obsidian desktop.
- An AI tool that supports local Agent Skills, file access, and Python execution. This project has been validated in Codex.
- Python 3.10 or newer. The shell commands below target macOS / Linux.
- The `deeppapernote` skill, installed separately using the [upstream installation instructions](https://github.com/917Dhj/DeepPaperNote#-quick-start). It is independently maintained and is not redistributed here.

Download and extract this repository, then open a terminal in its root directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install PyMuPDF
```

PyYAML handles this project’s YAML properties; PyMuPDF supports DeepPaperNote’s PDF processing. Have your agent use the interpreter from this environment, and follow upstream instructions for any additional dependencies needed for a particular paper.

#### 2. Install the paper-intake skill

Copy the entire `skills/paper-intake` folder to your tool’s skill directory. Copying only `SKILL.md` is insufficient.

For Codex, the user-level location is `~/.agents/skills/`; a project can also use `.agents/skills/`. See the [official OpenAI skills documentation](https://learn.chatgpt.com/docs/build-skills) for discovery rules. Follow the supported installation path for other tools.

This copy command stops if the destination already exists, preserving any customized version:

```bash
python - <<'PY'
from pathlib import Path
import shutil
target = Path.home() / '.agents/skills/paper-intake'
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree('skills/paper-intake', target)
print(target)
PY
```

If a skill with the same name is already installed elsewhere, choose which copy to keep to avoid duplicate discovery. Confirm that your tool can find both `paper-intake` and `deeppapernote`.

#### 3. Create a blank vault — skip if you extracted the ZIP

Run this from the repository root. The destination’s parent directory must already exist; change the path if you want another location:

```bash
python skills/paper-intake/scripts/init_vault.py --vault "$HOME/Desktop/文献阅读工作台"
```

The script creates a new folder only. If the destination exists, it stops without merging or overwriting anything. In Obsidian, choose **Open folder as vault**, open the new directory, enable **学术文献助手**, and go to `10 文献/文献入口`.

Optionally install PDF++ from Obsidian’s community plugins to make copying links to source passages easier. You can still open PDFs, write notes, and browse the catalog without it.

#### 4. Configure the deep-reading destination

You can ask your agent:

> Set DeepPaperNote’s default save mode to Obsidian, its output language to Chinese, its Vault to the absolute path of my new reading vault, and its AI notes directory to `10 文献/AI辅助阅读`. Save the preferences using the upstream configuration script and verify that the configuration is ready.

This matches the Chinese-first vault’s defaults. If you prefer English AI notes, request English output instead; the corresponding language option is `en` rather than `zh-CN`. Changing the output language does not rename the vault folders or translate its interface.

The configuration script is located inside the installed DeepPaperNote skill:

```text
python <deeppapernote-directory>/scripts/user_configuration.py --set-output-language zh-CN --set-save-mode obsidian --set-vault <absolute-vault-path> --set-papers-dir "10 文献/AI辅助阅读"
```

Replace the angle-bracket placeholders with real paths and quote paths containing spaces. `init_vault.py` does not change an existing default vault. When using multiple vaults, specify the destination path in each request.

#### 5. Import your first paper

Give the agent a paper link or PDF and ask:

> Use $paper-intake to deeply read this paper and import it into my Obsidian reading vault. Link the PDF, my personal reading page, and the illustrated AI note. Continue the existing numbering and update the paper catalog and tag index.

Numbering starts at `001` in an empty vault. If files were imported manually, the agent first checks their identities and existing numbers before reconciling them.

### Reading, numbering, and tagging conventions

- **Write personal content on the reading page.** Add source links, questions, critiques, and research connections yourself. AI output should not impersonate your personal judgment.
- **Keep AI notes and figures in their own archives.** Figures that fail inspection may remain as explained placeholders. Not every paper will yield every image successfully.
- **Keep numbers stable.** Use prefixes such as `001` and `002` consistently across a paper’s files. Do not recycle deleted numbers; new papers take the highest currently reserved number plus one. The agent maintains numbering according to the skill’s rules.
- **Manage paper tags on the reading page.** Examples include `主题/人机交互` (topic/HCI) and `方法/用户研究` (method/user study). Store reading progress in `status`. Tags in AI notes are not automatically merged into the paper index.
- **Count each paper once, even with multiple AI notes.** Deduplication relies on a stable `reference_id`; identical titles alone do not establish that two files represent the same paper.
- **Keep personal writing outside generated sections.** The catalog and AI reference sections use HTML comment markers. Refreshing replaces content inside those markers only.

Detailed numbering and archive migration rules are in [numbering.md](skills/paper-intake/references/numbering.md).

### Frequently asked questions

**Why did dropping a PDF into the vault not generate an AI note?** The local plugin only creates a reading record. Request deep reading separately, and ensure that your agent can access the full text and use DeepPaperNote.

**Why is the catalog not updating?** Check that **学术文献助手** is enabled and that the PDF is in the expected directory. Run its command **刷新文献目录并补建阅读笔记** (“Refresh the catalog and create missing reading pages”). When Obsidian is closed, `intake.py --vault <path> refresh` updates existing pages and indexes, but does not create missing reading pages.

**Why does an AI note show “待核对” (“Pending review”)?** Passing structure and hash checks does not mean that a person has verified the content. Personal review status is tracked separately.

**Can I use an existing Obsidian vault?** The initializer creates new vaults only. Back up an existing vault first, then have your agent adapt paths and associations against this template. Do not overwrite an existing vault with the template.

**How many tokens does one paper cost?** There is no fixed amount. Paper length, figure count, model, revision rounds, context length, and caching affect consumption. This project does not promise a fixed price or token budget.

**Do I need EndNote or Zotero?** No. Provide a link or PDF directly. Automatic EndNote synchronization is not implemented in this version.

### Repository contents and validation

```text
README.md                     Bilingual introduction, installation, and usage
skills/paper-intake/SKILL.md    Agent workflow entry point
skills/paper-intake/scripts/   Vault initialization, registration, and refresh
skills/paper-intake/references/ Numbering and migration rules
skills/paper-intake/assets/    Blank content, visible configuration, and plugin source
downloads/文献阅读工作台.zip   Complete, ready-to-open blank vault
tests/                        Behavior tests in isolated environments
docs/发布到GitHub.md           Publishing instructions in Chinese
THIRD_PARTY.md                Dependency attribution
LICENSE                       MIT license for this project's own materials
```

Run the tests:

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

The Python tests cover initialization, intake validation, repeat associations, preservation of personal content, version counting, the reading-only layout, the downloadable ZIP, and source distribution without hidden files. With Node.js installed, the suite also runs plugin tests against a simulated Obsidian API. These are not real desktop UI tests and do not rerun model-based deep reading of an actual paper. Revalidate the archive and configuration interfaces after upstream upgrades.

In the source distribution, settings live in the ordinary `assets/obsidian-config` folder. The initializer copies them into the vault’s actual `.obsidian` directory and creates the empty content folders. This avoids losing essential settings during web uploads. The downloadable vault ZIP already contains the final structure.

### Attribution and license

This project’s own code, templates, and documentation are distributed under the MIT license. DeepPaperNote, Obsidian, PDF++, and Python dependencies retain their own terms and are not bundled in this release. See [THIRD_PARTY.md](THIRD_PARTY.md).

The repository contains blank templates and synthetic test content, not personal libraries, real paper PDFs, paper figures, private notes, or chat histories.

[返回中文 / Back to Chinese](#chinese)
