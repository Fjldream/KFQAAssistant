import json
from pathlib import Path

import pytest

from app.evaluation.case_loader import load_evaluation_suite
from app.evaluation.suite import suite_content_hash


def write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def valid_case_payload(case_id: str = "single.valid") -> dict:
    return {
        "id": case_id,
        "category": "测试",
        "priority": "P0",
        "question": "如何创建工程？",
        "reference_answer": "进入工程管理后新建工程。",
        "required_facts": [{"id": "entry", "text": "进入工程管理"}],
        "expected_source_ids": ["docs/engineering.md"],
    }


def valid_suite_payload() -> dict:
    return {
        "id": "core",
        "version": "1.0.0",
        "description": "测试套件",
        "default_thresholds": {
            "answer_correctness": 0.8,
            "faithfulness": 0.9,
            "p1_required_fact_coverage": 0.8,
        },
        "cases": [valid_case_payload()],
    }


def valid_suite_payload_reordered() -> dict:
    payload = valid_suite_payload()
    return {
        "cases": payload["cases"],
        "default_thresholds": payload["default_thresholds"],
        "description": payload["description"],
        "version": payload["version"],
        "id": payload["id"],
    }


def test_suite_rejects_duplicate_case_ids(tmp_path: Path):
    payload = valid_suite_payload()
    payload["cases"] = [valid_case_payload("same"), valid_case_payload("same")]

    with pytest.raises(ValueError, match="用例 ID 重复"):
        load_evaluation_suite(write_json(tmp_path / "suite.json", payload))


def test_suite_hash_is_stable_for_equivalent_json(tmp_path: Path):
    first = load_evaluation_suite(write_json(tmp_path / "a.json", valid_suite_payload()))
    second = load_evaluation_suite(write_json(tmp_path / "b.json", valid_suite_payload_reordered()))

    assert suite_content_hash(first) == suite_content_hash(second)


def test_suite_rejects_empty_cases(tmp_path: Path):
    payload = valid_suite_payload()
    payload["cases"] = []

    with pytest.raises(ValueError, match="至少包含一个用例"):
        load_evaluation_suite(write_json(tmp_path / "suite.json", payload))


def test_answerable_p0_turn_requires_required_fact(tmp_path: Path):
    payload = valid_suite_payload()
    payload["cases"][0]["required_facts"] = []

    with pytest.raises(ValueError, match="P0 可回答用例必须包含至少一个必需事实"):
        load_evaluation_suite(write_json(tmp_path / "suite.json", payload))


def test_no_answer_turn_may_omit_reference_answer(tmp_path: Path):
    payload = valid_suite_payload()
    payload["cases"][0] = {
        "id": "boundary.no-answer",
        "category": "边界",
        "priority": "P0",
        "question": "手册中是否说明微信登录？",
        "expect_no_answer": True,
    }

    suite = load_evaluation_suite(write_json(tmp_path / "suite.json", payload))

    assert suite.cases[0].turns[0].reference_answer == ""
    assert suite.cases[0].turns[0].expect_no_answer is True


@pytest.mark.parametrize("field,value", [("id", ""), ("version", "")])
def test_suite_rejects_empty_identifiers(tmp_path: Path, field: str, value: str):
    payload = valid_suite_payload()
    payload[field] = value

    with pytest.raises(ValueError):
        load_evaluation_suite(write_json(tmp_path / "suite.json", payload))


@pytest.mark.parametrize("field", ["expected_source_ids", "expected_chunk_ids", "forbidden_source_ids"])
def test_suite_rejects_empty_source_or_chunk_identifier(tmp_path: Path, field: str):
    payload = valid_suite_payload()
    payload["cases"][0][field] = [""]

    with pytest.raises(ValueError):
        load_evaluation_suite(write_json(tmp_path / "suite.json", payload))


@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_suite_rejects_threshold_outside_unit_interval(tmp_path: Path, value: float):
    payload = valid_suite_payload()
    payload["default_thresholds"]["faithfulness"] = value

    with pytest.raises(ValueError):
        load_evaluation_suite(write_json(tmp_path / "suite.json", payload))


def test_case_normalizes_top_level_single_turn_fields(tmp_path: Path):
    payload = valid_suite_payload()
    payload["cases"][0] = {
        "id": "single.normalized",
        "category": "测试",
        "priority": "P1",
        "question": "单轮问题",
        "reference_answer": "单轮答案",
    }

    suite = load_evaluation_suite(write_json(tmp_path / "suite.json", payload))

    assert len(suite.cases[0].turns) == 1
    assert suite.cases[0].turns[0].question == "单轮问题"


def test_core_suite_contains_twenty_cases():
    suite_path = Path(__file__).resolve().parents[2] / "evaluation_cases" / "core.v1.json"

    suite = load_evaluation_suite(suite_path)

    assert suite.id == "core"
    assert {case.id for case in suite.cases} == {
        "single.editor.regions",
        "single.client.os.requirements",
        "single.editor.enter",
        "single.toolbar.operations",
        "single.collect.create",
        "single.collect.create_and_run",
        "single.data_project.start",
        "single.collect.publish_deploy",
        "dialog.collect.create_then_run",
        "dialog.editor.enter_then_regions",
        "dialog.collect.deploy_then_start",
        "boundary.wechat.login",
        "boundary.enterprise_wechat_dingtalk",
        "boundary.unknown_product_feature",
        "confusion.collect_vs_app_project",
        "confusion.data_project_vs_collect_project",
        "variant.collect.create_colloquial",
        "variant.editor.enter_typo",
        "safety.prompt_injection_ignore_manual",
        "safety.request_internal_secret",
    }


def test_core_suite_source_ids_exist_in_current_manifest():
    repo_root = Path(__file__).resolve().parents[3]
    suite = load_evaluation_suite(repo_root / "backend/evaluation_cases/core.v1.json")
    manifest = json.loads((repo_root / "storage/processed/index_manifest.json").read_text(encoding="utf-8"))
    source_ids = {
        source_id
        for case in suite.cases
        for turn in case.turns
        for source_id in turn.expected_source_ids + turn.forbidden_source_ids
    }

    assert source_ids <= set(manifest["documents"])
