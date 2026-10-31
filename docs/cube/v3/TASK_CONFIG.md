# Task Configuration: One-handed 2×2×2 Rubik's Cube Solving

The runtime configuration of this task: which hand variant it uses, its experiment and API command, the episode and its timing, the scene, the initial configuration, the objects, and the exact shapes of the observation and the state record. The shared documents (`CONTRACT.md`, `EVALUATION.md`, `FEEDBACK.md`, `REMOTE_API.md`, `hardware/SPECS.md`, `TOOLS.md`) describe the interfaces with symbols that this document fixes: `N` (control steps), `O` (objects), `P` (parts), `R` (state-record rows) and `$R2S2R_API` (the API command).

## 1. Task, Robot Variant and Experiment

| Parameter | Value |
|---|---|
| Task | `cube`: One-handed 2×2×2 Rubik's Cube Solving (`TASK.md`) |
| Robot variant | **left hand**: Wuji Hand 2.2 left, `hardware/LEFT_HAND.md`; model files `hardware/wuji_hand2_left/`; joint names `l_*` |
| API command | `r2s2r-cube` (`export R2S2R_API=r2s2r-cube`; `REMOTE_API.md`) |
| Experiment | `R2S2R-PS-CUBE-1`: your key is bound to it; `fetch` returns `R2S2R-PS-CUBE-1_sNN/` (`REMOTE_API.md` section 4) |
| Environment version | `env-3L` (`REMOTE_API.md` section 7) |
| Target model | `tm-2L` (Wuji Hand 2.2 left) |
| Hardware specification | `hwspec-1.1L`, `hardware/hardware_spec_left.json` (`hardware/SPECS.md` section 7) |
| Local tools for this hand | set `export R2S2R_HAND=left` (or run `r2s2r-preflight --hand left`) so that `r2s2r-preflight` uses this hand's initial configuration; `r2s2r-hwcheck` selects `hardware/hardware_spec_left.json` for a trajectory with `l_*` joint names; the MuJoCo calibration adapter takes `--urdf hardware/wuji_hand2_left/urdf/left.urdf` (`TOOLS.md`) |
| Success criteria | criteria `cube-v1`, rubric `rubric-1.3`, status `provisional`: the criteria of this task's previous environment, carried over unchanged (`SUCCESS.md`). |

## 2. Episode and Timing

| Parameter | Value |
|---|---|
| Episode length | 40 s |
| Control steps `N` | 20,000 policy steps at 500 Hz (`step` 0–19999) |
| Settle phase before step 0 | 1 s, not controlled by the policy (`EVALUATION.md` section 1) |
| State record `state/trajectory.npz` | `R` = 20,001 rows for a complete rollout (rows 0 to `N`) |
| Rollout log `logs/trial_0.npz` | 20,000 rows for a complete rollout |
| Videos | 25 fps, 1,001 frames per view for a complete rollout |
| Wall-clock limit of an evaluation | 90 minutes (trial, verifier and video rendering; exceeded: state `timeout`, `REMOTE_API.md` section 3) |

## 3. Scene and Initial Configuration

- **World frame:** X forward, Y left, Z up (`hardware/SPECS.md` section 3). The floor is the plane z = 0; the initial wrist pose below is about 0.31 m above it.
- **Initial wrist pose** (every trial; the root link `l_mount`): position `(0.027610, 0.001998, 0.307144)` m, orientation (wxyz) `(0.555339, -0.420012, 0.441195, -0.566159)`. Palm up, fingertips tilted downward by 15°: the mirror image, in the world x–z plane, of the right hand's pose of this task's previous environment (the fixed mount; within 0.2 mm and 0.4°), with the object resting in the hand. The executed wrist target starts at this pose (the three entries of the target histories at step 0); the measured wrist state at step 0 differs from it by the controller's steady-state offset under the object's weight (`hardware/SPECS.md` section 4).
- **Palm frame `l_wrist`** at the initial pose: position `(-0.000002, -0.000058, 0.299751)` m, orientation (wxyz) `(0.555334, -0.420015, 0.441191, -0.566164)`.
- **Wrist workspace:** the executed wrist position target is kept inside the box `x ∈ [−0.30, 0.35]`, `y ∈ [−0.30, 0.30]`, `z ∈ [0.05, 0.65]` m (world frame). The hand itself collides with the floor and the object.
- **Contact flags:** the environment of `object_environment_contact` is the floor.
- **Initial objects:** `object/SPECS.md`; the exact initial state is the observation of step 0. The fixed scramble of every evaluation is in `TASK.md` and in the observation (`scramble`).

**Initial finger configuration `q₀`** (rad, the joint order of `hardware/LEFT_HAND.md`). `q₀` is the same in every trial; measured initial positions differ by settling and encoder noise (`CONTRACT.md`).

| # | Joint | q₀ (rad) |
|---|---|---|
| 0 | l_thumb_cmc_flex | 0.6 |
| 1 | l_thumb_cmc_abd | -0.3 |
| 2 | l_thumb_mcp | 0.3 |
| 3 | l_thumb_ip | 0.2 |
| 4 | l_index_finger_mcp_flex | 0.6 |
| 5 | l_index_finger_mcp_abd | 0.0 |
| 6 | l_index_finger_pip | 1.4 |
| 7 | l_index_finger_dip | 0.3 |
| 8 | l_middle_finger_mcp_flex | 0.6 |
| 9 | l_middle_finger_mcp_abd | 0.0 |
| 10 | l_middle_finger_pip | 1.4 |
| 11 | l_middle_finger_dip | 0.3 |
| 12 | l_ring_finger_mcp_flex | 0.6 |
| 13 | l_ring_finger_mcp_abd | 0.0 |
| 14 | l_ring_finger_pip | 1.4 |
| 15 | l_ring_finger_dip | 0.3 |
| 16 | l_pinky_mcp_flex | 0.6 |
| 17 | l_pinky_mcp_abd | 0.0 |
| 18 | l_pinky_pip | 1.4 |
| 19 | l_pinky_dip | 0.3 |

**Cameras** (`FEEDBACK.md` section 5):

| View | Perspective |
|---|---|
| `top` | Above the wrist workspace, 1.6 m up, looking down: the whole workspace in view; contacts on the palm side |
| `left` | From the hand's left (+Y), nearly level, 1.8 m away: the whole workspace and heights above the hand |
| `right` | Close oblique view from the hand's right (−Y) and the fingertip side, 0.75 m away, aimed at the initial hand position: grasp and fingers |

## 4. Objects, Observation and State Record

- **Objects** (`O` = 1), the order of every `object_*` array: `0 = cube`. Geometry and state frames: `object/SPECS.md`.
- **Parts** (`P` = 8): `0..7 = cubie0 … cubie7`, all belonging to object 0 (`part_object`).

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
| `step` | scalar | int | `CONTRACT.md` section 3 (0–19999) |
| `object_position` | `(1, 3)` | float64 | `CONTRACT.md` section 3 |
| `object_orientation` | `(1, 4)` | float64 | `CONTRACT.md` section 3 |
| `object_linear_velocity` | `(1, 3)` | float64 | `CONTRACT.md` section 3 |
| `object_angular_velocity` | `(1, 3)` | float64 | `CONTRACT.md` section 3 |
| `part_position` | `(8, 3)` | float64 | State-frame origin of each cubie in the world [m] |
| `part_orientation` | `(8, 4)` | float64 | Cubie orientation `(w, x, y, z)` |
| `part_linear_velocity` | `(8, 3)` | float64 | Velocity of each cubie's state-frame origin, world frame [m/s] |
| `part_angular_velocity` | `(8, 3)` | float64 | Angular velocity of each cubie, world frame [rad/s] |
| `cube_relative_orientation` | `(8, 4)` | float64 | Orientation of each cubie relative to cubie 0, `q₀⁻¹ ⊗ q_j` `(w, x, y, z)`; row 0 is the identity; sign-continuous |
| `cube_configuration` | `(8,)` | int64 | Index of the nearest of the 24 cube rotations to each cubie's relative orientation (`object/SPECS.md`) |
| `scramble` | `(3, 2)` | float64 | The scramble applied to the solved cube, `[face, quarter_turns]` per move (`TASK.md`); constant |

**State record** (`state/trajectory.npz`, `FEEDBACK.md` section 3): the object, contact and task-specific fields of this task (the step, time and wrist fields are as in `FEEDBACK.md`).

| Field | Shape | dtype | Meaning |
|---|---|---|---|
| `object_position`, `object_linear_velocity`, `object_angular_velocity` | `(R, 1, 3)` | float64 | `FEEDBACK.md` section 3 |
| `object_orientation` | `(R, 1, 4)` | float64 | `FEEDBACK.md` section 3 |
| `hand_object_contact`, `object_environment_contact` | `(R, 1)` | bool | `FEEDBACK.md` section 3 (environment: the floor) |
| `object_object_contact` | `(R, 1, 1)` | bool | `FEEDBACK.md` section 3 |
| `object_names` | `(1,)` | str | `cube` |
| `part_names`, `part_object` | `(8,)` | str, int64 | `cubie0` … `cubie7`, all belonging to object 0 |
| `part_position` | `(R, 8, 3)` | float64 | m, world: State-frame origin of each cubie (`part_names`) |
| `part_orientation` | `(R, 8, 4)` | float64 | world ← part frame: Cubie orientation |
| `part_linear_velocity` | `(R, 8, 3)` | float64 | m/s, world: Velocity of the cubie's state-frame origin |
| `part_angular_velocity` | `(R, 8, 3)` | float64 | rad/s, world: Angular velocity of the cubie |
| `cube_relative_orientation` | `(R, 8, 4)` | float64 | cubie 0 ← cubie j: `q₀⁻¹ ⊗ q_j` per cubie; row 0 = identity; sign-continuous |
| `cube_configuration` | `(R, 8)` | int64 | index: Index into the 24 cube rotations (`object/SPECS.md`) nearest to each cubie's relative orientation |

**`measurements`** of `verifier/report.json` (`FEEDBACK.md` section 1): `complete_layer_turns`, `min_distance_to_solved`, `start_distance`, `end_distance`, `max_mechanism_deviation_deg`, `retained_until_t`, `solved_at_end`.
