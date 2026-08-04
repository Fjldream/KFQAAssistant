import json
from pathlib import Path

from app.evaluation.case_loader import load_evaluation_cases


# 验证旧版单轮 JSON 评测集可以平滑迁移为新的统一用例结构。
def test_loader_accepts_legacy_single_turn_shape(tmp_path: Path):
    path = tmp_path / "cases.json"
    path.write_text(
        json.dumps(
            [{"question": "如何创建采集工程？", "expected_keywords": ["新建工程"]}],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    cases = load_evaluation_cases(path)

    assert cases[0].id == "case-1"
    assert cases[0].category == "未分类"
    assert cases[0].case_type == "single"
    assert cases[0].turns[0].question == "如何创建采集工程？"
    assert cases[0].turns[0].expected_keywords == ["新建工程"]


# 验证新版连续对话 JSON 可以加载为多轮评测用例。
def test_loader_accepts_dialogue_shape(tmp_path: Path):
    path = tmp_path / "dialogues.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "dialog.collect",
                    "category": "数采管理",
                    "priority": "P0",
                    "tags": ["dialogue"],
                    "turns": [
                        {"question": "如何创建采集工程？"},
                        {"question": "那怎么运行？", "expected_keywords": ["启动"]},
                    ],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    cases = load_evaluation_cases(path)

    assert cases[0].id == "dialog.collect"
    assert cases[0].priority == "P0"
    assert cases[0].tags == ["dialogue"]
    assert cases[0].case_type == "dialogue"
    assert cases[0].turns[1].expected_keywords == ["启动"]


# 验证评测集可以声明同义关键词组，组内任意命中即可通过该语义点。
def test_loader_accepts_keyword_groups(tmp_path: Path):
    path = tmp_path / "cases.json"
    path.write_text(
        json.dumps(
            [
                {
                    "question": "如何创建采集工程？",
                    "expected_keyword_groups": [["新建工程", "新建数采工程"]],
                    "expected_source_keyword_groups": [["数采管理/工程开发-Windows", "数采管理"]],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    cases = load_evaluation_cases(path)

    assert cases[0].turns[0].expected_keyword_groups == [["新建工程", "新建数采工程"]]
    assert cases[0].turns[0].expected_source_keyword_groups == [["数采管理/工程开发-Windows", "数采管理"]]


# 验证缺失文件会被当作空评测集，方便平台首次启动。
def test_loader_returns_empty_list_when_file_missing(tmp_path: Path):
    cases = load_evaluation_cases(tmp_path / "missing.json")

    assert cases == []
