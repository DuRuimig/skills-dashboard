# Skills Dashboard

> 一个给 Codex、Claude Code、Hermes 和 Agent Skills 生态使用的本地 Skill 管理中枢。

如果你已经开始给 AI Agent 安装各种 Skills，你大概率会遇到同一个问题：

装得越多，越不知道自己到底装了什么。

`SKILL.md` 散落在不同目录里，名字看起来很像，描述有的很长、有的全英文、有的只适合特定工具。真正使用时，你还得靠记忆判断：

- 我现在有哪些 Skills？
- 这个 Skill 到底适合什么时候用？
- 它是 Codex 的，Claude Code 的，还是 Hermes 的？
- 常用 Skills 能不能收藏？
- 能不能按分类、颜色、备注整理？
- 后面装了新的 Skill，能不能自动扫出来？

**Skills Dashboard 想解决的就是这件事：把本地 Agent Skills 变成一个可浏览、可理解、可整理、可持续维护的能力中心。**

English summary: Skills Dashboard is a local web UI for discovering, browsing, categorizing, and managing Agent Skills across Codex, Claude Code, Hermes, cc-switch, and other compatible setups.

## 为什么做这个项目

Agent Skills 正在变成 AI 工作流里很重要的一层。

一个好的 Skill 不只是提示词，它可能包含流程、脚本、工具调用、参考资料和项目经验。随着 Skills 越装越多，管理体验会变得越来越重要。

现在的问题是：生态里已经有很多好 Skills，但缺少一个足够清晰的入口。

Skills Dashboard 的目标不是替代 Codex、Claude Code 或 Hermes，而是做它们旁边的一个本地控制台：

- 帮你看清楚本机已经安装了哪些 Skills
- 帮你理解每个 Skill 的用途和调用方式
- 帮你用分类、颜色、收藏、备注把 Skills 管起来
- 帮不同 Agent 工具之间形成一个统一的 Skill 目录视图

如果你也在沉淀自己的 AI 工作流，这个工具应该会很有用。

## 当前功能

- 自动扫描常见 Skill 目录
- 支持 Codex、Claude Code、Hermes、cc-switch、`~/.agents/skills`
- 支持自定义额外扫描路径
- 本地网页 UI，无需云端账号
- Skill 卡片视图和列表视图
- 分类筛选、搜索、收藏、隐藏
- 分类颜色自定义
- Skill 备注、标签、调用提示
- 响应式界面，支持桌面和移动端布局
- 本地保存元数据，不修改原始 Skill 文件

## 截图

截图和演示视频会在后续版本补充。当前版本已经可以直接安装和运行。

如果你愿意帮忙设计更好的产品展示图、录制演示视频，欢迎提 PR。

## 快速安装

克隆仓库：

```bash
git clone https://github.com/DuRuimig/skills-dashboard.git
cd skills-dashboard
```

安装到 Codex：

```bash
mkdir -p ~/.codex/skills
cp -R skills-dashboard ~/.codex/skills/
```

安装到 Claude Code：

```bash
mkdir -p ~/.claude/skills
cp -R skills-dashboard ~/.claude/skills/
```

安装到 Hermes：

```bash
mkdir -p ~/.hermes/skills
cp -R skills-dashboard ~/.hermes/skills/
```

然后对你的 Agent 说：

```text
Use skills-dashboard to open my Skill center.
```

或者中文：

```text
用 skills-dashboard 打开我的 Skill 中枢
```

## 手动启动

进入已安装的 `skills-dashboard` 目录：

```bash
python3 scripts/launch_dashboard.py --browser chrome
```

默认地址：

```text
http://127.0.0.1:8787/
```

如果端口被占用：

```bash
python3 scripts/launch_dashboard.py --port 8788 --browser chrome
```

## 扫描目录

默认会扫描：

```text
~/.agents/skills
~/.codex/skills
~/.codex/plugins/cache
~/.cc-switch/skills
~/.claude/skills
~/.config/claude/skills
~/.hermes/skills
~/.config/hermes/skills
./.agents/skills
./.codex/skills
./.claude/skills
./.hermes/skills
./.github/skills
```

添加自定义目录：

```bash
python3 scripts/launch_dashboard.py --extra-root /path/to/skills
```

或者使用环境变量：

```bash
export SKILLS_DASHBOARD_EXTRA_ROOTS="/path/a:/path/b"
```

## 隐私和安全

Skills Dashboard 是本地优先的工具。

- 服务只绑定到 `127.0.0.1`
- 不上传你的 Skill 列表
- 不修改原始 Skill 文件
- 不读取浏览器密码或账号信息
- 分类、颜色、备注等个人元数据只保存在本机

macOS 默认元数据位置：

```text
~/Library/Application Support/SkillsDashboard/catalog.json
```

Windows 和 Linux 会使用对应的系统应用数据目录。

你也可以自定义：

```bash
export SKILLS_DASHBOARD_DATA_DIR="/path/to/data"
```

## 路线图

我会持续维护这个项目。接下来计划做：

- 更准确的 Skill 自动分类
- 更好的中文/英文双语体验
- 一键安装、更新、删除 Skills
- Skill 版本检测
- GitHub Skill 仓库发现
- 团队共享 Skill 集合
- 配置同步和跨设备使用
- 更完整的移动端体验
- 更漂亮的默认主题和深色模式
- 更清晰的 Skill 评分、使用频率和推荐机制

这个项目还在早期，很多方向都值得一起探索。

## 适合谁使用

如果你是下面这些用户，可能会喜欢它：

- 正在使用 Codex、Claude Code、Hermes 或其他 Agent 工具
- 已经安装了很多 Skills，但缺少统一管理入口
- 想把自己的 AI 工作流沉淀成可复用 Skills
- 想给团队整理一套共享的 Agent Skills
- 想参与 Agent Skills 生态的基础工具建设

## 欢迎参与

我希望 Skills Dashboard 不只是一个个人小工具，而是一个大家都能用、也愿意一起完善的开源项目。

非常欢迎你：

- Star 这个项目，让更多使用 Agent Skills 的人看到它
- 提 issue 反馈你的使用场景和问题
- 提 PR 优化 UI、交互、扫描规则或安装体验
- 分享你正在使用的 Skills 目录结构
- 帮忙补充 Codex、Claude Code、Hermes 之外的适配路径
- 帮忙设计图标、截图、演示视频和文档

如果你觉得 Agent Skills 会成为未来 AI 工作流的重要组成部分，欢迎一起把它的管理体验做好。

## Star History

如果这个项目对你有帮助，欢迎点一个 Star。它会让我知道这个方向值得继续投入，也能让更多人发现这个工具。

项目地址：

```text
https://github.com/DuRuimig/skills-dashboard
```

## License

MIT
