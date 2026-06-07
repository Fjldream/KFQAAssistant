import sys

from app.rag.factory import create_rag_chain


# 命令行问答入口：方便不启动 Web 服务时快速验证 RAG 效果。
def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        raise SystemExit("用法：python -m scripts.ask 页面编辑器有哪些区域？")
    chain = create_rag_chain()
    response = chain.answer(question)
    print(response.answer)
    if response.sources:
        print("\n参考来源：")
        for source in response.sources:
            print(f"- {source.title} {source.source_path}")


if __name__ == "__main__":
    main()
