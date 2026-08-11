from dataclasses import dataclass

@dataclass(frozen=True)
class Task:
    task_id: int
    arrival_s: float
    picking_point: int
    eta_state: int
