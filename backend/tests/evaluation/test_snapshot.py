import json

from app.core.config import Settings
from app.evaluation.snapshot import build_run_snapshot
from app.evaluation.suite import EvaluationSuite
from app.rag.ingestion.index_manifest import IndexManifest, ManifestEntry


def _suite() -> EvaluationSuite:
    return EvaluationSuite.model_validate({
        "id": "core", "version": "v1", "default_thresholds": {
            "answer_correctness": 0.8, "faithfulness": 0.8, "p1_required_fact_coverage": 0.6,
        },
        "cases": [{"id": "case-1", "category": "cat", "priority": "P0", "question": "q",
                   "required_facts": [{"id": "fact", "text": "answer"}]}],
    })


def test_snapshot_contains_reproducibility_data_but_not_secrets(monkeypatch, tmp_path):
    settings = Settings(
        deepseek_api_key="secret-key",
        chunk_size=512,
        chunk_overlap=64,
        top_k=7,
        index_manifest_path=tmp_path / "manifest.json",
    )
    monkeypatch.setattr("app.evaluation.snapshot._git_metadata", lambda: ("abc123", True))
    monkeypatch.setattr(
        "app.evaluation.snapshot.load_manifest",
        lambda path: IndexManifest(
            documents={"manual.md": ManifestEntry(content_hash="content", chunk_ids=["manual.md::0"])},
            index_signature="index-signature",
        ),
    )
    monkeypatch.setattr("app.evaluation.snapshot._prompt_hashes", lambda: {"answer": "prompt-hash"})
    monkeypatch.setattr("app.evaluation.snapshot._runtime_versions", lambda: {"python": "3.12", "pydantic": "2.10"})

    snapshot = build_run_snapshot(settings, _suite())
    payload = snapshot.model_dump(mode="json")
    rendered = json.dumps(payload)

    assert payload["suite_hash"]
    assert payload["suite_id"] == "core"
    assert payload["suite_version"] == "v1"
    assert payload["model"] == "deepseek-v4-flash"
    assert payload["thinking_enabled"] is False
    assert payload["git_commit"] == "abc123"
    assert payload["git_dirty"] is True
    assert payload["index_signature"] == "index-signature"
    assert payload["prompt_hashes"] == {"answer": "prompt-hash"}
    assert payload["chunk_size"] == 512
    assert payload["chunk_overlap"] == 64
    assert payload["top_k"] == 7
    assert payload["runtime_versions"] == {"python": "3.12", "pydantic": "2.10"}
    assert "api_key" not in rendered.lower()
    assert settings.deepseek_api_key not in rendered
