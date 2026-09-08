# Physical WPT efficiency experiment

## Method

Mutual inductance is computed with a segmented Neumann line integral over each pair of segments in two identical 15-turn 300 mm by 300 mm planar square spirals. The geometry uses a 100 mm inner side, 7.142857 mm turn pitch, 40 mm air gap, and 0-175 mm lateral offset.

Self-inductance uses the Mohan square-spiral current-sheet expression. The electrical link uses a lossy series-series compensated 85 kHz fundamental harmonic approximation with R1 = R2 = 0.15 ohm and FHA AC load resistance 0.623 ohm. This electromagnetic/FHA calculation supplies efficiency states to the DES; the DES itself does not solve the field or circuit equations.

## Derived circuit parameters

- L1 = L2 = 55.414 uH
- C1 = C2 = 63.268 nF
- Q1 = Q2 = 197.299
- M(0 mm) = 28.134 uH; M(175 mm) = 3.062 uH
- SS-FHA efficiency: 80.554% at 0 mm and 77.245% at 175 mm

## DES efficiency-state assumption

Because field data for actual AGV parking error were not supplied, DES samples the eight 0-175 mm states at equal probability. This is a sensitivity assumption, not a measured parking distribution.

## Primary Challenge 50-replication mean

| strategy   |   mean_delay |   urgent_on_time_rate |   completion_rate |   wpt_loss |   fleet_min_soc |   charging_wait |
|:-----------|-------------:|----------------------:|------------------:|-----------:|----------------:|----------------:|
| C1         |      5.73926 |               55.6893 |           99.5788 |    6.9746  |         29.6491 |         29.5502 |
| C2         |      3.2818  |               73.5089 |           99.1091 |    7.96082 |         19.6966 |         20.9691 |
| C3         |      6.33953 |               85.2194 |           97.2182 |    7.15653 |         24.8561 |         57.7781 |
| C4         |      6.89236 |               82.7594 |           96.9676 |    7.47398 |         22.4332 |         59.5473 |
| C5         |      6.98138 |               82.596  |           97.0051 |    7.37393 |         21.3348 |         55.561  |
