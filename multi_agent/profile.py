import enum

class ReasoningEffort(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Sandbox(enum.StrEnum):
    READ_ONLY = "read-only"
    WORKSPACE_WRITE = "workspace-write"