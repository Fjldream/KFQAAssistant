import hashlib
import importlib.metadata
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import Settings
from app.evaluation.suite import EvaluationSuite, suite_content_hash
from app.rag.ingestion.index_manifest import load_manifest


DEFAULT_DEEPSEEK_RATES = {
    "input_cache_hit_per_million": "0",
    "input_cache_miss_per_million": "0",
    "output_per_million": "0",
}


class RunSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    suite_id: str
    suite_version: str
    suite_hash: str
    model: str
    judge_model: str
    thinking_enabled: bool = False
    git_commit: str | None = None
    git_dirty: bool = False
    index_signature: str | None = None
    prompt_hashes: dict[str, str] = Field(default_factory=dict)
    chunk_size: int
    chunk_overlap: int
    top_k: int
    runtime_versions: dict[str, str] = Field(default_factory=dict)
    price_rates: dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_DEEPSEEK_RATES))


def _git_metadata() -> tuple[str | None, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True,
        ).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"], check=True, capture_output=True, text=True,
        ).stdout.strip())
        return commit or None, dirty
    except (OSError, subprocess.CalledProcessError):
        return None, False


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prompt_hashes() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    paths = {
        "answer": root / "rag" / "generation" / "llm.py",
        "judge": root / "evaluation" / "judge.py",
    }
    return {name: _file_hash(path) for name, path in paths.items() if path.exists()}


def _runtime_versions() -> dict[str, str]:
    versions = {"python": sys.version.split()[0]}
    for package in ("fastapi", "pydantic", "langchain", "chromadb"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            continue
    return versions


def build_run_snapshot(settings: Settings, suite: EvaluationSuite) -> RunSnapshot:
    commit, dirty = _git_metadata()
    manifest = load_manifest(settings.index_manifest_path)
    return RunSnapshot(
        suite_id=suite.id,
        suite_version=suite.version,
        suite_hash=suite_content_hash(suite),
        model=settings.deepseek_model,
        judge_model=settings.deepseek_judge_model,
        git_commit=commit,
        git_dirty=dirty,
        index_signature=manifest.index_signature if manifest else None,
        prompt_hashes=_prompt_hashes(),
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        top_k=settings.top_k,
        runtime_versions=_runtime_versions(),
    )
