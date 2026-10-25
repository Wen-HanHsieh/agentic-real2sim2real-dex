# Research Tools

These tools run on your machine and never compute or change official results. `r2s2r-harness` is the client of the standard research workflow (`README.md`, `REMOTE_API.md` section 5). `r2s2r-maskiou` and `r2s2r-hwcheck` are optional analysis tools, as are your own diagnostics. `r2s2r-preflight` checks a package before you send it. Only `r2s2r-harness` contacts the target environment, and only through the commands of `REMOTE_API.md`.

| Tool | Category | Purpose | Reference |
|---|---|---|---|
| `r2s2r-harness` | Standard research workflow | Research records (intent, reflection), history, comparisons, best evaluated policy, local archives | Section 1 |
| `r2s2r-maskiou` | Optional analysis | Compare target segmentation masks with masks from your simulation | Section 2 |
| `r2s2r-hwcheck` | Optional analysis | Check local trajectories against the hardware rules | `HARDWARE_CHECK.md` |
| `r2s2r-preflight` | Package check | Check a policy package before `validate` / `submit` | `PACKAGE.md` |

Implementations: `tools/harness/`, `tools/maskiou/`, `tools/hwcheck/`.

## 1. Research Harness (Standard Research Workflow)

`r2s2r-harness` keeps the standard research records and policy artifacts using the API commands `intent`, `submit`, `history`, `note`, `fetch`, and `package`; its optional `video` command uses `training-video`.

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
- **`video`** (optional, display only): links a video of your own training-simulation rollout of the policy submitted as `sNN` (MP4 or WebM, ≤ 64 MB). `--package` is the directory or archive you submitted; the harness packs it the same way as `submit`, refuses it unless its SHA-256 equals the submission's `archive_sha256`, uploads with `training-video`, and checks the stored video's SHA-256. Never evaluated or charged (`REMOTE_API.md` section 6).

The best policy, the gate, and the comparisons are computed by the target environment from official results; the harness only records and displays them, and never restores or deploys a policy unless you ask (`best --download`). **You decide which experiments to run, which policies to keep, and how to improve them.**

## 2. Sim-to-Target Mask IoU (Optional Analysis)

`r2s2r-maskiou` compares the masks of a fetched feedback bundle (`masks/`) with masks rendered by your simulation, per frame and view. It is an optional diagnostic, not an official reward or success criterion.

```bash
r2s2r-maskiou sNN_bundle/ my_sim_masks.npz --json iou.json --vis overlays/
```

**Simulation input (`.npz`):**

- `top`, `left`, `right`: `(n, H, W)` binary masks (any subset of views).
- `t` (seconds since control step 0) or `control_step`: `(n,)`.
- The camera you rendered with: `calibration_sha256` of the bundle's `calibration.json`, or `K_<view>` and `T_world_cam_<view>`.

**Rules:**

- Each frame is matched to the target frame at the same control step (within 1 ms; `--max-time-error` to change); nothing is interpolated or warped. `--time-offset` shifts your clock by a constant you choose and is reported.
- A view whose camera or image size does not match is refused (with `--allow-calibration-mismatch`: compared but marked unreliable).
- Both masks empty gives an undefined IoU, not 1. Frames where the target mask is invalid, occluded (`visible_fraction` < 0.5; render your hand as an occluder too), or has low colour agreement are reported.

**Output:** per-frame IoU, per-view mean, median and minimum, multi-view mean, warnings, and optional overlays (green: target only, magenta: yours only, white: both).
