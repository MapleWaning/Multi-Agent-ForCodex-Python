from dataclasses import dataclass

@dataclass
class PlanArtifact:
    id: str
    filename: str
    description: str
    content: str

@dataclass
class PlanTask:
    id: str
    title: str
    objective: str
    instructions: str
    dependencies: list[str]
    inputs: list[str]
    expected_outputs: list[str]
    acceptance_criteria: list[str]

@dataclass
class Plan:
    objective: str
    summary: str
    artifacts: list[PlanArtifact]
    tasks: list[PlanTask]
    acceptance_criteria: list[str]