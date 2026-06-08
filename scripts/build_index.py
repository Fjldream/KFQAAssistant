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
    chunks_with_images = sum(1 for chunk in chunks if chunk.images)
    print(f"已构建索引 chunks: {count}")
    print(f"其中带图片 metadata 的 chunks: {chunks_with_images}")
    first_chunk_with_images = next((chunk for chunk in chunks if chunk.images), None)
    if first_chunk_with_images:
        print(f"图片样例来源: {first_chunk_with_images.source_path}")
        print(f"图片样例: {first_chunk_with_images.images[:3]}")


if __name__ == "__main__":
    main()
