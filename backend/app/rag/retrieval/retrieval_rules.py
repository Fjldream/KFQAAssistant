from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


DEFAULT_RULES_PATH = Path(__file__).with_name("retrieval_rules.yaml")


@dataclass(frozen=True)
class TermRule:
    triggers: list[str]
    terms: list[str]
    required_any: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class WorkflowRule:
    triggers: list[str]
    required_any: list[str]
    terms: list[str]
    min_matches: int = 3
    score_per_match: float = 2.0


@dataclass(frozen=True)
class RetrievalRules:
    term_groups: list[TermRule]
    workflow: WorkflowRule


# 将 YAML 中的列表字段规范化为字符串列表，避免空值或数字破坏匹配逻辑。
def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


# 判断某条规则是否被当前问题触发，同时满足可选的 required_any 条件。
def _rule_matches(query: str, triggers: list[str], required_any: list[str]) -> bool:
    if not any(trigger in query for trigger in triggers):
        return False
    return not required_any or any(term in query for term in required_any)


# 从原始 YAML 字典构造检索规则对象，集中处理默认值。
def _parse_rules(raw: dict[str, Any]) -> RetrievalRules:
    term_groups = [
        TermRule(
            triggers=_string_list(item.get("triggers")),
            required_any=_string_list(item.get("required_any")),
            terms=_string_list(item.get("terms")),
        )
        for item in raw.get("term_groups", [])
        if isinstance(item, dict)
    ]
    workflow = raw.get("workflow", {})
    if not isinstance(workflow, dict):
        workflow = {}
    return RetrievalRules(
        term_groups=term_groups,
        workflow=WorkflowRule(
            triggers=_string_list(workflow.get("triggers")),
            required_any=_string_list(workflow.get("required_any")),
            terms=_string_list(workflow.get("terms")),
            min_matches=int(workflow.get("min_matches", 3)),
            score_per_match=float(workflow.get("score_per_match", 2.0)),
        ),
    )


# 从配置文件加载检索兜底规则，默认读取随代码发布的 YAML 文件。
@lru_cache(maxsize=8)
def load_retrieval_rules(path: Path | None = None) -> RetrievalRules:
    rules_path = path or DEFAULT_RULES_PATH
    raw = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raw = {}
    return _parse_rules(raw)


# 根据配置规则扩展查询词，作为向量召回之外的关键词兜底。
def expand_terms_with_rules(query: str, rules: RetrievalRules | None = None) -> list[str]:
    active_rules = rules or load_retrieval_rules()
    expanded: list[str] = []
    for rule in active_rules.term_groups:
        if _rule_matches(query, rule.triggers, rule.required_any):
            expanded.extend(rule.terms)
    return list(dict.fromkeys(item for item in expanded if len(item) >= 2))


# 针对“启动/运行工程”问题，提升包含完整运行流程证据的片段。
def workflow_intent_score(query: str, text: str, rules: RetrievalRules | None = None) -> float:
    active_rules = rules or load_retrieval_rules()
    rule = active_rules.workflow
    if not _rule_matches(query, rule.triggers, rule.required_any):
        return 0.0

    matched_count = sum(1 for term in rule.terms if term in text)
    if matched_count < rule.min_matches:
        return 0.0
    return float(matched_count * rule.score_per_match)
