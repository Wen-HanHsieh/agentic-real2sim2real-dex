# TOOLS.md — Research Tools

The following tools are available to support autonomous robot research.

All tools run locally, except `r2s2r-harness`, which communicates with the target through the official API defined in `sim2target/REMOTE_API.md`.

## 1. Available Tools

| Tool | Purpose | Reference |
|---|---|---|
| `r2s2r-harness` | Research records, submission workflow, history, comparisons, best policy | Section 2 |
| `r2s2r-calib` | Mandatory simulation-to-target calibration after each target evaluation with available feedback | Section 3 |
| `r2s2r-preflight` | Validate policy packages before submission | `sim2target/PACKAGE.md` |
| `r2s2r-hwcheck` | Check local trajectories against hardware limits | `sim2target/HARDWARE_CHECK.md` |
| Reconstruction tools | Video segmentation, camera calibration, hand/object reconstruction, tracking, validation | Section 4 |

**Implementations:** `tools/harness/`, `tools/calib/`, `tools/preflight/`, `tools/hwcheck/`, `tools/recon/`.

**Task-specific API:**

`export R2S2R_API=r2s2r-<task>`

Use the exact command defined in `TASK_CONFIG.md`.

## 2. Research Harness

`r2s2r-harness` manages experiment records, submissions, comparisons, and policy artifacts.

### Commands

| Command | Purpose |
|---|---|
| `submit` | Record experiment intent, package a policy, and submit |
| `reflect` | Record diagnosis and decisions after evaluation |
| `summary` | Show submission history and progress |
| `result` | Inspect an individual evaluation result |
| `record` | Add research notes and evidence |
| `gate` | Inspect regression checks and comparisons |
| `best` | Retrieve the best evaluated policy |
| `archive` / `verify` | Archive records and verify integrity |
| `video` | Link a local training-simulation rollout to a submission |

**Examples:**

- Submit: `r2s2r-harness submit my_policy/ --hypothesis "..." --change "..."`
- Dry run: `r2s2r-harness submit my_policy/ --hypothesis "..." --change "..." --dry-run`
- Reflect: `r2s2r-harness reflect sNN --diagnosis "..." --evidence "..." --keep keep|reject|undecided`
- Summary: `r2s2r-harness summary`
- Result: `r2s2r-harness result sNN`
- Regression gate: `r2s2r-harness gate sNN`
- Best policy: `r2s2r-harness best --download best/`
- Archive: `r2s2r-harness archive ~/records`
- Verify archive: `r2s2r-harness verify ~/records`
- Training video: `r2s2r-harness video sNN my_rollout.mp4 --package my_policy/`

### Progress and Ranking

- Official success, progress, stage scores, ranking, and regression comparisons are computed by the target's active Ground-Truth Verifier, not by the harness.
- A valid rollout is rankable even if the task fails immediately or its progress is `0.0`.
- Early task failure alone does not make a rollout unrankable.
- Technically invalid rollouts are unranked according to the official evaluation rules.
- Missing progress (`null` or unavailable) is not equivalent to valid zero progress.
- The harness must preserve and display the target's actual criteria version, success, progress, milestones, rankability, and regression-gate results.
- Comparisons must use compatible criteria versions; results evaluated under different rubrics must not be silently compared.
- The harness must not manufacture progress values or independently override official verifier decisions.

The exact ranking and regression-gate rules are defined in `sim2target/REMOTE_API.md`.

### Important Behavior

- `submit` captures the policy package, Git revision, source changes, experiment intent, and submission receipt.
- Local research records are write-once. The submitted package is hashed for reproducibility.
- `--dry-run` does not contact the target.
- `reflect` records post-evaluation diagnosis, evidence, and the next research direction.
- `video` links a local training rollout to the exact submitted policy package. The archive hash must match; uploading the video does not trigger target evaluation.
- The harness does not automatically restore or deploy the best policy.
- The agent independently chooses which experiments to run, which policies to keep, and how to improve them.

See `sim2target/REMOTE_API.md` and `sim2target/EXPERIMENT.md` for workflow and record requirements.

## 3. Sim-to-Target Calibration

`r2s2r-calib` compares a target rollout with the agent's own simulator.

**Calibration is mandatory after every target evaluation with accessible feedback and before the next target submission.**

Calibration is not required before the first target evaluation.

The agent must use `r2s2r-calib` to analyze simulation-to-target discrepancies. It may choose its own simulator, physics parameters, calibration algorithm, controller, and learning method.

### Required Workflow

1. **Extract:** Extract target states, actions, and contacts from the fetched feedback.
2. **Replay:** Replay the target action sequence in the agent's own simulator.
3. **Compare:** Quantify errors between the target and simulation trajectories.
4. **Diagnose:** Identify discrepancies in robot motion, object dynamics, and contact behavior.
5. **Update:** Modify the simulation or explicitly document why no modification is justified.
6. **Validate:** Test the next candidate policy in the updated simulation.
7. **Record:** Save the calibration evidence and summarize the findings in the research reflection before the next submission.

The agent must attempt and document this workflow for every applicable evaluation.

If target feedback is unavailable, sealed, or technically unusable, the agent must record the blocker. It must not claim calibration was completed or fabricate target measurements.

If replay is genuinely infeasible, the agent must preserve the failed tool evidence, document the reason, and record a calibration exception (see Exception Procedure) before proceeding without replay-based calibration.

### Exception Procedure

A calibration exception is self-declared; no human approval is required. It is allowed only when the target feedback is unavailable or sealed, or when replay is genuinely infeasible. Inconvenience is never grounds for an exception.

An exception record must contain:

- the actual tool error logs, or the evidence that the feedback is unavailable (for example the `fetch` output);
- a written explanation of why calibration cannot be completed;
- any feasible alternative diagnosis;
- the status `exception`, never `completed`.

### Recording a Calibration

Record every calibration or exception with `r2s2r-calib record DIR --hypothesis TEXT --notes TEXT --config cfg.json --files ...`, then cite it in the research reflection with `r2s2r-harness reflect sNN --calibration DIR`.

- **Completed calibration (`cfg.json`):** `status` = `completed`, `submission_id` (sNN), `feedback_sha256` (the submission's feedback hash in `history`), `replay_mode` (`commanded` or `executed`), `simulator_revision`, and `simulator_changes` or `no_change_reason`. `--files` includes the `metrics.json` of `r2s2r-calib compare` or `diagnose` on that feedback.
- **Exception (`cfg.json`):** `status` = `exception`, `submission_id`, `feedback_sha256` (the hash, or `unavailable`), `exception_reason_class` (`feedback_unavailable`, `feedback_sealed`, or `replay_infeasible`), `explanation`, and `alternative_diagnosis`. `--files` includes at least one evidence file. `replay_infeasible` requires accessible feedback.
- **Optional keys:** `experiment`, `archive_sha256`, `policy_sha256`, `simulator_config`, `local_validation`, `calib_mode` (`action`, `state-step`, or `state-segment`). Other keys are refused.
- **Record location:** The harness looks for records under `--calib-records DIR`, else `$R2S2R_CALIB_RECORDS`, else `<records>/<api>/calibration`.

### Submission Check

By default, `r2s2r-harness submit` refuses the next submission when the latest finished submission has neither a valid completed calibration record nor a valid exception record. The first submission is exempt. No option or environment variable skips this check. It is a local check of the harness, not a server-side gate: the target never blocks a submission for a missing research record.

### Commands

| Command | Purpose |
|---|---|
| `extract` | Extract target trajectory and actions from feedback |
| `replay` | Replay target actions in the agent's simulator |
| `compare` | Quantify simulation-to-target trajectory errors |
| `diagnose` | Analyze error growth and contact phases |
| `video` | Generate a side-by-side target/simulation video |
| `record` | Save calibration hypotheses, evidence, and changes |

**Examples:**

- Extract: `r2s2r-calib extract <bundle.tgz|dir> -o target.npz`
- Replay: `r2s2r-calib replay target.npz --driver adapter.py -o sim.npz`
- Compare: `r2s2r-calib compare target.npz sim.npz -o comparison/`
- Diagnose: `r2s2r-calib diagnose target.npz sim.npz -o diagnosis/`
- Video: `r2s2r-calib video target.mp4 sim.mp4 -o comparison.mp4`
- Record: `r2s2r-calib record diagnosis/ --hypothesis "..."`

### Replay Modes

- **`action`:** Open-loop replay from the target's initial state.
- **`state-step`:** Reset to the target state before every action, measuring one-step prediction errors.
- **`state-segment`:** Reset at the start of each target contact phase.
- **`--targets executed`:** Replay the targets actually executed by the target controller (default).
- **`--targets commanded`:** Replay the policy's original commands; the simulator adapter must model command limits.

The agent provides its own simulator adapter:

- Python adapter: `--driver adapter.py`
- External process: `--adapter-cmd "<command>"`

The adapter interface is defined in `tools/calib/calib_adapter.py`.

### Available Adapters

- `tools/calib/calib_kinematic_adapter.py` — NumPy-only reference; ideal hand motion, frozen objects, no physics.
- `tools/calib/calib_mujoco_adapter.py` — MuJoCo example using the public robot URDF, hardware controllers, and object specifications.

The MuJoCo example uses default contact parameters and does not reproduce articulated object mechanisms such as Cube layer turns.

### Calibration Requirements

- Compare robot joints, wrist, objects, articulated parts, and contact phases when available.
- Investigate controller, actuator, free-body dynamics, and contact-model discrepancies.
- Use the actual target rollout and the agent's own simulator for comparison.
- Test candidate corrections locally before another target submission.
- Preserve calibration evidence and record remaining limitations.
- Summarize the calibration results in the next experiment hypothesis and reflection.
- Do not substitute a successful local simulation for the required sim-to-target comparison.

`r2s2r-calib` operates locally and does not contact the target or change official evaluation results.

## 4. Reconstruction Tools

Reconstruction tools are provided under `tools/recon/`.

**Environment setup:**

`source $R2S2R_RECON_HOME/env.sh`

This provides:

- `recon-python` — SAM 3, HaWoR, MANO, MuJoCo, PyTorch, trimesh, python-fcl.
- `aux-python` — SAM 2.1, MoGe, PyTorch3D.
- `blender` — Blender 4.2 LTS, headless rendering.
- `uv` and `micromamba`.

Model paths and dependencies are configured by the environment.

**Manifest:** `$R2S2R_RECON_HOME/manifest.json`

**Licenses:** `$R2S2R_RECON_HOME/`

The reconstruction environment and installed tools are read-only. Output files should be written to the agent's research workspace. GPU acceleration is needed for the segmentation and hand models.

### Available Reconstruction Tools

| Tool | Purpose |
|---|---|
| `frames.py` | Extract demonstration frames |
| `sam3_seg.py` | Segment objects and hands using SAM 3 |
| `sam2_video_seg.py` | Propagate segmentation masks through video |
| `moge_intrinsics.py` | Estimate camera intrinsics and pointmaps using a learned prior |
| `camera_calib.py` | Calibrate camera intrinsics, rotation, and world transforms |
| `pose_track.py` | Track rigid-object 6D poses |
| `objpose_track.py` | Track object poses with render-and-compare optimization |
| `hawor_cam.py` | Estimate initial 3D hand poses using HaWoR |
| `handfit_inputs.py` | Prepare hand-fit inputs using camera, scene, masks, and contacts |
| `mano_fit/handlib/fit.py` | Fit MANO hands to the reconstructed scene |
| `mano_fit/handlib/score.py` | Evaluate hand-fit quality |
| `handfit_export.py` | Export validated hand reconstruction |
| `export_reference.py` | Convert reconstructed data into the reference contract |
| `render_compare.py` | Compare reconstruction renders with demonstration |
| `validate_reconstruction.py` | Validate geometry, tracking, and motion reconstruction |
| `check_reference.py` | Validate reconstruction output format |
| `build_viewer.py` | Build an interactive 3D reconstruction viewer |
| `fixture/run_e2e.py` | Test the reconstruction toolchain using a synthetic demonstration |
| `blender` | Build object meshes and render reconstructed scenes |

### Important Notes

- The default reconstruction workflow is defined in `demo2sim/RECONSTRUCTION.md`.
- Reconstruction outputs and validation requirements are defined in `demo2sim/REFERENCE.md`.
- The agent may modify, extend, or replace individual reconstruction tools while following the required workflow and output contract.
- Learned monocular camera estimates are priors, not guaranteed calibrations. Prefer geometric calibration when reliable correspondences are available.
- Tool scripts document their command-line arguments and expected input/output formats.
- The agent is responsible for checking reconstruction quality against the human video.

### Reconstruction Validation

- `recon-python validate_reconstruction.py --recon <recon>`
- `recon-python check_reference.py <recon> --task-dir . --video <demo file>`
- `recon-python fixture/run_e2e.py --work <empty dir> --gpu-models`

A reconstruction must satisfy the checks defined in `demo2sim/REFERENCE.md`.

## 5. Research Freedom and Tool Boundaries

- Tools are provided to assist research, not to prescribe the agent's learning algorithm.
- The agent may develop additional local tools and diagnostics.
- The agent must complete the required sim-to-target calibration workflow before subsequent submissions.
- Use only the documented remote API to interact with the target.
- Never inspect, modify, or bypass protected target internals.
- Preserve experiment evidence and reproducibility.
- Follow `README.md` for the overall workflow, `SUCCESS.md` for evaluation criteria, and the shared interface documents for technical contracts.
