NO_ANSWER_MESSAGE = "手册中没有找到相关说明。"

NO_ANSWER_PATTERNS = [
    "手册中没有找到相关说明",
    "没有找到相关说明",
    "未找到相关说明",
    "无法根据手册片段回答",
]

ENTITY_TERMS_REQUIRING_EVIDENCE = ["微信", "企业微信", "钉钉"]


# 判断模型回答是否属于拒答，统一处理标点和常见拒答表达。
def is_no_answer(answer: str) -> bool:
    normalized = answer.strip().replace(" ", "")
    return any(pattern in normalized for pattern in NO_ANSWER_PATTERNS)


# 将拒答文案统一成产品固定表达，避免不同模型输出造成前端展示不一致。
def normalize_answer(answer: str) -> str:
    if is_no_answer(answer):
        return NO_ANSWER_MESSAGE
    return answer


# 从问题中提取必须在检索上下文中出现的关键实体词，用于提前识别明显无依据的问题。
def required_query_terms(question: str) -> list[str]:
    return [term for term in ENTITY_TERMS_REQUIRING_EVIDENCE if term in question]


# 判断检索上下文是否缺少问题里的关键实体；缺少时直接拒答比交给模型猜更稳。
def is_missing_required_terms(question: str, contexts: list[str]) -> bool:
    terms = required_query_terms(question)
    if not terms:
        return False
    context_text = "\n".join(contexts)
    return not all(term in context_text for term in terms)
