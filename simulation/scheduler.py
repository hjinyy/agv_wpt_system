import numpy as np

def normalized(x, lo, hi):
    if hi <= lo:
        return 0.0
    return float(np.clip((x-lo)/(hi-lo), 0, 1))

class Scheduler:
    def __init__(self, strategy: str, weights: dict, cfg: dict):
        self.strategy = strategy
        s = sum(float(v) for v in weights.values()) or 1.0
        self.w = {k: float(v)/s for k,v in weights.items()}
        self.cfg = cfg
        self.feature_records = []

    def select_agv(self, agvs, arrival_s):
        # FCFS + first-available AGV, deterministic ID tie-break
        return min(agvs, key=lambda a: (a.available_s, a.agv_id))

    def priority_features(self, agv, idle_gap_s, eta, expected_task_kwh, expected_delay_s):
        max_soc = float(self.cfg['max_soc']); min_soc = float(self.cfg['min_soc'])
        f_soc = normalized(max_soc - agv.soc, 0, max_soc-min_soc)
        f_en = normalized(expected_task_kwh, 0, 0.05)  # base route energy scale; intentionally reports low variance when route fixed
        f_idle = normalized(idle_gap_s, 0, 3600)
        f_eta = normalized(eta, float(self.cfg.get('eta_min',0.35)), float(self.cfg.get('eta_max',0.95)))
        f_delay = normalized(expected_delay_s, 0, 600)
        score = (self.w['w1']*f_soc + self.w['w2']*f_en + self.w['w3']*f_idle + self.w['w4']*f_eta - self.w['w5']*f_delay)
        rec = {'one_minus_soc': f_soc, 'E_next': f_en, 'T_idle': f_idle, 'eta_WPT': f_eta, 'D': f_delay, 'score': score}
        self.feature_records.append(rec)
        return score, rec

    def wants_opportunity(self, agv, idle_gap_s, eta, expected_task_kwh, expected_delay_s):
        if self.strategy == 'C1':
            return False
        if agv.soc >= float(self.cfg['max_soc']) - 1e-9:
            return False
        if idle_gap_s <= 1.0:
            return False
        if self.strategy == 'C2':
            return True
        if self.strategy == 'C3':
            return agv.soc < 0.88
        if self.strategy == 'C4':
            score,_ = self.priority_features(agv, idle_gap_s, eta, expected_task_kwh, expected_delay_s)
            return (agv.soc <= float(self.cfg['critical_soc'])) or score > 0.12
        return False
