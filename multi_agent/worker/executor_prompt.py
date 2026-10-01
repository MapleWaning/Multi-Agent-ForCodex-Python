"""把执行者职责、本机环境、项目目录和任务文件拼成 Worker 的 prompt。"""

_ROLE = """你是 Executor。职责是将方案落地。
按任务文件实现方案，不重新设计方案。"""

_BOUNDARY = """.multi_agent 目录只读。
可以读取其中的方案和任务文件，禁止修改、删除或新增其中的文件。"""


def build_executor_prompt(dev_env: str, project_root: str, task_file: str) -> str:
    return (
        f"{_ROLE}\n"
        "\n"
        f"{_BOUNDARY}\n"
        "\n"
        "## 本机环境\n"
        "\n"
        f"{dev_env}\n"
        "\n"
        "## 项目目录\n"
        "\n"
        f"{project_root}\n"
        "\n"
        "## 任务文件\n"
        "\n"
        f"按 {task_file} 执行本次任务。\n"
    )
