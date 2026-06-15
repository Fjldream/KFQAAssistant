NO_ANSWER_MESSAGE = "手册中没有找到相关说明。"

NO_ANSWER_PATTERNS = [
    "手册中没有找到相关说明",
    "没有找到相关说明",
    "未找到相关说明",
    "无法根据手册片段回答",
]


# 判断模型回答是否属于拒答，统一处理标点和常见拒答表达。
def is_no_answer(answer: str) -> bool:
    normalized = answer.strip().replace(" ", "")
    return any(pattern in normalized for pattern in NO_ANSWER_PATTERNS)


# 将拒答文案统一成产品固定表达，避免不同模型输出造成前端展示不一致。
def normalize_answer(answer: str) -> str:
    if is_no_answer(answer):
        return NO_ANSWER_MESSAGE
    return answer
