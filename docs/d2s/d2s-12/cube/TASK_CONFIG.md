# TASK_CONFIG.md — One-Handed Rubik's Cube (Demo-to-Sim)

## 1. Task, Hand and Experiment

| Parameter | Value |
|---|---|
| Task | `cube` |
| Robot | Wuji Hand 2.2 — Left Hand |
| Robot model | `hardware/wuji_hand2_left/` |
| Hardware specification | `hwspec-1.3L` (`hardware/hardware_spec_left.json`) |
| Experiment | `D2S-CUBE-5` |
| API command | `r2s2r-cube` |
| Time budget | 8 h in total |
| Target rounds | none in this stage |

- **Hand specifications:** `hardware/LEFT_HAND.md`
- **Joint naming:** `l_*`
- **MuJoCo URDF:** `hardware/wuji_hand2_left/urdf/left.urdf`
- **Records:** `export R2S2R_API=r2s2r-cube`, then `r2s2r-d2s` (`demo2sim/RECORDS.md`).

## 2. World Frame and Scene

### World Frame

- **X:** Forward
- **Y:** Left
- **Z:** Up
- **Floor:** `z = 0`

See `hardware/SPECS.md` for coordinate conventions.

## 3. Objects

- **Number of objects (`O`):** 1
- **Object index 0:** `cube`
- **Object geometry, physical properties and state frames:** Not given. Identify each object, estimate its geometry, physical properties and, where it has one, its mechanism from the video and from public information about it (search the web for it), and record each value with its source. Define each object's state frame and record it with your reconstruction (`demo2sim/REFERENCE.md`). Looked-up information is a prior, not ground truth: use it, check it against the video, and record any disagreement and how you resolved it.
- **Object–environment contact:** Contact with the floor.

## 4. Start and Episode

The hand's start pose (wrist pose and finger positions) is yours to choose. The objects start as `TASK.md` (Deployment) describes. The episode length, the control rate and the wrist workspace are not prescribed in this stage: choose them and record them with your simulation (`demo2sim/SIMULATION.md`).
