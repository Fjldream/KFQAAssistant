# KF RAG 问答助手

这是一个面向 KF 产品手册的 RAG 问答服务。第一版使用 FastAPI 提供接口，本地 embedding 模型构建向量库，DeepSeek API 生成最终回答。

## 第一版能力

- 从 `data/help` 加载产品手册。
- 优先使用 Markdown，必要时清洗 HTML。
- 构建本地 Chroma 向量库。
- 通过 `POST /api/chat` 返回答案、引用片段和相关图片。
- 提供本地 demo 页面用于验证效果。

## 后续学习路线

1. 文档清洗
2. 文档切块
3. Embedding 和向量库
4. 检索
5. Prompt 和 LLM 生成
6. API 服务化
7. RAG 评估
