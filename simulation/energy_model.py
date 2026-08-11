import numpy as np

class EnergyModel:
    def __init__(self, cfg):
        self.e_dist = float(cfg['e_dist_kwh_per_km'])
        self.p_aux = float(cfg.get('p_aux_kw', 0.0))
        self.battery = float(cfg['battery_kwh'])
        self.speed = float(cfg['agv_speed_mps'])

    def move_energy(self, distance_m: float, duration_s: float | None = None):
        if duration_s is None:
            duration_s = distance_m / self.speed
        traction = self.e_dist * distance_m / 1000.0
        aux = self.p_aux * duration_s / 3600.0
        return traction, aux

    def service_aux(self, duration_s: float):
        return self.p_aux * duration_s / 3600.0

    def consume(self, agv, traction_kwh: float, aux_kwh: float):
        total = traction_kwh + aux_kwh
        agv.traction_kwh += traction_kwh
        agv.aux_kwh += aux_kwh
        agv.soc -= total / self.battery
        if agv.soc < 0:
            agv.stops += 1
            agv.soc = 0.0
        agv.record(agv.available_s)
        return total

    def efficiency_values(self, cfg):
        proto = np.array(cfg['prototype_eff'], dtype=float)
        rel = proto / 0.7996
        return np.clip(float(cfg.get('eta_base', 0.90)) * rel, float(cfg.get('eta_min', 0.35)), float(cfg.get('eta_max', 0.95)))
