# Tools

All tools run locally on your machine, are optional, and send nothing anywhere unless they call the SuperDex API on
your behalf (`r2s2r-baseball`). None of them computes or changes official results.

| Tool | Use it to | Documentation |
|---|---|---|
| `r2s2r-preflight my_policy/` | check a package before `validate` / `submit` | `PACKAGE.md` |
| `r2s2r-hwcheck traj.npz` | check your own trajectories against the hardware rules | `HARDWARE_CHECK.md` |
| `r2s2r-maskiou BUNDLE sim.npz` | compare SuperDex masks with masks from your simulation | below |
| `r2s2r-harness --api r2s2r-baseball ...` | keep experiment records, archive results, retrieve your best policy | below |

## Sim-to-Real mask IoU (`r2s2r-maskiou`)

Compares the camera-derived masks of a fetched submission (`masks/`) with masks rendered by your simulation, per frame
and view. It is a diagnostic: it is not a SuperDex reward, score or success criterion, and it is never required.

```bash
r2s2r-maskiou sNN_bundle/ my_sim_masks.npz --json iou.json --vis overlays/
```

`my_sim_masks.npz`: `top` / `left` / `right` as (n, H, W) masks (any subset), `t` (s since control step 0) or
`control_step` (n,), and the camera you rendered with: `calibration_sha256` of the bundle's `calibration.json`, or
`K_<view>` and `T_world_cam_<view>`. Rules: frames are matched to the SuperDex frame at the same control step (within
1 ms; `--max-time-error` to change), never interpolated or warped; `--time-offset` shifts your clock by a constant you
choose and is reported. A view whose camera or image size does not match is refused (or, with
`--allow-calibration-mismatch`, marked unreliable). Both masks empty gives an undefined IoU, not 1. Frames where the
SuperDex mask is invalid, occluded (`visible_fraction` < 0.5; render your hand as an occluder too) or has low colour
agreement are reported. Output: per-frame IoU, per-view mean / median / min, multi-view mean, overlays (green SuperDex
only, magenta yours only, white both).

## Research harness (`r2s2r-harness`)

```bash
export R2S2R_API=r2s2r-baseball
r2s2r-harness summary                       # every submission: role, keep, official status / score / bounds, hardware, gate
r2s2r-harness record sNN --kind improvement --hypothesis ... --change ... --evidence ... --decision ... \
    [--keep keep|reject|undecided] [--repo .] [--sim-config cfg.json] [--checkpoint REF] [--analysis TEXT] [--local res.json]
r2s2r-harness gate sNN                      # official regression gate of sNN against the best comparable earlier submission
r2s2r-harness best --download best/         # the best evaluated policy and its exact package (hash verified)
r2s2r-harness archive ~/records             # write-once local copy of history, feedback bundles and packages, with a manifest
r2s2r-harness verify ~/records              # detect modified or missing archive files
```

`record` fills `source_revision` and the latest commit's diff stat from `--repo`. The best policy and the regression
gate are computed by SuperDex from official results under comparable versions (`REMOTE_API.md` section 7); the harness
only displays them. Which candidate to investigate next is your decision.
