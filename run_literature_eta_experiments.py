from __future__ import annotations

from pathlib import Path
from copy import deepcopy
import json
import shutil
import numpy as np
import pandas as pd

import v2_runner
import v3_runner
import v3_extended_experiments as v3ext

_ORIGINAL_LOAD_CFG = v2_runner.load_cfg

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results_v_lit_eta'
FIG_OUT = ROOT / 'results_v_lit_eta_figures'

MISALIGNMENT_MM = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
EFFICIENCY_PCT = [92.1, 92.4, 92.5, 92.8, 92.7, 92.5, 92.6, 91.7, 90.8, 89.4, 87.9]
EFFICIENCY = [x / 100.0 for x in EFFICIENCY_PCT]


def literature_eta_values(cfg):
    """Return the literature AGV-WPT system-efficiency table directly.

    The rest of the simulator still uses the existing discrete eta_state flow.
    Because the literature table supplies states but no occurrence probabilities,
    the states are sampled uniformly across the supplied misalignment values.
    """
    return np.array(cfg['efficiency_states'].get('literature_eff', EFFICIENCY), dtype=float)


def load_lit_cfg():
    cfg = _ORIGINAL_LOAD_CFG()
    cfg = deepcopy(cfg)
    cfg['efficiency_states'] = {
        'labels': [f'misalignment_{m}mm' for m in MISALIGNMENT_MM],
        'misalignment_mm': MISALIGNMENT_MM,
        'literature_eff': EFFICIENCY,
        'efficiency_pct': EFFICIENCY_PCT,
        'probabilities': [1.0 / len(EFFICIENCY)] * len(EFFICIENCY),
        'source_note': 'Literature-based AGV WPT system efficiency table supplied by user.',
    }
    cfg['eta_input_source'] = 'literature_agv_wpt_table'
    return cfg


def patch_modules():
    # Replace only the WPT efficiency input/model hook and output folders.
    v2_runner.eta_values = literature_eta_values
    v3_runner.eta_values = literature_eta_values
    v2_runner.load_cfg = load_lit_cfg
    v3_runner.load_cfg = load_lit_cfg
    v3ext.load_cfg = load_lit_cfg
    v3_runner.RESULTS = OUT
    v3ext.OUT = OUT


def write_lit_fig_script():
    src = ROOT / 'create_v3_main_figures.py'
    dst = ROOT / 'create_lit_eta_figures.py'
    text = src.read_text(encoding='utf-8')
    text = text.replace("SRC = ROOT / 'results_v3'", "SRC = ROOT / 'results_v_lit_eta'")
    text = text.replace("OUT = ROOT / 'results_v3_figures'", "OUT = ROOT / 'results_v_lit_eta_figures'")
    text = text.replace("if SRC.name != 'results_v3':\n    raise RuntimeError(f'Invalid source directory for V3 figures: {SRC}')\n", "if SRC.name != 'results_v_lit_eta':\n    raise RuntimeError(f'Invalid source directory for literature-eta figures: {SRC}')\n")
    text = text.replace('Generated V3-only figures', 'Generated literature-eta figures')
    text = text.replace('V3 Base', 'Lit-eta Base')
    text = text.replace('V3 Primary', 'Lit-eta Primary')
    text = text.replace('Figure 1. V3 Base vs Primary Challenge', 'Figure 1. Literature-eta Base vs Primary Challenge')
    dst.write_text(text, encoding='utf-8')
    return dst


def summarize_outputs():
    base = pd.read_csv(OUT / 'base_case_runs.csv')
    primary = pd.read_csv(OUT / 'c1_c5_results.csv')
    metrics = ['mean_delay', 'urgent_on_time_rate', 'completion_rate', 'wpt_loss', 'fleet_min_soc', 'charging_wait', 'mean_efficiency']
    base_summary = base.groupby('strategy')[metrics].mean().round(4)
    primary_summary = primary.groupby('strategy')[metrics].mean().round(4)
    base_summary.to_csv(OUT / 'base_case_summary.csv')
    primary_summary.to_csv(OUT / 'primary_challenge_summary.csv')
    c3c4 = pd.DataFrame({
        'metric': metrics,
        'C3': [primary_summary.loc['C3', m] for m in metrics],
        'C4': [primary_summary.loc['C4', m] for m in metrics],
        'C4_minus_C3': [primary_summary.loc['C4', m] - primary_summary.loc['C3', m] for m in metrics],
    })
    c3c4.to_csv(OUT / 'c3_c4_primary_lit_eta_comparison.csv', index=False)
    meta = {
        'output_folder': str(OUT),
        'figure_folder': str(FIG_OUT),
        'change_scope': 'Only WPT efficiency input table replaced; scenarios, strategies, reps, metrics, and result CSV formats kept unchanged.',
        'misalignment_mm': MISALIGNMENT_MM,
        'efficiency_pct': EFFICIENCY_PCT,
        'discrete_state_probability_assumption': 'uniform across the 11 supplied literature misalignment states because no occurrence probabilities were supplied',
        'replications': 50,
    }
    (OUT / 'literature_eta_metadata.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
    return base_summary, primary_summary, c3c4


def main(debug=False):
    patch_modules()
    OUT.mkdir(exist_ok=True)
    FIG_OUT.mkdir(exist_ok=True)
    # Preserve older literature-eta runs if present by moving them aside instead of overwriting silently.
    existing = [p for p in OUT.iterdir()] if OUT.exists() else []
    if existing and not debug:
        backup = ROOT / 'results_v_lit_eta_previous'
        if backup.exists():
            shutil.rmtree(backup)
        shutil.copytree(OUT, backup)
    v3_runner.main(debug=debug)
    v3ext.main(debug=debug)
    fig_script = write_lit_fig_script()
    # Execute generated figure script in-process namespace.
    ns = {'__name__': '__main__', '__file__': str(fig_script)}
    exec(compile(fig_script.read_text(encoding='utf-8'), str(fig_script), 'exec'), ns)
    base_summary, primary_summary, c3c4 = summarize_outputs()
    print('\nBASE_SUMMARY')
    print(base_summary.to_string())
    print('\nPRIMARY_SUMMARY')
    print(primary_summary.to_string())
    print('\nC3_C4_PRIMARY')
    print(c3c4.to_string(index=False))


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--debug', action='store_true')
    args = ap.parse_args()
    main(debug=args.debug)
