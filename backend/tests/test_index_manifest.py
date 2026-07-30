from pathlib import Path

import pytest

from app.rag.ingestion.index_manifest import (
    IndexManifest,
    ManifestEntry,
    ManifestFormatError,
    hash_file,
    load_manifest,
    save_manifest,
)


# 验证相同内容生成稳定 SHA-256，内容变化后哈希也会变化。
def test_hash_file_tracks_content_changes(tmp_path: Path):
    path = tmp_path / "guide.md"
    path.write_text("第一版", encoding="utf-8")
    first = hash_file(path)

    assert hash_file(path) == first

    path.write_text("第二版", encoding="utf-8")

    assert hash_file(path) != first


# 验证清单不存在时返回 None，表示这是第一次构建。
def test_load_manifest_returns_none_when_file_is_missing(tmp_path: Path):
    assert load_manifest(tmp_path / "index_manifest.json") is None


# 验证 manifest 可以完整保存并重新加载。
def test_manifest_round_trip(tmp_path: Path):
    path = tmp_path / "processed" / "index_manifest.json"
    expected = IndexManifest(
        documents={"guide.md": ManifestEntry(content_hash="abc", chunk_ids=["guide.md::0"])},
        index_signature="signature-v1",
    )

    save_manifest(path, expected)

    assert load_manifest(path) == expected
    assert not path.with_name(f"{path.name}.tmp").exists()


# 验证旧版 manifest 没有配置指纹时仍可读取，并交给索引服务自动升级。
def test_load_manifest_supports_legacy_file_without_index_signature(tmp_path: Path):
    path = tmp_path / "index_manifest.json"
    path.write_text(
        '{"version": 1, "documents": {"guide.md": {"content_hash": "abc", "chunk_ids": ["guide.md::0"]}}}',
        encoding="utf-8",
    )

    manifest = load_manifest(path)

    assert manifest is not None
    assert manifest.index_signature == ""


# 验证损坏清单会给出明确业务错误，避免错误判断文档是否已索引。
def test_load_manifest_rejects_invalid_json(tmp_path: Path):
    path = tmp_path / "index_manifest.json"
    path.write_text("{bad json", encoding="utf-8")

    with pytest.raises(ManifestFormatError, match="--full"):
        load_manifest(path)


# 验证字段类型不正确的清单同样会被拒绝。
def test_load_manifest_rejects_invalid_structure(tmp_path: Path):
    path = tmp_path / "index_manifest.json"
    path.write_text('{"version": 1, "documents": []}', encoding="utf-8")

    with pytest.raises(ManifestFormatError, match="--full"):
        load_manifest(path)
