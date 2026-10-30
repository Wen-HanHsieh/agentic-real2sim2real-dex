# Research Tools

These tools run on your machine and never compute or change official results. `r2s2r-harness` is the client of the standard research workflow (`README.md`, `REMOTE_API.md` section 5). `r2s2r-calib` serves the sim-to-target calibration required after each target evaluation (section 2); `r2s2r-hwcheck` and your own diagnostics are optional. `r2s2r-preflight` checks a package before you send it. Only `r2s2r-harness` contacts the target environment, and only through the commands of `REMOTE_API.md`.

| Tool | Category | Purpose | Reference |
|---|---|---|---|
| `r2s2r-harness` | Standard research workflow | Research records (intent, reflection), history, comparisons, best evaluated policy, local archives | Section 1 |
| `r2s2r-hwcheck` | Optional analysis | Check local finger trajectories against the hardware rules | `HARDWARE_CHECK.md` |
| `r2s2r-calib` | Sim-to-target calibration (required after each target evaluation) | Compare your simulation with a target rollout: extract, replay through your simulator adapter, compare wrist, objects, parts and joints step by step, diagnose by contact phase, plots, side-by-side video, experiment records | Section 2 |
| `r2s2r-preflight` | Package check | Check a policy package (contract `v2`) before `validate` / `submit` | `PACKAGE.md` |
| Reconstruction tools | Demo-to-Sim | Segment the demonstration video, track the hand, reconstruct the object and its motion (`REFERENCE.md`) | Section 3 |

Implementations: `tools/harness/`, `tools/hwcheck/`, `tools/calib/`, `tools/preflight/`, `tools/recon/`.

## 1. Research Harness (Standard Research Workflow)

`r2s2r-harness` keeps the standard research records and policy artifacts using the API commands `intent`, `submit`, `history`, `note`, `fetch`, and `package`; its `video` command uses `training-video`.

```bash
export R2S2R_API=r2s2r-plug        # or pass --api r2s2r-plug

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
- **`reflect`:** after the result, appends your reflection (`REMOTE_API.md` section 5); refused while the evaluation is still running.
- **`summary`:** every submission with role, keep, state, official status, verifier status, progress, criteria status, hardware, gate, comparison with the previous comparable submission, intent and reflection status, and the incomplete records. While the task's criteria are undefined it shows `criteria not defined` instead of a score.
- **`result`:** the official result of one submission as recorded in `history`: status, criteria id and status, success and progress (or `criteria not defined`), stage scores, milestones reached, hardware and runtime validity, versions.
- **`record`:** appends a plain note (original schema); `--repo` adds the source revision and the latest commit's diff stat.
- **`gate`:** the official regression gate and the comparisons (`vs_previous`, `vs_best_before`) of a submission.
- **`best`:** the best evaluated policy and the ranking rule; `--download` retrieves its exact package on demand after verifying the hash.
- **`archive` / `verify`:** a write-once local copy of history, feedback bundles, and packages with a manifest, and its integrity check.
- **`video`** (standard research artifact, for every submission): links a video of your own training-simulation rollout of the policy submitted as `sNN` (MP4 or WebM, ≤ 64 MB). `--package` is the directory or archive you submitted; the harness packs it the same way as `submit`, refuses it unless its SHA-256 equals the submission's `archive_sha256`, uploads with `training-video`, and checks the stored video's SHA-256. Then state the rollout (full or partial) with a `training_video` record. Never evaluated or charged (`REMOTE_API.md` section 5).

The best policy, the gate, and the comparisons are computed by the target environment from official results; the harness only records and displays them, and never restores or deploys a policy unless you ask (`best --download`). **You decide which experiments to run, which policies to keep, and how to improve them.**

## 2. Sim-to-Target Calibration (required after each target evaluation)

After each target evaluation, and before your next submission, calibrate your simulator against that rollout; no calibration is required before your first target rollout. `r2s2r-calib` works on the feedback you fetched (the ground-truth state record, the rollout log with the commanded and executed finger and wrist targets, timestamps, videos). The target's state record is exact, so every discrepancy between it and your replay is a property of your simulator, your controller model, or your contact model, not of a measurement. Local only; it never contacts the target and never changes official results. The simulator, physics parameters, calibration algorithm, policy, controller, and learning method are your choice; the tool aligns, compares and attributes.

1. **Extract, replay, compare:** `extract` the target trajectory, `replay` its action sequence in your own simulator through an adapter you write, and `compare` the wrist, object, part and joint trajectories step by step (plus a side-by-side `video`).
2. **Diagnose:** `diagnose` segments the episode by the target's contact phases and charges the error growth to your wrist controller model, finger actuator model, free object motion or contact model where the evidence supports it, and says "cannot determine" otherwise. Turn the discrepancies into testable failure hypotheses.
3. **Update:** change your simulator accordingly, or state why a discrepancy cannot be modeled.
4. **Screen:** test candidate repairs in simulation before the next target submission.
5. **Record:** the calibration evidence, modifications, and results (`record` below; summarize them in your reflection and next intent, `REMOTE_API.md` section 5).

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
| `extract` | Writes a trajectory file (`r2s2r-traj/3`, NumPy `.npz`): the rollout log (`step`, `t`, `joint_names`, measured `q` and `qd`, the finger commands `q_target` and `qd_target`, the wrist commands `wrist_*_command`, the executed wrist targets `wrist_*_target`, `wrist_command_limited`) and the state record (`state_step`, `state_t`, `wrist_position` … `object_angular_velocity`, `part_*`, `cube_relative_orientation`, `cube_configuration` and the contact flags where the task has them, `object_names`, `part_names`), with `meta` (task, submission, versions, rates, the target's own wrist and finger tracking). Frames and quaternion conventions are those of `FEEDBACK.md`. A bundle of another feedback protocol, a missing file or a misaligned record is refused with the reason |
| `replay` | Drives your simulator with the target's action sequence through an adapter (`tools/calib/calib_adapter.py`): a Python class `reset(initial_state)`, `apply(action)`, `read_state()`, optional `set_state(state)`, created by `make(meta)` in the `--driver` module, or any program speaking the JSON-lines protocol (`hello`, `reset`, `set_state`, `apply`, `read_state`, `close`) given as `--adapter-cmd`. `--mode action`: reset to the target's step-0 state, then apply every action open loop (the standard replay). `--mode state-step`: before each action, teleport to the target's recorded state of that step, so every row is a one-step prediction error (no accumulation). `--mode state-segment`: teleport only at the start of each contact phase of the target. `--targets executed` (default) feeds the wrist targets the target actually tracked; `--targets commanded` feeds the policy's commands, so your adapter must apply the command limits itself (`tools/preflight/preflight.py` `CommandLimiter`). Your adapter's states use the keys and conventions of the state record; optional blocks (parts, contacts) are compared when present |
| `compare` | Aligns by control step (state row `k` versus your row `k`; a simulated file at a higher rate is resampled onto the target's rows, a slower one is refused): per-joint RMSE, maximum and mean error, first step over the threshold, best time shift when one reduces the RMSE; wrist position error, geodesic orientation error, linear and angular velocity error per step; per object position, geodesic orientation, linear and angular velocity errors per step with maxima and the first step over 1 cm / 10°; per part (cube) the same plus the configuration agreement; contact-flag agreement where your adapter provides contacts; writes `metrics.json` and plain-SVG plots (joints, wrist, objects) into `<dir>` |
| `diagnose` | `compare` plus: segments from the target's contact flags (free / hand / environment / both, per object), per segment the error at its start and end, its growth and maxima for the wrist, the fingers and every object, the tracking of the same executed targets on both sides, and an attribution per segment and object: `free-body dynamics`, `inherited velocity error`, `contact model`, `none (reproduced)`, or `cannot determine` (the hand itself moved differently), plus the wrist controller / finger actuator attribution over the whole rollout; `report.md` with the thresholds used and, with matplotlib installed, PNG plots (`errors.png`, `positions.png`, `fingers.png`) |
| `video` | Scales both videos to the same height and plays them side by side, start-aligned (`--sim-offset` shifts yours) |
| `record` | Saves a calibration experiment: hypothesis, notes, your configuration, copies and hashes of the given files, a summary; appends one line to `<dir>/index.jsonl` |

**Adapters shipped with the tool** (`tools/calib/`): `calib_kinematic_adapter.py`, a NumPy-only reference without physics (the hand follows its targets ideally, objects stay frozen) for testing the pipeline and as a template; `calib_mujoco_adapter.py`, a working example on MuJoCo (`pip install mujoco`) that builds a scene from public information only: the vendor URDF with `r_mount` as a free body, the finger PD controller and the wrist impedance controller of `hardware/SPECS.md`, and rigid objects with the dimensions and masses of `object/SPECS.md` (the cube as one rigid block without its turning mechanism). Its contact properties are MuJoCo defaults: calibrating them against the target record is exactly the work this section asks for. Run it with `--selftest` first; `--scene scene.json` overrides the objects, their contact properties, the table and the floor. Both adapters run in process (`--driver`) or as a subprocess (`--adapter-cmd "python tools/calib/calib_mujoco_adapter.py --urdf hardware/wuji_hand2_right/urdf/right.urdf"`), so your simulator may live in its own interpreter.

The tool needs NumPy only (plots are written as SVG without a plotting library; `diagnose` adds PNG plots when matplotlib is available); `video` needs `ffmpeg`. `frames` (`REMOTE_API.md` section 6) gives RGB and depth frames of the target rollout at any instant for visual comparison.

## 3. Reconstruction Tools (Demo-to-Sim)

The reconstruction tools of `REFERENCE.md` section 3 are scripts under `tools/recon/`, each run in its own Python environment (they depend on different deep-learning stacks). They run on your machine (a GPU is needed for the segmentation and hand models), never contact the target, and write the artifact layout of `REFERENCE.md` section 2 under a directory you choose; every stage writes a `provenance.json` with its `method`. You may use any of them, all of them, or your own methods. The object geometry comes from `object/SPECS.md` (the tracking tool uses a mesh of it in the state frame of `object/SPECS.md`); no shape-reconstruction model is provided.

| Entry point | Stage | Status |
|---|---|---|
| `sam2_video_seg.py --video <video> --prompts <prompts.json> --out <dir>/seg` | Video segmentation: object and hand masks on every frame from a few point prompts (SAM 2.1); writes frames, masks, `objects.json`, `stats.json`, `overlay.mp4` | implemented, verified |
| `moge_intrinsics.py --frames <frames...> --out <dir>/transforms/moge` | Camera intrinsics and metric pointmaps from single frames (MoGe) | implemented, verified |
| `hawor_stages.py --video_path <video> --work <dir>/hand --stages detect,masks,slam,hawor,infill [--masks-from-sam2 <dir>/seg]` | Hand detection and tracking, hand masks, masked camera trajectory with metric scale, per-frame hand fits, world-frame hand motion (HaWoR) | installed and running; `detect`/`hawor` verified on all four demonstrations, `slam`/`infill` verified on one |
| `hawor_render.py --seq <dir>/hand/<video>` | Hand overlay video and `hand_world.npz` | implemented, not yet run |
| `objpose_track.py --task <task> --object <object> [--fx PX] [--frames a:b]` | Known-geometry 6D object tracking (render-and-compare v1): object pose per frame from the masks, the known geometry and the intrinsics; writes `objects/<object>/` | implemented, verified |
| `objpose_validate.py --task <task> --object <object>` | Metrics, physical checks, overlays and `REPORT.md` of a tracked object | implemented, verified |
| `objpose_moge_depth.py --frames_dir <dir> --out <dir>` | Per-frame depth maps (MoGe) used by the validation checks | implemented |
| `objpose_export.py` | Writes the `pose6d/<object>/` contract (`traj_world.npz`, `method.json`) from `objects/<object>/` | implemented |
| `objpose_run_all.sh`, `objpose_validate_all.sh` | Tracking and validation of every object of the four demonstrations | implemented |
| `compare_video.py` | Three-panel comparison video (input, hand overlay, 3D view) | implemented, not yet run |

Whether the tools are shipped in the bundle with their environments or only their outputs is the open decision of `REFERENCE.md` section 3; until then, treat this table as the intended interface.
