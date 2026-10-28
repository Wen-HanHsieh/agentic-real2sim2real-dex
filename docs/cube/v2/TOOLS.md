# Research Tools

These tools run on your machine and never compute or change official results. `r2s2r-harness` is the client of the standard research workflow (`README.md`, `REMOTE_API.md` section 5). `r2s2r-calib` serves the sim-to-target calibration required after each target evaluation (section 2); `r2s2r-hwcheck` and your own diagnostics are optional. `r2s2r-preflight` checks a package before you send it. Only `r2s2r-harness` contacts the target environment, and only through the commands of `REMOTE_API.md`.

| Tool | Category | Purpose | Reference |
|---|---|---|---|
| `r2s2r-harness` | Standard research workflow | Research records (intent, reflection), history, comparisons, best evaluated policy, local archives | Section 1 |
| `r2s2r-hwcheck` | Optional analysis | Check local trajectories against the hardware rules | `HARDWARE_CHECK.md` |
| `r2s2r-calib` | Sim-to-target calibration (required after each target evaluation) | Compare your simulation with a target rollout: extract, replay, align, discrepancies, plots, side-by-side video, experiment records | Section 2 |
| `r2s2r-preflight` | Package check | Check a policy package before `validate` / `submit` | `PACKAGE.md` |

Implementations: `tools/harness/`, `tools/hwcheck/`, `tools/calib/`.

## 1. Research Harness (Standard Research Workflow)

`r2s2r-harness` keeps the standard research records and policy artifacts using the API commands `intent`, `submit`, `history`, `note`, `fetch`, and `package`; its `video` command uses `training-video`.

```bash
export R2S2R_API=r2s2r-cube        # or pass --api r2s2r-cube

r2s2r-harness submit my_policy/ --hypothesis ... --change ... [--rationale ...] [--parent sMM] \
    [--kind improvement|diagnostic|experimental] [--repo .] [--local result.json] [--sim-config cfg.json] \
    [--checkpoint REF] [--records DIR] [--dry-run]
r2s2r-harness reflect sNN --diagnosis ... --evidence ... --keep keep|reject|undecided [--worked ...] \
    [--failed ...] [--decision ...] [--next ...] [--limitation ...] [--analysis ...]
r2s2r-harness summary
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
- **`summary`:** every submission with role, keep, official status, score and bounds, hardware, gate, comparison with the previous comparable submission, intent and reflection status, and the incomplete records.
- **`record`:** appends a plain note (original schema); `--repo` adds the source revision and the latest commit's diff stat.
- **`gate`:** the official regression gate and the comparisons (`vs_previous`, `vs_best_before`) of a submission.
- **`best`:** the best evaluated policy; `--download` retrieves its exact package on demand after verifying the hash.
- **`archive` / `verify`:** a write-once local copy of history, feedback bundles, and packages with a manifest, and its integrity check.
- **`video`** (standard research artifact, for every submission): links a video of your own training-simulation rollout of the policy submitted as `sNN` (MP4 or WebM, ≤ 64 MB). `--package` is the directory or archive you submitted; the harness packs it the same way as `submit`, refuses it unless its SHA-256 equals the submission's `archive_sha256`, uploads with `training-video`, and checks the stored video's SHA-256. Then state the rollout (full or partial) with a `training_video` record. Never evaluated or charged (`REMOTE_API.md` section 5).

The best policy, the gate, and the comparisons are computed by the target environment from official results; the harness only records and displays them, and never restores or deploys a policy unless you ask (`best --download`). **You decide which experiments to run, which policies to keep, and how to improve them.**

## 2. Sim-to-Target Calibration (required after each target evaluation)

After each target evaluation, and before your next submission, calibrate your simulator against that rollout; no calibration is required before your first target rollout. `r2s2r-calib` works on the feedback you fetched (joint log, action sequence, timestamps, sensor-estimated object tracks, videos). Local only; it never contacts the target and never changes official results.

1. **Extract, replay, compare:** `extract` the target trajectory, `replay` its action sequence in your own simulator, and `compare` the observable behavior (joints, object quantities, side-by-side `video`).
2. **Diagnose:** turn the discrepancies into testable failure hypotheses.
3. **Update:** change your simulator accordingly, or state why a discrepancy cannot be modeled.
4. **Screen:** test candidate repairs in simulation before the next target submission.
5. **Record:** the calibration evidence, modifications, and results (`record` below; summarize them in your reflection and next intent, `REMOTE_API.md` section 5).

If replay is genuinely infeasible, record the reason and validate the next candidate in another documented way. The simulator, physics parameters, calibration algorithm, policy, controller, and learning method are your choice.

```bash
r2s2r-calib extract <bundle.tgz> -o <target.npz>                         # fetched feedback -> trajectory file
r2s2r-calib replay <target.npz> --driver <driver.py> -o <sim.npz>        # same action sequence in your simulator
r2s2r-calib compare <target.npz> <sim.npz> -o <dir> [--by step|time] [--lag N] [--threshold RAD]
r2s2r-calib video <target.mp4> <sim.mp4> -o <out.mp4> [--sim-offset S]   # side-by-side video (needs ffmpeg)
r2s2r-calib record <dir> --hypothesis TEXT [--notes TEXT] [--config <cfg.json>] [--files ...]
```

| Command | What it does |
|---|---|
| `extract` | Writes a trajectory file: `step`, `t` (s), `joint_names`, measured `q` and `qd`, the commands `q_target` and `qd_target` (the action sequence), and `track_<name>` object quantities at video-frame times `track_t` (NaN = not observed) |
| `replay` | Feeds the target's action sequence, step by step, to your simulator through a driver module you write: `make(meta, joint_names)` returns `reset_fn()` and `step_fn(q_target, qd_target, step)`, which applies one 2 ms command and returns `{"q": (20,), "qd": ..., "<name>": value}`; extra keys become `track_<name>` |
| `compare` | Aligns by control step (default) or by time; per-joint RMSE, maximum and mean error, first step over the threshold, best time shift within ± N steps; object quantities present in both files (same names as the target tracks) at the target's observation times; writes the metrics (JSON) and plain-SVG plots (joints, error norm, objects) into `<dir>` |
| `video` | Scales both videos to the same height and plays them side by side, start-aligned (`--sim-offset` shifts yours) |
| `record` | Saves a calibration experiment: hypothesis, notes, your configuration, copies and hashes of the given files, a summary; appends one line to `<dir>/index.jsonl` |

The tool needs NumPy only (plots are written as SVG without a plotting library); `video` needs `ffmpeg`. Your simulator's trajectory file uses the same keys as the target's, so `compare` works on any simulator that can record joint positions per step. `frames` (`REMOTE_API.md` section 6) gives RGB and depth frames of the target rollout at any instant for visual comparison.
