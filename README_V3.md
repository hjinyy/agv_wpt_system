# V3 Runner

Run from the project root:

```bash
.venv/bin/python v3_runner.py --debug   # 2 replications smoke test
.venv/bin/python v3_runner.py           # 50 replications, writes results_v3/
.venv/bin/python -m pytest -q
```

V3 implements the C4 per-AGV next-task feature fix and adds C5 15-minute rolling-horizon MILP charging allocation with scipy/HiGHS. C5 optimizes 15 future 60-second charging slots but executes only the first slot, then re-solves. The current C5 objective includes SOC reserve risk, forecast task-impact slack, forecast conflict penalty, and an independent KPI-risk charging term; it does not use the C4 priority score. Existing `results/` and `results_v2/` are not overwritten.
