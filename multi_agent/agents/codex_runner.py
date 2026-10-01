"""只负责启动一次 `codex exec`，并取回退出码、stdout、stderr。

不创建 run_id，不决定 COMPLETED / FAILED，不写本地文件。
"""
import subprocess
import json
from pathlib import Path

from multi_agent.exceptions import WorkerProviderError
from multi_agent.models import WorkerProfile

def run_codex(
    prompt: str,
    project_root: str,
    worker_profile: WorkerProfile,
    schema: bool = False,
    schema_file: Path | None = None,
) -> tuple[int, list[dict], str]:
    command = [
        "codex", "exec",
        "--json",
        "--skip-git-repo-check",
        "--sandbox", worker_profile.sandbox,
        "-m", worker_profile.model,
        "-c", f'model_provider="{worker_profile.name}"',
        "-c", f'model_reasoning_effort="{worker_profile.reasoning_effort}"',
        "-c", f'approval_policy="{worker_profile.approval_policy}"',
    ]
    if schema:
        command.extend(["--output-schema", str(schema_file)])
    if worker_profile.forced_login_method is not None:
        command.extend(["-c", f'forced_login_method="{worker_profile.forced_login_method}"'])
    if worker_profile.context_window is not None:
        command.extend(["-c", f"model_context_window={worker_profile.context_window}"])
    if worker_profile.tool_output_token_limit is not None:
        command.extend(["-c", f"tool_output_token_limit={worker_profile.tool_output_token_limit}"])
    if worker_profile.base_url is not None:
        provider_id = worker_profile.name
        if worker_profile.provider_name is not None:
            command.extend(["-c", f'model_providers.{provider_id}.name="{worker_profile.provider_name}"'])
        command.extend(["-c", f'model_providers.{provider_id}.base_url="{worker_profile.base_url}"'])
        if worker_profile.wire_api is not None:
            command.extend(["-c", f'model_providers.{provider_id}.wire_api="{worker_profile.wire_api}"'])
        if worker_profile.env_key is not None:
            command.extend(["-c", f'model_providers.{provider_id}.env_key="{worker_profile.env_key}"'])
    command.append(prompt)
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            cwd=project_root,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError as error:
        raise WorkerProviderError("codex_not_found", str(error)) from error
    except OSError as error:
        raise WorkerProviderError("codex_start_failed", str(error)) from error
    events = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise WorkerProviderError("invalid_jsonl", f"{error}: {line}") from error
        events.append(event)
    return completed.returncode, events, completed.stderr or ""
