# TASK_CONFIG.md — Plug Manipulation (Demo-to-Sim)

## 1. Task, Hand and Experiment

| Parameter | Value |
|---|---|
| Task | `plug` |
| Robot | Wuji Hand 2.2 — Right Hand |
| Robot model | `hardware/wuji_hand2_right/` |
| Hardware specification | `hwspec-1.3` (`hardware/hardware_spec.json`) |
| Experiment | `D2S-PLUG-14` |
| API command | `r2s2r-plug` |
| Time budget | 12 h in total |
| Target rounds | none in this run |

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
- **Table sides:** The left side of the table is world `y > +0.15 m`; the right side is `y ≤ +0.15 m` (+Y is the demonstration camera's left). A plug's side is given by its body center. The plugs start on the right side (`TASK.md`).

See `hardware/SPECS.md` for coordinate conventions.

## 3. Objects

- **Number of objects (`O`):** 2 in the demonstration; 1 in each episode of this run: one plug, like the white plug or the black plug of the video (`TASK.md`).
- **Object index 0:** `plug`. Your policy may observe which of the two plugs it holds (`object_kind`: 0 = like the white plug, 1 = like the black plug).
- **Object geometry, physical properties and state frames:** Not given. Identify each object, estimate its geometry, physical properties and, where it has one, its mechanism from the video and from public information about it (search the web for it), and record each value with its source. Define each object's state frame and record it with your reconstruction (`demo2sim/REFERENCE.md`). Looked-up information is a prior, not ground truth: use it, check it against the video, and record any disagreement and how you resolved it.
- **Object–environment contact:** Contact with the table (the plug starts in the hand above it).

## 4. Start and Episode

The hand's start pose (wrist pose and finger positions) and how the plug starts in it are yours to choose, as `TASK.md` (Deployment) describes. The episode length, the control rate and the wrist workspace are not prescribed in this run: choose them and record them with your simulation (`demo2sim/SIMULATION.md`).
