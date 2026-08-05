# KingIAsk 运行命令速查

这份文档只放常用命令，方便本地开发、测试、构建索引、接口验证和部署排查。

项目根目录：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant"
```

## 1. Conda 环境

创建环境：

```bash
conda create -n kf-rag python=3.11 -y
```

激活环境：

```bash
conda activate kf-rag
```

安装后端依赖：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/backend"
pip install -r requirements.txt
```

## 2. 环境变量

复制环境变量模板：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant"
cp .env.example .env
```

然后编辑 `.env`，至少配置：

```text
DEEPSEEK_API_KEY=你的 DeepSeek API Key
```

本地开发常用配置：

```text
APP_ENV=local
DISABLE_AUTH=true
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5174,http://localhost:5174
DATA_DIR=data/help
CHROMA_PERSIST_DIR=storage/chroma
INDEX_MANIFEST_PATH=storage/processed/index_manifest.json
EVALUATION_DB_PATH=storage/evaluation/kingiask_eval.db
EVALUATION_CASES_PATH=backend/evaluation_cases/eval_questions.json
EVALUATION_DIALOGUES_PATH=backend/evaluation_cases/eval_dialogues.json
```

## 3. 准备手册目录

创建数据目录：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant"
mkdir -p data/help storage/chroma storage/processed
```

把 KF 产品手册放到：

```text
data/help/
```

## 4. 构建向量索引

默认增量构建：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/backend"
conda activate kf-rag
python -m scripts.build_index
```

强制全量重建：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/backend"
conda activate kf-rag
python -m scripts.build_index --full
```

说明：服务启动不会自动重新 embedding。只有运行 `scripts.build_index`，并且文档有新增、修改、删除，或者使用 `--full` 时，才会更新向量库。

## 5. 启动后端

推荐本地启动命令：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/backend"
conda activate kf-rag
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

开发热更新启动：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/backend"
conda activate kf-rag
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

后端地址：

```text
http://127.0.0.1:8000
```

## 6. 后端健康检查

服务存活检查：

```bash
curl --noproxy '*' http://127.0.0.1:8000/api/health
```

就绪检查：

```bash
curl --noproxy '*' http://127.0.0.1:8000/api/health/ready
```

查看索引状态：

```bash
curl --noproxy '*' http://127.0.0.1:8000/api/index/status
```

通过接口执行增量索引：

```bash
curl --noproxy '*' -X POST "http://127.0.0.1:8000/api/index/rebuild"
```

通过接口执行全量索引：

```bash
curl --noproxy '*' -X POST "http://127.0.0.1:8000/api/index/rebuild?full=true"
```

## 7. 调用问答接口

本地免认证调用：

```bash
curl --noproxy '*' -X POST "http://127.0.0.1:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"question":"如何创建采集工程，如何运行它呢？"}'
```

如果开启认证，增加 `X-API-Key`：

```bash
curl --noproxy '*' -X POST "http://127.0.0.1:8000/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 你的 APP_API_KEY" \
  -d '{"question":"如何创建采集工程，如何运行它呢？"}'
```

Postman 配置：

```text
Method: POST
URL: http://127.0.0.1:8000/api/chat
Headers:
  Content-Type: application/json
Body raw JSON:
  {"question":"如何创建采集工程，如何运行它呢？"}
```

## 8. 启动前端

新前端 `frontend/`（Apple 风格工作台，推荐）：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/frontend"
npm install
npm run dev
```

前端地址：

```text
http://127.0.0.1:5174
```

生产构建：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/frontend"
npm run build
```

运行测试：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/frontend"
npm run test
```

旧版前端 `frontend-legacy/`（已弃用，仅存档）：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/frontend-legacy"
pnpm install
pnpm dev          # http://127.0.0.1:5173
pnpm run build
pnpm run preview
```

## 9. Streamlit Demo

先启动后端，再启动 Demo：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/backend"
conda activate kf-rag
streamlit run demo/streamlit_app.py
```

## 10. 命令行问答

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/backend"
conda activate kf-rag
python -m scripts.ask "页面编辑器主要包括哪些区域？"
```

## 11. 检索调试

查看某个问题命中的资料：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/backend"
conda activate kf-rag
python -m scripts.inspect_retrieval "如何创建采集工程，如何运行它呢？" --top-k 5
```

关闭 Query Rewrite，只看原始问题检索：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/backend"
conda activate kf-rag
python -m scripts.inspect_retrieval "如何创建采集工程，如何运行它呢？" --top-k 5 --no-rewrite
```

## 12. RAG 可信评测门禁

评测中心的 Run 由后端执行和持久化；浏览器只负责创建、轮询、查看、取消和批准基准。Suite 为 `backend/evaluation_cases/core.v1.json`，包含 20 条人工审核用例；运行数据库为 `storage/evaluation/kingiask_eval.db`。

首次校准或重新校准：

```bash
cd backend
conda run -n kf-rag --no-capture-output \
python -m scripts.evaluation_gate \
  --suite core \
  --mode calibration \
  --output ../storage/reports/core-calibration.json
```

重复校准 3-5 次且不改动代码、索引或配置。仅在所有 Run 有效、P0 Judge 判断已人工复核、分数波动未不可预测地跨越阈值后，才在前端评测中心选择该完成的校准 Run，点击“批准基准”，填写批准人和备注并确认。

有已批准基准后，执行发布阻断检查：

```bash
cd backend
conda run -n kf-rag --no-capture-output \
python -m scripts.evaluation_gate \
  --suite core \
  --mode blocking \
  --output ../storage/reports/core-blocking.json
echo $?
```

退出码：`0` 表示有效 Run 同时通过绝对门禁和基准回归门禁；`1` 表示有效 Run 的真实质量失败；`2` 表示无效执行（包括缺少已批准基准）。`INVALID` 不是质量失败，而是 Case 未完成、Judge 覆盖率非 100%、指标错误、取消或依赖异常导致无法可靠判定。

绝对阈值：通过率 `>=80%`、全部 P0 通过、平均正确性 `>=80%`、平均事实覆盖 `>=80%`、平均忠实度 `>=90%`、P95 `<=30000ms`。基准门禁还会拒绝新的 P0 退化或严重幻觉、超过 5 个百分点的通过率下降，以及超过 `min(125% x baseline P95, 30000ms)` 的 P95。

状态含义：`created` 等待执行，`running` 正在跑 Case，`scoring` 正在计算指标，`completed` 已有最终结果，`INVALID` 结果不可靠，`cancelled` 已取消。`FAILED` 是有效 Run 的门禁结果，不是 Run 状态。

排查 Judge：在 Run 详情查看 Case 失败原因和 `ERROR` 指标错误码，并用 Run ID、时间和错误码查询后端日志。不要将 Judge 提示词、`.env`、API Key 或 Authorization 头写入工单、报告或 Git。完整操作说明见 `docs/evaluation/README.md`。

## 14. 测试

后端全量测试：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/backend"
conda activate kf-rag
python -m pytest -q
```

前端测试：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/frontend"
npm test
```

前端构建验证：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/frontend"
npm run build
```

## 15. 轻量压测

默认压测：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/backend"
conda activate kf-rag
python -m scripts.load_test -n 10 -c 2
python -m scripts.load_test -n 5 -c 1 --output ../storage/reports/load-test.json
```

指定问题压测：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/backend"
conda activate kf-rag
python -m scripts.load_test -n 20 -c 4 --question "如何创建采集工程？"
```

压测报告包含成功率、平均耗时、P50/P95/P99、状态码分布和吞吐量。压测会调用真实问答接口，可能产生 DeepSeek 费用；启用后端认证时可追加 `--api-key`，接口地址使用 `--url` 指定。

## 16. Docker Compose

准备目录和配置：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant"
cp .env.example .env
mkdir -p data/help storage/chroma storage/processed
```

构建镜像：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant"
docker compose build
```

Docker 中构建索引：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant"
docker compose run --rm kf-rag-api python -m scripts.build_index
```

启动服务：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant"
docker compose up -d
```

查看日志：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant"
docker compose logs -f kf-rag-api
```

停止服务：

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant"
docker compose down
```

## 17. Git 常用命令

查看状态：

```bash
git status --short --branch
```

查看最近提交：

```bash
git log --oneline -5
```

提交代码：

```bash
git add .
git commit -m "你的提交说明"
```

推送当前分支：

```bash
git push
```

推送指定分支：

```bash
git push -u origin feature/kf-rag-v1
```

## 18. 最常用启动顺序

终端 1：启动后端。

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/backend"
conda activate kf-rag
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

终端 2：启动前端。

```bash
cd "/Users/fengjinlong/Fjldream/AILearning/KF Assistant/frontend"
npm run dev
```

浏览器打开：

```text
http://127.0.0.1:5174
```
