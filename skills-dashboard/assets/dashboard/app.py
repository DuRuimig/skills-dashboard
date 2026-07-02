#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"


def default_data_dir():
    if os.environ.get("SKILLS_DASHBOARD_DATA_DIR"):
        return Path(os.environ["SKILLS_DASHBOARD_DATA_DIR"]).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "SkillsDashboard"
    if sys.platform.startswith("win"):
        return Path(os.environ.get("APPDATA", Path.home())) / "SkillsDashboard"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "skills-dashboard"


DATA = default_data_dir()
CATALOG = DATA / "catalog.json"
CATALOG_CATEGORY_COLORS_KEY = "__categoryColors"

HOME = Path.home()


def configured_skill_roots():
    workspace = Path(os.environ.get("SKILLS_DASHBOARD_WORKSPACE", Path.cwd())).expanduser()
    roots = [
        (HOME / ".agents" / "skills", "Agent skills"),
        (HOME / ".codex" / "skills", "Codex skills"),
        (HOME / ".codex" / "plugins" / "cache", "Codex plugin skills"),
        (HOME / ".cc-switch" / "skills", "cc-switch skills"),
        (HOME / ".claude" / "skills", "Claude Code skills"),
        (HOME / ".config" / "claude" / "skills", "Claude Code skills"),
        (HOME / ".hermes" / "skills", "Hermes skills"),
        (HOME / ".config" / "hermes" / "skills", "Hermes skills"),
        (workspace / ".agents" / "skills", "Project agent skills"),
        (workspace / ".codex" / "skills", "Project Codex skills"),
        (workspace / ".claude" / "skills", "Project Claude skills"),
        (workspace / ".hermes" / "skills", "Project Hermes skills"),
        (workspace / ".github" / "skills", "Project GitHub skills"),
    ]

    extra = os.environ.get("SKILLS_DASHBOARD_EXTRA_ROOTS", "")
    for raw_path in extra.split(os.pathsep):
        raw_path = raw_path.strip()
        if raw_path:
            roots.append((Path(raw_path).expanduser(), "Custom skills"))

    seen = set()
    unique_roots = []
    for path, label in roots:
        resolved = str(path.expanduser())
        if resolved not in seen:
            seen.add(resolved)
            unique_roots.append((path.expanduser(), label))
    return unique_roots


SKILL_ROOTS = configured_skill_roots()
CLI_TOOLS = ["agent-reach", "markitdown", "gh", "opencli", "mcporter", "yt-dlp"]

CATEGORY_ALIASES = {
    "All": "全部",
    "Browser": "知识搜索",
    "CLI Tools": "其他工具",
    "Creation": "个人知识库",
    "Documents": "文档媒体",
    "Internet": "知识搜索",
    "Media": "文档媒体",
    "OpenAI": "个人知识库",
    "Development": "代码开发",
    "Other": "其他工具",
    "工程研发": "代码开发",
    "互联网与浏览器": "知识搜索",
    "文档与媒体": "文档媒体",
    "设计与产品": "产品研发",
    "工作流与知识": "个人知识库",
}

CATEGORY_GROUPS = {
    "代码质量": "代码开发",
    "架构设计": "代码开发",
    "需求交付": "代码开发",
    "开发协作": "代码开发",
    "互联网调研": "知识搜索",
    "浏览器与桌面": "知识搜索",
    "抖音": "知识搜索",
    "文档处理": "文档媒体",
    "媒体处理": "文档媒体",
    "设计体验": "产品研发",
    "OpenAI": "个人知识库",
    "知识管理": "个人知识库",
    "创建与扩展": "个人知识库",
    "命令工具": "其他工具",
    "其他": "其他工具",
}

SOURCE_ALIASES = {
    "User": "用户安装",
    "System": "系统内置",
    "Codex": "Codex",
    "CLI": "命令行工具",
}

DEFAULT_CATEGORY_COLORS = {
    "代码开发": "#2563eb",
    "知识搜索": "#0f766e",
    "文档媒体": "#d97706",
    "产品研发": "#7c3aed",
    "个人知识库": "#be123c",
    "其他工具": "#64748b",
}

SKILL_PROFILES = {
    "agent-reach": {
        "category": "互联网调研",
        "summary": "把网页、GitHub、小红书、B站、YouTube、RSS、社交平台等入口统一路由给 Agent 使用。",
        "whenToUse": "需要查资料、读链接、看平台讨论、搜索仓库、查看小红书/B站/YouTube 内容时使用。",
        "requirements": "部分平台依赖 Chrome 登录态；小红书等通过 OpenCLI 复用浏览器登录。",
        "examples": ["查小红书：AI 记账 App", "读这个 GitHub 仓库的 issue", "总结这个 YouTube 视频字幕"],
    },
    "imagegen": {
        "category": "媒体处理",
        "summary": "生成或编辑位图图片，适合封面图、插画、纹理、产品视觉和图片改造。",
        "whenToUse": "需要从文字生成图片，或对已有图片做风格、颜色、内容修改时使用。",
        "requirements": "图片编辑需要你提供原图；生成内容要符合安全规则。",
        "examples": ["生成一张深色科技感封面图", "把这张图改成产品海报风格"],
    },
    "openai-docs": {
        "category": "OpenAI",
        "summary": "查询 OpenAI/Codex/API 的官方文档，适合需要最新模型、接口和用法时使用。",
        "whenToUse": "问 OpenAI API、Codex、模型选择、迁移或提示词升级时使用。",
        "requirements": "会优先查官方来源；需要联网。",
        "examples": ["最新 Responses API 怎么用", "Codex 和 ChatGPT 里写代码有什么区别"],
    },
    "plugin-creator": {
        "category": "创建与扩展",
        "summary": "创建 Codex 插件目录、manifest 和个人插件市场条目。",
        "whenToUse": "要把一组 skill、MCP、脚本打包成 Codex 插件时使用。",
        "requirements": "需要明确插件名称和想暴露的能力。",
        "examples": ["帮我创建一个管理 Obsidian 的 Codex 插件"],
    },
    "skill-creator": {
        "category": "创建与扩展",
        "summary": "帮助设计和编写新的 Codex skill，包括触发条件、说明和工作流。",
        "whenToUse": "想把一套重复工作流程沉淀成可复用 skill 时使用。",
        "requirements": "需要描述目标任务、输入输出和边界。",
        "examples": ["帮我做一个研究论文的 skill"],
    },
    "skill-installer": {
        "category": "创建与扩展",
        "summary": "从官方列表或 GitHub 仓库安装 Codex skill。",
        "whenToUse": "要安装、列出或从 GitHub 添加 skill 时使用。",
        "requirements": "安装后通常需要重启 Codex 才会自动识别新 skill。",
        "examples": ["安装 ui-ux-pro-max skill", "列出可安装的 curated skills"],
    },
    "ui-ux-pro-max": {
        "category": "设计体验",
        "summary": "UI/UX 设计智能库，覆盖颜色、字体、布局、可访问性、动效和产品类型建议。",
        "whenToUse": "设计或重构网页、控制台、表单、仪表盘、移动端界面时使用。",
        "requirements": "适合做设计决策和验收；不是后端逻辑工具。",
        "examples": ["重做这个技能管理台的 UI", "检查这个页面的可访问性和布局"],
    },
    "context-compressor": {
        "category": "知识管理",
        "summary": "把长对话压缩成可续聊的检查点摘要，保留目标、状态、路径、决策和下一步。",
        "whenToUse": "你说“压缩上下文”“续聊摘要”“交接摘要”“checkpoint”或准备开新线程继续工作时使用。",
        "requirements": "不需要外部工具；依赖当前对话里已有的信息，未验证的内容会标注为推断。",
        "examples": ["压缩一下当前上下文", "生成一个续聊摘要", "做一个可以贴到新线程的 checkpoint"],
    },
    "grill-me": {
        "category": "代码质量",
        "summary": "在动手前对计划和设计进行高压追问，逼出隐藏需求、边界条件、风险和替代方案。",
        "whenToUse": "准备做复杂功能、架构改动、产品方案或不确定需求时，用它先把问题问透。",
        "requirements": "它标记为手动触发型 skill；适合你明确说“grill me / 拷问一下这个方案”。",
        "examples": ["grill me：我要做一个 skill 管理器", "拷问一下这个实现方案", "在写代码前先质询我的设计"],
    },
    "ask-matt": {
        "category": "知识管理",
        "summary": "把 Matt Pocock 的工程判断当作参考顾问，用来讨论代码组织、工程习惯和方案取舍。",
        "whenToUse": "你想要偏资深工程师口吻的建议，而不是马上写代码时使用。",
        "requirements": "适合作为讨论和校准，不替代项目内真实约束。",
        "examples": ["用 ask-matt 帮我判断这个抽象值不值得做", "这个工程方案像不像过度设计？"],
    },
    "code-review": {
        "category": "代码质量",
        "summary": "按“代码规范”和“需求实现”两条线审查 diff，适合防止 AI 改出隐藏回归。",
        "whenToUse": "改完一批代码、准备提交、处理 PR 或想看是否偏离需求时使用。",
        "requirements": "最好有明确的对比点，例如 main、某个 commit、PRD 或 issue。",
        "examples": ["review since main", "审一下当前改动有没有偏离需求", "按代码规范和 spec 两条线看 diff"],
    },
    "codebase-design": {
        "category": "架构设计",
        "summary": "提供深模块、接口边界、seam、adapter 等工程设计词汇，帮助减少浅层碎片化代码。",
        "whenToUse": "要设计模块接口、拆分边界、提升可测试性或避免到处散落逻辑时使用。",
        "requirements": "需要先读相关代码和现有约定；不适合空谈架构。",
        "examples": ["帮我设计这个模块的边界", "这段逻辑应该放在哪个 seam？", "怎么让这个模块更 deep？"],
    },
    "diagnosing-bugs": {
        "category": "代码质量",
        "summary": "调试纪律：先建立可重复的反馈循环，再提出假设、验证、缩小范围。",
        "whenToUse": "遇到 bug、性能退化、测试失败、线上异常或“不知道为什么坏了”时使用。",
        "requirements": "需要尽量拿到复现步骤、日志、失败测试或可观察信号。",
        "examples": ["诊断这个测试为什么失败", "这个页面变慢了，帮我定位", "先建立反馈循环再修 bug"],
    },
    "domain-modeling": {
        "category": "架构设计",
        "summary": "沉淀项目术语、领域模型和架构决策，防止团队/Agent 对同一概念各说各话。",
        "whenToUse": "业务概念混乱、命名摇摆、模型边界不清、需要写 ADR 或 CONTEXT.md 时使用。",
        "requirements": "适合重要概念，不必为很小的实现细节建模。",
        "examples": ["帮我整理这个项目的领域词汇", "这几个概念应该怎么命名？", "把这个决策写成 ADR"],
    },
    "grill-with-docs": {
        "category": "架构设计",
        "summary": "一边拷问方案，一边沉淀文档、ADR 和术语，适合复杂设计前的高强度澄清。",
        "whenToUse": "做架构/产品方案前，既要被追问，也要把结论写进项目文档时使用。",
        "requirements": "需要你愿意逐步回答问题；它会比普通实现流程更慢但更稳。",
        "examples": ["grill-with-docs：设计技能管理器架构", "一边拷问这个方案一边写 ADR"],
    },
    "implement": {
        "category": "需求交付",
        "summary": "按 PRD 或 issue 实现功能，过程中跑类型检查/测试，最后触发代码审查。",
        "whenToUse": "需求已经相对明确，要进入正式实现阶段时使用。",
        "requirements": "最好有 PRD、issue、任务列表或清晰验收标准。",
        "examples": ["按这个 PRD 实现功能", "根据这些 issues 完成开发", "实现后跑测试并 review"],
    },
    "improve-codebase-architecture": {
        "category": "架构设计",
        "summary": "扫描代码库里的架构摩擦和可深化模块机会，适合做重构路线图。",
        "whenToUse": "代码开始散、抽象变浅、重复逻辑多，想系统性找重构机会时使用。",
        "requirements": "适合中大型代码库；小修 bug 时不要默认触发。",
        "examples": ["扫描这个仓库的架构改进机会", "找出最值得重构的浅模块"],
    },
    "prototype": {
        "category": "需求交付",
        "summary": "快速做原型验证想法，强调探索速度，不把原型误当生产实现。",
        "whenToUse": "想先验证交互、API 形状、技术路径或产品想法时使用。",
        "requirements": "需要明确原型范围和可丢弃边界。",
        "examples": ["先做一个可点的原型", "快速验证这个方案是否可行"],
    },
    "resolving-merge-conflicts": {
        "category": "代码质量",
        "summary": "处理 merge/rebase 冲突，要求理解两边意图，而不是机械保留某一边。",
        "whenToUse": "Git 合并冲突、rebase 冲突、升级分支时使用。",
        "requirements": "需要当前 repo 处在冲突状态或提供冲突文件。",
        "examples": ["帮我解决当前 merge conflicts", "理解两边改动后处理冲突"],
    },
    "setup-matt-pocock-skills": {
        "category": "知识管理",
        "summary": "为 Matt Pocock 这套 skills 配置项目约定，例如 issue tracker、文档位置和协作规则。",
        "whenToUse": "想在某个仓库里长期使用这套工程 skills 时先运行它。",
        "requirements": "最好在具体项目仓库内使用，而不是全局空跑。",
        "examples": ["给这个项目配置 Matt Pocock skills", "设置 issue tracker 和项目上下文"],
    },
    "tdd": {
        "category": "代码质量",
        "summary": "测试驱动开发：先写失败测试，再最小实现，通过后重构，防止靠猜修代码。",
        "whenToUse": "修 bug、加核心逻辑、改容易回归的模块，或你明确说 test-first/TDD 时使用。",
        "requirements": "项目需要有可运行测试；没有测试时先建立最小反馈循环。",
        "examples": ["用 TDD 修这个 bug", "先写失败测试再实现", "红绿重构这个功能"],
    },
    "to-issues": {
        "category": "需求交付",
        "summary": "把讨论、PRD 或大任务拆成可执行 issues，让后续 Agent 能逐项实现。",
        "whenToUse": "需求太大、任务模糊、需要拆分工作项或准备项目看板时使用。",
        "requirements": "需要有目标说明或现有 PRD/对话作为输入。",
        "examples": ["把这个方案拆成 issues", "把当前计划变成 agent-ready 任务"],
    },
    "to-prd": {
        "category": "需求交付",
        "summary": "把想法整理成 PRD，明确目标、范围、用户故事、非目标和验收标准。",
        "whenToUse": "想法还散、准备正式实现前，需要先写清需求时使用。",
        "requirements": "可能会先追问关键产品决策。",
        "examples": ["把这个想法写成 PRD", "整理一个可实现的需求文档"],
    },
    "triage": {
        "category": "需求交付",
        "summary": "对 issue/外部 PR 做分诊：分类、验证、补充上下文，并产出 Agent 可执行 brief。",
        "whenToUse": "仓库有一堆 issues/PRs，需要判断优先级、复现价值或交给 Agent 处理时使用。",
        "requirements": "最好已配置 issue tracker；公开评论要注意免责声明和权限。",
        "examples": ["triage 这些 issues", "把这个 bug issue 变成可执行 brief"],
    },
    "grilling": {
        "category": "代码质量",
        "summary": "完整拷问会话：一次只问一个关键问题，直到计划、边界和依赖被问清楚。",
        "whenToUse": "准备做复杂功能、重构、产品方案或你感觉需求没问透时使用。",
        "requirements": "需要你逐题反馈；如果问题能通过读代码回答，就应先读代码。",
        "examples": ["grilling：我要重构技能管理器", "在开工前拷问我的方案"],
    },
    "handoff": {
        "category": "知识管理",
        "summary": "把当前对话压成交接文档，让另一个 Agent 能继续工作。",
        "whenToUse": "长线程要交接、准备换线程、或想保存当前工作状态时使用。",
        "requirements": "会避免复制已有 artifact，优先引用路径/URL；敏感信息要脱敏。",
        "examples": ["生成 handoff 文档", "把当前工作交接给下一个 Agent"],
    },
    "teach": {
        "category": "知识管理",
        "summary": "把某个主题讲清楚，适合学习工程概念、代码模式或项目设计。",
        "whenToUse": "你不是要我立刻改代码，而是要解释、教学、帮你理解时使用。",
        "requirements": "需要明确学习目标和当前水平。",
        "examples": ["教我什么是 deep module", "讲清楚这个架构模式"],
    },
    "writing-great-skills": {
        "category": "知识管理",
        "summary": "指导如何写高质量 skill，尤其是触发条件、边界、示例和上下文负担。",
        "whenToUse": "你要创建/改进自己的 skill，或者把高手工作流沉淀成 skill 时使用。",
        "requirements": "适合和 `skill-creator` 搭配；需要具体使用场景。",
        "examples": ["帮我把这个工作流写成好 skill", "检查这个 skill 触发条件是否清楚"],
    },
    "git-guardrails-claude-code": {
        "category": "代码质量",
        "summary": "为 Claude Code 设置 Git 防护钩子，阻止危险命令如 push、reset --hard、clean 等。",
        "whenToUse": "你担心 AI 误执行破坏性 Git 命令，希望给项目加护栏时使用。",
        "requirements": "主要面向 Claude Code；在 Codex 里可参考思路，但不一定直接适配。",
        "examples": ["给这个项目加 Git guardrails", "阻止 AI 执行 git reset --hard"],
    },
    "analytics-tracking": {
        "category": "知识管理",
        "summary": "设计、检查和优化网站埋点方案，覆盖 GA4、事件、转化、归因和数据层。",
        "whenToUse": "需要规划统计口径、检查埋点是否完整、设计转化事件或排查 GA4 数据问题时使用。",
        "requirements": "需要知道目标网站、关键动作和当前使用的统计工具；真实数据权限仍由你掌握。",
        "examples": ["帮我设计一个 GA4 事件方案", "检查这个页面的转化埋点是否完整"],
    },
    "douyin": {
        "category": "媒体处理",
        "summary": "下载抖音视频或读取视频基础信息，例如标题、作者和互动数据。",
        "whenToUse": "你发来抖音短链接或视频链接，并希望下载视频或查看视频信息时使用。",
        "requirements": "只处理可访问的视频链接；部分视频可能受登录态、地区或平台限制影响。",
        "examples": ["下载这个抖音视频", "看一下这个抖音链接的视频信息"],
    },
    "douyin-video": {
        "category": "媒体处理",
        "summary": "获取抖音无水印视频，并可提取视频里的语音文案保存为文本。",
        "whenToUse": "需要保存抖音视频、整理视频口播内容，或批量提取抖音文案时使用。",
        "requirements": "需要有效的抖音分享链接；语音转文字质量取决于音频清晰度。",
        "examples": ["把这个抖音视频下载下来", "提取这个抖音视频里的文案"],
    },
    "douyin-video-summary": {
        "category": "媒体处理",
        "summary": "把抖音视频转成文字摘要：先提取音频和字幕，再整理成结构化总结。",
        "whenToUse": "你不想看完整视频，只想快速知道一个抖音视频讲了什么时使用。",
        "requirements": "依赖本地转写工具；长视频或音质差的视频会更慢、更不稳定。",
        "examples": ["总结这个抖音视频", "把这个抖音链接转成要点"],
    },
    "tiktok-captions": {
        "category": "媒体处理",
        "summary": "为 TikTok 短视频生成标题、字幕、脚本和发布文案。",
        "whenToUse": "要做 TikTok 视频内容、优化开头钩子、写字幕或准备发布文案时使用。",
        "requirements": "需要明确目标受众、视频主题和语气；不负责实际发布。",
        "examples": ["给这个 TikTok 视频写 caption", "帮我写一版 TikTok 开头钩子"],
    },
    "video-marketing": {
        "category": "设计体验",
        "summary": "规划短视频或长视频营销内容，包括选题、脚本、钩子和内容节奏。",
        "whenToUse": "需要做视频营销方案、短视频脚本、Reels/TikTok/YouTube 内容规划时使用。",
        "requirements": "需要产品、受众、平台和转化目标；它负责内容策略，不负责剪辑发布。",
        "examples": ["帮我写一个短视频营销脚本", "规划一周 TikTok 内容选题"],
    },
    "setup-pre-commit": {
        "category": "代码质量",
        "summary": "给前端/Node 项目配置 Husky、lint-staged、Prettier、类型检查和测试钩子。",
        "whenToUse": "想在提交前自动格式化、跑类型检查、跑测试，减少低级错误时使用。",
        "requirements": "适合有 package.json 的项目；会修改项目依赖和脚本。",
        "examples": ["给这个项目设置 pre-commit", "提交前自动跑 prettier 和 typecheck"],
    },
    "control-in-app-browser": {
        "category": "浏览器与桌面",
        "summary": "控制 Codex 内置浏览器，用于打开、检查和测试本地网页或外部网站。",
        "whenToUse": "需要验证 localhost 页面、截图、点击测试、读取页面状态时使用。",
        "requirements": "适合测试本地网页；涉及登录和敏感操作需要明确确认。",
        "examples": ["打开本地页面并检查手机布局"],
    },
    "control-chrome": {
        "category": "浏览器与桌面",
        "summary": "控制你的 Chrome 浏览器，适合需要复用真实登录态、扩展或当前标签页的任务。",
        "whenToUse": "目标网站只在你已登录的 Chrome 里可访问时使用。",
        "requirements": "不会静默读取密码或敏感数据；外部提交动作需要确认。",
        "examples": ["用我 Chrome 里登录的小红书页面查内容"],
    },
    "computer-use": {
        "category": "浏览器与桌面",
        "summary": "通过屏幕、鼠标和键盘操作本机 App，适合没有 API 的桌面任务。",
        "whenToUse": "需要点击本地应用、读窗口内容、操作系统 UI 时使用。",
        "requirements": "比 API 慢；涉及敏感输入需要你确认。",
        "examples": ["帮我在某个 Mac App 里改设置"],
    },
    "documents": {
        "category": "文档处理",
        "summary": "处理 Word 等文档文件，读取内容、修改结构或生成文档。",
        "whenToUse": "要分析、编辑或生成 DOCX 文档时使用。",
        "requirements": "需要本地文件路径或上传文件。",
        "examples": ["把这个 Word 改成正式报告格式"],
    },
    "pdf": {
        "category": "文档处理",
        "summary": "读取、解析和处理 PDF 文件。",
        "whenToUse": "需要提取 PDF 内容、截图页、分析排版或转写时使用。",
        "requirements": "扫描版 PDF 可能需要 OCR。",
        "examples": ["把这个 PDF 总结成 Markdown"],
    },
    "presentations": {
        "category": "文档处理",
        "summary": "处理 PPT/演示文稿，读取结构、生成幻灯片或整理大纲。",
        "whenToUse": "要改 PPT、生成提纲、提取演示内容时使用。",
        "requirements": "需要源文件或明确的演示目标。",
        "examples": ["把这个报告整理成 10 页 PPT 大纲"],
    },
    "spreadsheets": {
        "category": "文档处理",
        "summary": "处理 Excel/表格文件，读取数据、生成表、做简单分析。",
        "whenToUse": "需要查看 xlsx/csv、清洗数据或输出 Markdown 表格时使用。",
        "requirements": "复杂统计建模可能需要额外脚本。",
        "examples": ["把这个表格转成 Markdown 表"],
    },
    "template-creator": {
        "category": "创建与扩展",
        "summary": "创建可复用模板，用于文档、表格、幻灯片等生成场景。",
        "whenToUse": "你想把固定格式沉淀为模板时使用。",
        "requirements": "需要示例文件或目标版式说明。",
        "examples": ["把这份周报做成以后可复用的模板"],
    },
}

CLI_PROFILES = {
    "agent-reach": SKILL_PROFILES["agent-reach"],
    "markitdown": {
        "category": "文档处理",
        "summary": "Microsoft 的文件转 Markdown 工具，适合 PDF、Word、HTML、表格等格式转换。",
        "whenToUse": "你说“把这个文件转成 Markdown”时优先用它。",
        "requirements": "音视频文件需要 ffmpeg；普通文档不需要。",
        "examples": ["markitdown input.pdf -o output.md", "markitdown input.docx -o output.md"],
    },
    "gh": {
        "category": "开发协作",
        "summary": "GitHub 官方命令行工具，已授权后可搜索仓库、读 issue/PR、操作 GitHub。",
        "whenToUse": "需要查 GitHub 仓库、Issue、PR、Release 或私有仓库时使用。",
        "requirements": "当前已登录 GitHub CLI；权限来自 OAuth token。",
        "examples": ["gh search repos \"agent reach\" --limit 10", "gh issue list -R owner/repo"],
    },
    "opencli": {
        "category": "浏览器与桌面",
        "summary": "连接 Chrome 扩展，复用浏览器登录态读取小红书、Twitter、Reddit 等平台。",
        "whenToUse": "平台需要登录、但网页端已经在 Chrome 登录时使用。",
        "requirements": "Chrome 扩展要保持连接；目标网站需要你已登录。",
        "examples": ["opencli xiaohongshu search \"关键词\" -f yaml"],
    },
    "mcporter": {
        "category": "互联网调研",
        "summary": "MCP 工具路由器，可连接 Exa 等搜索后端。",
        "whenToUse": "需要更强的全网语义搜索后端时使用。",
        "requirements": "Exa 还需要执行配置命令并可能需要账号/API 权限。",
        "examples": ["mcporter config add exa https://mcp.exa.ai/mcp"],
    },
    "yt-dlp": {
        "category": "媒体处理",
        "summary": "视频信息和字幕提取工具，Agent Reach 的 YouTube 能力依赖它。",
        "whenToUse": "需要获取视频字幕、标题、元数据时使用。",
        "requirements": "YouTube 某些视频需要可用网络和 JS runtime；当前已配置 Node。",
        "examples": ["yt-dlp --write-sub --skip-download URL"],
    },
}


def load_catalog():
    if not CATALOG.exists():
        return {}
    try:
        return json.loads(CATALOG.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_catalog(catalog):
    DATA.mkdir(parents=True, exist_ok=True)
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")


def valid_hex_color(value):
    return bool(re.match(r"^#[0-9a-fA-F]{6}$", value or ""))


def category_colors(catalog):
    saved = catalog.get(CATALOG_CATEGORY_COLORS_KEY, {})
    colors = dict(DEFAULT_CATEGORY_COLORS)
    if isinstance(saved, dict):
        for category, color in saved.items():
            normalized = normalize_category(category)
            if valid_hex_color(color):
                colors[normalized] = color
    return colors


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    block = match.group(1)
    data = {}
    current_key = None
    current_lines = []
    for line in block.splitlines():
        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if key_match and not line.startswith(" "):
            if current_key:
                data[current_key] = "\n".join(current_lines).strip()
            current_key = key_match.group(1)
            value = key_match.group(2).strip()
            current_lines = [value] if value else []
        elif current_key:
            current_lines.append(line.strip())
    if current_key:
        data[current_key] = "\n".join(current_lines).strip()
    return data


def clean_description(value):
    if not value:
        return ""
    value = clean_scalar(value)
    value = re.sub(r"^>\s*", "", value.strip())
    value = re.sub(r"\n\s+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value[:900]


def clean_scalar(value):
    value = (value or "").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def infer_category(name, description, path="", kind="skill"):
    haystack = f"{name} {description} {path}".lower()
    rules = [
        ("设计体验", ["ui-ux", "design", "ux", "ui/ux"]),
        ("互联网调研", ["agent-reach", "search", "internet", "twitter", "reddit", "xiaohongshu", "github", "rss", "web url"]),
        ("文档处理", ["document", "pdf", "spreadsheet", "presentation", "markdown", "markitdown", "word", "excel", "slides"]),
        ("浏览器与桌面", ["browser", "chrome", "computer-use", "opencli"]),
        ("创建与扩展", ["creator", "create", "plugin", "skill"]),
        ("OpenAI", ["openai", "chatgpt", "api"]),
        ("媒体处理", ["image", "yt-dlp", "youtube", "audio", "video"]),
        ("开发协作", ["github", "gh", "code", "repo", "git"]),
    ]
    for category, words in rules:
        if any(word in haystack for word in words):
            return category
    return "其他" if kind == "skill" else "命令工具"


def skill_source(path):
    text = str(path)
    if "/.agents/skills/" in text:
        return "用户安装"
    if "/.cc-switch/skills/" in text:
        return "cc-switch"
    if "/.claude/skills/" in text or "/.config/claude/skills/" in text:
        return "Claude Code"
    if "/.hermes/skills/" in text or "/.config/hermes/skills/" in text:
        return "Hermes"
    if "/.github/skills/" in text:
        return "GitHub"
    if "/.codex/plugins/cache/" in text:
        parts = text.split("/.codex/plugins/cache/", 1)[1].split("/")
        return f"插件：{parts[0]}" if parts else "插件"
    if "/.codex/skills/.system/" in text:
        return "系统内置"
    if "/.codex/skills/" in text:
        return "本地安装"
    return "未知"


def profile_for(name, kind):
    profiles = CLI_PROFILES if kind == "cli" else SKILL_PROFILES
    return profiles.get(name, profiles.get(name.lower(), {}))


def mostly_english(value):
    letters = sum(ch.isascii() and ch.isalpha() for ch in value or "")
    chinese = sum("\u4e00" <= ch <= "\u9fff" for ch in value or "")
    return letters > max(30, chinese * 2)


def normalize_category(value):
    value = CATEGORY_ALIASES.get(value, value or "其他工具")
    return CATEGORY_GROUPS.get(value, value)


def enrich_item(item):
    profile = profile_for(item["name"], item["kind"])
    if profile:
        item["category"] = profile.get("category", item["category"])
        item["summary"] = profile.get("summary", item.get("description", ""))
        item["whenToUse"] = profile.get("whenToUse", "")
        item["requirements"] = profile.get("requirements", "")
        item["examples"] = profile.get("examples", [])
    else:
        if mostly_english(item.get("description", "")):
            item["summary"] = "暂未整理中文介绍；建议先根据 Skill 名称、分类和调用提示判断用途。"
        else:
            item["summary"] = item.get("description") or "暂未整理中文介绍；可以在备注里补充你的理解。"
        item["whenToUse"] = "当你的需求和这个条目的名称或说明匹配时使用。"
        item["requirements"] = "无额外记录。"
        item["examples"] = [item.get("callHint", "")]
    item["category"] = normalize_category(item["category"])
    item["source"] = SOURCE_ALIASES.get(item["source"], item["source"])
    return item


def scan_skills():
    items = []
    seen = set()
    for root, _label in SKILL_ROOTS:
        if not root.exists():
            continue
        for skill_file in root.rglob("SKILL.md"):
            if skill_file in seen:
                continue
            seen.add(skill_file)
            try:
                text = skill_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            fm = parse_frontmatter(text)
            folder_name = skill_file.parent.name
            name = clean_scalar(fm.get("name")) or folder_name
            description = clean_description(fm.get("description", ""))
            source = skill_source(skill_file)
            item_id = f"skill:{skill_file}"
            items.append(
                enrich_item({
                    "id": item_id,
                    "kind": "skill",
                    "name": name,
                    "source": source,
                    "category": infer_category(name, description, str(skill_file), "skill"),
                    "description": description,
                    "path": str(skill_file),
                    "folder": str(skill_file.parent),
                    "callHint": f"直接描述需求，或说：用 {name} ...",
                })
            )
    return items


def command_path(name):
    try:
        result = subprocess.run(["/usr/bin/env", "which", name], capture_output=True, text=True, timeout=4)
    except subprocess.SubprocessError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def command_version(name):
    candidates = [[name, "--version"], [name, "version"]]
    for cmd in candidates:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
        except (OSError, subprocess.SubprocessError):
            continue
        output = (result.stdout or result.stderr).strip()
        if output:
            return output.splitlines()[0][:160]
    return ""


def scan_cli_tools():
    items = []
    hints = {
        "agent-reach": "agent-reach doctor",
        "markitdown": "markitdown input.pdf -o output.md",
        "gh": "gh search repos \"query\" --limit 10",
        "opencli": "opencli xiaohongshu search \"关键词\" -f yaml",
        "mcporter": "mcporter config add exa https://mcp.exa.ai/mcp",
        "yt-dlp": "yt-dlp --write-sub --skip-download URL",
    }
    for name in CLI_TOOLS:
        path = command_path(name)
        if not path:
            continue
        profile = CLI_PROFILES.get(name, {})
        description = profile.get("summary", "")
        items.append(
            enrich_item({
                "id": f"cli:{name}",
                "kind": "cli",
                "name": name,
                "source": "命令行工具",
                "category": infer_category(name, description, path, "cli"),
                "description": description,
                "path": path,
                "folder": str(Path(path).parent),
                "version": command_version(name),
                "callHint": hints.get(name, name),
            })
        )
    return items


def merged_items():
    catalog = load_catalog()
    colors = category_colors(catalog)
    items = scan_skills() + scan_cli_tools()
    for item in items:
        saved = catalog.get(item["id"], {})
        item["autoCategory"] = item["category"]
        item["category"] = normalize_category(saved.get("category")) if saved.get("category") else item["category"]
        item["categoryColor"] = colors.get(item["category"], DEFAULT_CATEGORY_COLORS["其他工具"])
        item["notes"] = saved.get("notes", "")
        item["tags"] = saved.get("tags", [])
        item["favorite"] = bool(saved.get("favorite", False))
        item["hidden"] = bool(saved.get("hidden", False))
        item["customCallHint"] = saved.get("customCallHint", "")
    return sorted(items, key=lambda x: (not x["favorite"], x["category"].lower(), x["name"].lower()))


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        url_path = urlparse(path).path
        if url_path == "/":
            return str(STATIC / "index.html")
        if url_path.startswith("/static/"):
            return str(STATIC / url_path.removeprefix("/static/"))
        return str(STATIC / url_path.lstrip("/"))

    def json_response(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.json_response({"ok": True, "catalogPath": str(CATALOG), "skillRoots": [str(root) for root, _ in SKILL_ROOTS]})
            return
        if parsed.path == "/api/items":
            catalog = load_catalog()
            self.json_response({"items": merged_items(), "categoryColors": category_colors(catalog), "catalogPath": str(CATALOG)})
            return
        if parsed.path == "/api/open":
            target = parse_qs(parsed.query).get("path", [""])[0]
            if not target or not Path(target).exists():
                self.json_response({"error": "Path not found"}, 404)
                return
            subprocess.run(["open", "-R", target], check=False)
            self.json_response({"ok": True})
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/meta":
            body = self.read_json()
            item_id = body.get("id")
            if not item_id:
                self.json_response({"error": "Missing id"}, 400)
                return
            catalog = load_catalog()
            current = catalog.get(item_id, {})
            for key in ["category", "notes", "tags", "favorite", "hidden", "customCallHint"]:
                if key in body:
                    current[key] = body[key]
            catalog[item_id] = current
            save_catalog(catalog)
            self.json_response({"ok": True, "item": current})
            return
        if self.path == "/api/category-color":
            body = self.read_json()
            category = normalize_category(body.get("category", ""))
            color = body.get("color", "")
            if not category:
                self.json_response({"error": "Missing category"}, 400)
                return
            if not valid_hex_color(color):
                self.json_response({"error": "Invalid color"}, 400)
                return
            catalog = load_catalog()
            colors = catalog.get(CATALOG_CATEGORY_COLORS_KEY, {})
            if not isinstance(colors, dict):
                colors = {}
            colors[category] = color.lower()
            catalog[CATALOG_CATEGORY_COLORS_KEY] = colors
            save_catalog(catalog)
            self.json_response({"ok": True, "category": category, "color": color.lower()})
            return
        self.json_response({"error": "Not found"}, 404)


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    port = int(os.environ.get("PORT", "8787"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Skills Dashboard running at http://127.0.0.1:{port}")
    print(f"Catalog metadata: {CATALOG}")
    server.serve_forever()


if __name__ == "__main__":
    main()
