"""接收命令行参数，调用 Orchestrator，把最终摘要打印给 Root。

不在这里启动 Codex，也不在这里读写 `.multi-agent/runs/`。
"""
import argparse
from pathlib import Path
from multi_agent.models import WorkerProfile
from multi_agent.orchestrator import create_run
from multi_agent.profile import ReasoningEffort, Sandbox

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--profile", default="token-plan")
    parser.add_argument("--reasoning-effort", default="high")
    parser.add_argument("--sandbox", default="workspace-write")
    parser.add_argument("--model", default="qwen3.8-max")
    args = parser.parse_args()
    project_root = args.project_root or str(Path.cwd())
    result = create_run(args.prompt, project_root, WorkerProfile(name=args.profile, sandbox=Sandbox(args.sandbox), model=args.model, reasoning_effort=ReasoningEffort(args.reasoning_effort)))
    print(result.summary)