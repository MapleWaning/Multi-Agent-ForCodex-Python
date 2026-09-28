import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from multi_agent.orchestrator import create_run
from multi_agent.storage import get_run_dir

EVENTS = [
    {"type": "thread.started", "thread_id": "t1"},
    {
        "type": "item.completed",
        "item": {"id": "item_0", "type": "error", "message": "ignored setting"},
    },
    {
        "type": "item.completed",
        "item": {"id": "item_2", "type": "agent_message", "text": "hello"},
    },
    {"type": "turn.completed"},
]


class OrchestratorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.tmp.name)

    def test_completed_saves_run_and_returns_agent_message(self):
        seen = []

        def fake_run(prompt, project_root):
            self.assertEqual(prompt, "用一句话回复：hello")
            self.assertEqual(project_root, r"E:\project\demo")
            run_dir = next(Path(".multi_agent/run").iterdir())
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            seen.append(state["status"])
            return 0, EVENTS, ""

        with patch("multi_agent.orchestrator.run_codex", side_effect=fake_run):
            result = create_run("用一句话回复：hello", r"E:\project\demo")

        self.assertEqual(seen, ["RUNNING"])
        self.assertEqual(result.status, "COMPLETED")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.summary, "hello")

        run_dir = get_run_dir(result.run_id)
        task = json.loads((run_dir / "task.json").read_text(encoding="utf-8"))
        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        saved = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        lines = (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()

        self.assertEqual(task["prompt"], "用一句话回复：hello")
        self.assertEqual(task["project_root"], r"E:\project\demo")
        self.assertEqual(state["status"], "COMPLETED")
        self.assertEqual(saved["summary"], "hello")
        self.assertEqual(saved["exit_code"], 0)
        self.assertEqual([json.loads(line)["type"] for line in lines], [
            "thread.started",
            "item.completed",
            "item.completed",
            "turn.completed",
        ])

    def test_failed_marks_failed_and_uses_stderr(self):
        with patch(
            "multi_agent.orchestrator.run_codex",
            return_value=(1, EVENTS, "codex failed"),
        ) as run_codex:
            result = create_run("改一个文件", r"E:\project\demo")

        run_codex.assert_called_once_with("改一个文件", r"E:\project\demo")
        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.summary, "codex failed")
        state = json.loads(
            (get_run_dir(result.run_id) / "state.json").read_text(encoding="utf-8")
        )
        self.assertEqual(state["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
