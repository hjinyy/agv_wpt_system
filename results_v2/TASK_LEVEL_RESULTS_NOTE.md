# Large local-only result files

`results_v2/task_level_results.csv` is intentionally excluded from git because the full task-level event table is about 1.6 GB, far above GitHub's normal file-size limits.

The V2 run still produced it locally at:

```text
/home/hy/wpt_agv_opportunity_charging/results_v2/task_level_results.csv
```

A compressed copy was prepared during chat delivery as:

```text
/home/hy/wpt_agv_v2_task_level_results_xz.zip
```

All replication-level summaries, stress-grid results, decision diagnostics, feature diagnostics, figures, and reports are committed to the repository.
