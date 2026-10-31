# Task Configuration: Plug Handling on a Table

The runtime configuration of this task: which hand variant it uses, its experiment and API command, the episode and its timing, the scene, the initial configuration, the objects, and the exact shapes of the observation and the state record. The shared documents (`CONTRACT.md`, `EVALUATION.md`, `FEEDBACK.md`, `REMOTE_API.md`, `hardware/SPECS.md`, `TOOLS.md`) describe the interfaces with symbols that this document fixes: `N` (control steps), `O` (objects), `P` (parts), `R` (state-record rows) and `$R2S2R_API` (the API command).

## 1. Task, Robot Variant and Experiment

| Parameter | Value |
|---|---|
| Task | `plug`: Plug Handling on a Table (`TASK.md`) |
| Robot variant | **right hand**: Wuji Hand 2.2 right, `hardware/RIGHT_HAND.md`; model files `hardware/wuji_hand2_right/`; joint names `r_*` |
| API command | `r2s2r-plug` (`export R2S2R_API=r2s2r-plug`; `REMOTE_API.md`) |
| Experiment | `R2S2R-PS-PLUG-1`: your key is bound to it; `fetch` returns `R2S2R-PS-PLUG-1_sNN/` (`REMOTE_API.md` section 4) |
| Environment version | `env-3` (`REMOTE_API.md` section 7) |
| Target model | `tm-2` (Wuji Hand 2.2 right) |
| Hardware specification | `hwspec-1.1`, `hardware/hardware_spec.json` (`hardware/SPECS.md` section 7) |
| Local tools for this hand | `r2s2r-preflight` and `r2s2r-hwcheck` use the right hand by default; the MuJoCo calibration adapter takes `--urdf hardware/wuji_hand2_right/urdf/right.urdf` (`TOOLS.md`) |
| Success criteria | no criteria defined for this task: `criteria.id` and `rubric` are `null`, `criteria.status` `undefined`. Every report has `status: criteria_undefined`, and `history` ranks nothing until criteria are published (`SUCCESS.md`). |

## 2. Episode and Timing

| Parameter | Value |
|---|---|
| Episode length | 15 s |
| Control steps `N` | 7,500 policy steps at 500 Hz (`step` 0–7499) |
| Settle phase before step 0 | 1 s, not controlled by the policy (`EVALUATION.md` section 1) |
| State record `state/trajectory.npz` | `R` = 7,501 rows for a complete rollout (rows 0 to `N`) |
| Rollout log `logs/trial_0.npz` | 7,500 rows for a complete rollout |
| Videos | 100 fps, 1,501 frames per view for a complete rollout |
| Wall-clock limit of an evaluation | 45 minutes (trial, verifier and video rendering; exceeded: state `timeout`, `REMOTE_API.md` section 3) |

## 3. Scene and Initial Configuration

- **World frame:** X forward, Y left, Z up (`hardware/SPECS.md` section 3). The tabletop is the plane z = 0; the origin lies on it at the midpoint between the two plugs' initial body centres (`object/SPECS.md`). The table is a 1.20 × 1.20 m block, 0.03 m thick, centred at (0.10, 0.00) with its top face at z = 0; the floor is at z = −0.75 m.
- **Initial wrist pose** (every trial; the root link `r_mount`): position `(-0.260000, -0.080000, 0.090000)` m, orientation (wxyz) `(0.353553, -0.353553, -0.612372, 0.612372)`. Palm down (palm normal −Z), fingers level and pointing along (0.866, 0.5, 0), 9 cm above the table on its near-right side; with the open initial finger configuration `q₀` the fingertips are 3.6–5.6 cm above the table and the hand touches nothing. The executed wrist target starts at this pose (the three entries of the target histories at step 0), and the hand is at rest there at step 0.
- **Palm frame `r_wrist`** at the initial pose: position `(-0.236820, -0.063152, 0.090000)` m, orientation (wxyz) `(0.353548, -0.353558, -0.612370, 0.612375)`.
- **Wrist workspace:** the executed wrist position target is kept inside the box `x ∈ [−0.45, 0.35]`, `y ∈ [−0.40, 0.40]`, `z ∈ [0.03, 0.50]` m (world frame). The hand itself collides with the table top (the plane z = 0 over the table block) and the two plugs; the floor at z = −0.75 m is below the table.
- **Contact flags:** the environment of `object_environment_contact` is the table.
- **Initial objects:** `object/SPECS.md`; the exact initial state is the observation of step 0.

**Initial finger configuration `q₀`** (rad, the joint order of `hardware/RIGHT_HAND.md`). `q₀` is the same in every trial; measured initial positions differ by settling and encoder noise (`CONTRACT.md`).

| # | Joint | q₀ (rad) |
|---|---|---|
| 0 | r_thumb_cmc_flex | 0.3 |
| 1 | r_thumb_cmc_abd | -0.2 |
| 2 | r_thumb_mcp | 0.2 |
| 3 | r_thumb_ip | 0.2 |
| 4 | r_index_finger_mcp_flex | 0.25 |
| 5 | r_index_finger_mcp_abd | 0.0 |
| 6 | r_index_finger_pip | 0.35 |
| 7 | r_index_finger_dip | 0.15 |
| 8 | r_middle_finger_mcp_flex | 0.25 |
| 9 | r_middle_finger_mcp_abd | 0.0 |
| 10 | r_middle_finger_pip | 0.35 |
| 11 | r_middle_finger_dip | 0.15 |
| 12 | r_ring_finger_mcp_flex | 0.25 |
| 13 | r_ring_finger_mcp_abd | 0.0 |
| 14 | r_ring_finger_pip | 0.35 |
| 15 | r_ring_finger_dip | 0.15 |
| 16 | r_pinky_mcp_flex | 0.25 |
| 17 | r_pinky_mcp_abd | 0.0 |
| 18 | r_pinky_pip | 0.35 |
| 19 | r_pinky_dip | 0.15 |

**Cameras** (`FEEDBACK.md` section 5):

| View | Perspective |
|---|---|
| `top` | Above the table region, 1.9 m up, looking down: the whole wrist workspace and both plugs in view |
| `left` | Oblique view from −X (the demonstration camera's side), pitched 40° down, 0.9 m away: plugs, blades and the hand's approach |
| `right` | Level side view from −Y, 1.6 m away: heights above the table, lift and placement |

## 4. Objects, Observation and State Record

- **Objects** (`O` = 2), the order of every `object_*` array: `0 = plug_white`, `1 = plug_black`. Geometry and state frames: `object/SPECS.md`.
- **Parts** (`P` = 0): none (`part_names` and `part_object` are empty).

**Observation** (`act(obs)`, `CONTRACT.md` section 3): the exact key set, shapes and dtypes of this task, as `validate` and `r2s2r-preflight` check them.

| Key | Shape | dtype | Meaning |
|---|---|---|---|
| `q` | `(20,)` | float64 | `CONTRACT.md` section 3 |
| `qd` | `(20,)` | float64 | `CONTRACT.md` section 3 |
| `prev_q_target` | `(3, 20)` | float64 | `CONTRACT.md` section 3 |
| `prev_qd_target` | `(3, 20)` | float64 | `CONTRACT.md` section 3 |
| `wrist_position` | `(3,)` | float64 | `CONTRACT.md` section 3 |
| `wrist_orientation` | `(4,)` | float64 | `CONTRACT.md` section 3 |
| `wrist_linear_velocity` | `(3,)` | float64 | `CONTRACT.md` section 3 |
| `wrist_angular_velocity` | `(3,)` | float64 | `CONTRACT.md` section 3 |
| `prev_wrist_position_target` | `(3, 3)` | float64 | `CONTRACT.md` section 3 |
| `prev_wrist_orientation_target` | `(3, 4)` | float64 | `CONTRACT.md` section 3 |
| `step` | scalar | int | `CONTRACT.md` section 3 (0–7499) |
| `object_position` | `(2, 3)` | float64 | `CONTRACT.md` section 3 |
| `object_orientation` | `(2, 4)` | float64 | `CONTRACT.md` section 3 |
| `object_linear_velocity` | `(2, 3)` | float64 | `CONTRACT.md` section 3 |
| `object_angular_velocity` | `(2, 3)` | float64 | `CONTRACT.md` section 3 |
| `goal_defined` | `(2,)` | int64 | 1 if a goal is defined for the object, else 0; constant |
| `goal_position` | `(2, 3)` | float64 | Goal position of the object's state-frame origin [m]; NaN where undefined or unconstrained; constant |
| `goal_orientation` | `(2, 4)` | float64 | Goal orientation `(w, x, y, z)`; NaN where undefined; constant |
| `goal_free_axis` | `(2, 3)` | float64 | State-frame axis about which rotation is ignored for the goal; zeros = none; constant |

**State record** (`state/trajectory.npz`, `FEEDBACK.md` section 3): the object, contact and task-specific fields of this task (the step, time and wrist fields are as in `FEEDBACK.md`).

| Field | Shape | dtype | Meaning |
|---|---|---|---|
| `object_position`, `object_linear_velocity`, `object_angular_velocity` | `(R, 2, 3)` | float64 | `FEEDBACK.md` section 3 |
| `object_orientation` | `(R, 2, 4)` | float64 | `FEEDBACK.md` section 3 |
| `hand_object_contact`, `object_environment_contact` | `(R, 2)` | bool | `FEEDBACK.md` section 3 (environment: the table) |
| `object_object_contact` | `(R, 2, 2)` | bool | `FEEDBACK.md` section 3 |
| `object_names` | `(2,)` | str | `plug_white`, `plug_black` |
| `part_names`, `part_object` | `(0,)` | str, int64 | empty: this task has no parts |
| `goal_defined` | `(2,)` | int64 | —: 1 if a goal is defined for the object, else 0 (constant: the goal block of the observation) |
| `goal_position` | `(2, 3)` | float64 | m, world: Goal position of the object's state-frame origin; NaN where undefined |
| `goal_orientation` | `(2, 4)` | float64 | world ← state frame: Goal orientation; NaN where undefined |
| `goal_free_axis` | `(2, 3)` | float64 | state frame: Axis about which rotation is ignored for the goal; zeros = none |

**`measurements`** of `verifier/report.json` (`FEEDBACK.md` section 1): none: `measurements` is empty while no criteria are defined.
