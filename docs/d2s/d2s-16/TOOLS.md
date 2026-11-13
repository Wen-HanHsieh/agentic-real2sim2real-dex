# TOOLS.md — Research Tools

All tools run locally, except `r2s2r-d2s`, which sends your research records to the record store (`demo2sim/RECORDS.md`).

## 1. Available Tools

| Tool | Purpose | Reference |
|---|---|---|
| Reconstruction tools | Video segmentation, camera calibration, hand and object reconstruction, tracking, validation, comparison video, 3D viewer | Section 2 |
| `r2s2r-d2s` | Research records (reconstruction, criteria, simulation, training iterations, verification, notes), test suites and the gate, status and time | Section 3, `demo2sim/RECORDS.md` |

**Implementations:** `tools/recon/`, `tools/d2s/`.

**Experiment:** `export R2S2R_API=r2s2r-<task>` (the exact command and your experiment ID: `TASK_CONFIG.md` section 1).

## 2. Reconstruction Tools

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

## 3. Research Records

`r2s2r-d2s` records your reconstruction, criteria, simulation, training iterations, verdicts and notes, registers your test suites and runs the gate. `/usr/local/lib/r2s2r-v3/tools/d2s_measures.py` (numpy only) defines the standard state log and measurements that the gate, the target and `r2s2r-d2s replay` use, the start check (`python d2s_measures.py start <state.npz> hand|environment`) and the handoff states of a chain; you may import it. `/usr/local/lib/r2s2r-v3/tools/d2s_teacher.py` (numpy and PyTorch) trains a skill with privileged state and distils it into a deployable policy: a PPO teacher (optionally residual over, or behavior-cloned from, your own controller), a DAgger student over a history of observations, a success-driven curriculum (`Curriculum`) and a numpy export; its docstring describes the interface your simulation provides. `/usr/local/lib/r2s2r-v3/tools/d2s_parity.py` (run it with your own Python that has `mujoco` and `mujoco_warp`) checks that a MuJoCo Warp training simulation matches your CPU evaluator: `static` (models and options), `states` (contacts and buffer overflow on your own states), `outcome` (the same policy on both, at least 128 seeds: the check that counts), `replay` (a smoke test) and `snippet` (code to record what they read); `python d2s_parity.py --help`. `/usr/local/lib/r2s2r-v3/tools/d2s_warp_scene.py` (`recon-python`, which has mujoco 3.17.0, mujoco_warp 3.17.0, warp-lang 1.19.0 and PyTorch) builds one MuJoCo model of your hand and scene for both your CPU evaluator and MuJoCo Warp training: `HandScene` loads your hand from `hardware/` (floating wrist, joint limits, armature) and adds your objects and environment (`add_box` and `add_cylinder` build convex meshes; `attach_mjcf` takes your own MJCF), with solver settings verified to give the same outcomes on both. `CpuHand` and `WarpHandEnv` run the wrist and finger controllers of `hardware/SPECS.md` the same way on the CPU and in thousands of GPU worlds (1 kHz, commands held for two ticks, torque saturation, the per-tick hardware rules); `WarpHandEnv` resets to the states you give, steps, and returns observations, contacts, buffer-overflow flags and per-episode hardware-violation counts as PyTorch tensors without copying. `python d2s_warp_scene.py check MODEL` lists the settings in any model that break CPU/GPU parity; `port` checks a controller port; `verify` and `bench` repeat the tool's own parity and speed measurements; `python d2s_warp_scene.py --help`, and the docstrings give the API. Its commands, record contents and limits are in `demo2sim/RECORDS.md`. `r2s2r-d2s recon` runs `check_reference.py` on the reconstruction before it is recorded.

**Failure analysis.** After a gate with failing episodes, a separate model that changes nothing reads the gate's failure package and writes a diagnosis to `analysis.md` and `analysis.json` in the gate's output.
- The package: your criteria, the funnel, the failing episodes' measurements and failed predicates, where the measurements overruled your evaluation, state-log summaries, the failure montages, your `--method`, `--hypothesis` and `--observed`, and the latest feasibility or skill result for the same primitives. It sees only what you can see.
- The diagnosis: the first observable failure, a cause labelled as inference with its evidence, one proposed change with its expected physical effect and the number that should move, a confidence level, and checks.
- It usually arrives within about 10 minutes of the gate decision. `r2s2r-d2s status` lists the newest under `failure_analyses`; `r2s2r-d2s gate --wait` shows its status.
- Not every gate gets one (there is an hourly limit); `analysis_status.json` says skipped or unavailable, and why.
- It is an independent inference, not a measurement and not a gate decision, and it can be wrong. The gate does not wait for it and nothing depends on it.
- A commanded-versus-actual comparison needs your commanded joint targets: log them in the state log as `joint_target` where your policy sets them.

## 4. Research Freedom and Tool Boundaries

- Tools are provided to assist research, not to prescribe your method; you may modify, extend or replace your own copies of them.
- You may develop additional local tools, simulators and diagnostics.
- The final policy follows the learning rules of `demo2sim/LEARNING.md`.
- Preserve experiment evidence and reproducibility.
- Follow `README.md` for the overall workflow and order.
