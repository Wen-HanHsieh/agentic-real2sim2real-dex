# TASK_CONFIG.md — Pen Spinning (Demo-to-Sim)

## 1. Task, Hand and Experiment

| Parameter | Value |
|---|---|
| Task | `pen` |
| Robot | Wuji Hand 2.2 — Right Hand |
| Robot model | `hardware/wuji_hand2_right/` |
| Hardware specification | `hwspec-1.3` (`hardware/hardware_spec.json`) |
| Experiment | `D2S-PEN-3` |
| API command | `r2s2r-pen` |
| Target rounds | none in this stage |

- **Hand specifications:** `hardware/RIGHT_HAND.md`
- **Joint naming:** `r_*`
- **MuJoCo URDF:** `hardware/wuji_hand2_right/urdf/right.urdf`
- **Records:** `export R2S2R_API=r2s2r-pen`, then `r2s2r-d2s` (`demo2sim/RECORDS.md`).

## 2. World Frame and Scene

### World Frame

- **X:** Forward
- **Y:** Left
- **Z:** Up
- **Floor:** `z = 0`

See `hardware/SPECS.md` for coordinate conventions.

## 3. Objects

- **Number of objects (`O`):** 1
- **Object index 0:** `pen`
- **Object geometry, physical properties and state frames:** Not given. Identify each object, estimate its geometry, physical properties and, where it has one, its mechanism from the video and from public information about it (search the web for it), and record each value with its source. Define each object's state frame and record it with your reconstruction (`demo2sim/REFERENCE.md`). Looked-up information is a prior, not ground truth: use it, check it against the video, and record any disagreement and how you resolved it.
- **Object–environment contact:** Contact with the floor.

## 4. Start and Episode

The hand's start pose (wrist pose and finger positions) is yours to choose. The objects start as `TASK.md` (Deployment) describes. The episode length, the control rate and the wrist workspace are not prescribed in this stage: choose them and record them with your simulation (`demo2sim/SIMULATION.md`).
