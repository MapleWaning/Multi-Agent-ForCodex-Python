import io
import unittest
from pathlib import Path
from unittest.mock import patch

from multi_agent.cli import main
from multi_agent.models import TaskResult


def completed_result() -> TaskResult:
    return TaskResult(
        run_id="run-1",
        status="COMPLETED",
        exit_code=0,
        summary="hello",
    )


class CliTest(unittest.TestCase):
    def test_passes_prompt_and_project_root(self):
        with (
            patch("multi_agent.cli.create_run", return_value=completed_result()) as create_run,
            patch(
                "sys.argv",
                ["multi_agent", "--prompt", "用一句话回复：hello", "--project-root", r"E:\project\demo"],
            ),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            main()

        create_run.assert_called_once_with("用一句话回复：hello", r"E:\project\demo")
        self.assertEqual(stdout.getvalue().strip(), "hello")

    def test_project_root_defaults_to_cwd(self):
        with (
            patch("multi_agent.cli.create_run", return_value=completed_result()) as create_run,
            patch("sys.argv", ["multi_agent", "--prompt", "hello"]),
            patch("sys.stdout", new_callable=io.StringIO),
        ):
            main()

        create_run.assert_called_once_with("hello", str(Path.cwd()))

    def test_missing_prompt_exits_before_orchestrator(self):
        with (
            patch("multi_agent.cli.create_run") as create_run,
            patch("sys.argv", ["multi_agent"]),
            self.assertRaises(SystemExit) as raised,
        ):
            main()

        self.assertEqual(raised.exception.code, 2)
        create_run.assert_not_called()
