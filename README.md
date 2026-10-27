# Paper Intake · Obsidian 文献阅读工作台

把一篇论文的 **PDF、AI 精读和个人阅读笔记** 放进同一个可持续使用的阅读流程。

将论文链接或 PDF 发给 AI，它调用 DeepPaperNote 精读，再把结果整理进 Obsidian：建立阅读主页、保留原图、关联原文、核对编号，并更新文献总目录和标签索引。

本项目是 **Agent Skill + 空白 Obsidian 工作台 + 本地文献助手**。精读能力来自独立项目 [DeepPaperNote](https://github.com/917Dhj/DeepPaperNote)；本项目负责组织与入库联动。

> 当前版本：0.1.0，供本地试用。以 macOS、Codex 和 Obsidian 桌面端为验证环境。Python helper 使用 POSIX 文件锁，暂不支持 Windows 原生 Python；Linux 尚未完成实际桌面验证。

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

### 3. 创建空白工作台

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

尖括号是需要替换的说明，不是可原样执行的路径。`init_vault.py` 不会自行改变任何现有默认库；多库使用时，在每次请求中写明目标路径。

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
README.md                     项目介绍、安装与使用
skills/paper-intake/SKILL.md    Agent 工作流入口
skills/paper-intake/scripts/    新建工作台、关联与刷新脚本
skills/paper-intake/references/ 编号迁移规则
skills/paper-intake/assets/    空白工作台及文献助手源码
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

Python 测试覆盖新库初始化、入库校验、重复关联、个人内容保留、多版本计数及阅读版目录布局；安装 Node.js 后还会运行插件的模拟 Obsidian API 测试。模拟测试不等同于真实桌面 UI 测试，也不重新运行一次真实论文的模型精读。上游升级后应重新验证归档和配置接口。

## 来源与许可

本项目自有代码、模板与文档采用 MIT 许可。DeepPaperNote、Obsidian、PDF++ 及 Python 依赖分别遵循其自身条款，不随本发布包附带。来源见 [THIRD_PARTY.md](THIRD_PARTY.md)。

仓库仅包含空白模板与测试用合成文本，不包含个人文献库、真实论文 PDF、论文图片、私人笔记或聊天记录。
