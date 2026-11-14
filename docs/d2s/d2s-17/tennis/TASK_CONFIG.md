# TASK_CONFIG.md — Tennis Ball Manipulation (Demo-to-Sim)

## 1. Task, Hand and Experiment

| Parameter | Value |
|---|---|
| Task | `tennis` |
| Robot | Wuji Hand 2.2 — Right Hand |
| Robot model | `hardware/wuji_hand2_right/` |
| Hardware specification | `hwspec-1.3` (`hardware/hardware_spec.json`) |
| Experiment | `D2S-TENNIS-8` |
| API command | `r2s2r-tennis` |
| Time budget | 12 h in total; first delivery within 8 h (`DELIVERY.md` section 7) |
| Target rounds | yes: section 5 and `DELIVERY.md` |

- **Hand specifications:** `hardware/RIGHT_HAND.md`
- **Joint naming:** `r_*`
- **MuJoCo URDF:** `hardware/wuji_hand2_right/urdf/right.urdf`
- **Records:** `export R2S2R_API=r2s2r-tennis`, then `r2s2r-d2s` (`demo2sim/RECORDS.md`).

## 2. World Frame and Scene

### World Frame

- **X:** Forward
- **Y:** Left
- **Z:** Up
- **Floor:** `z = 0`

See `hardware/SPECS.md` for coordinate conventions.

## 3. Objects

- **Number of objects (`O`):** 1
- **Object index 0:** `tennis_ball`
- **Object geometry, physical properties and state frames:** Not given. Identify each object, estimate its geometry, physical properties and, where it has one, its mechanism from the video and from public information about it (search the web for it), and record each value with its source. Define each object's state frame and record it with your reconstruction (`demo2sim/REFERENCE.md`). Looked-up information is a prior, not ground truth: use it, check it against the video, and record any disagreement and how you resolved it.
- **Object–environment contact:** Contact with the floor.

## 4. Start and Episode

The hand's start pose (wrist pose and finger positions) is yours to choose. The objects start as `TASK.md` (Deployment) describes. The episode length, the control rate and the wrist workspace are those of the target (section 5). Record your choices with your simulation (`demo2sim/SIMULATION.md`).

## 5. Target Rounds

| Parameter | Value |
|---|---|
| Trials per round | 3 |
| Episode | 15 s: N = 7500 steps at 500 Hz, from t = 0 (after placement and settle) |
| Wrist workspace (world frame, wrist-frame origin) | x ∈ [−0.30, 0.35], y ∈ [−0.30, 0.30], z ∈ [0.05, 0.65] m |
| Object state frame | `tennis_ball`: origin at the ball's centre, axes fixed to the ball |
| Start pose nominal | `ball_nominal`: position only |
| Additional observations | none |
