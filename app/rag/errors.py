class RagServiceError(Exception):
    # 保存可安全返回给前端的错误信息和 HTTP 状态码。
    def __init__(self, public_message: str, status_code: int = 503) -> None:
        super().__init__(public_message)
        self.public_message = public_message
        self.status_code = status_code


class IndexNotReadyError(RagServiceError):
    # 表示知识库索引为空或尚未构建。
    def __init__(self) -> None:
        super().__init__("知识库索引还没有构建，请先执行索引构建。")


class LLMGenerationError(RagServiceError):
    # 表示大模型调用失败、超时或返回格式异常。
    def __init__(self) -> None:
        super().__init__("大模型服务暂时不可用，请稍后重试。")
