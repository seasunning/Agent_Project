# SD Multi Agents System

一个基于 `FastAPI + Vue 3` 的多阶段软件开发辅助系统，当前已实现：

- Phase 2：需求智能分析
- Phase 3：设计方案自动生成
- Phase 4：代码原型自动生成

前端负责交互展示，后端负责调用 DeepSeek 模型完成结构化分析、设计生成与代码原型生成。

---

## 目录结构

```text
SD_Muilt_Agents_System/
├─ backend/     # FastAPI 后端
├─ frontend/    # Vue 3 + Vite 前端
└─ test/        # 一些调试脚本与输出样例
```

---

## 环境要求

建议环境：

- Python 3.10+
- Node.js 18+
- npm 9+

---

## 一、启动后端

### 1. 进入后端目录

```bash
cd backend
```

### 2. 创建虚拟环境

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows CMD：

```bat
python -m venv .venv
.\.venv\Scripts\activate.bat
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

当前后端依赖来自 `backend/requirements.txt`：

- `fastapi`
- `uvicorn[standard]`
- `httpx`
- `pydantic`
- `pydantic-settings`
- `python-dotenv`
- `requests`

### 4. 配置环境变量

后端通过 `backend/.env` 读取配置。

你至少需要确认这些变量：

```env
APP_NAME=SD Multi Agents System
APP_ENV=development
API_PREFIX=/api/v1
DEEPSEEK_API_KEY=你的 DeepSeek Key
DEEPSEEK_BASE_URL=https://api.deepseek.com/chat/completions
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=120
```

> 注意：请不要把真实的 `DEEPSEEK_API_KEY` 提交到公开仓库。

### 5. 启动后端服务

在 `backend` 目录执行：

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 6. 访问后端

启动成功后可访问：

- 根地址：`http://127.0.0.1:8000/`
- Swagger 文档：`http://127.0.0.1:8000/docs`
- API 前缀：`http://127.0.0.1:8000/api/v1`

---

## 二、启动前端

### 1. 进入前端目录

```bash
cd frontend
```

### 2. 安装依赖

```bash
npm install
```

### 3. 配置前端环境变量

前端通过 `frontend/.env` 读取后端地址。

默认配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

如果你的后端端口或地址变了，这里也要同步修改。

### 4. 启动前端开发服务

```bash
npm run dev
```

### 5. 访问前端

Vite 启动后，终端会输出访问地址，通常类似：

- `http://127.0.0.1:5173/`

---

## 三、推荐启动顺序

建议按下面顺序启动：

1. 先启动后端
2. 确认 `http://127.0.0.1:8000/docs` 可打开
3. 再启动前端
4. 打开前端页面开始使用

---

## 四、使用流程

### Phase 2：需求分析

进入：`/requirements`

可完成：

- 输入原始需求
- 使用快速 / 深度模式分析
- 查看结构化需求结果
- 编辑需求结果
- 导出 JSON / Markdown

### Phase 3：设计生成

进入：`/design`

可完成：

- 基于需求结果生成设计方案
- 查看模块、接口、实体与 Mermaid 图
- 编辑设计结果
- 导出 JSON / Markdown
- 复制 Mermaid

### Phase 4：代码原型生成

进入：`/codegen`

可完成：

- 基于设计结果生成代码原型
- 查看项目摘要、技术栈、文件树
- 查看关键源码文件
- 复制文件树与代码片段

---

## 五、常见问题

### 1. 前端报 `Failed to resolve import "mermaid"`

在 `frontend` 目录重新安装依赖：

```bash
npm install
```

然后重新启动前端：

```bash
npm run dev
```

### 2. 后端启动时报缺少 `DEEPSEEK_API_KEY`

说明后端没有正确读取 `backend/.env`，请检查：

- `backend/.env` 是否存在
- `DEEPSEEK_API_KEY` 是否已填写
- 你是否在 `backend` 目录下启动 `uvicorn`

### 3. 前端能打开，但点击生成失败

通常检查这几项：

- 后端是否已启动
- `VITE_API_BASE_URL` 是否正确
- DeepSeek Key 是否有效
- 网络是否能访问 DeepSeek 接口

---

## 六、开发命令速查

### 后端

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

---

## 七、后续建议

如果你准备继续推进，可以下一步做：

- Phase 4 结果一键写入工作区文件
- 文件树 + 代码预览器
- ZIP 导出
- Phase 5：多智能体编排 / LangGraph 工作流
