# Resume Matcher - AI 简历匹配评估系统

基于 Qwen 3.6 35B 大语言模型，自动评估 PDF 简历与岗位 JD 的匹配度，并按分数排序展示。

## 技术架构

```
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│   Frontend (React)   │────▶│  Backend (FastAPI)    │────▶│   vLLM (Qwen 3.6)   │
│  Vite + TailwindCSS  │◀────│  PDF解析 + LLM调用    │◀────│  localhost:11434     │
└──────────────────────┘     └──────────────────────┘     └──────────────────────┘
```

- **前端**: React 18 + Vite + TailwindCSS
- **后端**: Python FastAPI
- **PDF 解析**: PyMuPDF
- **LLM**: Qwen 3.6 35B (通过 vLLM 部署，OpenAI 兼容 API)

## 工作流程

1. 用户在前端输入岗位 JD 描述
2. 用户上传一份或多份 PDF 格式简历
3. 后端解析 PDF 提取文本
4. 后端将简历文本 + JD 发送到 vLLM 模型进行评估
5. 模型从技能、经验、教育、综合素质四个维度打分
6. 结果按综合匹配分数降序排列，展示在前端

## 快速启动

### 前置条件

- Python 3.10+
- Node.js 18+
- vLLM 已部署 Qwen 3.6 35B 模型，运行在 `http://localhost:11434`

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
python main.py
```

后端运行在 `http://localhost:8080`，API 文档: `http://localhost:8080/docs`

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 `http://localhost:5173`

### 3. 配置

修改 `backend/.env` 文件配置 vLLM 服务地址和模型名称：

```env
VLLM_BASE_URL=http://localhost:11434/v1
VLLM_MODEL_NAME=qwen3.6-35b
VLLM_API_KEY=EMPTY
```

## 项目结构

```
resume-matcher/
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── App.jsx           # 主应用组件
│   │   ├── main.jsx          # 入口
│   │   ├── index.css         # TailwindCSS 入口
│   │   └── components/
│   │       ├── JDInput.jsx   # JD 输入组件
│   │       ├── ResumeUpload.jsx  # 简历上传组件
│   │       └── ResultList.jsx    # 结果展示组件
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── backend/                   # FastAPI 后端
│   ├── main.py               # 主服务入口 + API 路由
│   ├── config.py             # 配置管理
│   ├── .env                  # 环境变量
│   ├── requirements.txt
│   └── services/
│       ├── pdf_parser.py     # PDF 文本提取
│       └── llm_service.py    # LLM 调用与评估
└── README.md
```

## API 接口

### POST /api/match

上传简历并进行匹配评估。

- **Content-Type**: `multipart/form-data`
- **参数**:
  - `files`: PDF 文件列表
  - `jd`: 岗位描述文本
- **返回**: 按匹配分数降序排列的评估结果列表
