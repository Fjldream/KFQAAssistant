# KF RAG 问答助手

这是一个面向 KF 产品手册的 RAG 问答服务。第一版使用 FastAPI 提供接口，本地 embedding 模型构建向量库，DeepSeek API 生成最终回答。

## 第一版能力

- 从 `data/help` 加载产品手册。
- 优先使用 Markdown，必要时清洗 HTML。
- 构建本地 Chroma 向量库。
- 通过 `POST /api/chat` 返回答案、引用片段和相关图片。
- 提供本地 demo 页面用于验证效果。

## 环境准备

建议使用项目专用 conda 环境，避免污染 base 环境：

```bash
conda create -n kf-rag python=3.11 -y
conda activate kf-rag
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，填入 `DEEPSEEK_API_KEY`。

默认 DeepSeek 模型是 `deepseek-v4-flash`。这是 DeepSeek 官方当前支持的模型之一，适合第一版产品问答的速度和成本需求。

## 构建索引

```bash
python -m scripts.build_index
```

第一次运行会下载 `BAAI/bge-small-zh-v1.5`，需要网络。索引会写入 `storage/chroma`。

## 启动 API 服务

```bash
uvicorn app.main:app --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

预期返回：

```json
{"status":"ok"}
```

## 命令行提问

```bash
python -m scripts.ask 页面编辑器主要包括哪些区域？
```

## 启动 demo 页面

先启动 API 服务，再运行：

```bash
streamlit run demo/streamlit_app.py
```

浏览器打开 Streamlit 地址后，输入 KF 产品使用问题即可测试问答效果。

## 测试

```bash
pytest tests -v
```

如果不想激活环境，也可以使用：

```bash
conda run -n kf-rag pytest tests -v
```

## RAG 处理流程

当前文档处理链路：

```text
data/help 原始手册
  -> 选择 Markdown 或 HTML
  -> 清洗正文
  -> 提取图片路径
  -> 统一成 ManualDocument
  -> 切成 DocumentChunk
  -> 写入 Chroma 向量库
  -> 检索相关片段
  -> DeepSeek 生成回答
```

## 重要安全说明

- 不要提交 `.env`。
- 不要在日志中打印真实 API Key。
- 如果部署到公司服务器，建议关闭 `DISABLE_AUTH` 并配置 `APP_API_KEY`。
- 当前 embedding 在本地执行，DeepSeek API 会收到用户问题和检索出来的手册片段。

## 后续学习路线

1. 文档清洗
2. 文档切块
3. Embedding 和向量库
4. 检索
5. Prompt 和 LLM 生成
6. API 服务化
7. RAG 评估
