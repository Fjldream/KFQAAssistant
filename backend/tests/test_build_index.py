from pathlib import Path
from types import SimpleNamespace

import scripts.build_index as build_index
from app.rag.index_service import IndexUpdateResult


# 创建 CLI 测试使用的固定索引结果。
def make_result(mode: str) -> IndexUpdateResult:
    return IndexUpdateResult(
        mode=mode,
        added_documents=1,
        modified_documents=2,
        deleted_documents=3,
        skipped_documents=4,
        written_chunks=5,
        total_chunks=6,
    )


# 为 CLI 注入轻量依赖，并返回 update_index 收到的参数。
def prepare_cli(monkeypatch, mode: str) -> list[dict[str, object]]:
    received: list[dict[str, object]] = []
    settings = SimpleNamespace(
        data_dir=Path("data/help"),
        index_manifest_path=Path("storage/processed/index_manifest.json"),
        embedding_model_name="test-embedding-model",
        chunk_size=700,
        chunk_overlap=100,
    )
    vector_store = object()
    monkeypatch.setattr(build_index, "get_settings", lambda: settings)
    monkeypatch.setattr(build_index, "create_vector_store", lambda: vector_store)

    # 记录 CLI 是否正确传递 full 参数和路径配置。
    def fake_update_index(**kwargs):
        received.append(kwargs)
        return make_result(mode)

    monkeypatch.setattr(build_index, "update_index", fake_update_index, raising=False)
    return received


# 验证命令行默认执行增量索引并输出结构化统计。
def test_build_index_defaults_to_incremental(monkeypatch, capsys):
    received = prepare_cli(monkeypatch, mode="incremental")

    build_index.main([])

    assert received[0]["full"] is False
    assert received[0]["root_dir"] == Path("data/help")
    assert received[0]["embedding_model_name"] == "test-embedding-model"
    assert received[0]["chunk_size"] == 700
    assert received[0]["chunk_overlap"] == 100
    output = capsys.readouterr().out
    assert "运行模式: incremental" in output
    assert "跳过文档: 4" in output
    assert "写入 chunks: 5" in output


# 验证 --full 会要求索引服务执行强制全量重建。
def test_build_index_full_flag_requests_full_rebuild(monkeypatch, capsys):
    received = prepare_cli(monkeypatch, mode="full")

    build_index.main(["--full"])

    assert received[0]["full"] is True
    assert "运行模式: full" in capsys.readouterr().out
