from app.core.config import get_settings
from app.rag.document_loader import load_documents
from app.rag.factory import create_vector_store
from app.rag.splitter import split_documents


# 命令行索引构建入口：从原始手册生成 chunks 并写入 Chroma。
def main() -> None:
    settings = get_settings()
    documents = load_documents(settings.data_dir)
    chunks = split_documents(documents)
    vector_store = create_vector_store()
    count = vector_store.rebuild(chunks)
    print(f"已构建索引 chunks: {count}")


if __name__ == "__main__":
    main()
