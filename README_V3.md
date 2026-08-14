# V3 Runner

Run from the project root:

```bash
.venv/bin/python v3_runner.py --debug   # 2 replications smoke test
.venv/bin/python v3_runner.py           # 50 replications, writes results_v3/
.venv/bin/python -m pytest -q
```

V3 implements the C4 per-AGV next-task feature fix and adds C5 rolling MILP charging allocation with scipy/HiGHS. Existing `results/` and `results_v2/` are not overwritten.
