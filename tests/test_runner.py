import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from multi_agent.agents.codex_runner import run_codex
from multi_agent.exceptions import WorkerProviderError
from multi_agent.models import WorkerProfile
from multi_agent.models.profile import ApprovalPolicy, ReasoningEffort, Sandbox


def worker_profile() -> WorkerProfile:
    return WorkerProfile(
        name="token-plan",
        sandbox=Sandbox.WORKSPACE_WRITE,
        model="qwen3.8-max",
        reasoning_effort=ReasoningEffort.HIGH,
        approval_policy=ApprovalPolicy.ON_REQUEST,
        context_window=1000000,
        provider_name="LAB TOKEN PLAN",
        base_url="https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
        wire_api="responses",
        env_key="TOKENPLAN_API_KEY",
    )


class RunnerTest(unittest.TestCase):
    def test_run_codex_uses_project_root_as_cwd(self):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = '{"type": "turn.completed"}\n'
        completed.stderr = ""

        with patch("multi_agent.agents.codex_runner.subprocess.run", return_value=completed) as run:
            exit_code, events, stderr = run_codex("hello", r"E:\project\demo", worker_profile())

        self.assertEqual(exit_code, 0)
        self.assertEqual(events, [{"type": "turn.completed"}])
        self.assertEqual(stderr, "")
        self.assertEqual(run.call_args.kwargs["cwd"], r"E:\project\demo")
        self.assertEqual(
            run.call_args.args[0],
            [
                "codex", "exec",
                "--json",
                "--skip-git-repo-check",
                "--sandbox", "workspace-write",
                "-m", "qwen3.8-max",
                "-c", 'model_provider="token-plan"',
                "-c", 'model_reasoning_effort="high"',
                "-c", 'approval_policy="on-request"',
                "-c", "model_context_window=1000000",
                "-c", 'model_providers.token-plan.name="LAB TOKEN PLAN"',
                "-c", 'model_providers.token-plan.base_url="https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"',
                "-c", 'model_providers.token-plan.wire_api="responses"',
                "-c", 'model_providers.token-plan.env_key="TOKENPLAN_API_KEY"',
                "hello",
            ],
        )

    def test_architect_omits_provider_endpoint(self):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = ""
        completed.stderr = ""
        architect = WorkerProfile(
            name="openai",
            sandbox=Sandbox.READ_ONLY,
            model="gpt-6-astra",
            reasoning_effort=ReasoningEffort.MEDIUM,
            approval_policy=ApprovalPolicy.NEVER,
            forced_login_method="chatgpt",
        )

        schema_file = Path(r"E:\project\demo\schema.json")
        with patch("multi_agent.agents.codex_runner.subprocess.run", return_value=completed) as run:
            run_codex("做一份方案", r"E:\project\demo", architect, schema=True, schema_file=schema_file)

        command = run.call_args.args[0]
        self.assertEqual(
            command,
            [
                "codex", "exec",
                "--json",
                "--skip-git-repo-check",
                "--sandbox", "read-only",
                "-m", "gpt-6-astra",
                "-c", 'model_provider="openai"',
                "-c", 'model_reasoning_effort="medium"',
                "-c", 'approval_policy="never"',
                "--output-schema", str(schema_file),
                "-c", 'forced_login_method="chatgpt"',
                "做一份方案",
            ],
        )
        self.assertNotIn("model_providers.openai.base_url", " ".join(command))

    def test_missing_codex_is_provider_error(self):
        with patch(
            "multi_agent.agents.codex_runner.subprocess.run",
            side_effect=FileNotFoundError("codex"),
        ):
            with self.assertRaises(WorkerProviderError) as raised:
                run_codex("hello", r"E:\project\demo", worker_profile())

        self.assertEqual(raised.exception.code, "codex_not_found")
        self.assertIsInstance(raised.exception.__cause__, FileNotFoundError)

    def test_start_failure_is_provider_error(self):
        with patch(
            "multi_agent.agents.codex_runner.subprocess.run",
            side_effect=PermissionError("access denied"),
        ):
            with self.assertRaises(WorkerProviderError) as raised:
                run_codex("hello", r"E:\project\demo", worker_profile())

        self.assertEqual(raised.exception.code, "codex_start_failed")

    def test_invalid_jsonl_is_provider_error(self):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = "not-json\n"
        completed.stderr = ""

        with patch("multi_agent.agents.codex_runner.subprocess.run", return_value=completed):
            with self.assertRaises(WorkerProviderError) as raised:
                run_codex("hello", r"E:\project\demo", worker_profile())

        self.assertEqual(raised.exception.code, "invalid_jsonl")
        self.assertIn("not-json", raised.exception.message)
