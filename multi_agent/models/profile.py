import enum
from dataclasses import dataclass


class ReasoningEffort(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Sandbox(enum.StrEnum):
    READ_ONLY = "read-only"
    WORKSPACE_WRITE = "workspace-write"

class ApprovalPolicy(enum.StrEnum):
    ON_REQUEST = "on-request"
    NEVER = "never"
