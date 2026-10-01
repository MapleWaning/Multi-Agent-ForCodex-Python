"""接收用户任务，读取 Architect 配置，调用 Orchestrator，把 run 结果打印给 Root。

不在这里启动 Codex，也不在这里写 Plan Package。
"""
import argparse
import json
from pathlib import Path

from multi_agent.architect.prompt import build_architect_prompt
from multi_agent.core.orchestrator import create_run
from multi_agent.exceptions import OrchestratorError, WorkerProviderError
from multi_agent.models import WorkerProfile
from multi_agent.storage.architects import list_architects


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-task", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dev-env", required=True)
    args = parser.parse_args()
    try:
        architects = list_architects()
        if not architects:
            raise OrchestratorError("没有可用的 Architect 配置")
        architect = architects[0]
        run, summary = create_run(
            build_architect_prompt(args.user_task, args.dev_env),
            args.project_root,
            WorkerProfile(
                name="openai",
                sandbox=architect.sandbox,
                model=architect.model,
                reasoning_effort=architect.reasoning_effort,
                approval_policy=architect.approval_policy,
                forced_login_method=architect.forced_login_method,
            ),
            schema=True,
            schema_file=Path(__file__).resolve().parents[1] / "doc" / "architect_output_schema.json",
            dev_env=args.dev_env,
        )
    except (OrchestratorError, WorkerProviderError) as error:
        print(f"Error: {error}")
        return
    for message in getattr(run, "business_errors", []):
        print(message)
    print(_result_json(run, summary))


def _result_json(run, summary: str) -> str:
    status = getattr(run, "status", None)
    return json.dumps(
        {
            "run_id": getattr(run, "id", None),
            "status": None if status is None else str(status),
            "summary": summary,
        },
        ensure_ascii=False,
    )
