# TASK_CONFIG.md — Plug Manipulation (Demo-to-Sim)

## 1. Task, Hand and Experiment

| Parameter | Value |
|---|---|
| Task | `plug` |
| Robot | Wuji Hand 2.2 — Right Hand |
| Robot model | `hardware/wuji_hand2_right/` |
| Hardware specification | `hwspec-1.3` (`hardware/hardware_spec.json`) |
| Experiment | `D2S-PLUG-10` |
| API command | `r2s2r-plug` |
| Time budget | 12 h in total; first delivery within 8 h (`DELIVERY.md` section 7) |
| Target rounds | yes: section 5 and `DELIVERY.md` |

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

- **Number of objects (`O`):** 2 in the demonstration; 2 or 3 in deployment, varying between trials (`TASK.md`).
- **Object index 0:** `plug_white`
- **Object index 1:** `plug_black`
- **Deployment objects:** each plug is like the white plug or the black plug of the video. Where your task has target rounds, the target reports each plug's kind (section 5).
- **Object geometry, physical properties and state frames:** Not given. Identify each object, estimate its geometry, physical properties and, where it has one, its mechanism from the video and from public information about it (search the web for it), and record each value with its source. Define each object's state frame and record it with your reconstruction (`demo2sim/REFERENCE.md`). Looked-up information is a prior, not ground truth: use it, check it against the video, and record any disagreement and how you resolved it.
- **Object–environment contact:** Contact with the table.

## 4. Start and Episode

The hand's start pose (wrist pose and finger positions) is yours to choose. The objects start as `TASK.md` (Deployment) describes. The episode length, the control rate and the wrist workspace are those of the target (section 5). Record your choices with your simulation (`demo2sim/SIMULATION.md`).

## 5. Target Rounds

| Parameter | Value |
|---|---|
| Trials per round | 6: 3 with two plugs, 3 with three plugs |
| Episode | 30 s: N = 15000 steps at 500 Hz, from t = 0 (after placement and settle) |
| Wrist workspace (world frame, wrist-frame origin) | x ∈ [−0.45, 0.35], y ∈ [−0.40, 0.40], z ∈ [0.03, 0.50] m |
| Object state frame | each plug: origin at the body's centre, +Z along the blades toward their tips, +Y across the gap between the blades |
| Start pose nominal | none (the plugs start on the table) |
| Additional observations | `object_kind` `(O,)` int64: 0 = like the white plug, 1 = like the black plug |
