| Category   | Parameter                        | Symbol      | Value                            | Note                          |
|:-----------|:---------------------------------|:------------|:---------------------------------|:------------------------------|
| Simulation | Operation horizon                | —           | 24 h                             | Frozen final design           |
| Simulation | Final replications               | —           | 50                               | Seeds 8007–8056               |
| AGV        | Speed                            | $v$         | 1.0 m/s                          |                               |
| Service    | Picking service                  | $T_{pick}$  | 45 s                             |                               |
| Service    | Staging service                  | $T_{stage}$ | 45 s                             |                               |
| Battery    | Capacity                         | —           | 5 kWh                            |                               |
| Battery    | Initial SOC                      | —           | Uniform(50%, 80%)                |                               |
| Battery    | Minimum / critical / maximum SOC | —           | 15% / 20% / 90%                  |                               |
| Energy     | Traction / auxiliary             | —           | 0.20 kWh km$^{-1}$ / 0.05 kW     |                               |
| Energy     | Pad detour                       | —           | 5 m one-way                      |                               |
| WPT        | Nominal pad rating               | —           | 3.0 kW                           | [3]-normalized availability   |
| Deadline   | Urgent / normal slack            | —           | 240 s / 480 s                    | $T_{min}+slack$               |
| C4         | Frozen weights                   | —           | 0.00 / 0.70 / 0.00 / 0.00 / 0.30 | SOC / E / idle / P / deadline |
| C5         | Horizon / slot                   | —           | 15 min / 60 s                    |                               |
| C5         | Time limit / MIP gap             | —           | 0.10 s / 0.001                   |                               |
