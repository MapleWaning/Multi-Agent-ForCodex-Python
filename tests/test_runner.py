import unittest
from unittest.mock import MagicMock, patch

from multi_agent.runner import run_codex


class RunnerTest(unittest.TestCase):
    def test_run_codex_uses_project_root_as_cwd(self):
        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = '{"type": "turn.completed"}\n'
        completed.stderr = ""

        with patch("multi_agent.runner.subprocess.run", return_value=completed) as run:
            exit_code, events, stderr = run_codex("hello", r"E:\project\demo")

        self.assertEqual(exit_code, 0)
        self.assertEqual(events, [{"type": "turn.completed"}])
        self.assertEqual(stderr, "")
        self.assertEqual(run.call_args.kwargs["cwd"], r"E:\project\demo")
        self.assertEqual(
            run.call_args.args[0][:4],
            ["codex", "exec", "--json", "--skip-git-repo-check"],
        )
