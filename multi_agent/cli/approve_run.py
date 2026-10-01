"""接收审批结果，调用 Orchestrator 的 worker_run。

不在这里启动 Codex，也不在这里写 Plan Package。
"""
import argparse

from multi_agent.core.orchestrator import worker_run
from multi_agent.exceptions import OrchestratorError


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--approve", required=True, choices=["true", "false"])
    args = parser.parse_args()
    try:
        worker_run(args.run_id, args.approve == "true")
    except OrchestratorError as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
