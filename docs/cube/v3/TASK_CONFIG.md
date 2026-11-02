# TASK_CONFIG.md — One-Handed 2×2×2 Rubik's Cube Solving

## 1. Task and Environment

| Parameter | Value |
|---|---|
| Task | `cube` |
| Robot | Wuji Hand 2.2 — Left Hand |
| Robot model | `hardware/wuji_hand2_left/` |
| Hardware specification | `hwspec-1.1L` (`hardware/hardware_spec_left.json`) |
| Target model | `tm-2L` |
| Environment | `env-3L` |
| Experiment | `R2S2R-PS-CUBE-1` |
| API command | `r2s2r-cube` |
| Success criteria | `SUCCESS.md` |

- **Hand specifications:** `hardware/LEFT_HAND.md`
- **Joint naming:** `l_*`
- **API setup:**
  - `export R2S2R_API=r2s2r-cube`
  - `export R2S2R_HAND=left`
- **Policy interface:** `sim2target/CONTRACT.md`
- **Evaluation interface:** `sim2target/REMOTE_API.md`
- **Local tools:**
  - `r2s2r-preflight` uses the left-hand initial configuration when `R2S2R_HAND=left` or `--hand left` is specified.
  - `r2s2r-hwcheck` selects `hardware/hardware_spec_left.json` for trajectories with `l_*` joint names.
- **MuJoCo URDF:** `hardware/wuji_hand2_left/urdf/left.urdf`
- **Submission records:** The task-bound API key accesses this experiment; fetched submissions use the directory prefix `R2S2R-PS-CUBE-1_sNN/`.

## 2. Episode Configuration

| Parameter | Value |
|---|---|
| Episode duration | 40 s |
| Control frequency | 500 Hz |
| Control steps (`N`) | 20,000 |
| Policy step index | 0–19999 |
| Settle phase | 1 s before step 0 (not policy-controlled) |
| State-record rows (`R`) | 20,001 (initial state + 20,000 steps) |
| Rollout-log rows | 20,000 |
| Video | 25 fps, 1,001 frames per view |
| Evaluation wall-clock limit | 90 min |

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

The left hand starts palm-up with fingertips tilted downward by 15°, with the cube resting in the hand.

- **Root link:** `l_mount`
- **Position (xyz, m):** `(0.027610, 0.001998, 0.307144)`
- **Orientation (wxyz):** `(0.555339, -0.420012, 0.441195, -0.566159)`

Initial palm frame (`l_wrist`):

- **Position (xyz, m):** `(-0.000002, -0.000058, 0.299751)`
- **Orientation (wxyz):** `(0.555334, -0.420015, 0.441191, -0.566164)`

The initial pose is the mirror image, across the world X–Z plane, of the previous right-hand fixed-mount pose, within 0.2 mm and 0.4°.

The executed wrist target starts at this initial root-link pose. The measured wrist state may differ slightly after settling because of controller steady-state offsets under object weight.

The three initial wrist-target history entries contain this starting target.

### Wrist Workspace

The executed wrist position target is clipped to:

- **X:** `[-0.30, 0.35]` m
- **Y:** `[-0.30, 0.30]` m
- **Z:** `[0.05, 0.65]` m

These bounds apply to the executed wrist position target in the world frame. The hand can collide with the floor and the cube.

### Initial Finger Configuration

The initial joint targets `q₀` are fixed across trials.

Joint order follows `hardware/LEFT_HAND.md`.

| Joint | Initial angle (rad) |
|---|---:|
| `l_thumb_cmc_flex` | 0.6 |
| `l_thumb_cmc_abd` | -0.3 |
| `l_thumb_mcp` | 0.3 |
| `l_thumb_ip` | 0.2 |
| `l_index_finger_mcp_flex` | 0.6 |
| `l_index_finger_mcp_abd` | 0.0 |
| `l_index_finger_pip` | 1.4 |
| `l_index_finger_dip` | 0.3 |
| `l_middle_finger_mcp_flex` | 0.6 |
| `l_middle_finger_mcp_abd` | 0.0 |
| `l_middle_finger_pip` | 1.4 |
| `l_middle_finger_dip` | 0.3 |
| `l_ring_finger_mcp_flex` | 0.6 |
| `l_ring_finger_mcp_abd` | 0.0 |
| `l_ring_finger_pip` | 1.4 |
| `l_ring_finger_dip` | 0.3 |
| `l_pinky_mcp_flex` | 0.6 |
| `l_pinky_mcp_abd` | 0.0 |
| `l_pinky_pip` | 1.4 |
| `l_pinky_dip` | 0.3 |

Measured initial joint positions may differ slightly due to settling and encoder noise (`sim2target/CONTRACT.md`).

### Initial Cube Scramble

Every evaluation starts from the same scrambled configuration.

- **Scramble:** `R' F U2`
- **Encoded sequence:** `[[1, 3], [2, 1], [0, 2]]`
- **Start distance to solved:** 3 face turns
- **Initial cube pose and state:** Available in the observation at step 0.

Encoding conventions:

- **Face indices:** `0 = U`, `1 = R`, `2 = F`
- **Quarter turns:**
  - `1` = clockwise 90°
  - `2` = 180°
  - `3` = counterclockwise 90°
- **Move notation:** Clockwise and counterclockwise are defined while looking at the corresponding face from outside the cube.
- **Scramble application:** Apply `R'`, then `F`, then `U2` to a solved cube in its starting orientation.
- **Starting orientation:** U faces up (world +Z) and F faces the fingertips (world −X), within about 12° of yaw and 6° of tilt; the exact initial pose is in the observation at step 0.

The initial scramble is provided in the policy observation as `scramble`.

Cube face conventions, cubie mechanics, solved-state definitions, and configuration encoding are documented in `object/SPECS.md`.

The agent may choose any valid solving sequence; the shortest solution is not mandatory.

## 4. Objects and Scene

- **Number of objects (`O`):** 1
- **Object index 0:** `cube`
- **Articulated parts (`P`):** 8
- **Part indices:** `0–7 = cubie0 … cubie7`
- **Part ownership:** All eight cubies belong to object 0.
- **Initial object and cubie states:** Available in the observation at step 0.
- **Object geometry, physical properties, mechanics, and state frames:** `object/SPECS.md`
- **Object–environment contact:** Contact with the floor.

### Camera Views

| View | Configuration |
|---|---|
| `top` | 1.6 m above the workspace center, looking downward; shows the full workspace and palm-side contacts |
| `left` | From the hand's left (+Y), nearly level, 1.8 m away; shows the workspace and heights above the hand |
| `right` | Close oblique view from the hand's right (−Y), on the fingertip side, 0.75 m away; aimed at the initial hand position |

See `sim2target/FEEDBACK.md` for video and camera-record details.

## 5. Observation and State Record

The exact observation/action semantics are defined in `sim2target/CONTRACT.md`. This section specifies the Cube task's dimensions and record fields.

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
| `step` | Scalar integer (0–19999) |

Additional task-specific observation fields:

| Key | Shape | dtype | Meaning |
|---|---|---|---|
| `part_position` | `(8, 3)` | float64 | Cubie state-frame origins in world coordinates (m) |
| `part_orientation` | `(8, 4)` | float64 | Cubie orientations (wxyz) |
| `part_linear_velocity` | `(8, 3)` | float64 | Cubie state-frame linear velocities in world coordinates (m/s) |
| `part_angular_velocity` | `(8, 3)` | float64 | Cubie angular velocities in world coordinates (rad/s) |
| `cube_relative_orientation` | `(8, 4)` | float64 | Cubie orientations relative to cubie 0, `q₀⁻¹ ⊗ qⱼ`; row 0 is identity, sign-continuous |
| `cube_configuration` | `(8,)` | int64 | Index of the nearest of 24 cube rotations for each cubie's relative orientation |
| `scramble` | `(3, 2)` | float64 | Initial scramble encoded as `[face, quarter_turns]` per move; constant |

The exact key set, shapes, dtypes, and cubie-state semantics must match `sim2target/CONTRACT.md`, `object/SPECS.md`, and the validation tools.

### State Record

File: `state/trajectory.npz`

For a complete episode, `R = 20001`.

| Fields | Shape | dtype |
|---|---|---|
| `object_position`, `object_linear_velocity`, `object_angular_velocity` | `(R, 1, 3)` | float64 |
| `object_orientation` | `(R, 1, 4)` | float64 |
| `hand_object_contact`, `object_environment_contact` | `(R, 1)` | bool |
| `object_object_contact` | `(R, 1, 1)` | bool |
| `object_names` | `(1,)` | str |
| `part_names` | `(8,)` | str |
| `part_object` | `(8,)` | int64 |

Additional task-specific state-record fields:

| Field | Shape | dtype |
|---|---|---|
| `part_position` | `(R, 8, 3)` | float64 |
| `part_orientation` | `(R, 8, 4)` | float64 |
| `part_linear_velocity` | `(R, 8, 3)` | float64 |
| `part_angular_velocity` | `(R, 8, 3)` | float64 |
| `cube_relative_orientation` | `(R, 8, 4)` | float64 |
| `cube_configuration` | `(R, 8)` | int64 |

- **Object name:** `cube`
- **Part names:** `cubie0` … `cubie7`
- **Part ownership:** `part_object = [0, 0, 0, 0, 0, 0, 0, 0]`
- **Relative orientation:** Computed as `q₀⁻¹ ⊗ qⱼ`, where the quaternions refer to cubie 0 and cubie j; row 0 is identity.
- **Shared time, step, robot, wrist, and control fields:** `sim2target/FEEDBACK.md`.
- **Task measurements:** The active verifier reports `valid_layer_turns`, `start_distance`, `min_distance_to_solved`, `end_distance`, `solved_at_end`, `hand_contact_at_end`, and `full_length` through `verifier/report.json`.

All state-record field semantics follow `sim2target/FEEDBACK.md`.
