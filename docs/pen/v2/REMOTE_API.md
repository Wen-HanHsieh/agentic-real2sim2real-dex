# Remote Evaluation API (feedback protocol v2)

SuperDex executes submitted policies on the target cell and returns what its sensors observed: three calibrated camera
views, your robot's own logs, and a sensor-based assessment of the trial against `SUCCESS.md`. Protocol identifier:
`r2s2r-feedback/2` (see `FEEDBACK.md`).

## 1. Commands

```bash
r2s2r-pen budget
r2s2r-preflight my_policy/
tar -C my_policy -czf - . | r2s2r-pen validate
tar -C my_policy -czf - . | r2s2r-pen submit
r2s2r-pen status
r2s2r-pen fetch sNN > sNN.tgz
r2s2r-pen frames sNN <top|left|right|all> <t1,t2,...> [depth] > frames.tgz
r2s2r-pen masks sNN <top|left|right|all> <i0:i1[:step] | i,j,...> > masks.tgz
r2s2r-pen history
r2s2r-pen note sNN < note.json
r2s2r-pen package sNN > sNN.tar
```

Local tools on AWS (optional, nothing is sent anywhere; `TOOLS.md`): `r2s2r-preflight`, `r2s2r-hwcheck`,
`r2s2r-maskiou`, `r2s2r-harness`.

Responses are JSON (`fetch` and `frames` return a .tar.gz); errors return `{"error": "..."}` with a non-zero exit code.

`validate` checks the package without executing a full trial or consuming submission budget. `r2s2r-preflight` is a local
compatibility check; remote `validate` is authoritative.

## 2. Submission

- **Package:** `.tar` or `.tar.gz`, ≤ 500 MB, ≤ 2000 files; `policy.py` at the archive root or inside one top-level directory (`PACKAGE.md`).
- No links, absolute paths, or `..` paths.
- One evaluation at a time; every accepted submission consumes one budget slot.
- **Budget:** 100 submissions.

## 3. Evaluation

Each submission executes **1 trial**, lasting **12 s (6000 steps at 500 Hz)**, with fixed initial conditions. The policy interface is
unchanged (`CONTRACT.md`): the policy itself never receives camera images.

States: `queued` → `running` → `done`, or `timeout` / `error`.

## 4. Feedback (`fetch`)

```text
<experiment>_<id>/
├── feedback.json            protocol, file list with SHA-256
├── calibration.json         camera intrinsics, extrinsics, conventions, depth model
├── logs/trial_0.npz         joint_names, q, qd, q_target, qd_target (6000 steps)
├── masks/
│   ├── top.npz  left.npz  right.npz   object segmentation masks from the cameras, one per frame and view
│   └── masks.json           encoding and fields
├── video/
│   ├── top.mp4  left.mp4  right.mp4   three synchronized views, real time, 100 fps
│   ├── frames.json          frame_t and control_step of every frame (identical for every view)
│   └── video.json
└── sensor/
    ├── sensor_report.json   sensor-based verifier: status, score with uncertainty, stages, events, measurements
    └── sensor_tracks.npz    the perceived tracks behind the report
```

The sensor report is computed only from the cameras, your robot log and public documents. It reports what was observed,
never why. See `FEEDBACK.md` for every field, its accuracy, and what cannot be observed.

## 5. Frame queries (`frames`)

Re-renders exact instants of a finished trial in any view, after the rollout (the trial itself is never paused):
up to 8 times per call (seconds since control step 0, up to 3 decimals; the nearest 1 ms instant is returned), optional
16-bit depth (0.1 mm units). Up to 240 frames (times × views) per submission; not charged to the budget.

## 6. Masks (`masks`)

Selected segmentation masks as PNG (0 = background, 255 = object) with `masks/masks.json` (frame index, time, control
step, validity, visibility, colour agreement), read from the immutable record: a range `i0:i1[:step]` or a list of frame
indices of `video/frames.json`, one view or `all`, up to 60 masks per call. The complete masks are also in the `fetch`
bundle (`masks/`). See `FEEDBACK.md` section 4.

## 7. Experiment records (`history`, `note`, `package`)

`history` lists every submission: package, archive and feedback SHA-256, state, the **official** sensor results with
their versions, your notes, the submission's role (from your latest note), and a regression `gate` against the best
comparable earlier submission (`improved`, `equal`, `regressed`, `not_comparable` when the verifier, rubric, rig or
hardware-spec version differs). It names `best_evaluated` (official results only: runtime valid, then no hardware
violation, then task success, then score, then its lower bound; ties: earlier) and `latest_candidate` (latest submission
not marked diagnostic or experimental). Official results cannot be set or changed by notes.

`note sNN` appends one record (append-only, hash-chained; corrections are new notes):

```json
{"kind": "improvement | diagnostic | experimental", "hypothesis": "...", "change": "...", "evidence": "...",
 "decision": "...", "keep": "keep | reject | undecided", "source_revision": "git commit (optional)",
 "code_change": "summary or diff stat (optional)", "sim_config": {"...": "your local simulation configuration (optional, ≤ 8 KB)"},
 "checkpoint": "your checkpoint reference (optional)", "analysis": "... (optional)",
 "local": {"...": "your own local-simulation result (optional, ≤ 4 KB)"}, "parent": "sNN (optional)"}
```

`package sNN` returns the exact package archive of a submission (its SHA-256 equals `archive_sha256`), so the best
evaluated policy is never lost. `r2s2r-harness` (`TOOLS.md`) wraps these commands. Records never affect evaluation.

## 8. Limits

- **Timeout:** 45 minutes per evaluation.
- Completed or timed-out submissions consume budget; operator-side errors do not.
- Identical resubmissions consume budget.
