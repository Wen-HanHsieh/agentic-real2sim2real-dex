# TASK_CONFIG.md — Plug Manipulation (Demo-to-Sim)

## 1. Task, Hand and Experiment

| Parameter | Value |
|---|---|
| Task | `plug` |
| Robot | Wuji Hand 2.2 — Right Hand |
| Robot model | `hardware/wuji_hand2_right/` |
| Hardware specification | `hwspec-1.1` (`hardware/hardware_spec.json`) |
| Experiment | `D2S-PLUG-4` |
| API command | `r2s2r-plug` |

- **Hand specifications:** `hardware/RIGHT_HAND.md`
- **Joint naming:** `r_*`
- **MuJoCo URDF:** `hardware/wuji_hand2_right/urdf/right.urdf`
- **Records:** `export R2S2R_API=r2s2r-plug`, then `r2s2r-d2s` (`demo2sim/RECORDS.md`).

## 2. World Frame and Scene

### World Frame and Table

- **X:** Forward
- **Y:** Left
- **Z:** Up
- **Tabletop:** `z = 0`
- **Floor:** `z = -0.75 m`
- **World origin:** On the tabletop.

Table geometry:

- **Dimensions:** 1.20 × 1.20 m
- **Thickness:** 0.03 m
- **Center (XY):** `(0.10, 0.00)` m
- **Top surface:** `z = 0`
- **Table sides:** The left side of the table is world `y > +0.15 m`; the right side is `y ≤ +0.15 m` (+Y is the demonstration camera's left). A plug's side is given by its body center (state-frame origin, `object/SPECS.md`). Both plugs start on the right side (`TASK.md`).

See `hardware/SPECS.md` and `object/SPECS.md` for coordinate and object conventions.

## 3. Objects

- **Number of objects (`O`):** 2
- **Object index 0:** `plug_white`
- **Object index 1:** `plug_black`
- **Articulated parts (`P`):** 0
- **Object geometry, physical properties, and state frames:** `object/SPECS.md`
- **Object–environment contact:** Contact with the table.

## 4. What Is Not Prescribed

There is no prescribed initial wrist pose, finger configuration, object placement, episode length or wrist workspace in this stage. The wrist is free in position and orientation. Choose the initial conditions and the episode from your reconstruction and record them with your simulation (`demo2sim/SIMULATION.md`).
