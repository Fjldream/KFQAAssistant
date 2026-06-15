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

问答接口：

```bash
curl -X POST "http://127.0.0.1:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"question":"如何创建采集工程"}'
```

返回结构包含回答、来源片段和图片路径：

```json
{
  "answer": "回答内容",
  "sources": [
    {
      "title": "来源标题",
      "source_path": "html/...",
      "snippet": "命中的手册片段",
      "images": ["html/.../1.png"],
      "score": 0.5
    }
  ]
}
```

如果手册片段中没有可靠答案，接口会返回固定拒答文案，并且 `sources` 为空：

```json
{
  "answer": "手册中没有找到相关说明。",
  "sources": []
}
```

本地默认 `DISABLE_AUTH=true`，接口不需要鉴权。部署到公司服务器时建议改为：

```text
DISABLE_AUTH=false
APP_API_KEY=自定义内部访问密钥
```

此时调用接口需要增加请求头：

```bash
-H "x-api-key: 自定义内部访问密钥"
```

## 使用 Postman 测试接口

在 Postman 中创建一个请求：

```text
POST http://127.0.0.1:8000/api/chat
```

Headers：

```text
Content-Type: application/json
```

Body 选择 `raw` 和 `JSON`，填写：

```json
{
  "question": "如何创建采集工程"
}
```

如果启用了 `APP_API_KEY`，还需要在 Headers 中增加：

```text
x-api-key: 自定义内部访问密钥
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

## RAG 效果评估

评估集位于 `tests/eval_questions.json`。每个问题包含：

```json
{
  "question": "页面编辑器主要包括哪些区域？",
  "expected_keywords": ["菜单栏", "工具栏"]
}
```

运行评估：

```bash
python -m scripts.evaluate
```

脚本会逐题调用 RAG，并检查回答和来源片段中是否包含预期关键词。这个评估不是最终标准答案评分，而是第一阶段用来发现“检索跑偏”和“回答缺关键点”的轻量检查。

## RAG 处理流程

当前文档处理链路：

```text
data/help 原始手册
  -> 选择 Markdown 或 HTML
  -> 在图片位置插入内部标记
  -> 清洗正文并保留图片位置
  -> 统一成 ManualDocument
  -> 切成 DocumentChunk，并只给相关 chunk 绑定附近图片
  -> 写入 Chroma 向量库
  -> 检索相关片段
  -> DeepSeek 生成回答
```

图片不会直接进入向量文本，而是作为 metadata 返回。系统会先在 Markdown 图片或 HTML `img` 标签位置插入内部标记，切块时根据标记把图片绑定到对应 chunk，最后再从 chunk 正文中移除内部标记。

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
