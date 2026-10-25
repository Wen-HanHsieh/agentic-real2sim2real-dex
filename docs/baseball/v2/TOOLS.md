# Research Tools

These tools run on your machine and never compute or change official results. The research record is standard (`README.md`); `r2s2r-harness` is the simplest way to keep it, the other tools are optional. Only `r2s2r-harness` contacts the target environment, and only through the commands of `REMOTE_API.md`.

| Tool | Purpose | Reference |
|---|---|---|
| `r2s2r-preflight` | Check a policy package before `validate` / `submit` | `PACKAGE.md` |
| `r2s2r-hwcheck` | Check local trajectories against the hardware rules | `HARDWARE_CHECK.md` |
| `r2s2r-maskiou` | Compare target segmentation masks with masks from your simulation | Section 1 |
| `r2s2r-harness` | Research records (intent, reflection), archives, comparisons, best evaluated policy | Section 2 |

Implementations: `tools/hwcheck/`, `tools/maskiou/`, `tools/harness/`.

## 1. Sim-to-Target Mask IoU

`r2s2r-maskiou` compares the masks of a fetched feedback bundle (`masks/`) with masks rendered by your simulation, per frame and view. It is a diagnostic, not an official reward or success criterion.

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

## 2. Research Harness

`r2s2r-harness` keeps research records and policy artifacts using the API commands `intent`, `submit`, `history`, `note`, `fetch`, and `package`.

```bash
export R2S2R_API=r2s2r-baseball        # or pass --api r2s2r-baseball

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
```

- **`submit`:** packs the directory deterministically (or uses an existing `.tar` / `.tar.gz`), captures the git revision, uncommitted changes, and the diff against the parent submission's revision (else the previous commit) from `--repo` (default: the current directory), records the intent, then submits the same archive. It keeps a write-once local copy (intent, receipt, full diff, package) under `--records` (default `~/r2s2r_records`). Missing fields are reported; a failed intent does not stop the submission. `--dry-run` prints the intent without contacting the target.
- **`reflect`:** after the result, appends your reflection (`REMOTE_API.md` section 6); refused while the evaluation is still running.
- **`summary`:** every submission with role, keep, official status, score and bounds, hardware, gate, comparison with the previous comparable submission, intent and reflection status, and the incomplete records.
- **`record`:** appends a plain note (original schema); `--repo` adds the source revision and the latest commit's diff stat.
- **`gate`:** the official regression gate and the comparisons (`vs_previous`, `vs_best_before`) of a submission.
- **`best`:** the best evaluated policy; `--download` saves its exact package after verifying the hash.
- **`archive` / `verify`:** a write-once local copy of history, feedback bundles, and packages with a manifest, and its integrity check.

The best policy, the gate, and the comparisons are computed by the target environment from official results; the harness only records and displays them, and never restores or deploys a policy unless you ask (`best --download`). **You decide which experiments to run, which policies to keep, and how to improve them.**
