# Remote Evaluation API (feedback protocol v2)

SuperDex executes submitted policies on the target cell and returns what its sensors observed: three calibrated camera
views, your robot's own logs, and a sensor-based assessment of the trial against `SUCCESS.md`. Protocol identifier:
`r2s2r-feedback/2` (see `FEEDBACK.md`).

## 1. Commands

```bash
r2s2r-cube budget
r2s2r-preflight my_policy/
tar -C my_policy -czf - . | r2s2r-cube validate
tar -C my_policy -czf - . | r2s2r-cube submit
r2s2r-cube status
r2s2r-cube fetch sNN > sNN.tgz
r2s2r-cube frames sNN <top|left|right|all> <t1,t2,...> [depth] > frames.tgz
r2s2r-cube history
r2s2r-cube note sNN < note.json
```

Responses are JSON (`fetch` and `frames` return a .tar.gz); errors return `{"error": "..."}` with a non-zero exit code.

`validate` checks the package without executing a full trial or consuming submission budget. `r2s2r-preflight` is a local
compatibility check; remote `validate` is authoritative.

## 2. Submission

- **Package:** `.tar` or `.tar.gz`, ≤ 500 MB, ≤ 2000 files; `policy.py` at the archive root or inside one top-level directory (`PACKAGE.md`).
- No links, absolute paths, or `..` paths.
- One evaluation at a time; every accepted submission consumes one budget slot.
- **Budget:** 100 submissions.

## 3. Evaluation

Each submission executes **1 trial**, lasting **40 s (20000 steps at 500 Hz)**, with fixed initial conditions. The policy interface is
unchanged (`CONTRACT.md`): the policy itself never receives camera images.

States: `queued` → `running` → `done`, or `timeout` / `error`.

## 4. Feedback (`fetch`)

```text
<experiment>_<id>/
├── feedback.json            protocol, file list with SHA-256
├── calibration.json         camera intrinsics, extrinsics, conventions, depth model
├── logs/trial_0.npz         joint_names, q, qd, q_target, qd_target (20000 steps)
├── video/
│   ├── top.mp4  left.mp4  right.mp4   three synchronized views, real time, 25 fps
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

## 6. Experiment records (`history`, `note`)

`history` lists every submission with its package hash, archive hash, feedback hash, state and the sensor summary, plus
your notes, and marks the best submission so far (highest sensor score; ties: hardware compliant, runtime valid, earliest).
`note sNN` appends one record to a submission (append-only; corrections are new notes):

```json
{"kind": "diagnostic | improvement", "hypothesis": "...", "change": "...", "evidence": "...", "decision": "...",
 "local": {"score": 0.4, "...": "your own local-simulation result for this package (optional, ≤ 4 KB)"}, "parent": "sNN (optional)"}
```

Records are bookkeeping only; they never affect evaluation.

## 7. Limits

- **Timeout:** 90 minutes per evaluation.
- Completed or timed-out submissions consume budget; operator-side errors do not.
- Identical resubmissions consume budget.
