---
name: multi-agent-v01
description: >-
  Dispatches one coding task to the V0.1 Python orchestrator at
  E:\project\Multi-Agent-Python and shows the worker summary.
  Use only when the user explicitly invokes $multi-agent-v01.
  Do not use for ordinary single-agent coding, and do not call the
  PowerShell orchestrator at E:\project\Multi-Agent.
---

# Multi-Agent V0.1 Root

Invocation is explicit. Act only when the user message contains `$multi-agent-v01`.
Otherwise answer as a normal single agent and do not run this CLI.

You are Root. Python decides run state. You do not decide `COMPLETED` or `FAILED`,
and you do not retry, switch profile, or start a second worker.

## What you do

1. Read the user task after `$multi-agent-v01`.
2. Look at the target project only enough to write a concrete worker prompt.
3. Run the command below from `E:\project\Multi-Agent-Python`.
4. Show the command's stdout to the user. That stdout is the worker summary.

Do not implement the task yourself. Do not review the worker's code.

## Command

`--project-root` is the project the worker may edit. The shell's current directory
stays the orchestrator repo so `python -m multi_agent` can import.

```powershell
Set-Location E:\project\Multi-Agent-Python
D:\miniconda\python.exe -m multi_agent `
  --project-root "<target project>" `
  --profile token-plan `
  --sandbox workspace-write `
  --model deepseek-v4.1-flash `
  --reasoning-effort high `
  --prompt "<worker prompt>"
```

Keep those profile, sandbox, model, and reasoning values. Do not add other Codex flags.

## Worker prompt

Write the prompt so the worker can finish alone. Include:

- the user goal
- the target project path
- which files or behavior to change
- which test to run
- a request that the final message state what changed, which test ran, and any known problem

The CLI prints that final message. Do not read `.multi_agent/run/` unless the command fails
and stdout is empty.
