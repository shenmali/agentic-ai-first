from dataclasses import dataclass, field
from typing import Literal

StepKind = Literal["thought", "action", "observation", "final"]


@dataclass
class Step:
    kind: StepKind
    content: str
    tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0


@dataclass
class Trace:
    steps: list[Step] = field(default_factory=list)

    def add(self, step: Step) -> None:
        self.steps.append(step)

    def total_tokens(self) -> int:
        return sum(s.tokens for s in self.steps)

    def total_cost(self) -> float:
        return sum(s.cost_usd for s in self.steps)
