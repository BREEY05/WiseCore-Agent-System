# WiseCore 智能体系统 (WiseCore Agent System)

基于 **本地大模型 (Ollama)** 和 **MCP (Model Context Protocol)** 构建的多模态 AI 智能体平台。

## 🎯 项目简介

**WiseCore** 是一个高度模块化、可扩展的智能体开发框架。它通过 MCP 协议标准，实现了大模型与本地/远程工具链的深度集成，旨在为用户提供一个安全、私密且功能强大的本地 AI 助手。

- **核心价值**：本地化部署确保数据隐私，MCP 架构提供无限的工具扩展性。
- **项目目标**：构建一个集对话、思考、工具调用、文档处理及多媒体生成于一体的智能系统。

---

## 📁 项目目录结构

为了保持项目整洁，我们将代码和资源进行了模块化整合：

```
my_agent/
├── WiseCore Agent System/                # 智能体核心层 (Agent Core)
│   ├── client.py             # MCP 客户端管理（协议连接与工具路由）
│   ├── memory.py             # 对话记忆持久化管理
│   ├── web_server.py         # FastAPI WebSocket 服务器
│   ├── static/               # 前端 UI 交互资源
│   └── data/                 # 核心数据（对话历史等）
├── skills_server/             # 技能服务层 (MCP Servers)
│   ├── skill_server.py       # 本地 MCP 技能服务器
│   └── skills/               # 技能插件库 (image_generator, docx, pdf 等)
├── tools/                     # 开发与调试工具
│   ├── probe_mcd.py          # 远程服务探测脚本
│   └── generate_pptx.js      # PPT 生成辅助脚本
├── docs/                      # 项目文档
│   ├── AGENT.md              # 智能体设计说明
│   ├── progress.md           # 开发进度记录
│   └── task_plan.md          # 任务规划文件
├── startup/                   # 启动与环境配置 (推荐)
│   ├── run.py                # 启动入口
│   ├── launcher.py           # 一键启动/环境检查脚本
│   ├── package.json          # Node.js 环境配置
│   └── package-lock.json     # Node.js 依赖锁定
├── requirements.txt           # Python 依赖清单
└── README.md                  # 本文档
```

---

## 🛠️ 技术栈

| 层级 | 技术选型 |
|------|---------|
| **AI 框架** | LangChain + LangGraph (状态机管理) |
| **模型部署** | Ollama (默认 qwen3:4b, 支持多模态 qwen3-vl) |
| **协议标准** | MCP (Model Context Protocol) |
| **通信层** | FastAPI + WebSocket (全异步实时双向通信) |
| **前端** | HTML5 + TailwindCSS + JavaScript (流式渲染) |
| **存储** | 本地 JSON 持久化 (Memory Manager) |

---

## 📊 系统架构

系统采用分层架构，确保各组件间的低耦合与高扩展性：

```
┌─────────────────────────────────────────────────────────┐
│                    前端交互层 (Web UI)                    │
│              流式对话界面 + 实时状态展示                   │
└─────────────────────────────────────────────────────────┘
                          ↕ WebSocket
┌─────────────────────────────────────────────────────────┐
│                  智能体核心层 (Agent Core)                │
│   - LangGraph 状态机管理                                 │
│   - MCP Client 多服务器连接 (Stdio/SSE)                  │
│   - 对话记忆持久化 (Memory Manager)                      │
└─────────────────────────────────────────────────────────┘
                          ↕ MCP Protocol
┌─────────────────────────────────────────────────────────┐
│                  工具服务层 (MCP Servers)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Local Skills │  │  GitHub MCP  │  │ McDonald's   │  │
│  │   Server     │  │   (Stdio)    │  │   (SSE)      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ 核心功能

### 1. 深度 MCP 集成
- **多协议支持**：同时兼容 `Stdio` (本地子进程) 和 `SSE` (远程流式) 两种 MCP 通信模式。
- **动态发现**：自动扫描并注册本地技能，支持热插拔。
- **已集成服务**：GitHub、McDonald's (远程)、本地文件系统。

### 2. 强大的技能库 (Skills)

**skills_server** 是本系统的核心技能服务层，提供了丰富的 MCP 技能插件：

#### 📁 skills_server 目录结构
```
skills_server/
├── skill_server.py          # 本地 MCP 技能服务器主程序
└── skills/                  # 技能插件库
    ├── article_illustration_generator/  # 文章插图生成器
    ├── docx/                # Word 文档处理技能
    ├── frontend_design/     # 前端设计技能
    ├── image-generator/     # 基础图片生成
    ├── imagen/              # Imagen 图片生成
    ├── knowledge_2_web/     # 知识库转网页
    └── manimgl_best_practices/  # ManimGL 数学动画
```

#### 🔧 已集成的技能

- ✨ **图像生成系列**：
  - `image_generator.py` - 集成字节跳动 Seedream API
  - `imagen/` - Google Imagen 图片生成
  - `article_illustration_generator/` - 专为文章生成插图
  
- 📄 **文档处理系列**：
  - `docx/` - Word 文档创建与编辑
  - `knowledge_2_web/` - 将知识库转换为网页
  
- 🎨 **设计与可视化**：
  - `frontend_design/` - 生产级 UI 组件生成
  - `manimgl_best_practices/` - 数学动画可视化（集成 3Blue1Brown 的 ManimGL）

所有技能都遵循 MCP 协议标准，支持动态发现和热插拔。

### 3. 智能对话体验
- **思考透明化**：通过 `<thought>` 标签展示 AI 的思考过程，前端支持实时折叠。
- **流式响应**：基于 WebSocket 实现毫秒级响应，支持打字机效果。
- **记忆管理**：自动保存对话上下文，支持会话断点续传。

---

## 🚀 快速开始

### 1. 环境准备
确保已安装 Python 3.10+ 和 Node.js。

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端/JS 工具依赖 (进入 startup 目录)
cd startup
npm install
```

### 2. 模型服务
下载并运行 [Ollama](https://ollama.com/)，拉取默认模型：
```bash
ollama pull qwen3:4b
```

### 3. 启动系统
运行一键启动脚本，它将自动检查环境并打开浏览器：
```bash
python startup/run.py
```
或使用：
```bash
python startup/launcher.py
```

---

## 🎓 后续优化方向

- [ ] **RAG 增强**：增加本地知识库支持，实现基于私有文档的问答。
- [ ] **多模态理解**：深度集成 Vision 模型，支持图片输入与分析。
- [ ] **可视化编排**：提供图形化界面，方便用户自定义智能体工作流。

---

## 📄 许可证
本项目仅供学习和研究使用。
