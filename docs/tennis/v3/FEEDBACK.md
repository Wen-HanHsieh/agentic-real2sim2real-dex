# Target Evaluation Feedback

The target environment evaluates each rollout from its exact simulation state: the wrist and object states it recorded at every control step, the contact flags of every control interval, the robot's joint log, and the finger actuation record. Nothing in the evaluation is estimated from cameras or sensors. Official success criteria are in `SUCCESS.md`. Feedback exists only after the rollout; the deployed policy receives the observation of `CONTRACT.md` and nothing else.

## 1. Official Evaluation

`verifier/report.json` (schema `r2s2r-verifier/1`, verifier `gv-1`) has the same top-level keys for every task:

| Field | Description |
|---|---|
| `schema`, `verifier_version`, `task` | `r2s2r-verifier/1`, `gv-1`, the task name |
| `criteria` | `id`, `rubric` and `status` of the success criteria the report was scored with: status `provisional`, `approved`, or `undefined` (`SUCCESS.md`) |
| `status` | `evaluated`, `criteria_undefined`, or `not_evaluable` (rule below) |
| `success` | `true` or `false`; `null` unless `status` is `evaluated` |
| `progress` | Task progress 0–1, the score of `SUCCESS.md`; `null` unless `status` is `evaluated` and the score could be computed (`note` says when it could not) |
| `milestones` | Per milestone `name`, `stage`, `label`, `credit`, `reached`, `time` (s since step 0; `null` if not reached). A stage with one milestone names it after the stage; otherwise `<stage>_<i>`. `[]` if no criteria |
| `stages` | Per stage `name`, `weight`, `progress` (0–1 within the stage), `score`. `[]` if no criteria |
| `events` | Timestamped observations: `time`, `step`, `type`, `detail` |
| `measurements` | Summary quantities of this task's criteria (exact values) (the releases, the complete cycles, and the flight, apex and retention quantities of each cycle) |
| `validity` | `run_valid`; `policy_runtime` (`pass`, `reason`: the policy error, if any); `physical` (the target's own run checks `R0_reference_config`, `R1_physics`, `R2_initial_state`, `R4_teleport`, `R9_integrity`, each `true`/`false`); `hardware` (section 2); `actions` (`pass`, `status`); `steps_executed`, `expected_steps`, `state_rows` |
| `versions` | `contract`, `state_schema`, `environment`, `wrist`, `rubric`, `hardware_spec`, `target_model` (`REMOTE_API.md` section 7) |
| `note` | A remark on the status (for example why nothing was scored), else `null` |

**Status rule:**

- `evaluated`: success criteria exist for the task. `success` is `true` only if the criteria are fully met (`progress` 1.0 and the final condition of `SUCCESS.md`), the hardware is compliant, the policy ran without failure and the run is valid; otherwise `false`. A policy failure or a hardware violation does not change the status: the record up to the failure is scored and `success` is `false`. A record too short for the final-window conditions of the criteria (a policy failure within the first 1.0 s, or before any step) is `evaluated` with `success` `false` and `progress` `null`: a score the criteria could not compute is never reported as a number; `note` says why.
- `criteria_undefined`: no success criteria are defined for the task (`criteria.status` `undefined`). `success` and `progress` are `null`, `milestones` and `stages` are empty, `measurements` is empty; `validity` is still reported. Nothing is scored.
- `not_evaluable`: the record itself is unusable (a target-side problem, explained in `note`); such a submission is not charged.

**Exact values.** Every value is computed from the target's simulation state; there are no measurement margins, uncertainty intervals or `unknown` outcomes. The evaluation reports what happened, not why: a stage that scored 0 is not explained, and a loss of retention gives its time, not the condition that ended it. Diagnosing causes from the state record, videos, frames and logs is your task.

## 2. Hardware and Runtime

`validity.hardware` applies `hardware/SPECS.md` section 7 to the finger joints over the whole policy phase, from the target's exact joint state and applied torque at the controller rate: `status` (`compliant` or `violation`), `spec_version`, `mode`, `checks` (`position`, `velocity`, `effort`, `actions`: each with its `status`, the worst joint and time, the maximum excess, the margin), `violations`, `joints` (the joints involved in a violation), `max_ratios` (`velocity`, `effort` relative to the limits; `position_excess_rad`), `steps`. The wrist has no rule beyond its controller; its tracking and saturation are visible in the state record and the rollout log, never a violation. `validity.policy_runtime` reports a policy failure with the error text; `validity.physical` lists the target's own run checks (reference configuration, finite state, initial state at rest, no position jumps, record integrity).

## 3. State Record

`state/trajectory.npz` is the ground-truth state of the rollout at the control rate, described field by field in `state/schema.json` (`schema` `objstate-1`: every field's `shape`, `dtype`, `unit`, `frame`, `description`; the conventions; `rows`, `control_steps_executed`, `objects`, `parts`, `goals`).

**Rows and time.** Row `k` (`0 ≤ k ≤ N`) is exactly the state the policy observed at control step `k` (the same instant and values as `obs` of `CONTRACT.md`); row `N` is the state after the last command, so a complete rollout has 5,001 rows for 5,000 steps. After a policy failure at step `k` the file has rows `0..k`. `t = 0.002 · step` s with `t = 0` at control step 0, the same time base as `logs/trial_0.npz` (row `k` = step `k`, 5,000 rows) and `video/frames.json`. The contact flags of row `k` cover the control interval ending at the row (row 0: its own instant). Quaternions are `(w, x, y, z)`, unit norm, sign-continuous as in `CONTRACT.md`.

| Field | Shape | dtype | Unit / frame | Description |
|---|---|---|---|---|
| `step` | `(R,)` | int64 | — | Control step `k` of the row |
| `t` | `(R,)` | float64 | s | `0.002 · k` |
| `wrist_position` | `(R, 3)` | float64 | m, world | Wrist-frame origin (`r_mount`) |
| `wrist_orientation` | `(R, 4)` | float64 | world ← wrist | Rotates wrist-frame vectors into the world frame |
| `wrist_linear_velocity` | `(R, 3)` | float64 | m/s, world | Velocity of the wrist-frame origin |
| `wrist_angular_velocity` | `(R, 3)` | float64 | rad/s, world | Angular velocity of the wrist frame |
| `object_position` | `(R, 1, 3)` | float64 | m, world | State-frame origin of each object (`object/SPECS.md`); axis 1 = object index |
| `object_orientation` | `(R, 1, 4)` | float64 | world ← state frame | State-frame orientation |
| `object_linear_velocity` | `(R, 1, 3)` | float64 | m/s, world | Velocity of the state-frame origin (not of the centre of mass) |
| `object_angular_velocity` | `(R, 1, 3)` | float64 | rad/s, world | Angular velocity of the object |
| `hand_object_contact` | `(R, 1)` | bool | — | Any contact between the hand and the object during the control interval ending at the row |
| `object_environment_contact` | `(R, 1)` | bool | — | Any contact between the object and the environment (the floor) during the interval |
| `object_object_contact` | `(R, 1, 1)` | bool | — | Any contact between two different objects during the interval (symmetric) |
| `object_names` | `(1,)` | str | — | Object order of every `object_*` array: `tennis_ball` |
| `part_names`, `part_object` | `(0,)` | str, int64 | — | Part order of every `part_*` array and the owning object index of each part (empty: this task has no parts) |

The contact flags exist only in this feedback file; they are never part of the policy observation. The rows are the same values the policy saw, so the state record and your own simulator's record of the same action sequence can be compared row by row (`TOOLS.md` section 2).

## 4. Rollout Log

`logs/trial_0.npz` (5,000 rows for a complete rollout; row `k` = control step `k`, up to the failure after a policy failure): `joint_names` `(20,)`; the measured `q`, `qd` `(N, 20)` the policy received (with encoder noise); the finger commands `q_target`, `qd_target` `(N, 20)` as sent (`None` recorded as zeros); the wrist commands as sent, `wrist_position_command` `(N, 3)`, `wrist_orientation_command` `(N, 4)`, `wrist_linear_velocity_command`, `wrist_angular_velocity_command` `(N, 3)` (`None` recorded as zeros); the **executed** wrist targets after the command limits, `wrist_position_target`, `wrist_orientation_target`, `wrist_linear_velocity_target`, `wrist_angular_velocity_target`; and `wrist_command_limited` `(N, 5)` bool, one flag per limit in the order `translation_rate`, `workspace`, `rotation_rate`, `linear_velocity`, `angular_velocity` (`true` where the limit changed the command at that step). The executed targets are what the wrist controller tracked (`hardware/SPECS.md` section 4); the wrist state it reached is in the state record.

## 5. Videos and Cameras

The three videos are renderings of the target rollout: the recorded ground-truth trajectory of the hand (at its floating pose) and of the objects, drawn with the published camera model. They show the same data as `state/trajectory.npz`; no camera or sensor pipeline is part of the evaluation.

Three fixed, synchronized views (global shutter, 848 × 480, pinhole without distortion):

| View | Perspective |
|---|---|
| `top` | Above the wrist workspace, 1.6 m up, looking down: the whole workspace in view; contacts on the palm side |
| `left` | From the hand's left (+Y), nearly level, 1.8 m away: the whole workspace and heights above the hand |
| `right` | Close oblique view from the hand's right (−Y) and the fingertip side, 0.75 m away, aimed at the initial hand position: grasp and fingers |

- **RGB video:** 100 fps, H.264, real time, covering the whole rollout (1,001 frames per view for a complete rollout; up to the failure after a policy failure).
- **Calibration:** `calibration.json`: `rig_version`, `layout`, per view `width`, `height`, `K`, `distortion`, `T_world_cam`, `T_cam_world`, `position_m`, `purpose`; world frame as in `hardware/SPECS.md`; OpenCV camera frame, pixel (0, 0) at the centre of the top-left pixel; `depth` model; `conventions`.
- **Timestamps:** `video/frames.json` gives each frame's time `frame_t` (s since control step 0) and `control_step = round(frame_t × 500)`, the same for all views; `video/video.json` gives the fps, frame count, duration and the files.
- **Frames on demand:** `frames sNN VIEW TIMES [depth]` (`REMOTE_API.md` section 6) renders the same trajectory at any instant, as RGB PNG and optionally 16-bit depth PNG in 0.1 mm units (0 = no return), noise σ = 1 mm × (z / 0.5 m)². Depth is available only through this query.

## 6. Standard Feedback

Evaluation evidence produced and stored automatically after every rollout (after a policy failure: up to the failure), never changed afterwards. It is not pushed to you; retrieve it with `fetch sNN` (`REMOTE_API.md` section 4).

| File | Contents |
|---|---|
| `feedback.json` | Protocol, task, policy SHA-256, every version (`versions`), criteria id and status, steps executed and expected, feedback categories (`contents`), and the SHA-256 of every returned file |
| `verifier/report.json` | Official evaluation (section 1) |
| `state/trajectory.npz`, `state/schema.json` | Ground-truth state record (section 3) and its field-by-field description |
| `logs/trial_0.npz` | Rollout log (section 4) |
| `video/top.mp4`, `video/left.mp4`, `video/right.mp4` | Synchronized renderings of the rollout (section 5) |
| `video/frames.json`, `video/video.json` | Per-frame time and control step; video metadata |
| `calibration.json` | Camera intrinsics, extrinsics, conventions, depth model |

**Feedback categories** (`feedback.json` `contents`):

| Category | Contents |
|---|---|
| Verifier results | `verifier/report.json`: `status`, `success`, `progress`, `milestones` with times, `stages`, `validity`, `versions`; the criteria status |
| Rollout evidence | `state/trajectory.npz` with `state/schema.json`, `logs/trial_0.npz`, the videos with `frames.json` and `video.json`, `calibration.json`, the report's `events` and `measurements`; RGB and depth frames on demand (`frames`) |
| Timestamps | `t = 0.002 · step`, `t = 0` at control step 0; state row `k` = the observation of step `k`; log row `k` = step `k`; `frames.json` per video frame |

Not provided: explanations of failures or suggested fixes, contact forces, contact depths, per-link contacts, joint torques, physical parameters, the evaluation condition, the target's diagnostics, and the simulator itself (`REMOTE_API.md` section 8).

## 7. Research Workflow, On-demand Access, and Analysis Tools

| Category | Commands and tools | Use |
|---|---|---|
| Standard research workflow | `history`, `intent`, `note`, `training-video` (`r2s2r-harness submit`, `reflect`, `video`) | Experiment history, best evaluated policy, comparisons with earlier comparable submissions; your research intent before and reflection after each submission; your training-simulation video of each submitted policy |
| On-demand access | `package`, `frames` | Exact earlier packages; RGB frames at any instant of a finished rollout, optionally with depth |
| Sim-to-target calibration (required after each target evaluation) | `r2s2r-calib` | Replay the target's action sequence in your simulator, compare the wrist, object and joint trajectories step by step with the target's state record, diagnose the discrepancies, update your simulator, screen repairs in simulation before the next submission, record the evidence (`TOOLS.md` section 2) |
| Optional analysis tools | `r2s2r-hwcheck`, your own diagnostics | Check finger trajectories against the hardware rules; your own diagnostics |

None of them changes official results. Syntax and limits: `REMOTE_API.md` sections 5 and 6; tools: `TOOLS.md`. For every submission, also link a video of your own training-simulation rollout of the submitted policy and state whether it is a full or partial rollout (`REMOTE_API.md` section 5); it is shown next to the target rollout and never evaluated.

## 8. Research Use

You may use the state record, videos, frames, logs and official results to diagnose failures and improve your simulation and policy. Your own diagnostic metrics do not replace the official evaluation.
