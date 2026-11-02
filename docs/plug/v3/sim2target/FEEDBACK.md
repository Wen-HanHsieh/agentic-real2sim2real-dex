# Target Evaluation Feedback

The target environment evaluates each rollout from its exact simulation state: the wrist and object states it recorded at every control step, the contact flags of every control interval, the robot's joint log, and the finger actuation record. Nothing in the evaluation is estimated from cameras or sensors. Official success criteria are in `SUCCESS.md`. Feedback exists only after the rollout; the deployed policy receives the observation of `sim2target/CONTRACT.md` and nothing else.

## 1. Official Evaluation

`verifier/report.json` uses schema `r2s2r-verifier/1` and has the same top-level keys for every task. Its `verifier_version` identifies the actual Ground-Truth Verifier used for that evaluation, as recorded by the target.

| Field | Description |
|---|---|
| `schema`, `verifier_version`, `task` | `r2s2r-verifier/1`, the actual verifier version, and the task name |
| `criteria` | ID, rubric and status of the success criteria the report was scored with: `provisional`, `approved`, or `undefined`; the criteria themselves are in `SUCCESS.md` |
| `status` | `evaluated`, `criteria_undefined`, or `not_evaluable` (rule below) |
| `success` | `true` or `false`; `null` unless status is `evaluated` |
| `progress` | Task progress 0–1, the score of `SUCCESS.md`; `null` if criteria are undefined or the score could not be computed |
| `milestones` | Per milestone name, stage, label, credit, reached, time (s since step 0; `null` if not reached). A stage with one milestone names it after the stage; otherwise `<stage>_<i>`. `[]` if no criteria |
| `stages` | Per stage name, weight, progress (0–1 within the stage), score. `[]` if no criteria |
| `events` | Timestamped observations: time, step, type, detail |
| `measurements` | Summary quantities of the task's criteria (exact values; the keys of your task: `TASK_CONFIG.md` section 5; empty while no criteria are defined) |
| `validity` | `run_valid`; `policy_runtime` (pass, reason: the policy error, if any); `physical` (the target's own run checks `R0_reference_config`, `R1_physics`, `R2_initial_state`, `R4_teleport`, `R9_integrity`, each true/false); `hardware` (section 2); `actions` (pass, status); `steps_executed`, `expected_steps`, `state_rows` |
| `versions` | Contract, state schema, environment, wrist, rubric, hardware specification and target model (`sim2target/REMOTE_API.md` section 7) |
| `note` | A remark on the status (for example why nothing was scored), otherwise `null` |

### Status Rule

**`evaluated`:** Success criteria exist for the task and the available record can be evaluated.

`success` is true only if the criteria are fully met (progress 1.0 and the final condition of `SUCCESS.md`), the hardware is compliant, the policy ran without failure, and the target's own run checks passed; otherwise it is false.

A policy failure or hardware violation does not automatically change the report's status: the available record may still be scored, but success is false and the rollout is technically invalid for ranking.

A physically unsuccessful but technically valid rollout must receive its actual task progress, including `0.0`, regardless of when the physical task failure occurred. Dropping an object or missing a milestone does not by itself end the episode.

If a policy execution failure truncates the record so that progress genuinely cannot be computed, `progress` may be `null`; the report must explain why. Such a technically invalid submission is unranked.

**`criteria_undefined`:** No success criteria are defined for the task (`criteria.status = undefined`). Success and progress are `null`, milestones and stages are empty, and measurements is empty; validity is still reported. Nothing is scored.

**`not_evaluable`:** The record itself is unusable due to a target-side problem, explained in `note`; such a submission is not charged.

### Progress and Rankability

The official Ground-Truth Verifier computes success and progress according to the active task criteria.

| Task | Official Progress |
|---|---|
| Tennis | 9 sequential stages, each contributing 1/9 |
| Plug | 4 sequential stages, each contributing 0.25 |
| Pen | 5 sequential stages, each contributing 0.20 |
| Cube | 4 sequential stages, each contributing 0.25 |

The detailed stage definitions, ordering, physical thresholds and success conditions remain in each task's `SUCCESS.md`.

For Cube, distance-to-solved measurements are diagnostics; they do not replace the four-stage progress rubric.

**Rankability rules:**

- A valid successful rollout is rankable.
- A valid partial-progress rollout is rankable.
- A valid rollout with `progress = 0.0` is rankable.
- A valid rollout that physically fails early but continues without technical failure is rankable.
- A policy-invalid, hardware-invalid, runtime-invalid or otherwise technically invalid rollout is unranked.
- A result with undefined criteria or genuinely uncomputed progress is unranked.
- Missing progress must never be silently converted to `0.0`.

The official evaluation system determines rankability. The research harness records and displays the official result; it must not independently recalculate progress or override the verifier.

**Exact values.** Every reported evaluation value is computed from the target's simulation state; there are no measurement margins, uncertainty intervals or unknown outcomes for quantities the verifier actually computes.

The evaluation reports what happened, not why: a stage that scored 0 is not explained, and a loss of retention gives its time, not the condition that ended it. Diagnosing causes from the state record, videos, frames and logs is your task.

## 2. Hardware and Runtime

`validity.hardware` applies `hardware/SPECS.md` section 7 to the finger joints over the whole policy phase, from the target's exact joint state and applied torque at the controller rate:

- `status`: `compliant` or `violation`
- `spec_version`
- `mode`
- `checks`: position, velocity, effort, actions — each with its status, worst joint and time, maximum excess and margin
- `violations`
- `joints`: joints involved in a violation
- `max_ratios`: velocity and effort relative to limits; position excess in radians
- `steps`

The wrist has no rule beyond its controller; its tracking and saturation are visible in the state record and rollout log, never a hardware violation.

`validity.policy_runtime` reports a policy failure with the error text.

`validity.physical` lists the target's own run checks: reference configuration, finite state, initial state at rest, no position jumps, and record integrity.

**Technical validity and task progress are separate.** A physical task failure does not imply hardware or runtime invalidity. Conversely, a policy or hardware violation may make the evaluation unrankable even when some task milestones were reached.

## 3. State Record

`state/trajectory.npz` is the ground-truth state of the rollout at the control rate, described field by field in `state/schema.json` (schema `objstate-1`: every field's shape, dtype, unit, frame, description; the conventions; rows, control_steps_executed, objects, parts, goals).

### Rows and Time

Row `k` (0 ≤ k ≤ N) represents the target state synchronized with policy observation step `k`.

Shared wrist and object-state fields have the same values and timestamps as the corresponding policy observation. The state record additionally contains feedback-only fields, such as contact flags, that are not available to the deployed policy.

Noisy finger observations and policy action commands are recorded in `logs/trial_0.npz`.

A complete rollout has `N + 1` state rows for `N` executed control steps (`TASK_CONFIG.md` section 2). Row `N` is the state after the last command.

After a policy failure at step `k`, the state record covers the available states up to the failure. The corresponding rollout log records the successfully captured control steps. Exact partial-record alignment follows the recorded step indices and metadata; do not infer missing actions or states.

Time is `t = 0.002 × step` seconds, with `t = 0` at control step 0, using the same time base as `logs/trial_0.npz` and `video/frames.json`.

The contact flags of row `k` cover the control interval ending at the row (row 0: its own instant).

Quaternions are `(w, x, y, z)`, unit norm, sign-continuous as in `sim2target/CONTRACT.md`.

| Field | Shape | dtype | Unit / frame | Description |
|---|---|---|---|---|
| `step` | `(R,)` | `int64` | — | Control step k of the row |
| `t` | `(R,)` | `float64` | s | `0.002 × k` |
| `wrist_position` | `(R, 3)` | `float64` | m, world | Wrist-frame origin (the hand's root link, `hardware/SPECS.md` section 3) |
| `wrist_orientation` | `(R, 4)` | `float64` | world ← wrist | Rotates wrist-frame vectors into the world frame |
| `wrist_linear_velocity` | `(R, 3)` | `float64` | m/s, world | Velocity of the wrist-frame origin |
| `wrist_angular_velocity` | `(R, 3)` | `float64` | rad/s, world | Angular velocity of the wrist frame |
| `object_position` | `(R, O, 3)` | `float64` | m, world | State-frame origin of each object (`object/SPECS.md`); axis 1 = object index |
| `object_orientation` | `(R, O, 4)` | `float64` | world ← state frame | State-frame orientation |
| `object_linear_velocity` | `(R, O, 3)` | `float64` | m/s, world | Velocity of the state-frame origin (not of the centre of mass) |
| `object_angular_velocity` | `(R, O, 3)` | `float64` | rad/s, world | Angular velocity of the object |
| `hand_object_contact` | `(R, O)` | `bool` | — | Any contact between the hand and the object during the control interval ending at the row |
| `object_environment_contact` | `(R, O)` | `bool` | — | Any contact between the object and the environment (the floor or table of the task's scene, `TASK_CONFIG.md` section 3) during the interval |
| `object_object_contact` | `(R, O, O)` | `bool` | — | Any contact between two different objects during the interval (symmetric) |
| `object_names` | `(O,)` | `str` | — | Object order of every `object_*` array (`TASK_CONFIG.md` section 4) |
| `part_names`, `part_object` | `(P,)` | `str`, `int64` | — | Part order of every `part_*` array and the owning object index of each part (`P = 0`: arrays are empty) |

`R` is the number of rows, `O` the number of objects and `P` the number of parts of your task.

A task adds its own fields to the state record (per-part states, configuration indices, the goal block); they are listed with their shapes in `TASK_CONFIG.md` section 5 and described in `state/schema.json`.

### Observation and Feedback Boundary

- The deployed policy receives only the fields documented in `sim2target/CONTRACT.md` and the task-specific observations in `TASK_CONFIG.md`.
- Wrist and object states shared between observation and feedback are synchronized.
- Finger encoder observations and action histories are recorded in the rollout log.
- Contact flags exist only in feedback; they are never part of the policy observation.
- The feedback does not expose contact forces, contact depths, per-link contact details, or hidden target dynamics.

The state record and the agent's own simulation of the same action sequence can be compared by timestamp and control step using `r2s2r-calib` (`TOOLS.md` section 3).

## 4. Rollout Log

`logs/trial_0.npz` contains `N` rows for a complete rollout (row k = control step k), or the available executed and recorded steps up to a policy failure.

The log contains:

- `joint_names` `(20,)`: the joint names of your task's hand.
- Measured `q`, `qd` `(N, 20)`: the policy's finger encoder observations, including noise.
- Finger commands `q_target`, `qd_target` `(N, 20)` as sent; `None` recorded as zeros.
- Wrist commands as sent:
  - `wrist_position_command` `(N, 3)`
  - `wrist_orientation_command` `(N, 4)`
  - `wrist_linear_velocity_command` `(N, 3)`
  - `wrist_angular_velocity_command` `(N, 3)`
  - Optional `None` values recorded as zeros.
- Executed wrist targets after command limits:
  - `wrist_position_target`
  - `wrist_orientation_target`
  - `wrist_linear_velocity_target`
  - `wrist_angular_velocity_target`
- `wrist_command_limited` `(N, 5)` boolean, one flag per limit in this order:
  1. `translation_rate`
  2. `workspace`
  3. `rotation_rate`
  4. `linear_velocity`
  5. `angular_velocity`

For a partial rollout, the first dimension is the number of recorded control-step rows rather than the full expected `N`. The metadata and step indices determine alignment.

The executed targets are what the wrist controller tracked (`hardware/SPECS.md` section 4); the wrist state it reached is in the state record.

**Calibration:** For sim-to-target replay, distinguish commanded actions from executed wrist targets. `r2s2r-calib` supports both modes; the agent's simulator must account for the command limits when replaying the original commanded targets.

## 5. Videos and Cameras

The three videos are renderings of the target rollout: the recorded ground-truth trajectory of the hand (at its floating pose) and of the objects, drawn with the published camera model.

They show the same underlying rollout as `state/trajectory.npz`; no camera or sensor pipeline is part of the evaluation.

Three fixed, synchronized views: `top`, `left` and `right` (global shutter, 848 × 480, pinhole without distortion). Their placement for your task is in `TASK_CONFIG.md` section 4.

**RGB video:** H.264, real time, covering the whole rollout (up to the failure after a policy failure); the frame rate and number of frames per view for a complete rollout are in `TASK_CONFIG.md` section 2.

**Camera calibration:** `calibration.json` contains `rig_version`, `layout`, and, per view, width, height, `K`, distortion, `T_world_cam`, `T_cam_world`, `position_m`, purpose; world frame as in `hardware/SPECS.md`; OpenCV camera frame; pixel `(0, 0)` at the centre of the top-left pixel; depth model and conventions.

**Timestamps:** `video/frames.json` gives each frame's `frame_t` (seconds since control step 0) and `control_step = round(frame_t × 500)`, the same for all views. `video/video.json` gives the fps, frame count, duration and files.

**Frames on demand:** `frames sNN VIEW TIMES [depth]` (`sim2target/REMOTE_API.md` section 6) renders the same trajectory at any instant, as RGB PNG and optionally 16-bit depth PNG in 0.1 mm units (`0` = no return), noise σ = 1 mm × (z / 0.5 m)². Depth is available only through this query.

**Important:** `calibration.json` describes the target camera rig. It is not the research agent's sim-to-target calibration output produced by `r2s2r-calib`.

## 6. Standard Feedback

Evaluation evidence is produced and stored automatically after every rollout (after a policy failure: up to the failure), never changed afterwards. It is not pushed to you; retrieve it with `fetch sNN` (`sim2target/REMOTE_API.md` section 4).

| File | Contents |
|---|---|
| `feedback.json` | Protocol, task, policy SHA-256, every version (`versions`), criteria ID and status, steps executed and expected, feedback categories (`contents`), and the SHA-256 of every returned file |
| `verifier/report.json` | Official evaluation (section 1) |
| `state/trajectory.npz`, `state/schema.json` | Ground-truth state record (section 3) and its field-by-field description |
| `logs/trial_0.npz` | Rollout log (section 4) |
| `video/top.mp4`, `video/left.mp4`, `video/right.mp4` | Synchronized renderings of the rollout (section 5) |
| `video/frames.json`, `video/video.json` | Per-frame time and control step; video metadata |
| `calibration.json` | Camera intrinsics, extrinsics, conventions and depth model |

### Feedback Categories (`feedback.json` contents)

| Category | Contents |
|---|---|
| Verifier results | `verifier/report.json`: status, success, progress, milestones with times, stages, validity, versions; criteria status |
| Rollout evidence | `state/trajectory.npz` with `state/schema.json`, `logs/trial_0.npz`, videos with `frames.json` and `video.json`, `calibration.json`, the report's events and measurements; RGB and depth frames on demand (`frames`) |
| Timestamps | `t = 0.002 × step`, `t = 0` at control step 0; state row k is synchronized with observation step k; log row k represents control step k; `frames.json` provides per-video-frame timestamps |

### Result Interpretation

- **Valid zero-progress result:** `progress = 0.0` is an actual computed score, not missing feedback.
- **Partial progress:** Milestones and stage scores are reported according to the active task criteria.
- **Technical invalidity:** Policy, hardware, or runtime failures are reported through validity fields; any available rollout evidence is preserved.
- **Uncomputed progress:** `progress = null` is not converted to zero. The report provides an explanation when available.
- **Undefined criteria:** Success and progress are `null`; no ranking occurs.
- **Historical versioning:** Every report retains the criteria and verifier versions used when it was evaluated.

The verifier's implementation and configuration remain protected. Agent-facing feedback contains the documented results and evidence, not hidden verifier internals.

**Not provided:** Explanations of failures or suggested fixes, contact forces, contact depths, per-link contacts, joint torques, physical parameters, the evaluation condition, the target's diagnostics, and the simulator itself (`sim2target/REMOTE_API.md` section 8).

## 7. Research Workflow, On-demand Access, and Analysis Tools

| Category | Commands and tools | Use |
|---|---|---|
| Standard research workflow | `history`, `intent`, `note`, `training-video` (`r2s2r-harness submit`, `reflect`, `video`) | Experiment history, best evaluated policy, comparisons with earlier comparable submissions; research intent before and reflection after each submission; local training-simulation video |
| On-demand access | `package`, `frames` | Exact earlier packages; RGB frames at any instant of a finished rollout, optionally with depth |
| Sim-to-target calibration (mandatory after every evaluation with accessible feedback) | `r2s2r-calib` | Replay the target action sequence in your simulator, compare wrist, object, part and joint trajectories, diagnose discrepancies, update and validate your simulator, and record evidence (`TOOLS.md` section 3) |
| Optional analysis tools | `r2s2r-hwcheck`, your own diagnostics | Check finger trajectories against hardware rules; run additional local diagnostics |

None of these tools changes official results.

Syntax and limits: `sim2target/REMOTE_API.md` sections 5 and 6; tools: `TOOLS.md`.

### Mandatory Sim-to-Target Calibration

After every target evaluation with accessible rollout feedback, and before the next target submission, the agent must complete the mandatory `r2s2r-calib` workflow defined in `TOOLS.md` section 3.

Required steps:

1. **Extract:** Use `r2s2r-calib extract` on the fetched feedback.
2. **Replay:** Use `r2s2r-calib replay` with the agent's simulator adapter.
3. **Compare:** Use `r2s2r-calib compare` to quantify simulation-to-target errors.
4. **Diagnose:** Use `r2s2r-calib diagnose` to identify discrepancies across contact phases and dynamics.
5. **Record:** Use `r2s2r-calib record` to preserve calibration hypotheses, evidence and configuration.
6. **Improve:** Decide which simulator changes are justified, validate the next candidate locally, and summarize the findings in the research reflection.

Calibration evidence must be associated with the corresponding submission and should identify:

- Submission ID and target feedback reference.
- Simulator configuration or revision.
- Replay mode and action-target mode.
- Comparison metrics and diagnostic findings.
- Simulator changes or reasons for leaving it unchanged.
- Local validation outcome.

The agent chooses its simulator, physics models and calibration algorithm; the use of `r2s2r-calib` for evidence-based comparison is mandatory.

If feedback is sealed, unavailable or technically unusable, record the blocker rather than inventing results. If replay is genuinely infeasible, preserve the failed tool evidence and follow the documented exception procedure before proceeding without completed replay-based calibration.

**Training-simulation video:** For every submission, also link a representative rollout of the exact submitted policy in the agent's training simulator and state whether it is a full or partial rollout (`sim2target/REMOTE_API.md` section 5).

This is a standard research artifact, but a missing video does not block the Remote API submission and never affects official scoring or ranking.

Mandatory calibration and training-video recording are separate requirements.

## 8. Research Use

You may use the state record, videos, frames, logs and official results to diagnose failures and improve your simulation and policy.

Your own diagnostic metrics do not replace the official evaluation.

Feedback describes the target's observed rollout behavior, but does not reveal its protected simulator, hidden dynamics or verifier implementation. The agent must independently determine why its policy succeeded or failed, using the available evidence.
