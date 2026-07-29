import argparse

from app.rag.factory import create_rag_chain


# 解析命令行参数，支持标准 --help，同时把剩余文本合并成一个问题。
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KingIAsk 命令行问答")
    parser.add_argument("question", nargs="*", help="要询问的 KF 产品使用问题")
    return parser.parse_args(argv)


# 命令行问答入口：方便不启动 Web 服务时快速验证 RAG 效果。
def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    question = " ".join(args.question).strip()
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
