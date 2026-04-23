# Resume Matcher - AI 简历匹配评估系统

基于大语言模型（LLM），自动评估 PDF 简历与岗位 JD 的匹配度，支持多维度评分、排序展示及一键生成面试问题。

## 功能特性

- **智能匹配评估** — 从技能、经验、教育背景、综合素质四个维度对简历进行打分，给出优势/不足分析和综合总结
- **批量上传** — 支持同时上传多份 PDF 简历，也支持上传 ZIP / TAR.GZ 压缩包（自动解压提取其中的 PDF）
- **候选人识别** — 自动从简历文本中提取候选人姓名，以人名而非文件名展示结果
- **面试问题生成** — 针对每位候选人，一键生成 10 个针对性面试问题（含考察意图、参考答案），支持流式逐条展示
- **实时反馈** — 上传与 AI 评估全程进度可视化

## 技术架构

```
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│   Frontend (React)   │────▶│  Backend (FastAPI)    │────▶│   LLM Service        │
│  Vite + TailwindCSS  │◀────│  PDF解析 + LLM调用    │◀────│  OpenAI 兼容 API     │
└──────────────────────┘     └──────────────────────┘     └──────────────────────┘
        :5173                       :8080                    (可配置地址)
```

| 层级 | 技术选型 |
|------|----------|
| 前端 | React 18 + Vite 6 + TailwindCSS 3 + Axios + Lucide Icons |
| 后端 | Python 3.10+ / FastAPI / Uvicorn |
| PDF 解析 | PyMuPDF (fitz) |
| 压缩包支持 | zipfile / tarfile（标准库） |
| LLM 调用 | OpenAI Python SDK（兼容任何 OpenAI API 格式的服务） |

## 工作流程

1. 用户在前端输入岗位描述（JD）
2. 上传一份或多份 PDF 简历（也可上传包含多份 PDF 的压缩包）
3. 后端解析 PDF / 压缩包，提取简历文本并自动识别候选人姓名
4. 后端将每份简历文本与 JD 并发发送给 LLM 进行评估
5. LLM 从四个维度打分，返回结构化评估结果
6. 结果按综合匹配分数降序排列，展示在前端
7. 用户可对感兴趣的候选人一键生成针对性面试问题（流式返回）

## 快速启动

### 前置条件

- **Python** 3.10 或更高版本
- **Node.js** 18 或更高版本（附带 npm）
- **LLM 服务** — 任何提供 OpenAI 兼容 API 的大模型推理服务（如 vLLM、Ollama、OpenAI 官方 API 等）

### 第一步：克隆项目

```bash
git clone <仓库地址>
cd resume-matcher
```

### 第二步：配置 LLM 服务

在 `backend/` 目录下创建 `.env` 文件（如果尚不存在），配置 LLM 相关参数：

```bash
cp backend/.env.example backend/.env   # 如有示例文件可直接复制
```

编辑 `backend/.env`，根据你实际使用的 LLM 服务填写以下配置：

```env
# LLM 服务地址（需提供 OpenAI 兼容的 /v1/chat/completions 接口）
VLLM_BASE_URL=http://localhost:11434/v1

# 模型名称（需与 LLM 服务中部署的模型名一致）
VLLM_MODEL_NAME=qwen

# API 密钥（本地部署通常无需认证，填 EMPTY 即可；使用 OpenAI 等云服务需填真实 Key）
VLLM_API_KEY=EMPTY

# LLM 单次请求最大 token 数（默认 8192，可根据模型能力调整）
LLM_MAX_TOKENS=8192

# 最大同时处理简历数（默认 20）
MAX_UPLOAD_FILES=20

# 单个 PDF 文件大小上限，单位 MB（默认 10）
MAX_FILE_SIZE_MB=10
```

> **提示**：以上配置项均有默认值，如果你的 LLM 服务运行在本地默认端口，可以只修改 `VLLM_MODEL_NAME` 为你部署的模型名称即可。

### 第三步：启动后端

```bash
# 进入后端目录
cd backend

# 安装 Python 依赖（建议使用虚拟环境）
pip install -r requirements.txt

# 启动后端服务
python main.py
```

启动成功后你将看到：
```
INFO:     Uvicorn running on http://0.0.0.0:8080
```

- 后端服务地址：`http://localhost:8080`
- API 交互文档：`http://localhost:8080/docs`

### 第四步：启动前端

打开**另一个终端窗口**：

```bash
# 进入前端目录
cd frontend

# 安装前端依赖（仅首次启动需要）
npm install

# 启动开发服务器
npm run dev
```

启动成功后你将看到：
```
VITE v6.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

### 第五步：开始使用

在浏览器中访问 **http://localhost:5173**，即可：

1. 在左侧文本框中粘贴岗位描述（JD）
2. 在右侧区域上传 PDF 简历文件（支持多选）或压缩包
3. 点击「开始匹配」，等待 AI 评估完成
4. 查看各候选人的匹配评分与详情
5. 展开某位候选人，点击「生成面试问题」获取针对性面试题

## 项目结构

```
resume-matcher/
├── frontend/                      # React 前端
│   ├── src/
│   │   ├── App.jsx               # 主应用组件（状态管理、API 调用）
│   │   ├── main.jsx              # 应用入口
│   │   ├── index.css             # TailwindCSS 全局样式
│   │   └── components/
│   │       ├── JDInput.jsx       # 岗位描述输入组件
│   │       ├── ResumeUpload.jsx  # 简历上传组件（支持拖拽）
│   │       └── ResultList.jsx    # 结果展示组件（评分、面试问题）
│   ├── package.json
│   ├── vite.config.js            # Vite 配置（含 API 代理）
│   └── tailwind.config.js
│
├── backend/                       # FastAPI 后端
│   ├── main.py                   # 主服务入口 + API 路由
│   ├── config.py                 # 配置管理（从 .env 读取）
│   ├── .env                      # 环境变量配置（需自行创建，已 gitignore）
│   ├── requirements.txt          # Python 依赖
│   ├── prompts/                  # LLM 提示词模板
│   │   ├── system.md             # 评估系统提示词
│   │   ├── user.md               # 评估用户提示词
│   │   └── interview_questions.md  # 面试问题生成提示词
│   ├── schemas/                  # Pydantic 数据模型
│   │   ├── resume.py             # 简历匹配结果模型
│   │   └── interview.py          # 面试问题模型
│   ├── services/                 # 核心业务逻辑
│   │   ├── pdf_parser.py         # PDF 文本提取 + 候选人姓名识别
│   │   ├── archive_parser.py     # 压缩包解析（ZIP/TAR）
│   │   └── llm_service.py        # LLM 调用（评估 + 面试问题生成）
│   └── utils/                    # 工具函数
│       ├── json_parser.py        # JSON 提取与流式解析
│       └── prompt_loader.py      # 提示词模板加载
│
└── README.md
```

## API 接口

启动后端后，可访问 `http://localhost:8080/docs` 查看完整的 Swagger 交互文档。以下为主要接口说明：

### POST /api/match

上传简历并进行匹配评估。

- **Content-Type**: `multipart/form-data`
- **参数**:
  - `files` — PDF 文件或压缩包（ZIP/TAR.GZ），支持多文件
  - `jd` — 岗位描述文本
- **返回**: 按综合匹配分数降序排列的评估结果列表，每项包含：
  - `candidate_name` — 候选人姓名（自动提取）
  - `filename` — 原始文件名
  - `overall_score` — 综合分数
  - `skill_score` / `experience_score` / `education_score` / `soft_skill_score` — 四维分数
  - `strengths` / `weaknesses` — 优势与不足
  - `summary` — 综合评价

### POST /api/interview-questions-stream

根据候选人简历流式生成面试问题（SSE）。

- **Content-Type**: `application/json`
- **参数**:
  - `resume_text` — 简历文本内容
  - `jd` — 岗位描述文本
- **返回**: Server-Sent Events 流，每个事件为一个面试问题 JSON 对象，包含 `id`、`question`、`intent`、`category`、`reference_answer`

### GET /api/health

健康检查接口，返回 `{"status": "ok"}`。

## 常见问题

**Q: 支持哪些 LLM 服务？**

任何提供 OpenAI 兼容 `/v1/chat/completions` 接口的服务均可使用，包括但不限于：
- vLLM
- Ollama
- OpenAI 官方 API
- Azure OpenAI
- 各类 LLM API 转发网关（如 OneAPI）

只需在 `.env` 中正确配置 `VLLM_BASE_URL`、`VLLM_MODEL_NAME` 和 `VLLM_API_KEY` 即可。

**Q: 请求超时怎么办？**

大模型推理耗时较长属于正常现象，前端默认超时时间为 5 分钟。如果仍然超时，请检查 LLM 服务是否正常运行，或适当减少同时上传的简历数量。

**Q: 上传压缩包有什么要求？**

支持 ZIP、TAR、TAR.GZ、TGZ、TAR.BZ2 格式。压缩包内的 PDF 文件会被自动提取和解析，非 PDF 文件将被跳过。
