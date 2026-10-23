# Research Tools

These tools run on your machine. They are optional and never compute or change official results. Only `r2s2r-harness` contacts the target environment, and only through the commands of `REMOTE_API.md`.

| Tool | Purpose | Reference |
|---|---|---|
| `r2s2r-preflight` | Check a policy package before `validate` / `submit` | `PACKAGE.md` |
| `r2s2r-hwcheck` | Check local trajectories against the hardware rules | `HARDWARE_CHECK.md` |
| `r2s2r-maskiou` | Compare target segmentation masks with masks from your simulation | Section 1 |
| `r2s2r-harness` | Experiment records, archives, regression gate, best evaluated policy | Section 2 |

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

`r2s2r-harness` keeps experiment records and policy artifacts using the API commands `history`, `note`, `fetch`, and `package`.

```bash
export R2S2R_API=r2s2r-pen        # or pass --api r2s2r-pen

r2s2r-harness summary
r2s2r-harness record sNN --kind improvement --hypothesis ... --change ... --evidence ... --decision ... \
    [--keep keep|reject|undecided] [--repo .] [--sim-config cfg.json] [--checkpoint REF] [--analysis TEXT] \
    [--local result.json] [--parent sMM]
r2s2r-harness gate sNN
r2s2r-harness best --download best/
r2s2r-harness archive ~/records
r2s2r-harness verify ~/records
```

- **`summary`:** every submission with role, keep, official status, score and bounds, hardware, and gate.
- **`record`:** appends a note (`REMOTE_API.md` section 6); `--repo` adds the source revision and the latest commit's diff stat.
- **`gate`:** the official regression gate of a submission against the best comparable earlier one.
- **`best`:** the best evaluated policy; `--download` saves its exact package after verifying the hash.
- **`archive` / `verify`:** a write-once local copy of history, feedback bundles, and packages with a manifest, and its integrity check.

The best policy and the gate are computed by the target environment from official results; the harness only records and displays them. **You decide which experiments to run, which policies to keep, and how to improve them.**
