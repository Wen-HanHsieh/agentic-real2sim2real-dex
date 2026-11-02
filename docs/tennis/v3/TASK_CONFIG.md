# TASK_CONFIG.md — Tennis Ball Manipulation

## 1. Task and Environment

| Parameter | Value |
|---|---|
| Task | `tennis` |
| Robot | Wuji Hand 2.2 — Right Hand |
| Robot model | `hardware/wuji_hand2_right/` |
| Hardware specification | `hwspec-1.1` (`hardware/hardware_spec.json`) |
| Target model | `tm-2` |
| Environment | `env-3` |
| Experiment | `R2S2R-PS-TENNIS-1` |
| API command | `r2s2r-tennis` |
| Success criteria | `SUCCESS.md` |

- **Hand specifications:** `hardware/RIGHT_HAND.md`
- **Joint naming:** `r_*`
- **API setup:** `export R2S2R_API=r2s2r-tennis`
- **Policy interface:** `sim2target/CONTRACT.md`
- **Evaluation interface:** `sim2target/REMOTE_API.md`
- **Local tools:** `r2s2r-preflight` and `r2s2r-hwcheck` default to the right hand.
- **MuJoCo URDF:** `hardware/wuji_hand2_right/urdf/right.urdf`
- **Submission records:** The task-bound API key accesses this experiment; fetched submissions use the directory prefix `R2S2R-PS-TENNIS-1_sNN/`.

## 2. Episode Configuration

| Parameter | Value |
|---|---|
| Episode duration | 15 s |
| Control frequency | 500 Hz |
| Control steps (`N`) | 7,500 |
| Policy step index | 0–7499 |
| Settle phase | 1 s before step 0 (not policy-controlled) |
| State-record rows (`R`) | 7,501 (initial state + 7,500 steps) |
| Rollout-log rows | 7,500 |
| Video | 100 fps, 1,501 frames per view |
| Evaluation wall-clock limit | 45 min |

- **State record:** `state/trajectory.npz`
- **Rollout log:** `logs/trial_0.npz`
- **Video views:** `top`, `left`, `right`
- **Timeout:** Exceeding the wall-clock limit results in evaluation state `timeout` (`sim2target/REMOTE_API.md`).

## 3. Initial Configuration

### World Frame

- **X:** Forward
- **Y:** Left
- **Z:** Up
- **Floor:** `z = 0`

See `hardware/SPECS.md` for coordinate conventions.

### Initial Wrist Pose

The hand starts palm-up with fingertips tilted downward by 15°, with the tennis ball resting in the hand.

- **Root link:** `r_mount`
- **Position (xyz, m):** `(0.027681, -0.002080, 0.307114)`
- **Orientation (wxyz):** `(0.553986, 0.421314, 0.439445, 0.567875)`

Initial palm frame (`r_wrist`):

- **Position (xyz, m):** `(0.000075, -0.000002, 0.299715)`
- **Orientation (wxyz):** `(0.553981, 0.421317, 0.439442, 0.567880)`

The executed wrist target starts at the initial root-link pose. The measured wrist state may differ slightly after settling because of controller steady-state offsets under object weight (approximately 0.3 mm).

The three initial wrist-target history entries contain this starting target.

### Wrist Workspace

The executed wrist position target is clipped to:

- **X:** `[-0.30, 0.35]` m
- **Y:** `[-0.30, 0.30]` m
- **Z:** `[0.05, 0.65]` m

These bounds apply to the executed wrist position target in the world frame. The hand can collide with the floor and the ball.

### Initial Finger Configuration

The initial joint targets `q₀` are fixed across trials.

Joint order follows `hardware/RIGHT_HAND.md`.

| Joint | Initial angle (rad) |
|---|---:|
| `r_thumb_cmc_flex` | 0.6 |
| `r_thumb_cmc_abd` | -0.3 |
| `r_thumb_mcp` | 0.3 |
| `r_thumb_ip` | 0.2 |
| `r_index_finger_mcp_flex` | 0.6 |
| `r_index_finger_mcp_abd` | 0.0 |
| `r_index_finger_pip` | 1.4 |
| `r_index_finger_dip` | 0.3 |
| `r_middle_finger_mcp_flex` | 0.6 |
| `r_middle_finger_mcp_abd` | 0.0 |
| `r_middle_finger_pip` | 1.4 |
| `r_middle_finger_dip` | 0.3 |
| `r_ring_finger_mcp_flex` | 0.6 |
| `r_ring_finger_mcp_abd` | 0.0 |
| `r_ring_finger_pip` | 1.4 |
| `r_ring_finger_dip` | 0.3 |
| `r_pinky_mcp_flex` | 0.6 |
| `r_pinky_mcp_abd` | 0.0 |
| `r_pinky_pip` | 1.4 |
| `r_pinky_dip` | 0.3 |

Measured initial joint positions may differ slightly due to settling and encoder noise (`sim2target/CONTRACT.md`).

## 4. Objects and Scene

- **Number of objects (`O`):** 1
- **Object index 0:** `tennis_ball`
- **Articulated parts (`P`):** 0
- **Initial object state:** Available in the observation at step 0.
- **Object geometry, physical properties and state frame:** `object/SPECS.md`
- **Object–environment contact:** Contact with the floor.
- **Permitted workspace:** The ball center must stay within 0.25 m horizontally of its initial position; touching the floor ends crediting.

### Camera Views

| View | Configuration |
|---|---|
| `top` | Above the workspace, 1.6 m high, looking downward; shows the full workspace and palm-side contacts |
| `left` | From the hand's left (+Y), nearly level, 1.8 m away; shows the workspace and ball height |
| `right` | Close oblique view from the hand's right (−Y), on the fingertip side, 0.75 m away; aimed at the initial hand position |

See `sim2target/FEEDBACK.md` for video and camera-record details.

## 5. Observation and State Record

The exact observation/action semantics are defined in `sim2target/CONTRACT.md`. This section specifies the Tennis task's dimensions and record fields.

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
| `object_position`, `object_linear_velocity`, `object_angular_velocity` | `(1, 3)` |
| `object_orientation` | `(1, 4)` |
| `step` | Scalar integer (0–7499) |

The exact key set, shapes, and dtypes must match `sim2target/CONTRACT.md` and the validation tools.

### State Record

File: `state/trajectory.npz`

For a complete episode, `R = 7501`.

| Fields | Shape | dtype |
|---|---|---|
| `object_position`, `object_linear_velocity`, `object_angular_velocity` | `(R, 1, 3)` | float64 |
| `object_orientation` | `(R, 1, 4)` | float64 |
| `hand_object_contact`, `object_environment_contact` | `(R, 1)` | bool |
| `object_object_contact` | `(R, 1, 1)` | bool |
| `object_names` | `(1,)` | str |
| `part_names` | `(0,)` | str |
| `part_object` | `(0,)` | int64 |

- **Object name:** `tennis_ball`
- **Articulated parts:** None.
- **Shared time, step, robot, wrist, and control fields:** `sim2target/FEEDBACK.md`.
- **Task measurements:** Releases, completed toss-and-catch cycles, flight durations, apex heights, retention durations, and applicable rotation/stage measurements are defined by the active verifier and reported through `verifier/report.json`.

All state-record field semantics follow `sim2target/FEEDBACK.md`.
