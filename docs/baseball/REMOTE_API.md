# Remote Evaluation API

SuperDex executes submitted policies and returns videos and robot logs for autonomous evaluation and improvement.

## 1. Commands

```bash
r2s2r-baseball budget
r2s2r-preflight my_policy/
tar -C my_policy -czf - . | r2s2r-baseball validate
tar -C my_policy -czf - . | r2s2r-baseball submit
r2s2r-baseball status
r2s2r-baseball fetch sNN > sNN.tgz
```

Responses are JSON; errors return `{"error": "..."}` with a non-zero exit code.

`validate` checks the package without executing a full trial or consuming submission budget. `r2s2r-preflight` is a local compatibility check; remote `validate` is authoritative.

## 2. Submission

- **Package:** `.tar` or `.tar.gz`, ≤ 500 MB, ≤ 2000 files; `policy.py` at the archive root or inside one top-level directory.
- No links, absolute paths, or `..` paths.
- One evaluation at a time; every accepted submission consumes one budget slot.
- **Budget:** 100 submissions.

## 3. Evaluation

Each submission executes **1 trial**, lasting **10 s (5000 steps at 500 Hz)**, with fixed initial conditions.

States: `queued` → `running` → `done`, or `timeout` / `error`.

## 4. Feedback

After execution, `fetch` returns:

```text
<experiment>_<id>/
├── logs/
│   └── trial_0.npz
└── video/
    ├── trial_0.mp4
    └── video.json
```

- **Video:** Two fixed camera views covering the full trial.
- **Robot logs:** `joint_names`, `q`, `qd`, `q_target`, `qd_target` (5000 steps).

SuperDex does not provide task success/failure labels, progress scores, object state, privileged physics metrics, or failure diagnoses.

The agent independently evaluates task progress and success using the video, robot logs, and `SUCCESS.md`.

## 5. Limits

- **Timeout:** 45 minutes per evaluation.
- Completed or timed-out submissions consume budget; operator-side errors do not.
- Identical resubmissions consume budget.
- Use `budget` to check remaining submissions.
