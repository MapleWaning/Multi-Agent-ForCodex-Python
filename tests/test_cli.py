import io
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from multi_agent.architect.prompt import build_architect_prompt
from multi_agent.cli.start_run import main
from multi_agent.exceptions import WorkerProviderError
from multi_agent.models import Architect, WorkerProfile
from multi_agent.models.profile import ApprovalPolicy, ReasoningEffort, Sandbox


def architect_rows() -> list[Architect]:
    return [
        Architect(
            model="gpt-6-astra",
            reasoning_effort=ReasoningEffort.MEDIUM,
            sandbox=Sandbox.READ_ONLY,
            forced_login_method="chatgpt",
            approval_policy=ApprovalPolicy.NEVER,
            id=1,
        ),
        Architect(
            model="other-model",
            reasoning_effort=ReasoningEffort.HIGH,
            sandbox=Sandbox.WORKSPACE_WRITE,
            forced_login_method="api",
            approval_policy=ApprovalPolicy.ON_REQUEST,
            id=2,
        ),
    ]


def architect_profile() -> WorkerProfile:
    return WorkerProfile(
        name="openai",
        sandbox=Sandbox.READ_ONLY,
        model="gpt-6-astra",
        reasoning_effort=ReasoningEffort.MEDIUM,
        approval_policy=ApprovalPolicy.NEVER,
        forced_login_method="chatgpt",
    )


def completed_result() -> tuple[SimpleNamespace, str]:
    return SimpleNamespace(id="run-1", status="WAITING_APPROVAL", business_errors=[]), "hello"


class CliTest(unittest.TestCase):
    def test_passes_user_task_and_first_architect(self):
        with (
            patch("multi_agent.cli.start_run.list_architects", return_value=architect_rows()),
            patch("multi_agent.cli.start_run.create_run", return_value=completed_result()) as create_run,
            patch("sys.argv", ["multi_agent", "--user-task", "做一份方案", "--project-root", r"E:\project\demo", "--dev-env", "Windows"]),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            main()

        create_run.assert_called_once_with(
            build_architect_prompt("做一份方案", "Windows"),
            r"E:\project\demo",
            architect_profile(),
            schema=True,
            schema_file=Path(__file__).resolve().parents[1] / "multi_agent" / "doc" / "architect_output_schema.json",
            dev_env="Windows",
        )
        self.assertEqual(
            stdout.getvalue().strip(),
            '{"run_id": "run-1", "status": "WAITING_APPROVAL", "summary": "hello"}',
        )

    def test_missing_user_task_exits_before_orchestrator(self):
        with (
            patch("multi_agent.cli.start_run.create_run") as create_run,
            patch("sys.argv", ["multi_agent"]),
            self.assertRaises(SystemExit) as raised,
        ):
            main()

        self.assertEqual(raised.exception.code, 2)
        create_run.assert_not_called()

    def test_missing_architect_prints_error(self):
        with (
            patch("multi_agent.cli.start_run.list_architects", return_value=[]),
            patch("multi_agent.cli.start_run.create_run") as create_run,
            patch("sys.argv", ["multi_agent", "--user-task", "做一份方案", "--project-root", r"E:\project\demo", "--dev-env", "Windows"]),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            main()

        create_run.assert_not_called()
        self.assertEqual(stdout.getvalue().strip(), "Error: 没有可用的 Architect 配置")

    def test_business_error_prints_message_and_summary(self):
        run, summary = completed_result()
        run.business_errors = ["额度耗尽"]
        with (
            patch("multi_agent.cli.start_run.list_architects", return_value=architect_rows()),
            patch("multi_agent.cli.start_run.create_run", return_value=(run, summary)),
            patch("sys.argv", ["multi_agent", "--user-task", "做一份方案", "--project-root", r"E:\project\demo", "--dev-env", "Windows"]),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            main()

        self.assertEqual(
            stdout.getvalue().strip(),
            '额度耗尽\n{"run_id": "run-1", "status": "WAITING_APPROVAL", "summary": "hello"}',
        )

    def test_provider_error_prints_code_and_message(self):
        with (
            patch("multi_agent.cli.start_run.list_architects", return_value=architect_rows()),
            patch(
                "multi_agent.cli.start_run.create_run",
                side_effect=WorkerProviderError("codex_not_found", "codex"),
            ),
            patch("sys.argv", ["multi_agent", "--user-task", "做一份方案", "--project-root", r"E:\project\demo", "--dev-env", "Windows"]),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            main()

        self.assertEqual(stdout.getvalue().strip(), "Error: [codex_not_found] codex")
