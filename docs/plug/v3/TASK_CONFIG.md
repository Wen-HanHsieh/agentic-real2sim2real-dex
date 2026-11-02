# TASK_CONFIG.md — Plug Manipulation

## 1. Task and Environment

| Parameter | Value |
|---|---|
| Task | `plug` |
| Robot | Wuji Hand 2.2 — Right Hand |
| Robot model | `hardware/wuji_hand2_right/` |
| Hardware specification | `hwspec-1.1` (`hardware/hardware_spec.json`) |
| Target model | `tm-2` |
| Environment | `env-3` |
| Experiment | `R2S2R-PS-PLUG-1` |
| API command | `r2s2r-plug` |
| Success criteria | `SUCCESS.md` |

- **Hand specifications:** `hardware/RIGHT_HAND.md`
- **Joint naming:** `r_*`
- **API setup:** `export R2S2R_API=r2s2r-plug`
- **Policy interface:** `sim2target/CONTRACT.md`
- **Evaluation interface:** `sim2target/REMOTE_API.md`
- **Local tools:** `r2s2r-preflight` and `r2s2r-hwcheck` default to the right hand.
- **MuJoCo URDF:** `hardware/wuji_hand2_right/urdf/right.urdf`
- **Submission records:** The task-bound API key accesses this experiment; fetched submissions use the directory prefix `R2S2R-PS-PLUG-1_sNN/`.

## 2. Episode Configuration

| Parameter | Value |
|---|---|
| Episode duration | 20 s |
| Control frequency | 500 Hz |
| Control steps (`N`) | 10,000 |
| Policy step index | 0–9999 |
| Settle phase | 1 s before step 0 (not policy-controlled) |
| State-record rows (`R`) | 10,001 (initial state + 10,000 steps) |
| Rollout-log rows | 10,000 |
| Video | 100 fps, 2,001 frames per view |
| Evaluation wall-clock limit | 45 min |

- **State record:** `state/trajectory.npz`
- **Rollout log:** `logs/trial_0.npz`
- **Video views:** `top`, `left`, `right`
- **Timeout:** Exceeding the wall-clock limit results in evaluation state `timeout` (`sim2target/REMOTE_API.md`).

## 3. Initial Configuration

### World Frame and Table

- **X:** Forward
- **Y:** Left
- **Z:** Up
- **Tabletop:** `z = 0`
- **Floor:** `z = -0.75 m`
- **World origin:** On the tabletop, midway between the initial body centers of the two plugs.

Table geometry:

- **Dimensions:** 1.20 × 1.20 m
- **Thickness:** 0.03 m
- **Center (XY):** `(0.10, 0.00)` m
- **Top surface:** `z = 0`
- **Table sides:** The left side of the table is world `y > +0.15 m`; the right side is `y ≤ +0.15 m` (+Y is the demonstration camera's left). A plug's side is given by its body center (state-frame origin, `object/SPECS.md`). Both plugs start on the right side.

See `hardware/SPECS.md` and `object/SPECS.md` for coordinate and object conventions.

### Initial Wrist Pose

The hand starts palm-down with open fingers, positioned above the near-right side of the table.

- **Root link:** `r_mount`
- **Position (xyz, m):** `(-0.260000, -0.080000, 0.090000)`
- **Orientation (wxyz):** `(0.353553, -0.353553, -0.612372, 0.612372)`
- **Palm normal:** World −Z
- **Finger direction:** `(0.866, 0.5, 0)`
- **Initial fingertip height:** 3.6–5.6 cm above the table
- **Initial contact:** None

Initial palm frame (`r_wrist`):

- **Position (xyz, m):** `(-0.236820, -0.063152, 0.090000)`
- **Orientation (wxyz):** `(0.353548, -0.353558, -0.612370, 0.612375)`

The executed wrist target starts at the initial root-link pose. The hand is at rest at step 0, and the three initial wrist-target history entries contain this starting target.

### Wrist Workspace

The executed wrist position target is clipped to:

- **X:** `[-0.45, 0.35]` m
- **Y:** `[-0.40, 0.40]` m
- **Z:** `[0.03, 0.50]` m

These bounds apply to the executed wrist position target in the world frame.

The hand can collide with the tabletop and both plugs. The floor lies below the table.

### Initial Finger Configuration

The initial joint targets `q₀` are fixed across trials.

Joint order follows `hardware/RIGHT_HAND.md`.

| Joint | Initial angle (rad) |
|---|---:|
| `r_thumb_cmc_flex` | 0.3 |
| `r_thumb_cmc_abd` | -0.2 |
| `r_thumb_mcp` | 0.2 |
| `r_thumb_ip` | 0.2 |
| `r_index_finger_mcp_flex` | 0.25 |
| `r_index_finger_mcp_abd` | 0.0 |
| `r_index_finger_pip` | 0.35 |
| `r_index_finger_dip` | 0.15 |
| `r_middle_finger_mcp_flex` | 0.25 |
| `r_middle_finger_mcp_abd` | 0.0 |
| `r_middle_finger_pip` | 0.35 |
| `r_middle_finger_dip` | 0.15 |
| `r_ring_finger_mcp_flex` | 0.25 |
| `r_ring_finger_mcp_abd` | 0.0 |
| `r_ring_finger_pip` | 0.35 |
| `r_ring_finger_dip` | 0.15 |
| `r_pinky_mcp_flex` | 0.25 |
| `r_pinky_mcp_abd` | 0.0 |
| `r_pinky_pip` | 0.35 |
| `r_pinky_dip` | 0.15 |

Measured initial joint positions may differ slightly due to settling and encoder noise (`sim2target/CONTRACT.md`).

## 4. Objects and Scene

- **Number of objects (`O`):** 2
- **Object index 0:** `plug_white`
- **Object index 1:** `plug_black`
- **Articulated parts (`P`):** 0
- **Initial object states:** Available in the observation at step 0.
- **Object geometry, physical properties, and state frames:** `object/SPECS.md`
- **Object–environment contact:** Contact with the table.

### Camera Views

| View | Configuration |
|---|---|
| `top` | Above the table region, 1.9 m high, looking downward; shows the wrist workspace and both plugs |
| `left` | Oblique view from −X, pitched 40° downward, 0.9 m away; shows the plugs, blades, and hand approach |
| `right` | Side view from −Y, elevated 20°, 1.6 m away, aimed at `(-0.05, 0.00, 0.20)` m; shows lifting and placement heights |

See `sim2target/FEEDBACK.md` for video and camera-record details.

## 5. Observation and State Record

The exact observation/action semantics are defined in `sim2target/CONTRACT.md`. This section specifies the Plug task's dimensions and record fields.

### Policy Observation

All floating-point arrays use `float64`.

| Keys | Shape per key |
|---|---|
| `q`, `qd` | `(20,)` |
| `prev_q_target`, `prev_qd_target` | `(3, 20)` |
| `wrist_position`, `wrist_linear_velocity`, `wrist_angular_velocity` | `(3,)` |
| `wrist_orientation` | `(4,)` |
| `prev_wrist_position_target` | `(3, 3)` |
| `prev_wrist_orientation_target` | `(3, 4)` |
| `object_position`, `object_linear_velocity`, `object_angular_velocity` | `(2, 3)` |
| `object_orientation` | `(2, 4)` |
| `step` | Scalar integer (0–9999) |

Additional task-specific observation fields:

| Key | Shape | dtype | Meaning |
|---|---|---|---|
| `goal_defined` | `(2,)` | int64 | Whether a goal is explicitly defined for each object |
| `goal_position` | `(2, 3)` | float64 | Goal position in world coordinates; NaN for undefined or unconstrained components |
| `goal_orientation` | `(2, 4)` | float64 | Goal orientation (wxyz); NaN where undefined |
| `goal_free_axis` | `(2, 3)` | float64 | Object state-frame axis whose rotation is unconstrained; zeros mean none |

The goal fields are constant during each episode. Their availability does not replace the task requirements in `SUCCESS.md`.

The exact key set, shapes, dtypes, and goal-field semantics must match `sim2target/CONTRACT.md` and the validation tools.

### State Record

File: `state/trajectory.npz`

For a complete episode, `R = 10001`.

| Fields | Shape | dtype |
|---|---|---|
| `object_position`, `object_linear_velocity`, `object_angular_velocity` | `(R, 2, 3)` | float64 |
| `object_orientation` | `(R, 2, 4)` | float64 |
| `hand_object_contact`, `object_environment_contact` | `(R, 2)` | bool |
| `object_object_contact` | `(R, 2, 2)` | bool |
| `object_names` | `(2,)` | str |
| `part_names` | `(0,)` | str |
| `part_object` | `(0,)` | int64 |

Additional task-specific state-record fields:

| Field | Shape | dtype |
|---|---|---|
| `goal_defined` | `(2,)` | int64 |
| `goal_position` | `(2, 3)` | float64 |
| `goal_orientation` | `(2, 4)` | float64 |
| `goal_free_axis` | `(2, 3)` | float64 |

- **Object names:** `plug_white`, `plug_black`
- **Articulated parts:** None.
- **Shared time, step, robot, wrist, and control fields:** `sim2target/FEEDBACK.md`.
- **Task measurements:** Pickup, placement, upright orientation, and stage-completion measurements are defined by the active verifier and reported through `verifier/report.json`.

All state-record field semantics follow `sim2target/FEEDBACK.md`.
