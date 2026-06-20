# Skill Manager 技能管理器

> 给 Claude Code / OpenCLAW 的本地技能做**浏览、安装、分发、查看、编辑**的 Web UI。

![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![Flask](https://img.shields.io/badge/flask-%3E=3.0-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Status](https://img.shields.io/badge/status-MVP-orange)

Skill Manager 是一个轻量级的 Flask 应用,把本地的 Claude Code / OpenCLAW
技能目录变成可浏览、可发现、可编辑的工作台 —— **无数据库、无云依赖、
无需注册**,装完即用。

---

## ✨ 功能特性

- 📂 **浏览** —— 一屏看完 Claude Code 和所有 OpenCLAW workspace 下的技能
- 📑 **查看详情** —— 点击技能卡片,右侧滑出面板:完整 `SKILL.md` Markdown
  渲染、文件树、总大小、最近修改时间
- ✏️ **浏览器内编辑** —— 任意可编辑文件直接在 CodeMirror 中打开,带语法高亮、
  行号,保存时自动 `.bak` 备份
- 📁 **一键打开文件夹** —— 每个技能卡片旁有一个 📁 按钮,跨平台调起系统
  文件管理器(Windows/macOS/Linux)
- 📦 **从 Skillhub 安装** —— 一键拉取技能,可选安装到 Claude Code 和/或
  任意 OpenCLAW workspace;页面顶部还放了 [腾讯 Skillhub 技能市场](https://www.skillhub.cn/skills?sortBy=score)
  的跳转链接,方便先浏览再装
- 🚚 **分发到项目** —— 勾选若干技能,复制到目标项目目录,跟着项目一起发布
- 🛡️ **默认安全** —— 所有读写都经过路径校验、大小上限和扩展名白名单三重把关

---

## 📸 截图

> _即将到来 —— `docs/screenshots/` 目录已预留。_

---

## 🚀 快速开始

### 方式一:直接跑(Python ≥ 3.10)

```bash
# 1. 克隆仓库
git clone https://github.com/harrycjs/skill-manager.git
cd skill-manager

# 2. 安装运行时依赖
pip install -r requirements.txt
# 或者装开发版(带测试和 lint 工具)
pip install -r requirements-dev.txt

# 3. 启动
python app.py
# 浏览器打开 http://127.0.0.1:5000
```

首次启动时,Skill Manager 会尝试从腾讯云 COS 镜像拉取 Skillhub CLI。
如果你**离线**或**不需要**安装功能,浏览 / 查看 / 编辑 / 分发
这四块都正常工作。

### 方式二:作为模块运行

```bash
flask --app skillhub run --host 0.0.0.0 --port 5000
```

### 生产部署

```bash
# 用 gunicorn
gunicorn 'skillhub:create_app()'

# 或用 waitress(Windows 友好)
waitress-serve --port=5000 'skillhub:create_app()'
```

---

## 🧩 架构一览

```
┌─────────── 浏览器 ───────────┐
│  标签页:  导入 | 安装 |      │
│           分发              │
│                            │
│  右侧详情面板:              │
│   [SKILL.md]  [文件]   ◄────── 点卡片打开
│   • Markdown 渲染           │
│   • 文件树 → CodeMirror    │
└──────────┬─────────────────┘
           │  /api/...
┌──────────▼─────────────────┐
│  Flask 应用 (skillhub 包)  │
│   skills_bp   install_bp   │
│   editor_bp   distribute_bp│
│           utils.py         │
└──────────┬─────────────────┘
           │
   ~/.claude/skills/skills/*
   ~/.openclaw/workspace*/skills/*
   ~/.skill-hub/cli/...
```

所有技能目录都做了**沙盒处理**:每个 API 调用都通过
`utils.resolve_skill_path` + `utils.safe_join` 校验路径,
恶意请求无法逃出技能根目录。

---

## 🧪 开发

```bash
# 跑测试
pytest --cov=skillhub

# 代码风格检查
ruff check .

# 自动格式化(可选)
ruff format .
```

测试套件自带 `temp_home` 装置:把 `HOME` 重定向到 `tmp_path` 并种一棵
小型技能树,所以测试**完全离线、可重现**。

### 项目结构

```
skill-manager/
├── app.py                      # 入口文件
├── skillhub/                   # 应用包
│   ├── __init__.py             #   create_app() 工厂
│   ├── utils.py                #   路径助手、workspace 发现
│   ├── skills_bp.py            #   列表 / 详情 / 文件树 API
│   ├── editor_bp.py            #   文件读写 API
│   ├── install_bp.py           #   Skillhub CLI 自举
│   ├── distribute_bp.py        #   复制技能到项目
│   ├── open_folder.py          #   跨平台调起文件管理器
│   └── cli.py                  #   留给未来 CLI 的占位
├── templates/
│   ├── base.html
│   ├── index.html
│   └── _skill_detail.html
├── static/
│   ├── css/app.css
│   └── js/
│       ├── app.js
│       └── editor.js
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_utils.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── LICENSE
├── CHANGELOG.md
├── ANNOUNCEMENT.md             # 现成的推广文案(中英双语)
└── .github/workflows/ci.yml
```

---

## 🔧 配置

通过环境变量或 Flask config 调整:

| 变量 | 默认值 | 说明 |
|---|---|---|
| `SKILLHUB_WEBSITE_URL` | `https://www.skillhub.cn/skills?sortBy=score` | 安装页"浏览 Skillhub"按钮跳转链接 |
| `HOME` / `USERPROFILE` | 系统默认 | Skill Manager 读取技能根目录的起点 |

在 Flask 应用层面覆盖示例:

```python
app.config["SKILLHUB_WEBSITE_URL"] = "https://你的镜像站点"
```

---

## 🗺️ 路线图

当前版本聚焦"浏览 + 查看 + 编辑 + 一键打开文件夹"。以下是计划中的
后续功能,欢迎贡献者认领:

- [ ] **CLI / TUI** —— `skill-manager` 子命令(用 Click 或 Textual)
- [ ] **技能市场浏览** —— 在 Web UI 内浏览 trending 技能
- [ ] **版本管理** —— 固定 `skill@1.2.0`、一键升级全部、依赖图解析
- [ ] **项目级 `skill.json`** —— 类似 `package.json`,`cd` 进入项目自动加载
- [ ] **保存前 diff 预览** —— 看清改了哪些行再写盘
- [ ] **实时安装日志** —— Server-Sent Events 流式输出
- [ ] **批量操作** —— 多选 → 批量安装 / 升级 / 导出
- [ ] **i18n** —— 英文 UI 与中文并列
- [ ] **技能模板脚手架** —— `skill create my-skill` 生成标准目录
- [ ] **备份中心** —— 集中浏览所有 `.bak`、一键恢复
- [ ] **多用户 + 权限** —— 团队模式(读 / 写 / 管理 角色)

**🙏 非常欢迎提 Issue 或开 Discussion 告诉我们你最想要哪个!**
详情见 [ANNOUNCEMENT.md](ANNOUNCEMENT.md) 里列的 4 个具体问题。

---

## 🤝 参与贡献

1. Fork 本仓库
2. 新建特性分支(`git checkout -b feat/amazing-feature`)
3. 提交改动(`git commit -m 'Add amazing feature'`)
4. 推送到你的 fork(`git push origin feat/amazing-feature`)
5. 提一个 Pull Request

请先开 Issue 讨论大方向,避免做出来发现跟路线图冲突。

---

## 📄 开源协议

[MIT](LICENSE) —— 详见协议全文。

---

## 🙏 致谢

- **CodeMirror** 团队提供的浏览器内编辑器(通过 jsDelivr CDN 加载)
- **marked.js** 提供客户端 Markdown 渲染
- 设计灵感来自 **Homebrew**、**Oh My Zsh**、**lazygit** 和
  **VSCode Remote Explorer** —— 它们都是"小工具用顺手了离不开"的典范
