from __future__ import annotations
import hashlib,json,platform,subprocess,sys
from pathlib import Path
import pandas as pd,scipy
from rho_pipeline import load_experiment_config
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results'/'pre_final_literature_wpt'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def main():
 data=load_experiment_config();c4=json.loads((OUT/'frozen_c4_parameters.json').read_text());c5=json.loads((OUT/'frozen_c5_parameters.json').read_text());rho=pd.read_csv(OUT/'frozen_rho_catalog.csv');rawc4=pd.read_csv(OUT/'c4_coarse_search.csv');rawc5=pd.read_csv(OUT/'c5_revalidation_raw.csv')
 manifest={'manifest_status':'literature WPT pre-final methodology frozen','methodology_source_sha':git('rev-parse','HEAD'),'archive_pre_tuning_sha':git('rev-parse','archive/pre-literature-wpt-tuning-20260927'),'physical_data_source':'data/wpt_reference/jeebklum_imura_sumpavakup_2026_table2_misalignment_measurements.csv','physical_data_sha256':sha(ROOT/data['physical_source']['table_path']),'tuning_seeds':list(range(7107,7157)),'reserved_final_seeds':list(range(8007,8057)),'seed_overlap':0,'reserved_final_block_accessed':False,'final_evaluation_executed':False,'deadline_rule':data['deadline_model'],'alignment_conditions':data['alignment_conditions'],'prediction_model':data['prediction_model'],'scenario_parameters':data['scenarios'],'rho_catalog':rho.to_dict(orient='records'),'c4':c4,'c5':c5,'run_counts':{'c4_coarse_rows':len(rawc4),'c5_rows':len(rawc5)},'software':{'python':sys.version,'scipy':scipy.__version__,'platform':platform.platform()},'solver':'scipy.optimize.milp / HiGHS','test_status':'see final test command output'}
 (OUT/'frozen_methodology.json').write_text(json.dumps(manifest,indent=2)+'\n')
 lines=['# PRE_FINAL_FREEZE_REPORT','','## Freeze contents','- [3]-based X/Y averaged condition lookup, 3-kW-normalized delivered power, and separate efficiency/loss accounting.','- Controlled misalignment-sensitivity scenarios and zero-mean discrete prediction-error model.','- Controlled urgency-slack deadline rule, selected before C4 tuning.','- C4 and C5 parameters selected with tuning-only seeds.','','## Seed provenance','- Tuning: 7107–7156.','- Reserved unseen final: 8007–8056.','- Overlap: 0; reserved final block accessed: false; final evaluation executed: false.','','## Safety gate','- Consult C4/C5 reports, raw outputs, and final test status. No final-unseen conclusion is claimed in this artifact.']
 (OUT/'PRE_FINAL_FREEZE_REPORT.md').write_text('\n'.join(lines)+'\n');print('PRE_FINAL_MANIFEST_OK')
if __name__=='__main__':main()
