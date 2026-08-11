from dataclasses import dataclass, field

@dataclass
class WPTPad:
    pad_id: int
    location: str
    available_s: float = 0.0
    busy_s: float = 0.0
    sessions: int = 0
    max_queue_proxy: int = 0
    wait_s: float = 0.0
    input_kwh: float = 0.0
    delivered_kwh: float = 0.0
