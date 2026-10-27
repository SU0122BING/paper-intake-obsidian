# 发布到 GitHub

建议仓库名称：`paper-intake-obsidian`

建议简介：连接 PDF、AI 精读与个人笔记的 Obsidian 文献阅读工作台，支持文献目录、标签索引和稳定编号。

## 发布哪些文件

上传本文件所在仓库的完整内容。根目录保留 `README.md`，GitHub 会将其显示为项目首页。`skills/paper-intake` 必须整体上传。配置源码放在可见的 `assets/obsidian-config`，初始化时会还原成 `.obsidian`。`downloads/文献阅读工作台.zip` 则保留了完整的成品工作台，包括隐藏配置。

网页上传时将发布目录里面的内容拖入上传区，勿拖最外层文件夹。Finder 可用 ⌘⇧. 显示根目录的 `.gitignore` 后一并选择。源码模板不再依赖隐藏目录和空目录占位文件。不要上传自己的实际工作台，也不要从更高层工作目录执行 `git add .`。

## 发布步骤

1. 在 GitHub 新建 `paper-intake-obsidian` 仓库。若使用以下本地推送流程，创建空仓库，不自动生成 README 或 LICENSE。
2. 在本发布目录打开终端，运行以下命令。最后的远程地址请替换为 GitHub 显示的真实地址。

```bash
git init
git add .
git status --short
git commit -m "Initial paper intake skill and reading workbench"
git branch -M main
git remote add origin <你的GitHub仓库地址>
git push -u origin main
```

这份文档只是操作说明，整理发布包不会自动执行发布、登录或推送。

## 初版说明

可用 Release 标题：`v0.1.0 · 文献阅读工作台初版`

可用说明：

> 将论文链接或 PDF 交给 AI，通过 DeepPaperNote 精读后导入 Obsidian，关联原文、个人阅读主页与 AI 图文笔记，并整理稳定编号、文献目录和标签索引。包含空白工作台和本地文献助手。当前以 macOS + Codex 验证，DeepPaperNote 与可选 PDF++ 需另行安装。

这是本地 skill 仓库的发布形式，尚不是 Obsidian 社区插件上架或官方 AI 插件目录提交。附带文献助手由模板本地安装。

本包自有部分已放入 MIT LICENSE，署名使用 `Paper Intake contributors`。你可以在首次发布前按希望公开的作者名称调整署名。

## 给读者提供现成工作台

仓库自带 `downloads/文献阅读工作台.zip`，README 已链接。读者打开该文件页面后点击 Download raw file 下载，解压并作为 Obsidian 仓库打开即可。这里的 ZIP 是成品资源，不要在 GitHub 网页上传时把它展开。

也可以在以后创建 GitHub Release 时把同一个 ZIP 作为附件上传，让读者从 Releases 下载；当前不需要先创建 Release。
