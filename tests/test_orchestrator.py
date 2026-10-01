import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from multi_agent.core.orchestrator import create_run
from multi_agent.exceptions import OrchestratorError
from multi_agent.models import WorkerProfile
from multi_agent.models.profile import ApprovalPolicy, ReasoningEffort, Sandbox
from multi_agent.models.states import OrchestrationEvent as OrchestrationEventType
from multi_agent.models.states import RunStatus, TaskStatus
from multi_agent.storage.executions import get_execution_for_run
from multi_agent.storage.orchestration_events import get_orchestration_events
from multi_agent.storage.runs import get_run
from multi_agent.storage.tasks import list_tasks

PLAN = {
    "objective": "完成接口",
    "summary": "先写契约",
    "artifacts": [],
    "tasks": [
        {
            "id": "write-api",
            "title": "写接口",
            "objective": "提供查询",
            "instructions": "按契约实现",
            "dependencies": [],
            "inputs": [],
            "expected_outputs": [],
            "acceptance_criteria": ["返回 200"],
        },
        {
            "id": "write-test",
            "title": "写测试",
            "objective": "覆盖查询",
            "instructions": "补测试",
            "dependencies": ["write-api"],
            "inputs": [],
            "expected_outputs": [],
            "acceptance_criteria": ["测试通过"],
        },
    ],
    "acceptance_criteria": ["接口可调用"],
}


def events(text: str) -> list[dict]:
    return [
        {"type": "thread.started", "thread_id": "t1"},
        {
            "type": "item.completed",
            "item": {"id": "item_2", "type": "agent_message", "text": text},
        },
        {"type": "turn.completed"},
    ]


def worker_profile() -> WorkerProfile:
    return WorkerProfile(
        name="token-plan",
        sandbox=Sandbox.WORKSPACE_WRITE,
        model="qwen3.8-max",
        reasoning_effort=ReasoningEffort.HIGH,
        approval_policy=ApprovalPolicy.ON_REQUEST,
    )


def current_status(table: str) -> str:
    connection = sqlite3.connect(".multi_agent/multi_agent.db")
    try:
        row = connection.execute(f"SELECT status FROM {table}").fetchone()
    finally:
        connection.close()
    return row[0]


class OrchestratorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.tmp.name)

    def test_completed_persists_plan_and_allocates_tasks(self):
        seen = []

        def fake_run(prompt, project_root, profile, schema=False, schema_file=None):
            self.assertEqual(prompt, "用一句话回复：hello")
            self.assertEqual(project_root, self.tmp.name)
            seen.append((current_status("runs"), current_status("executions"), current_status("tasks")))
            return 0, events(json.dumps(PLAN, ensure_ascii=False)), ""

        with patch("multi_agent.core.orchestrator.run_codex", side_effect=fake_run):
            result, summary = create_run("用一句话回复：hello", self.tmp.name, worker_profile())

        self.assertEqual(seen, [("ARCHITECT_RUNNING", "RUNNING", "RUNNING")])
        self.assertEqual(result.status, RunStatus.WAITING_APPROVAL)
        self.assertIn("write-api", summary)
        self.assertTrue(Path(result.plan_path).is_file())
        self.assertEqual(get_run(result.id).status, RunStatus.WAITING_APPROVAL)

        execution = get_execution_for_run(result.id)
        self.assertEqual(execution.status, "COMPLETED")
        self.assertEqual(execution.exit_code, 0)
        self.assertIn("write-api", execution.summary)

        tasks = list_tasks(result.id)
        self.assertEqual([task.task_type for task in tasks], ["ARCHITECT", "WORKER", "WORKER"])
        self.assertEqual(tasks[0].status, TaskStatus.COMPLETED)
        self.assertEqual([task.status for task in tasks[1:]], [TaskStatus.PENDING, TaskStatus.PENDING])
        self.assertTrue(tasks[1].content_path.endswith("write-api.md"))
        self.assertTrue(tasks[2].content_path.endswith("write-test.md"))
        recorded = get_orchestration_events(result.id)
        self.assertEqual(
            [event.event_type for event in recorded],
            [
                OrchestrationEventType.RUN_CREATED,
                OrchestrationEventType.ARCHITECT_STARTED,
                OrchestrationEventType.ARCHITECT_COMPLETED,
                OrchestrationEventType.PLAN_READY,
                OrchestrationEventType.WAITING_APPROVAL,
            ],
        )
        self.assertEqual(recorded[0].payload, f"工作流：{result.id} 启动")
        self.assertTrue(all(event.payload.startswith(f"工作流：{result.id} ") for event in recorded))

    def test_failed_marks_run_and_execution_failed(self):
        with patch(
            "multi_agent.core.orchestrator.run_codex",
            return_value=(1, events("ignored"), "codex failed"),
        ) as run_codex:
            result, summary = create_run("改一个文件", self.tmp.name, worker_profile())

        run_codex.assert_called_once_with("改一个文件", self.tmp.name, worker_profile(), False, None)
        self.assertEqual(result.status, RunStatus.FAILED)
        self.assertEqual(summary, "ignored")
        self.assertIsNone(result.plan_path)
        execution = get_execution_for_run(result.id)
        self.assertEqual(execution.status, "FAILED")
        self.assertEqual(execution.exit_code, 1)
        self.assertEqual(execution.summary, "codex failed")
        tasks = list_tasks(result.id)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].status, TaskStatus.FAILED)
        self.assertEqual(
            [event.event_type for event in get_orchestration_events(result.id)],
            [
                OrchestrationEventType.RUN_CREATED,
                OrchestrationEventType.ARCHITECT_STARTED,
                OrchestrationEventType.ARCHITECT_FAILED,
                OrchestrationEventType.RUN_FAILED,
            ],
        )

    def test_invalid_plan_fails_the_run(self):
        with patch(
            "multi_agent.core.orchestrator.run_codex",
            return_value=(0, events("hello"), ""),
        ):
            with self.assertRaises(OrchestratorError):
                create_run("改一个文件", self.tmp.name, worker_profile())

        run = sqlite3.connect(".multi_agent/multi_agent.db")
        try:
            status = run.execute("SELECT status FROM runs").fetchone()[0]
        finally:
            run.close()
        self.assertEqual(status, "FAILED")

    def test_sqlite_error_becomes_orchestrator_error(self):
        with patch(
            "multi_agent.core.orchestrator.save_run",
            side_effect=sqlite3.OperationalError("unable to open database file"),
        ):
            with self.assertRaises(OrchestratorError) as raised:
                create_run("改一个文件", self.tmp.name, worker_profile())

        self.assertIsInstance(raised.exception.__cause__, sqlite3.OperationalError)


if __name__ == "__main__":
    unittest.main()
