from dataclasses import dataclass
import hashlib
import json
from pathlib import Path


MANIFEST_VERSION = 1


# 表示一篇源文档在上一次成功索引后的内容指纹和 chunk 列表。
@dataclass(frozen=True)
class ManifestEntry:
    content_hash: str
    chunk_ids: list[str]


# 表示整个知识库的索引清单，用于比较两次构建之间的文档变化。
@dataclass(frozen=True)
class IndexManifest:
    documents: dict[str, ManifestEntry]
    index_signature: str = ""
    version: int = MANIFEST_VERSION


# 表示索引清单无法解析或字段结构不符合当前版本。
class ManifestFormatError(ValueError):
    pass


# 分块读取源文件并计算 SHA-256，避免大文件一次性全部载入内存。
def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while block := file.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


# 将 JSON 字典转换为经过类型校验的索引清单。
def _parse_manifest(data: object) -> IndexManifest:
    if not isinstance(data, dict):
        raise TypeError("manifest root must be an object")
    if data.get("version") != MANIFEST_VERSION:
        raise ValueError("unsupported manifest version")
    raw_documents = data.get("documents")
    if not isinstance(raw_documents, dict):
        raise TypeError("manifest documents must be an object")
    index_signature = data.get("index_signature", "")
    if not isinstance(index_signature, str):
        raise TypeError("manifest index signature must be a string")

    documents: dict[str, ManifestEntry] = {}
    for source_path, raw_entry in raw_documents.items():
        if not isinstance(source_path, str) or not isinstance(raw_entry, dict):
            raise TypeError("invalid manifest document entry")
        content_hash = raw_entry.get("content_hash")
        chunk_ids = raw_entry.get("chunk_ids")
        if not isinstance(content_hash, str) or not isinstance(chunk_ids, list):
            raise TypeError("invalid manifest document fields")
        if not all(isinstance(chunk_id, str) for chunk_id in chunk_ids):
            raise TypeError("manifest chunk ids must be strings")
        documents[source_path] = ManifestEntry(content_hash=content_hash, chunk_ids=chunk_ids)
    return IndexManifest(documents=documents, index_signature=index_signature)


# 读取索引清单；文件不存在表示还没有执行过受清单管理的构建。
def load_manifest(path: Path) -> IndexManifest | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return _parse_manifest(data)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ManifestFormatError("索引清单格式损坏，请执行 build_index.py --full 重新建立索引。") from exc


# 先写临时文件再原子替换正式清单，避免进程中断产生半个 JSON 文件。
def save_manifest(path: Path, manifest: IndexManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    payload = {
        "version": manifest.version,
        "index_signature": manifest.index_signature,
        "documents": {
            source_path: {
                "content_hash": entry.content_hash,
                "chunk_ids": entry.chunk_ids,
            }
            for source_path, entry in sorted(manifest.documents.items())
        },
    }
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    temporary_path.replace(path)
