"""编排过程中抛出的错误。状态检查、Run 控制都从这里派生。"""


class OrchestratorError(Exception):
    """编排器的全部异常都继承这个类。"""


class InvalidStateError(OrchestratorError):
    def __init__(self, current: str, target: str):
        self.current = current
        self.target = target
        super().__init__(f"不能把状态从 {current} 改为 {target}")
