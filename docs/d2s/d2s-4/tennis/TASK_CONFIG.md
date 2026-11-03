# TASK_CONFIG.md — Tennis Ball Manipulation (Demo-to-Sim)

## 1. Task, Hand and Experiment

| Parameter | Value |
|---|---|
| Task | `tennis` |
| Robot | Wuji Hand 2.2 — Right Hand |
| Robot model | `hardware/wuji_hand2_right/` |
| Hardware specification | `hwspec-1.1` (`hardware/hardware_spec.json`) |
| Experiment | `D2S-TENNIS-4` |
| API command | `r2s2r-tennis` |

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
- **Articulated parts (`P`):** 0
- **Object geometry, physical properties and state frame:** `object/SPECS.md`
- **Object–environment contact:** Contact with the floor.

## 4. What Is Not Prescribed

There is no prescribed initial wrist pose, finger configuration, object placement, episode length or wrist workspace in this stage. The wrist is free in position and orientation. Choose the initial conditions and the episode from your reconstruction and record them with your simulation (`demo2sim/SIMULATION.md`).
