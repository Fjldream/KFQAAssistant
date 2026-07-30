import argparse

from app.core.config import get_settings
from app.rag.factory import create_vector_store
from app.rag.ingestion.index_service import update_index


# 解析索引构建参数，默认增量更新，传入 --full 时强制全量重建。
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建 KF 手册向量索引")
    parser.add_argument(
        "--full",
        action="store_true",
        help="忽略已有增量清单，清空并重新构建全部向量",
    )
    return parser.parse_args(argv)


# 命令行索引构建入口：比较文档变化并更新本地 Chroma。
def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    settings = get_settings()
    result = update_index(
        root_dir=settings.data_dir,
        manifest_path=settings.index_manifest_path,
        vector_store=create_vector_store(),
        full=args.full,
        embedding_model_name=settings.embedding_model_name,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    print(f"运行模式: {result.mode}")
    print(f"新增文档: {result.added_documents}")
    print(f"修改文档: {result.modified_documents}")
    print(f"删除文档: {result.deleted_documents}")
    print(f"跳过文档: {result.skipped_documents}")
    print(f"写入 chunks: {result.written_chunks}")
    print(f"索引总 chunks: {result.total_chunks}")


if __name__ == "__main__":
    main()
