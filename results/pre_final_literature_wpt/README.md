# Pre-final Literature-WPT Artifacts

Large lossless raw CSV artifacts are stored as `.csv.gz` to stay below the GitHub 100-MB file limit. Decompress with `gzip -dk <file>.csv.gz` when raw rows are required.

| Artifact | Contents |
|---|---|
| `c4_coarse_search.csv.gz` | 17,500 coarse C4 runs |
| `c4_local_refinement.csv.gz` | Local 0.05-transfer C4 candidates |
| `c4_paired_statistics_raw.csv.gz` | C4–C3 paired tuning comparisons |
| `c4_feature_rows.csv.gz` | Full C4 feature records |
| `physical_feature_diagnostics.csv.gz` | Full-versus-no-P ranking diagnostics |
| `wpt_condition_realizations.csv.gz` | Predicted/realized condition records |
| `c4_decision_diagnostics.csv.gz` | C3/C4 decision comparison rows |
| `c5_revalidation_raw.csv` | 1,750 C5 OAT revalidation rows |

All compressed artifacts are lossless. The selected/frozen parameters, summaries, reports, methodology, scenario/rho catalog, and manifest remain directly readable.
