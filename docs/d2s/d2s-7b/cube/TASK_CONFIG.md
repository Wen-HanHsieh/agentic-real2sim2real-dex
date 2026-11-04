# TASK_CONFIG.md — One-Handed Rubik's Cube (Demo-to-Sim)

## 1. Task, Hand and Experiment

| Parameter | Value |
|---|---|
| Task | `cube` |
| Robot | Wuji Hand 2.2 — Left Hand |
| Robot model | `hardware/wuji_hand2_left/` |
| Hardware specification | `hwspec-1.2L` (`hardware/hardware_spec_left.json`) |
| Experiment | `D2S-CUBE-1` |
| API command | `r2s2r-cube` |

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
- **Articulated parts (`P`):** 8
- **Part indices:** `0–7 = cubie0 … cubie7`
- **Part ownership:** All eight cubies belong to object 0.
- **Object geometry, physical properties, mechanics, and state frames:** `object/SPECS.md`
- **Object–environment contact:** Contact with the floor.

## 4. What Is Not Prescribed

There is no prescribed initial wrist pose, finger configuration, object placement, episode length or wrist workspace in this stage. Choose the initial conditions and the episode from your reconstruction and record them with your simulation (`demo2sim/SIMULATION.md`).
