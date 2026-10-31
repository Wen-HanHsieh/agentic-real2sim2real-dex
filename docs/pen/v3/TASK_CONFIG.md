# Task Configuration: Pen Spinning

The runtime configuration of this task: which hand variant it uses, its experiment and API command, the episode and its timing, the scene, the initial configuration, the objects, and the exact shapes of the observation and the state record. The shared documents (`CONTRACT.md`, `EVALUATION.md`, `FEEDBACK.md`, `REMOTE_API.md`, `hardware/SPECS.md`, `TOOLS.md`) describe the interfaces with symbols that this document fixes: `N` (control steps), `O` (objects), `P` (parts), `R` (state-record rows) and `$R2S2R_API` (the API command).

## 1. Task, Robot Variant and Experiment

| Parameter | Value |
|---|---|
| Task | `pen`: Pen Spinning (`TASK.md`) |
| Robot variant | **right hand**: Wuji Hand 2.2 right, `hardware/RIGHT_HAND.md`; model files `hardware/wuji_hand2_right/`; joint names `r_*` |
| API command | `r2s2r-pen` (`export R2S2R_API=r2s2r-pen`; `REMOTE_API.md`) |
| Experiment | `R2S2R-PS-PEN-1`: your key is bound to it; `fetch` returns `R2S2R-PS-PEN-1_sNN/` (`REMOTE_API.md` section 4) |
| Environment version | `env-3` (`REMOTE_API.md` section 7) |
| Target model | `tm-2` (Wuji Hand 2.2 right) |
| Hardware specification | `hwspec-1.1`, `hardware/hardware_spec.json` (`hardware/SPECS.md` section 7) |
| Local tools for this hand | `r2s2r-preflight` and `r2s2r-hwcheck` use the right hand by default; the MuJoCo calibration adapter takes `--urdf hardware/wuji_hand2_right/urdf/right.urdf` (`TOOLS.md`) |
| Success criteria | criteria `pen-v1`, rubric `rubric-1.3`, status `provisional`: the criteria of this task's previous environment, carried over unchanged (`SUCCESS.md`). |

## 2. Episode and Timing

| Parameter | Value |
|---|---|
| Episode length | 12 s |
| Control steps `N` | 6,000 policy steps at 500 Hz (`step` 0–5999) |
| Settle phase before step 0 | 1 s, not controlled by the policy (`EVALUATION.md` section 1) |
| State record `state/trajectory.npz` | `R` = 6,001 rows for a complete rollout (rows 0 to `N`) |
| Rollout log `logs/trial_0.npz` | 6,000 rows for a complete rollout |
| Videos | 100 fps, 1,201 frames per view for a complete rollout |
| Wall-clock limit of an evaluation | 45 minutes (trial, verifier and video rendering; exceeded: state `timeout`, `REMOTE_API.md` section 3) |

## 3. Scene and Initial Configuration

- **World frame:** X forward, Y left, Z up (`hardware/SPECS.md` section 3). The floor is the plane z = 0; the initial wrist pose below is about 0.31 m above it.
- **Initial wrist pose** (every trial; the root link `r_mount`): position `(0.028196, -0.002080, 0.304675)` m, orientation (wxyz) `(0.534290, 0.445683, 0.463192, 0.548957)`. Palm up, fingertips tilted downward by 10°: the pose of the fixed mount of this task's previous environment, with the object resting in the hand. The executed wrist target starts at this pose (the three entries of the target histories at step 0); the measured wrist state at step 0 differs from it by the controller's steady-state offset under the object's weight (`hardware/SPECS.md` section 4, about 0.3 mm).
- **Palm frame `r_wrist`** at the initial pose: position `(0.000050, -0.000002, 0.299709)` m, orientation (wxyz) `(0.534286, 0.445687, 0.463188, 0.548962)`.
- **Wrist workspace:** the executed wrist position target is kept inside the box `x ∈ [−0.30, 0.35]`, `y ∈ [−0.30, 0.30]`, `z ∈ [0.05, 0.65]` m (world frame). The hand itself collides with the floor and the object.
- **Contact flags:** the environment of `object_environment_contact` is the floor.
- **Initial objects:** `object/SPECS.md`; the exact initial state is the observation of step 0.

**Initial finger configuration `q₀`** (rad, the joint order of `hardware/RIGHT_HAND.md`). `q₀` is the same in every trial; measured initial positions differ by settling and encoder noise (`CONTRACT.md`).

| # | Joint | q₀ (rad) |
|---|---|---|
| 0 | r_thumb_cmc_flex | 0.0 |
| 1 | r_thumb_cmc_abd | -1.4 |
| 2 | r_thumb_mcp | 0.0 |
| 3 | r_thumb_ip | 0.0 |
| 4 | r_index_finger_mcp_flex | 0.0 |
| 5 | r_index_finger_mcp_abd | 0.0 |
| 6 | r_index_finger_pip | 1.2 |
| 7 | r_index_finger_dip | 0.3 |
| 8 | r_middle_finger_mcp_flex | 0.0 |
| 9 | r_middle_finger_mcp_abd | 0.0 |
| 10 | r_middle_finger_pip | 1.2 |
| 11 | r_middle_finger_dip | 0.3 |
| 12 | r_ring_finger_mcp_flex | 0.0 |
| 13 | r_ring_finger_mcp_abd | 0.0 |
| 14 | r_ring_finger_pip | 1.2 |
| 15 | r_ring_finger_dip | 0.3 |
| 16 | r_pinky_mcp_flex | 0.0 |
| 17 | r_pinky_mcp_abd | 0.0 |
| 18 | r_pinky_pip | 1.2 |
| 19 | r_pinky_dip | 0.3 |

**Cameras** (`FEEDBACK.md` section 5):

| View | Perspective |
|---|---|
| `top` | Above the wrist workspace, 1.6 m up, looking down: the whole workspace in view; contacts on the palm side |
| `left` | From the hand's left (+Y), nearly level, 1.8 m away: the whole workspace and heights above the hand |
| `right` | Close oblique view from the hand's right (−Y) and the fingertip side, 0.75 m away, aimed at the initial hand position: grasp and fingers |

## 4. Objects, Observation and State Record

- **Objects** (`O` = 1), the order of every `object_*` array: `0 = pen`. Geometry and state frames: `object/SPECS.md`.
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
| `step` | scalar | int | `CONTRACT.md` section 3 (0–5999) |
| `object_position` | `(1, 3)` | float64 | `CONTRACT.md` section 3 |
| `object_orientation` | `(1, 4)` | float64 | `CONTRACT.md` section 3 |
| `object_linear_velocity` | `(1, 3)` | float64 | `CONTRACT.md` section 3 |
| `object_angular_velocity` | `(1, 3)` | float64 | `CONTRACT.md` section 3 |

**State record** (`state/trajectory.npz`, `FEEDBACK.md` section 3): the object, contact and task-specific fields of this task (the step, time and wrist fields are as in `FEEDBACK.md`).

| Field | Shape | dtype | Meaning |
|---|---|---|---|
| `object_position`, `object_linear_velocity`, `object_angular_velocity` | `(R, 1, 3)` | float64 | `FEEDBACK.md` section 3 |
| `object_orientation` | `(R, 1, 4)` | float64 | `FEEDBACK.md` section 3 |
| `hand_object_contact`, `object_environment_contact` | `(R, 1)` | bool | `FEEDBACK.md` section 3 (environment: the floor) |
| `object_object_contact` | `(R, 1, 1)` | bool | `FEEDBACK.md` section 3 |
| `object_names` | `(1,)` | str | `pen` |
| `part_names`, `part_object` | `(0,)` | str, int64 | empty: this task has no parts |

**`measurements`** of `verifier/report.json` (`FEEDBACK.md` section 1): `net_rotation_deg`, `max_rotation_deg`, `min_rotation_deg`, `max_tilt_deg`, `retained_until_t`, `revolution_times_s`.
