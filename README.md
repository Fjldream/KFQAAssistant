# KingIAsk

KingIAsk 是一个面向 KF 产品使用手册的企业级 RAG 问答助手。它会从 `data/help` 加载手册文档，构建本地 Chroma 向量库，再通过 DeepSeek 生成带资料来源和相关图片的回答。

当前版本优先保证本地轻量可运行，同时保留企业级产品需要的接口、配置、健康检查、评估和压测入口。

## 已支持能力

- 加载 Markdown 和 HTML 手册文档。
- 保留文档中的图片位置，并在回答来源中返回相关图片路径。
- 使用 `BAAI/bge-small-zh-v1.5` 在本地生成 embedding。
- embedding 模型按需懒加载，无变化索引检查不会加载重量级模型。
- 使用 Chroma 持久化向量库，默认目录为 `storage/chroma`。
- 使用 DeepSeek 生成最终回答。
- 支持向量检索和关键词召回混合排序。
- 支持资料来源去重、证据编号、图片数量限制和拒答保护。
- 提供 FastAPI 问答接口、KingIAsk Vue 前端和 Streamlit 轻量 Demo 页面。
- 提供索引状态、就绪检查、评估脚本和轻量压测脚本。

## 目录说明

```text
backend/          FastAPI RAG 后端，包含 API、RAG 核心代码、脚本和测试
frontend/            KingIAsk 前端工作台（Apple 风格，推荐）
frontend-legacy/  旧版 KingIAsk Vue 前端工作台（已弃用，仅存档）
data/             KF 产品手册原始文档，本地放置，不提交仓库
storage/          Chroma 向量库和增量索引清单，本地生成，不提交仓库
docs/             本地学习和设计文档，不提交仓库
.env.example      可提交的环境变量样例
.env              本地真实配置，不提交仓库
```

## 环境准备

建议使用独立 conda 环境，避免污染 base 环境。

```bash
conda create -n kf-rag python=3.11 -y
conda activate kf-rag
cd backend
pip install -r requirements.txt
cd ..
cp .env.example .env
```

编辑 `.env`，至少填写：

```text
DEEPSEEK_API_KEY=你的 DeepSeek API Key
```

第一次构建索引时会加载 embedding 模型。如果本机没有缓存，需要能访问 HuggingFace 或提前准备好模型缓存。

前端使用 Vue 3、Vite 和 npm。进入 `frontend/` 后安装依赖：

```bash
cd front
npm install
```

如果你习惯 pnpm，也可以使用 `pnpm install` 和 `pnpm run dev`；本项目新前端默认使用 `npm`。

## 本地完整启动顺序

第一次运行时，先准备手册和索引：

```bash
mkdir -p data/help storage/chroma storage/processed
```

把 KF 手册放入：

```text
data/help/
```

然后构建向量索引：

```bash
cd backend
python -m scripts.build_index
```

索引构建完成后，启动后端 API：

```bash
cd backend
uvicorn app.main:app --reload
```

再启动前端：

```bash
cd frontend
pnpm run dev
```

浏览器打开：

```text
http://127.0.0.1:5173
```

## 关键配置

`.env.example` 已列出项目用到的配置。常用配置如下：

```text
APP_ENV=local
DISABLE_AUTH=true
APP_API_KEY=
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173

DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_TIMEOUT_SECONDS=60

EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5
DATA_DIR=data/help
CHROMA_PERSIST_DIR=storage/chroma
INDEX_MANIFEST_PATH=storage/processed/index_manifest.json
CHUNK_SIZE=700
CHUNK_OVERLAP=100

TOP_K=5
MAX_IMAGES_PER_SOURCE=5
MAX_IMAGES_PER_ANSWER=8
KF_RAG_API_URL=http://127.0.0.1:8000/api/chat
```

`TOP_K` 表示每次问答检索多少个相关 chunk。值越大，可用资料越多，但大模型上下文更长、速度可能更慢。

`MAX_IMAGES_PER_SOURCE` 控制每个来源最多返回多少张图片；`MAX_IMAGES_PER_ANSWER` 控制一次回答最多返回多少张图片。

`CHUNK_SIZE` 是每个知识片段的目标字符数，`CHUNK_OVERLAP` 是相邻片段的重叠字符数。必须满足 `0 <= CHUNK_OVERLAP < CHUNK_SIZE`。

## 准备手册数据

把 KF 产品手册放到：

```text
data/help/
```

`data/` 已在 `.gitignore` 中忽略，手册文件不会被提交到远程仓库。

如果后续手册更新，只需要重新运行 `python -m scripts.build_index`。系统会对比文档哈希，只处理新增、修改和删除的文件。

## 构建向量索引

```bash
cd backend
python -m scripts.build_index
```

构建流程是：

```text
扫描 data/help 并计算 SHA-256
  -> 对比 storage/processed/index_manifest.json
  -> 只加载新增或修改的文档
  -> 清洗、保留图片位置并切分
  -> 只为变化 chunks 生成 embedding
  -> 同步更新 Chroma 和索引清单
```

服务启动不会自动重新 embedding。`python -m scripts.build_index` 默认执行增量更新：内容没有变化的文档会直接跳过，不调用 embedding，也不会重写 manifest；新增、修改和删除的文档会同步到 Chroma。

从不带 manifest 的旧版本第一次升级运行时，系统会自动执行一次全量重建来建立基线。以后再次运行就是增量更新。修改了 embedding 模型或分块规则时，使用下面的命令强制全量重建：

```bash
cd backend
python -m scripts.build_index --full
```

全量重建开始前会写入恢复标记。若 embedding 或 Chroma 写入中途失败，下一次默认构建会自动再次执行全量恢复，不会被旧 manifest 误判为“文档没有变化”。如果 `data/help` 不存在或没有可索引文档，构建会直接终止，不修改已有向量库，避免服务器挂载错误清空知识库。

manifest 同时保存索引配置指纹。embedding 模型、`CHUNK_SIZE`、`CHUNK_OVERLAP` 或内部文档处理版本变化时，系统会自动执行一次全量重建；配置不变时继续复用增量索引。旧版本 manifest 没有指纹时也会自动完成一次升级，无需手动删除向量库。

## 启动 API 服务

开发环境推荐：

```bash
cd backend
uvicorn app.main:app --reload
```

也可以显式指定地址和端口：

```bash
cd backend
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

接口地址：

```text
http://127.0.0.1:8000
```

后端还会把 `DATA_DIR` 中的手册静态资源挂载到：

```text
http://127.0.0.1:8000/manuals/<手册内相对路径>
```

问答接口返回的图片路径仍然保持为手册相对路径，例如 `html/xxx/1.png`。KingIAsk 前端会自动把它转换为 `/manuals/html/xxx/1.png`，所以用户点击证据图片时可以直接预览原始手册截图。

## 启动 KingIAsk 前端

先启动 API 服务，再运行：

```bash
cd front
npm install
npm run dev
```

默认访问地址：

```text
http://127.0.0.1:5174
```

如果后端地址不是 `http://127.0.0.1:8000`，可以在前端页面右上角设置里修改 API 地址。前端会把设置保存到浏览器本地存储，刷新页面后继续复用。

如果页面显示“后端未连接”，先确认后端服务已经启动，并检查 `.env` 中的 `CORS_ALLOWED_ORIGINS` 是否包含当前前端地址，例如 `http://127.0.0.1:5174`。

> 旧版前端已更名为 `frontend-legacy/`，仅作存档，不再维护。

## 使用 Docker Compose 部署

服务器上建议使用 Docker Compose 固定运行环境。先准备配置和目录：

```bash
cp .env.example .env
mkdir -p data/help storage/chroma storage/processed
```

把 KF 手册放入：

```text
data/help/
```

生产环境建议在 `.env` 中至少设置：

```text
APP_ENV=production
DISABLE_AUTH=false
APP_API_KEY=自定义内部访问密钥
DEEPSEEK_API_KEY=生产可用的 DeepSeek Key
DATA_DIR=data/help
CHROMA_PERSIST_DIR=storage/chroma
INDEX_MANIFEST_PATH=storage/processed/index_manifest.json
```

构建镜像：

```bash
docker compose build
```

`docker-compose.yml` 会使用 `./backend` 作为后端镜像构建上下文，实际读取的是 `backend/Dockerfile` 和 `backend/.dockerignore`。

第一次部署或手册更新后，先构建向量索引：

```bash
docker compose run --rm kf-rag-api python -m scripts.build_index
```

启动服务：

```bash
docker compose up -d
```

查看日志：

```bash
docker compose logs -f kf-rag-api
```

停止服务：

```bash
docker compose down
```

`docker-compose.yml` 默认挂载：

```text
./data/help -> /app/data/help:ro
./storage   -> /app/storage
```

手册目录用只读挂载，整个 `storage` 目录用可写挂载，让 Chroma 和增量索引清单一起持久化。这样升级镜像时，手册和索引数据仍然留在服务器磁盘上。

## 健康检查和就绪检查

存活检查只判断服务进程是否正常：

```bash
curl http://127.0.0.1:8000/api/health
```

预期返回：

```json
{"status":"ok"}
```

就绪检查判断系统是否具备真实问答条件：

```bash
curl http://127.0.0.1:8000/api/health/ready
```

它会检查：

- `DEEPSEEK_API_KEY` 是否配置。
- 生产环境是否关闭了免认证。
- 向量库索引是否已经构建。

如果未就绪，会返回 `503` 和 `issues` 列表，按提示处理即可。

## 查看索引状态

```bash
curl http://127.0.0.1:8000/api/index/status
```

返回示例：

```json
{
  "status": "ready",
  "chunks": 6291,
  "documents": 2275,
  "last_built_at": "2026-07-21T02:00:00+00:00",
  "index_signature": "当前索引配置指纹",
  "current_signature": "当前运行配置指纹",
  "config_matches": true,
  "rebuild_pending": false,
  "persist_dir": "storage/chroma",
  "manifest_path": "storage/processed/index_manifest.json",
  "issue": null
}
```

`last_built_at` 来自 manifest 的最后修改时间。无变化的增量检查不会刷新它，因此它表示最近一次真实索引更新，而不是最近一次执行命令的时间。

`status` 可能是：

- `ready`：向量库非空，manifest 与当前 embedding、分块配置一致，可以正常问答。
- `empty`：向量库为空，需要先构建索引。
- `stale`：已有索引与当前配置不一致，需要重新构建。
- `rebuild_required`：检测到上一次全量重建中断，需要再次构建以恢复完整索引。
- `error`：manifest 损坏，查看 `issue` 并执行全量重建。

手册更新后，可以通过接口执行默认增量更新：

```bash
curl -X POST "http://127.0.0.1:8000/api/index/rebuild"
```

修改 embedding 模型或分块规则后，可以强制全量重建：

```bash
curl -X POST "http://127.0.0.1:8000/api/index/rebuild?full=true"
```

接口会返回 `added_documents`、`modified_documents`、`deleted_documents`、`skipped_documents`、`written_chunks` 和 `total_chunks`。

同一服务进程一次只允许一个索引任务。已有任务运行时，重复请求会返回 `409`；当前 Docker 配置使用单 Uvicorn 进程，多 worker 或多副本部署需要额外配置跨进程索引锁。

## 调用问答接口

本地默认 `DISABLE_AUTH=true`，可以直接调用：

```bash
curl -X POST "http://127.0.0.1:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"question":"如何创建采集工程？"}'
```

返回结构：

```json
{
  "answer": "回答内容",
  "sources": [
    {
      "title": "来源标题",
      "source_path": "html/...",
      "snippet": "命中的手册片段",
      "evidence_ids": ["资料 1"],
      "images": ["html/.../1.png"],
      "score": 0.5
    }
  ]
}
```

如果手册中没有可靠依据，系统会返回固定拒答：

```json
{
  "answer": "手册中没有找到相关说明。",
  "sources": []
}
```

## 使用 Postman 测试

请求方式：

```text
POST http://127.0.0.1:8000/api/chat
```

Headers：

```text
Content-Type: application/json
```

Body 选择 `raw` 和 `JSON`：

```json
{
  "question": "如何创建采集工程？"
}
```

如果开启了接口认证，还需要增加：

```text
x-api-key: 你的 APP_API_KEY
```

## 启动 Demo 页面

Streamlit Demo 是轻量验证页面，正式体验建议优先使用 KingIAsk 前端。先启动 API 服务，再运行：

```bash
cd backend
streamlit run demo/streamlit_app.py
```

默认 Demo 会调用：

```text
http://127.0.0.1:8000/api/chat
```

如果 API 地址不同，可以在 `.env` 中修改：

```text
KF_RAG_API_URL=http://你的服务地址/api/chat
```

## 命令行问答

```bash
cd backend
python -m scripts.ask "页面编辑器主要包括哪些区域？"
```

这个脚本适合不打开 Demo 时快速验证问答效果。

## RAG 效果评估

评估集位于：

```text
backend/tests/eval_questions.json
```

运行评估：

```bash
cd backend
python -m scripts.evaluate
python -m scripts.evaluate --output ../storage/reports/evaluation.json
```

评估脚本会检查回答关键词、来源关键词、拒答行为和图片返回数量，并输出总通过率以及各规则通过率。它不是最终人工验收标准，但能快速发现检索跑偏、回答缺关键点、该拒答时没有拒答等问题。存在失败题目时命令返回非零退出码，适合后续接入 CI；`--output` 可以保存结构化 JSON 报告。

## 检索调试

如果某个问题回答不好，先看检索层找到了哪些 chunk：

```bash
python -m scripts.inspect_retrieval "如何创建采集工程？" --top-k 5
```

这个脚本不会调用大模型，适合定位问题是在“资料没找对”，还是“资料找对了但回答生成不好”。

## 轻量压测

启动 API 后运行：

```bash
python -m scripts.load_test -n 10 -c 2
python -m scripts.load_test -n 5 -c 1 --output ../storage/reports/load-test.json
```

参数含义：

- `-n`：总请求数。
- `-c`：并发数。
- `--question`：压测使用的问题。
- `--url`：问答接口地址，默认读取 `KF_RAG_API_URL`。
- `--timeout`：单请求超时时间，单位为秒。
- `--api-key`：可选的后端 API Key，通过 `X-API-Key` 请求头传递。
- `--output`：可选的 JSON 报告输出路径，不保存 API Key。

它会输出成功数、失败数、成功率、平均耗时、P50/P95/P99 耗时、状态码分布和吞吐量。性能测试会调用真实问答接口，可能产生 DeepSeek 费用，建议先用少量请求做冒烟测试。

## 生产环境建议配置

部署到公司服务器时，建议至少调整：

```text
APP_ENV=production
DISABLE_AUTH=false
APP_API_KEY=自定义内部访问密钥
DEEPSEEK_API_KEY=生产可用的 DeepSeek Key
CHROMA_PERSIST_DIR=/data/kf-rag/chroma
INDEX_MANIFEST_PATH=/data/kf-rag/processed/index_manifest.json
DATA_DIR=/data/kf-rag/help
```

生产调用接口时需要带请求头：

```text
x-api-key: 自定义内部访问密钥
```

建议把 `data/help` 和整个 `storage` 挂载到服务器持久化目录，避免服务升级或容器重建后丢失手册、向量库和增量索引清单。

## 安全说明

- 不要提交 `.env`。
- 不要把真实 API Key 写进 README、测试或日志。
- `data/` 和 `storage/` 默认不提交仓库。
- 生产环境不要使用 `DISABLE_AUTH=true`。
- DeepSeek API 会收到用户问题和检索出来的手册片段。

## 常见问题

### 每次启动都会重新 embedding 吗？

不会。服务启动时只会读取已有的 Chroma 向量库。重新运行 `python -m scripts.build_index` 或调用索引接口时，也只会 embedding 新增或修改的文档；未变化文档直接复用已有向量，而且不会加载本地 embedding 模型。只有真正写入变化 chunks、执行向量检索，或传入 `--full`、`full=true` 时才会按需加载模型。

### 为什么有些回答没有图片？

图片是绑定在命中的 chunk 上的。如果检索命中的 chunk 附近没有图片，回答就不会返回图片。系统不会为了展示图片而返回无关截图。

### `top_k=5` 是什么意思？

表示每次从知识库中选出 5 个最相关的 chunk 交给大模型。它影响资料覆盖范围、回答质量、速度和 token 消耗。

### 就绪检查返回 `not_ready` 怎么办？

查看 `issues` 字段。常见原因是没有填 `DEEPSEEK_API_KEY`、没有构建索引，或生产环境还开着 `DISABLE_AUTH=true`。
