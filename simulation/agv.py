from dataclasses import dataclass, field

@dataclass
class AGVState:
    agv_id: int
    soc: float
    available_s: float = 0.0
    idle_s: float = 0.0
    charge_s: float = 0.0
    mandatory_charge_s: float = 0.0
    opportunity_charge_s: float = 0.0
    wait_charge_s: float = 0.0
    traction_kwh: float = 0.0
    aux_kwh: float = 0.0
    wpt_input_kwh: float = 0.0
    delivered_kwh: float = 0.0
    wpt_loss_kwh: float = 0.0
    opp_energy_kwh: float = 0.0
    mandatory_energy_kwh: float = 0.0
    detour_m: float = 0.0
    min_soc: float = 1.0
    stops: int = 0
    completed: int = 0
    soc_trace: list = field(default_factory=list)

    def record(self, t: float):
        self.min_soc = min(self.min_soc, self.soc)
        # keep trace compact but sufficient
        self.soc_trace.append((float(t), float(self.soc)))
