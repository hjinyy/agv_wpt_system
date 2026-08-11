from __future__ import annotations
import math, json
from dataclasses import asdict
from pathlib import Path
import numpy as np
import pandas as pd
import simpy  # imported to satisfy/reveal DES dependency; lightweight event accounting is implemented below
from .agv import AGVState
from .wpt_pad import WPTPad
from .task import Task
from .energy_model import EnergyModel
from .scheduler import Scheduler

STRATEGIES = ['C1','C2','C3','C4']

def make_pad_locations(n):
    loc=[]
    for i in range(n):
        if n == 1:
            loc.append('staging')
        elif n == 2:
            loc.append('staging' if i==0 else 'picking')
        else:
            loc.append('staging' if i % 2 == 0 else 'picking')
    return loc

class WPTAGVSimulation:
    def __init__(self, cfg, strategy='C4', seed=1007, tasks=None, init_socs=None, eta_states=None, label='base'):
        self.cfg = dict(cfg)
        self.strategy = strategy
        self.seed = int(seed)
        self.rng = np.random.default_rng(seed)
        self.label = label
        self.env = simpy.Environment()
        self.energy = EnergyModel(self.cfg)
        self.scheduler = Scheduler(strategy, self.cfg['weights'], self.cfg)
        self.operation_s = float(self.cfg['operation_hours'])*3600
        self.n_agvs = int(self.cfg['n_agvs'])
        self.pads = [WPTPad(i+1, loc) for i,loc in enumerate(make_pad_locations(int(self.cfg['n_pads'])))]
        if init_socs is None:
            init_socs = self.rng.uniform(self.cfg['initial_soc_min'], self.cfg['initial_soc_max'], self.n_agvs)
        self.agvs = [AGVState(i+1, float(init_socs[i])) for i in range(self.n_agvs)]
        for a in self.agvs: a.record(0)
        self.tasks = tasks if tasks is not None else self.generate_tasks(eta_states)
        self.completed_tasks=[]
        self.completed_times=[]
        self.delays=[]
        self.queue_waits=[]
        self.charging_waits=[]
        self.charge_sessions=[]
        self.feature_records=[]
        self.max_queue_proxy=0

    def generate_tasks(self, eta_states=None):
        lam_s = float(self.cfg['task_arrival_rate_per_h'])/3600.0
        t=0.0; tasks=[]; i=0
        probs = np.array(self.cfg['efficiency_states']['probabilities'], dtype=float); probs=probs/probs.sum()
        while t < self.operation_s:
            t += float(self.rng.exponential(1.0/lam_s))
            if t >= self.operation_s: break
            pp = int(self.rng.integers(1, int(self.cfg['n_picking_points'])+1))
            st = int(self.rng.choice(len(probs), p=probs)) if eta_states is None else int(eta_states[i])
            tasks.append(Task(i+1,t,pp,st)); i += 1
        return tasks

    def task_duration_s(self):
        return 2*self.cfg['picking_staging_distance_m']/self.cfg['agv_speed_mps'] + self.cfg['picking_service_s'] + self.cfg['staging_service_s']

    def task_energy_kwh(self):
        dur = self.task_duration_s(); dist=2*self.cfg['picking_staging_distance_m']
        tr, aux_move = self.energy.move_energy(dist, 2*self.cfg['picking_staging_distance_m']/self.cfg['agv_speed_mps'])
        aux_srv = self.energy.service_aux(self.cfg['picking_service_s']+self.cfg['staging_service_s'])
        return tr + aux_move + aux_srv

    def eta_for_task(self, task):
        vals = self.energy.efficiency_values({**self.cfg['efficiency_states'], 'eta_base': self.cfg['eta_base'], 'eta_min': self.cfg['eta_min'], 'eta_max': self.cfg['eta_max']})
        if not self.cfg.get('variable_efficiency', True):
            return float(self.cfg['eta_base'])
        return float(vals[task.eta_state])

    def choose_pad(self, earliest_s=0.0, mandatory=False):
        # proxy queue: pads not yet free at requested time
        q=sum(1 for p in self.pads if p.available_s > earliest_s)
        self.max_queue_proxy=max(self.max_queue_proxy,q)
        p=min(self.pads, key=lambda x:(x.available_s, x.pad_id))
        start=max(earliest_s, p.available_s)
        wait=max(0.0, p.available_s-earliest_s)
        return p,start,wait

    def apply_detour(self, agv, t0):
        dist=2*float(self.cfg['zone_pad_distance_m'])
        dur=dist/float(self.cfg['agv_speed_mps'])
        tr,aux=self.energy.move_energy(dist,dur)
        agv.available_s=t0+dur
        agv.detour_m += dist
        self.energy.consume(agv,tr,aux)
        return dur

    def charge(self, agv, earliest_s, available_until_s, eta, mandatory=False):
        if agv.soc >= self.cfg['max_soc']-1e-9: return earliest_s,0,0
        pad,start,wait=self.choose_pad(earliest_s, mandatory)
        if not mandatory and start >= available_until_s:
            return earliest_s, wait, 1
        if wait>0:
            agv.wait_charge_s += wait; pad.wait_s += wait; self.charging_waits.append(wait)
        # detour included before pad occupation; for mandatory may delay task
        self.apply_detour(agv, start)
        start = agv.available_s
        target_kwh=(self.cfg['max_soc']-agv.soc)*self.cfg['battery_kwh']
        max_dur = target_kwh/(self.cfg['wpt_power_kw']*eta)*3600 if eta>0 else 0
        if mandatory:
            dur=max_dur
        else:
            dur=max(0.0, min(max_dur, available_until_s-start))
        if dur <= 0: return start, wait, 1
        input_kwh=self.cfg['wpt_power_kw']*dur/3600
        delivered=input_kwh*eta
        # avoid overcharge
        delivered=min(delivered, target_kwh)
        actual_dur=delivered/(self.cfg['wpt_power_kw']*eta)*3600 if eta>0 else 0
        pad.available_s=start+actual_dur; pad.busy_s += actual_dur; pad.sessions += 1; pad.input_kwh += input_kwh; pad.delivered_kwh += delivered
        agv.soc=min(self.cfg['max_soc'], agv.soc + delivered/self.cfg['battery_kwh'])
        agv.charge_s += actual_dur; agv.wpt_input_kwh += input_kwh; agv.delivered_kwh += delivered; agv.wpt_loss_kwh += max(0,input_kwh-delivered)
        if mandatory:
            agv.mandatory_charge_s += actual_dur; agv.mandatory_energy_kwh += delivered
        else:
            agv.opportunity_charge_s += actual_dur; agv.opp_energy_kwh += delivered
        agv.available_s=start+actual_dur; agv.record(agv.available_s)
        self.charge_sessions.append({'agv':agv.agv_id,'pad':pad.pad_id,'start_s':start,'duration_s':actual_dur,'eta':eta,'mandatory':mandatory,'delivered_kwh':delivered})
        return agv.available_s, wait, 0

    def consume_task(self, agv, start_s):
        dist=2*self.cfg['picking_staging_distance_m']; travel_s=dist/self.cfg['agv_speed_mps']; service_s=self.cfg['picking_service_s']+self.cfg['staging_service_s']
        tr,aux_m=self.energy.move_energy(dist,travel_s); aux_s=self.energy.service_aux(service_s)
        agv.available_s=start_s+self.task_duration_s()
        self.energy.consume(agv,tr,aux_m+aux_s)
        agv.completed += 1

    def run(self):
        phys = self.task_duration_s()
        expected_energy=self.task_energy_kwh()
        for task in self.tasks:
            agv=self.scheduler.select_agv(self.agvs, task.arrival_s)
            eta=self.eta_for_task(task)
            # opportunity while idle before arrival/start
            idle_gap=max(0.0, task.arrival_s-agv.available_s)
            if idle_gap>0:
                agv.idle_s += idle_gap
                if self.scheduler.wants_opportunity(agv, idle_gap, eta, expected_energy, 0.0):
                    self.charge(agv, agv.available_s, task.arrival_s, eta, mandatory=False)
            start=max(task.arrival_s, agv.available_s)
            # C1/C4 safety mandatory if critical or insufficient estimated next-task energy + reserve
            need_soc = expected_energy/self.cfg['battery_kwh'] + self.cfg['min_soc']
            mandatory = (self.strategy=='C1' and agv.soc <= self.cfg['critical_soc']) or (self.strategy in ['C4'] and agv.soc <= self.cfg['critical_soc']) or (agv.soc < need_soc)
            if mandatory:
                agv.stops += int(agv.soc < self.cfg['min_soc'])
                self.charge(agv, start, math.inf, eta, mandatory=True)
                start=agv.available_s
            delay=(start+phys) - (task.arrival_s+phys)
            self.delays.append(delay); self.queue_waits.append(max(0.0,start-task.arrival_s))
            self.consume_task(agv,start)
            self.completed_tasks.append(task.task_id)
            self.completed_times.append(agv.available_s)
        return self.metrics()

    def metrics(self):
        requested=len(self.tasks); completed=sum(1 for t in self.completed_times if t <= self.operation_s)
        pad_utils=[p.busy_s/self.operation_s for p in self.pads]
        wpt_in=sum(a.wpt_input_kwh for a in self.agvs); delivered=sum(a.delivered_kwh for a in self.agvs)
        out={
            'scenario': self.label.split(':')[0], 'scenario_value': self.label.split(':')[-1], 'strategy': self.strategy, 'seed': self.seed,
            'requested_tasks': requested, 'completed_tasks': completed,
            'throughput': completed/(self.operation_s/3600), 'completion_rate': completed/requested*100 if requested else 0,
            'mean_delay': np.mean(self.delays)/60 if self.delays else 0, 'max_delay': np.max(self.delays)/60 if self.delays else 0,
            'idle_ratio': np.mean([a.idle_s/self.operation_s for a in self.agvs]),
            'charging_wait': np.mean(self.charging_waits)/60 if self.charging_waits else 0,
            'low_soc_stops': sum(a.stops for a in self.agvs),
            'traction_energy': sum(a.traction_kwh for a in self.agvs), 'aux_energy': sum(a.aux_kwh for a in self.agvs),
            'wpt_input_energy': wpt_in, 'battery_delivered_energy': delivered, 'wpt_loss': sum(a.wpt_loss_kwh for a in self.agvs),
            'mean_efficiency': (delivered/wpt_in*100) if wpt_in>0 else 0,
            'fleet_min_soc': min(a.min_soc for a in self.agvs)*100,
            'pad_utilization': np.mean(pad_utils)*100 if pad_utils else 0, 'mean_queue': np.mean([1 if w>0 else 0 for w in self.charging_waits]) if self.charging_waits else 0,
            'max_queue': self.max_queue_proxy,
            'total_charging_time_h': sum(a.charge_s for a in self.agvs)/3600,
            'mandatory_charging_energy': sum(a.mandatory_energy_kwh for a in self.agvs), 'opportunity_charging_energy': sum(a.opp_energy_kwh for a in self.agvs),
            'detour_distance_m': sum(a.detour_m for a in self.agvs), 'charging_sessions': len(self.charge_sessions),
        }
        return out

    def agv_results(self):
        rows=[]
        for a in self.agvs:
            rows.append({'agv_id':a.agv_id,'strategy':self.strategy,'scenario':self.label.split(':')[0],'scenario_value':self.label.split(':')[-1],
                         'completed_tasks':a.completed,'min_soc':a.min_soc*100,'idle_ratio':a.idle_s/self.operation_s,'charge_h':a.charge_s/3600,'stops':a.stops,
                         'traction_energy':a.traction_kwh,'aux_energy':a.aux_kwh,'delivered_kwh':a.delivered_kwh,'detour_m':a.detour_m})
        return rows

    def pad_results(self):
        return [{'pad_id':p.pad_id,'location':p.location,'strategy':self.strategy,'scenario':self.label.split(':')[0],'scenario_value':self.label.split(':')[-1],
                 'utilization':p.busy_s/self.operation_s*100,'sessions':p.sessions,'wait_min':p.wait_s/60,'input_kwh':p.input_kwh,'delivered_kwh':p.delivered_kwh} for p in self.pads]

    def soc_trace_frame(self):
        rows=[]
        for a in self.agvs:
            for t,s in a.soc_trace:
                rows.append({'time_h':t/3600,'agv_id':a.agv_id,'soc':s*100,'strategy':self.strategy})
        return pd.DataFrame(rows)


def common_random_inputs(cfg, seed):
    sim=WPTAGVSimulation(cfg,'C1',seed)
    return sim.tasks, [a.soc for a in sim.agvs], [t.eta_state for t in sim.tasks]
