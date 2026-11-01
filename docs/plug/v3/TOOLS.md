# Research Tools

These tools run on your machine and never compute or change official results. `r2s2r-harness` is the client of the standard research workflow (`README.md`, `sim2target/REMOTE_API.md` section 5). `r2s2r-calib` serves the sim-to-target calibration required after each target evaluation (section 2); `r2s2r-hwcheck` and your own diagnostics are optional. `r2s2r-preflight` checks a package before you send it. Only `r2s2r-harness` contacts the target environment, and only through the commands of `sim2target/REMOTE_API.md`.

| Tool | Category | Purpose | Reference |
|---|---|---|---|
| `r2s2r-harness` | Standard research workflow | Research records (intent, reflection), history, comparisons, best evaluated policy, local archives | Section 1 |
| `r2s2r-hwcheck` | Optional analysis | Check local finger trajectories against the hardware rules | `sim2target/HARDWARE_CHECK.md` |
| `r2s2r-calib` | Sim-to-target calibration (required after each target evaluation) | Compare your simulation with a target rollout: extract, replay through your simulator adapter, compare wrist, objects, parts and joints step by step, diagnose by contact phase, plots, side-by-side video, experiment records | Section 2 |
| `r2s2r-preflight` | Package check | Check a policy package (contract `v2`) before `validate` / `submit`, with the initial configuration of your task's hand (`--hand left` or `R2S2R_HAND=left` for the left hand, `TASK_CONFIG.md` section 1) | `sim2target/PACKAGE.md` |
| Reconstruction tools | Demo-to-Sim | Segment the demonstration video, track the hand, reconstruct the object and its motion (`demo2sim/REFERENCE.md`) | Section 3 |

Implementations: `tools/harness/`, `tools/hwcheck/`, `tools/calib/`, `tools/preflight/`, `tools/recon/`. Where a tool takes the task name, it is the task name of `TASK_CONFIG.md` section 1.

## 1. Research Harness (Standard Research Workflow)

`r2s2r-harness` keeps the standard research records and policy artifacts using the API commands `intent`, `submit`, `history`, `note`, `fetch`, and `package`; its `video` command uses `training-video`.

```bash
export R2S2R_API=r2s2r-<task>   # your task's API command (TASK_CONFIG.md section 1), or pass --api

r2s2r-harness submit my_policy/ --hypothesis ... --change ... [--rationale ...] [--parent sMM] \
    [--kind improvement|diagnostic|experimental] [--repo .] [--local result.json] [--sim-config cfg.json] \
    [--checkpoint REF] [--records DIR] [--dry-run]
r2s2r-harness reflect sNN --diagnosis ... --evidence ... --keep keep|reject|undecided [--worked ...] \
    [--failed ...] [--decision ...] [--next ...] [--limitation ...] [--analysis ...]
r2s2r-harness summary
r2s2r-harness result sNN
r2s2r-harness record sNN --kind improvement --hypothesis ... --change ... --evidence ... --decision ... \
    [--keep keep|reject|undecided] [--repo .] [--sim-config cfg.json] [--checkpoint REF] [--analysis TEXT] \
    [--local result.json] [--parent sMM]
r2s2r-harness gate sNN
r2s2r-harness best --download best/
r2s2r-harness archive ~/records
r2s2r-harness verify ~/records
r2s2r-harness video sNN my_rollout.mp4 --package my_policy/ [--simulator NAME] [--local-run ID]
```

- **`submit`:** packs the directory deterministically (or uses an existing `.tar` / `.tar.gz`), captures the git revision, uncommitted changes, and the diff against the parent submission's revision (else the previous commit) from `--repo` (default: the current directory), records the intent, then submits the same archive. It keeps a write-once local copy (intent, receipt, full diff, package) under `--records` (default `~/r2s2r_records`). Missing fields are reported; a failed intent does not stop the submission. `--dry-run` prints the intent without contacting the target.
- **`reflect`:** after the result, appends your reflection (`sim2target/REMOTE_API.md` section 5); refused while the evaluation is still running.
- **`summary`:** every submission with role, keep, state, official status, verifier status, progress, criteria status, hardware, gate, comparison with the previous comparable submission, intent and reflection status, and the incomplete records. While the task's criteria are undefined it shows `criteria not defined` instead of a score. An evaluated failure whose progress could not be computed shows progress `N/A (not computed)` and gate `not ranked` (`sim2target/REMOTE_API.md` section 5).
- **`result`:** the official result of one submission as recorded in `history`: status, criteria id and status, success and progress (or `criteria not defined`, or `N/A (not computed)` with `rankable: False (progress_not_computed)`), stage scores, milestones reached, hardware and runtime validity, versions.
- **`record`:** appends a plain note (original schema); `--repo` adds the source revision and the latest commit's diff stat.
- **`gate`:** the official regression gate and the comparisons (`vs_previous`, `vs_best_before`) of a submission.
- **`best`:** the best evaluated policy and the ranking rule; `--download` retrieves its exact package on demand after verifying the hash.
- **`archive` / `verify`:** a write-once local copy of history, feedback bundles, and packages with a manifest, and its integrity check.
- **`video`** (standard research artifact, for every submission): links a video of your own training-simulation rollout of the policy submitted as `sNN` (MP4 or WebM, ≤ 64 MB). `--package` is the directory or archive you submitted; the harness packs it the same way as `submit`, refuses it unless its SHA-256 equals the submission's `archive_sha256`, uploads with `training-video`, and checks the stored video's SHA-256. Then state the rollout (full or partial) with a `training_video` record. Never evaluated or charged (`sim2target/REMOTE_API.md` section 5).

The best policy, the gate, and the comparisons are computed by the target environment from official results; the harness only records and displays them, and never restores or deploys a policy unless you ask (`best --download`). **You decide which experiments to run, which policies to keep, and how to improve them.**

## 2. Sim-to-Target Calibration (required after each target evaluation)

After each target evaluation, and before your next submission, calibrate your simulator against that rollout; no calibration is required before your first target rollout. `r2s2r-calib` works on the feedback you fetched (the ground-truth state record, the rollout log with the commanded and executed finger and wrist targets, timestamps, videos). The target's state record is exact, so every discrepancy between it and your replay is a property of your simulator, your controller model, or your contact model, not of a measurement. Local only; it never contacts the target and never changes official results. The simulator, physics parameters, calibration algorithm, policy, controller, and learning method are your choice; the tool aligns, compares and attributes.

1. **Extract, replay, compare:** `extract` the target trajectory, `replay` its action sequence in your own simulator through an adapter you write, and `compare` the wrist, object, part and joint trajectories step by step (plus a side-by-side `video`).
2. **Diagnose:** `diagnose` segments the episode by the target's contact phases and charges the error growth to your wrist controller model, finger actuator model, free object motion or contact model where the evidence supports it, and says "cannot determine" otherwise. Turn the discrepancies into testable failure hypotheses.
3. **Update:** change your simulator accordingly, or state why a discrepancy cannot be modeled.
4. **Screen:** test candidate repairs in simulation before the next target submission.
5. **Record:** the calibration evidence, modifications, and results (`record` below; summarize them in your reflection and next intent, `sim2target/REMOTE_API.md` section 5).

If replay is genuinely infeasible, record the reason and validate the next candidate in another documented way.

```bash
r2s2r-calib extract <bundle.tgz|dir> -o <target.npz>                     # fetched feedback -> trajectory file (r2s2r-traj/3)
r2s2r-calib replay <target.npz> --driver <adapter.py> -o <sim.npz>        # your simulator, in-process Python adapter
r2s2r-calib replay <target.npz> --adapter-cmd "<command>" -o <sim.npz>    # your simulator, any interpreter (JSON-lines protocol)
    [--mode action|state-step|state-segment] [--targets executed|commanded] [--steps N]
r2s2r-calib compare <target.npz> <sim.npz> -o <dir> [--lag N] [--threshold RAD]
r2s2r-calib diagnose <target.npz> <sim.npz> -o <dir>                      # metrics.json + report.md (+ PNG plots with matplotlib)
r2s2r-calib video <target.mp4> <sim.mp4> -o <out.mp4> [--sim-offset S]   # side-by-side video (needs ffmpeg)
r2s2r-calib record <dir> --hypothesis TEXT [--notes TEXT] [--config <cfg.json>] [--files ...]
```

| Command | What it does |
|---|---|
| `extract` | Writes a trajectory file (`r2s2r-traj/3`, NumPy `.npz`): the rollout log (`step`, `t`, `joint_names`, measured `q` and `qd`, the finger commands `q_target` and `qd_target`, the wrist commands `wrist_*_command`, the executed wrist targets `wrist_*_target`, `wrist_command_limited`) and the state record (`state_step`, `state_t`, `wrist_position` … `object_angular_velocity`, `part_*` and the other task-specific fields of `TASK_CONFIG.md` section 4 where the task has them, the contact flags, `object_names`, `part_names`), with `meta` (task, submission, versions, rates, the target's own wrist and finger tracking). Frames and quaternion conventions are those of `sim2target/FEEDBACK.md`. A bundle of another feedback protocol, a missing file or a misaligned record is refused with the reason |
| `replay` | Drives your simulator with the target's action sequence through an adapter (`tools/calib/calib_adapter.py`): a Python class `reset(initial_state)`, `apply(action)`, `read_state()`, optional `set_state(state)`, created by `make(meta)` in the `--driver` module, or any program speaking the JSON-lines protocol (`hello`, `reset`, `set_state`, `apply`, `read_state`, `close`) given as `--adapter-cmd`. `--mode action`: reset to the target's step-0 state, then apply every action open loop (the standard replay). `--mode state-step`: before each action, teleport to the target's recorded state of that step, so every row is a one-step prediction error (no accumulation). `--mode state-segment`: teleport only at the start of each contact phase of the target. `--targets executed` (default) feeds the wrist targets the target actually tracked; `--targets commanded` feeds the policy's commands, so your adapter must apply the command limits itself (`tools/preflight/preflight.py` `CommandLimiter`). Your adapter's states use the keys and conventions of the state record; optional blocks (parts, contacts) are compared when present |
| `compare` | Aligns by control step (state row `k` versus your row `k`; a simulated file at a higher rate is resampled onto the target's rows, a slower one is refused): per-joint RMSE, maximum and mean error, first step over the threshold, best time shift when one reduces the RMSE; wrist position error, geodesic orientation error, linear and angular velocity error per step; per object position, geodesic orientation, linear and angular velocity errors per step with maxima and the first step over 1 cm / 10°; per part (tasks with parts) the same plus the agreement of the configuration indices; contact-flag agreement where your adapter provides contacts; writes `metrics.json` and plain-SVG plots (joints, wrist, objects) into `<dir>` |
| `diagnose` | `compare` plus: segments from the target's contact flags (free / hand / environment / both, per object), per segment the error at its start and end, its growth and maxima for the wrist, the fingers and every object, the tracking of the same executed targets on both sides, and an attribution per segment and object: `free-body dynamics`, `inherited velocity error`, `contact model`, `none (reproduced)`, or `cannot determine` (the hand itself moved differently), plus the wrist controller / finger actuator attribution over the whole rollout; `report.md` with the thresholds used and, with matplotlib installed, PNG plots (`errors.png`, `positions.png`, `fingers.png`) |
| `video` | Scales both videos to the same height and plays them side by side, start-aligned (`--sim-offset` shifts yours) |
| `record` | Saves a calibration experiment: hypothesis, notes, your configuration, copies and hashes of the given files, a summary; appends one line to `<dir>/index.jsonl` |

**Adapters shipped with the tool** (`tools/calib/`): `calib_kinematic_adapter.py`, a NumPy-only reference without physics (the hand follows its targets ideally, objects stay frozen) for testing the pipeline and as a template; `calib_mujoco_adapter.py`, a working example on MuJoCo that builds a scene from public information only: the vendor URDF of your task's hand with its root link (`r_mount` or `l_mount`) as a free body, the finger PD controller and the wrist impedance controller of `hardware/SPECS.md`, and rigid objects with the dimensions and masses of `object/SPECS.md` (an object made of several parts as one rigid block, without its mechanism). Its contact properties are MuJoCo defaults: calibrating them against the target record is exactly the work this section asks for. Run it with `--selftest` first; `--scene scene.json` overrides the objects, their contact properties, the table and the floor. Both adapters run in process (`--driver`) or as a subprocess (`--adapter-cmd "python tools/calib/calib_mujoco_adapter.py --urdf URDF"`, with `URDF` = `hardware/wuji_hand2_right/urdf/right.urdf` or `hardware/wuji_hand2_left/urdf/left.urdf`, the hand of `TASK_CONFIG.md` section 1; the log's joint names must be that hand's), so your simulator may live in its own interpreter.

On the provided machine `r2s2r-calib` runs by default in a calibration environment with Python 3.12.3, NumPy 2.5.4, SciPy 1.18.1, Pillow 12.3.0, MuJoCo 3.17.0 and matplotlib 3.11.2, so the MuJoCo example adapter and the PNG plots of `diagnose` work as shipped; you may install other versions in your own environments. The tool itself needs NumPy only (plots are written as SVG without a plotting library; `diagnose` adds PNG plots when matplotlib is available); `video` needs `ffmpeg`. `frames` (`sim2target/REMOTE_API.md` section 6) gives RGB and depth frames of the target rollout at any instant for visual comparison.

## 3. Reconstruction Tools (Demo-to-Sim)

The reconstruction tools of `demo2sim/REFERENCE.md` section 3 are scripts under `tools/recon/`, the read-only installed copy (`$R2S2R_RECON_HOME/tools/recon`; your workspace's `tools/recon` links to it). They run on your machine in the pre-installed, read-only reconstruction environment: `source $R2S2R_RECON_HOME/env.sh` puts `recon-python` (SAM 3, HaWoR with its hand detector, MANO, MuJoCo, PyTorch, trimesh, python-fcl), `aux-python` (SAM 2.1, MoGe, pytorch3d), Blender 4.2 LTS (`blender`, headless `bpy`), `uv` and `micromamba` on `PATH` and sets the model paths (`MANO_DIR`, `SAM3_CHECKPOINT`, `HAWOR_CHECKPOINT`, `HAND_DETECTOR`, `SAM2_CHECKPOINT`, `MOGE_MODEL`). Versions, revisions and SHA-256 of every model and package: `$R2S2R_RECON_HOME/manifest.json`; licences: the licence file of the same directory. A GPU is needed for the segmentation and hand models. The tools never contact the target and write under directories you choose; the default sequence is `demo2sim/RECONSTRUCTION.md`. You may use any of them, all of them, or your own methods.

| Entry point | Stage | Inputs → outputs |
|---|---|---|
| `recon-python frames.py --video <demo file> --out <work>/frames` | Frames on the display-orientation grid | demonstration → `%06d.jpg`, `frames.json` |
| `recon-python sam3_seg.py --frames <work>/frames --out <work>/sam3 --prompt <name>="<text>" [--prompt hand=hand] [--box <name>=cx,cy,w,h]` | Object and hand masks on every frame (SAM 3, text prompts) | frames → `<name>/%06d.png` (+ every hand instance in `hand/%06d.npz`) |
| `aux-python sam2_video_seg.py --video <demo file> --prompts <prompts.json> --out <recon>/seg --sam2-ckpt $SAM2_CHECKPOINT` | Object and hand masks propagated from point prompts (SAM 2.1; `--sam2-ckpt` defaults to `$SAM2_CHECKPOINT`; you write `prompts.json` yourself, format in the script's docstring) | demonstration → `seg/` |
| `aux-python moge_intrinsics.py --frames <frame> ... --model $MOGE_MODEL --out <work>/moge` | Focal length and metric pointmaps from single frames (MoGe; `--model` defaults to `$MOGE_MODEL`): a learned prior only, not a calibration (on a flat-shaded synthetic render with a true focal of 600 px it returns 970–1102 px) | frames → `intrinsics.json` |
| `recon-python camera_calib.py pnp --points3d p3.json --points2d p2.json --image-size W H [--profile f0:f1:step]` | Focal length and object pose from 2D–3D correspondences of known geometry; RMS error over a focal grid. Calibrate the focal this way (or against other known geometry) rather than taking a monocular prior: on the same synthetic render it recovers 599.8 px for 600 | correspondences → `calib.json` |
| `recon-python camera_calib.py rotation --frames <work>/frames --K calib.json --exclude <mask dir> ...` | Camera rotation per frame from background flow | frames → `rotations.npz` |
| `recon-python camera_calib.py world --K calib.json --gravity-cam0 gx gy gz --frames-count T [--rotations rotations.npz] --out <recon>/transforms` | The world frame `W`, camera poses and time base | → `transforms/` |
| `recon-python pose_track.py --mesh <mesh.obj> --masks <mask dir> --transforms <recon>/transforms --init init.json --out track.npz [--dontcare <hand mask dir>]` | 6D tracking of a rigid object of known geometry from its masks | masks → per-frame `T_cam_obj`, `T_world_obj`, agreement |
| `aux-python objpose_track.py --task <task> --object <object> --root <dir> --mesh <mesh.obj>` | Render-and-compare 6D tracking with symmetry handling and re-initialisation (`objpose_validate.py`: its checks) | SAM 2.1 masks, intrinsics → `objects/<object>/` (camera-frame track `T_cam_obj`; with `transforms/` it gives `T_world_obj`) |
| `recon-python hawor_cam.py --frames <work>/frames --intrinsics <recon>/transforms/camera_intrinsics.json --out <work>/hawor_cam [--sides left,right]` | Hand detection and HaWoR hand initialisation in your camera frame, with your focal length | frames → `detections.npz`, `hawor_cam.npz` |
| `recon-python handfit_inputs.py --frames ... --transforms <recon>/transforms --hawor <work>/hawor_cam --hand-masks <work>/sam3/hand --scene <recon>/scene --contacts <recon>/interaction/contacts.json --out <work>/handfit/inputs [--occluders <dir> ...] [--assign detector\|image_side]` | The input folder of the MANO fit (cameras, hand masks with left/right assignment, HaWoR in `W`, your scene posed per frame, contact events) | → `mano_fit` inputs |
| `recon-python mano_fit/handlib/fit.py --inputs <work>/handfit/inputs --out <work>/handfit/fit [--config cfg.json] [--init <dir>]`, then `handlib/score.py --inputs ... --result ... --out .../score.json` | The MANO hand fit against your object scene (package `README.md`: method, configuration, inputs, outputs) | → `hands.npz`, `fit_log.json`, `score.json` |
| `recon-python handfit_export.py --result <work>/handfit/fit --inputs <work>/handfit/inputs --recon <recon> --demo-hands <left,right>` | Validity rule and the hand part of the contract | → `hand/` |
| `recon-python export_reference.py --src <per-task dir> --out <recon> --task <task> --task-dir . --video <demo file> --fps-real 30 --demo-hands <...> --labels labels.json [--no-hands]` | Converts the per-task file layout of the default workflow (`camera.npz`, `objects/`, `tracking/`, `hands.npz`, `hand_object.json`, `analysis.json`) into the contract; `labels_template.json` lists the labels it needs | → `<recon>` |
| `recon-python render_compare.py --recon <recon> --frames <work>/frames` | The comparison video | → `compare/compare.mp4`, `compare.json` |
| `recon-python validate_reconstruction.py --recon <recon> [--masks <mask dir>] [--flight <object>=a:b] [--rest <object>=a:b]` | The validation of `demo2sim/REFERENCE.md` section 4 (`--focal-prior PX` or `transforms/moge/intrinsics.json`: flags a focal that disagrees with the monocular prior by more than 1.25×) | → `validation/report.json` |
| `recon-python check_reference.py <recon> --task-dir . --video <demo file>` | The format check of `demo2sim/REFERENCE.md` section 2 (0 errors required) | → findings, exit code |
| `recon-python build_viewer.py --recon <recon> --frames <work>/frames --out <work>/viewer` | A local 3D viewer of hands, objects and fingertip distances; serve the directory (`python3 -m http.server`) and open it in a browser | → static web page |
| `blender -b --factory-startup --python <script.py> -- <args>` | Object models in Blender (`demo2sim/RECONSTRUCTION.md` section 2); EEVEE renders from your cameras | → meshes, renders |

`recon-python fixture/run_e2e.py --work <empty dir> --gpu-models` runs the whole chain on a synthetic demonstration (a MANO hand lifting a sphere) and scores it against that scene's ground truth: a quick check that your environment works.
