"""定位一次 Run 的目录，并限制文件写在该目录内。"""
from pathlib import Path

from multi_agent.exceptions import OrchestratorError

_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def run_directory(project_root: str, run_id: str) -> Path:
    path_component(run_id, "Run 编号")
    root = Path(project_root).resolve()
    runs = (root / ".multi_agent" / "runs").resolve()
    if not runs.is_relative_to(root):
        raise OrchestratorError("Run 目录必须位于业务项目内")
    directory = (runs / run_id).resolve()
    if not directory.is_relative_to(runs):
        raise OrchestratorError(f"Run 编号 {run_id} 超出了 .multi_agent")
    return directory


def list_task_files(project_root: str, run_id: str) -> list[Path]:
    directory = run_directory(project_root, run_id) / "tasks"
    if not directory.is_dir():
        return []
    files = [
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.casefold() == ".md"
    ]
    return sorted(files, key=lambda path: path.name.casefold())


def place_file(directory: Path, filename: str) -> Path:
    path_component(filename, "文件名")
    directory.mkdir(parents=True, exist_ok=True)
    base = directory.resolve()
    path = (base / filename).resolve()
    if path.parent != base or not path.is_relative_to(base):
        raise OrchestratorError(f"文件 {filename} 超出了目标目录")
    return path


def path_component(value: str, label: str) -> None:
    if value.strip() == "" or value != value.strip():
        raise OrchestratorError(f"{label} {value!r} 不能为空或包含首尾空白")
    if value in {".", ".."} or ".." in value:
        raise OrchestratorError(f"{label} {value} 不能包含目录")
    if any(separator in value for separator in ("/", "\\", ":")):
        raise OrchestratorError(f"{label} {value} 不能包含目录")
    if any(char in value for char in '<>"|?*') or any(ord(char) < 32 for char in value):
        raise OrchestratorError(f"{label} {value} 含有非法字符")
    if value.endswith("."):
        raise OrchestratorError(f"{label} {value} 不能以点结尾")
    stem = value.split(".", 1)[0].upper()
    if stem in _RESERVED_NAMES:
        raise OrchestratorError(f"{label} {value} 是系统保留名")
