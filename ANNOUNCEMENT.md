# 📢 Announcement drafts

Ready-to-copy promotional posts in Chinese (V2EX / 掘金 / 知乎) and English
(Twitter / Reddit / Hacker News). Each explicitly asks the community for
feedback and suggestions.

> **💡 建议先在仓库开一个 [GitHub Discussion](https://github.com/harrycjs/skill-manager/discussions)
> 把链接附在帖子后面,让反馈有地方汇总。**

---

## 🇬🇧 English (Twitter / Reddit / HN)

### Short — for Twitter / X

> 🎉 Just open-sourced **skill-manager** — a Flask web UI to browse, install,
> view, and edit Claude Code / OpenCLAW skills locally.
>
> ✨ In-browser file editor (CodeMirror)
> 📁 One-click "open in file manager"
> 🔒 Path-traversal safe
> 🧪 26 tests + GitHub Actions CI
>
> 🔗 https://github.com/harrycjs/skill-manager
>
> **Early MVP — feedback & suggestions very welcome!** 🙌

### Long — for Reddit / Hacker News / Dev.to

**Title:** Show HN: Skill Manager – Browse and Edit Claude Code Skills Locally

**Body:**

I built a small Flask app to manage skills installed for Claude Code and
OpenCLAW locally, and just open-sourced it:
**[harrycjs/skill-manager](https://github.com/harrycjs/skill-manager)**.

The original idea was just "list everything I have installed", but it grew
into a tiny workbench:

* **Browse** Claude Code + every OpenCLAW workspace in one place
* **View** skill details: full `SKILL.md` rendered as Markdown, file tree,
  size, last-modified
* **Edit** any file in the browser (CodeMirror) with a `.bak` backup
* **Open in Finder/Explorer** with one click per skill
* **Install** from Skillhub into any combination of targets
* **Distribute** selected skills into a target project folder

It's a single-binary Flask app — no DB, no cloud, no signup. Just
`pip install -r requirements.txt && python app.py` and you're at
`http://127.0.0.1:5000`.

The codebase is intentionally small and conservative: Flask blueprints,
stdlib helpers, ~700 lines of Python, vanilla JS, CodeMirror + marked.js
via CDN. 26 pytest cases cover the happy paths and every safety
boundary (path traversal, file-size cap, extension whitelist).

**Roadmap is in the README.** Things I want to add next: CLI/TUI,
version pinning, dependency graph, project-level `skill.json`.

**I would love feedback, especially on:**

1. Is this useful, or are you happy with a raw `ls ~/.claude/skills/skills`?
2. What feature would make you actually switch from "edit in your editor
   of choice" to "edit in the browser"?
3. What should the CLI look like, if any?
4. Anything I missed from your own skill-management workflow?

👉 Issues + Discussions are open:
https://github.com/harrycjs/skill-manager

---

## 🇨🇳 中文 (V2EX / 掘金 / 知乎 / 即刻)

### 短版 — V2EX / 即刻 / 微博

> 🎉 开源了一个小工具:**Skill Manager** —— 给 Claude Code / OpenCLAW
> 技能做本地管理。
>
> 📂 一键浏览所有已安装技能
> 📑 点技能卡片查看详情 + Markdown 渲染 SKILL.md
> ✏️ 浏览器内直接编辑文件(CodeMirror,带 .bak 备份)
> 📁 每个技能旁"在文件夹中打开"按钮,跨平台
> 🛡️ 路径穿越防护、文件大小限制、扩展名白名单
> 🧪 26 个 pytest 用例 + GitHub Actions CI
>
> 🔗 https://github.com/harrycjs/skill-manager
>
> **还是 MVP,非常希望大家给建议!** 🙌

### 长版 — 掘金 / 知乎

**标题:** 我把 Claude Code 技能管理做成了一个开源小工具:Skill Manager

**正文:**

最近用 Claude Code 装了不少 skills,装在 `~/.claude/skills/skills/` 下,
OpenCLAW 又有好几个 workspace,装来装去找不到谁装在哪、版本是什么。

干脆撸了个小工具:**[Skill Manager](https://github.com/harrycjs/skill-manager)**
(Flask 单体应用,~700 行 Python + 一份原生 JS + CodeMirror/marked.js CDN)。

**它能做什么:**

- 📂 **浏览** —— Claude Code + 所有 OpenCLAW workspace 里的技能一屏看完
- 📑 **详情** —— 点击卡片,右侧滑出面板:完整 SKILL.md 渲染成 HTML、
  递归文件树、大小、最近修改时间
- ✏️ **在线编辑** —— CodeMirror 5(.md/.py/.js/.json/.yaml/.sh 等),
  带语法高亮、行号,保存时自动 `.bak` 备份
- 📁 **一键打开文件夹** —— 每个技能卡片旁一个 📁 按钮,跨平台:
  Windows 走 `os.startfile`,macOS 走 `open`,Linux 走 `xdg-open`
- 📦 **从 Skillhub 安装** —— 一键装到 Claude Code 或任意 OpenCLAW workspace,
  旁边还放了腾讯 Skillhub 技能市场的跳转链接
- 🚚 **分发到项目** —— 勾选若干技能,复制到目标项目目录
- 🛡️ **安全** —— 每次读写都过 `resolve_skill_path` + `safe_join` 双层校验,
  2 MiB 大小上限,白名单扩展名

**怎么用:**

```bash
git clone https://github.com/harrycjs/skill-manager.git
cd skill-manager
pip install -r requirements-dev.txt
python app.py
# 打开 http://127.0.0.1:5000
```

**关于选型:**

坚持 Flask 单体,不上前后端分离 —— 装机即跑,新手友好。代码尽量保持
朴素,没有 ORM、没有状态管理、没有打包,目标是让一个 Python 初学者
也能 fork 后魔改。

测试用 pytest + 临时 HOME 重定向,完全离线可跑。CI 跑 Python 3.10/3.11/3.12
矩阵 + ruff。

**Roadmap(写在 README 里,欢迎挑):**

- CLI / TUI(`skill-manager` 命令)
- 版本管理与依赖图
- 项目级 `skill.json` 声明
- 实时安装日志(SSE)
- 技能市场浏览 / 评分

**🙏 特别希望听听大家的建议:**

1. 你们平时怎么管理 skills?这种集中式 UI 还是太重了?
2. "在浏览器里编辑文件"这个功能,你愿意用吗?还是更喜欢 VSCode?
3. CLI 你想要什么样的?(`skill list / install / remove / edit`)
4. 你最希望下一个版本加什么?

👉 仓库地址:**https://github.com/harrycjs/skill-manager**
Issues / Discussions 都开了,直接说就行 👀

---

## 📌 平台适配建议

| 平台 | 标题风格 | 字数 | 重点 |
|---|---|---|---|
| **V2EX** | "分享创造"节点,简洁技术向 | 300-500 | 痛点 + 链接 + 一句"求建议" |
| **掘金** | 标题党 + 干货长文 | 1500-2500 | 截图占位 + 完整 README 翻译 + Roadmap |
| **知乎** | 提问式标题 | 1000-1500 | "你平时怎么管理 Claude 技能?"互动向 |
| **即刻** | 一句话 + 链接 | 100-200 | 痛点共鸣 + 链接 |
| **Twitter / X** | thread,3-5 推 | 各 280 字内 | emoji 多 + 截图 + "feedback welcome" |
| **Reddit r/ClaudeAI** | Show HN 风格 | 500-800 | 强调 self-host / no tracking |
| **Hacker News** | Show HN | 200-400 | 一句"why this exists" + 链接 |
| **Dev.to** | tutorial-style | 800-1500 | 截图 + quick start + 完整 features |

---

## 🎯 配套动作建议

发布后顺手做这些能放大效果:

- [ ] 在仓库开一个 `📣 Announcements` Discussion,置顶
- [ ] 在 README 加 Discussions 徽章(已经 README 有空位)
- [ ] 录一段 30 秒演示 GIF,贴到 README 和帖子
- [ ] 把这个仓库 `star` 自己(给个小推动,后续更多人看到)
- [ ] 加到 awesome-claude-code / awesome-skills 之类的列表(如果有)
- [ ] 48h 内回复每一条 issue / 评论,趁热度建立社区印象
