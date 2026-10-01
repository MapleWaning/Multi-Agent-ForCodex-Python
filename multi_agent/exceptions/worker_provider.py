"""请求第三方 Worker Provider 时抛出的错误。"""


class WorkerProviderError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class BusinessError(WorkerProviderError):
    """Provider 在事件里返回的业务错误，例如额度耗尽或请求过多。"""

    def __init__(self, message: str):
        super().__init__("business", message)

    def __str__(self) -> str:
        return self.message
