# Remote Evaluation API

The target environment executes submitted policies and stores sensor-based feedback after each rollout. Feedback contents: `FEEDBACK.md`. Packaging: `PACKAGE.md`.

## 1. Commands

```bash
r2s2r-cube budget
r2s2r-preflight my_policy/
tar -C my_policy -czf - . | r2s2r-cube validate
tar -C my_policy -czf - . | r2s2r-cube submit
r2s2r-cube status
r2s2r-cube fetch sNN > sNN.tgz
r2s2r-cube frames sNN <top|left|right|all> <t1,t2,...> [depth] > frames.tgz
r2s2r-cube masks sNN <top|left|right|all> <i0:i1[:step] | i,j,...> > masks.tgz
r2s2r-cube history
r2s2r-cube note sNN < note.json
r2s2r-cube package sNN > sNN_package.tgz
```

Responses are JSON, except `fetch`, `frames`, and `masks` (`.tar.gz`) and `package` (the archive exactly as submitted). Errors return `{"error": "..."}` with a non-zero exit code. `r2s2r-preflight` is a local check (`PACKAGE.md`).

## 2. Submission

- **Archive:** `.tar` or `.tar.gz`, ≤ 500 MB, ≤ 2000 files; `policy.py` at the archive root or inside one top-level directory; no links, absolute paths, or `..` paths.
- **Checks:** `validate` and `submit` run the same package checks (`PACKAGE.md`). A rejected package is not recorded and not charged.
- **Receipt:** `submit` returns `submission_id`, `policy_sha256`, `state: queued`, and the check's inference timing and warnings.
- One evaluation runs at a time.

## 3. Evaluation and Budget

- **Trial:** one trial per submission, 40 s (20,000 steps at 500 Hz), from fixed initial conditions.
- **Budget:** 100 charged submissions; `budget` returns the used and total count.
- **States:** `queued` → `running` → `done`, or `error` / `timeout`. Results are not available during a rollout.

| Outcome | State | Charged | Standard feedback |
|---|---|---|---|
| Rollout completed | `done` | yes | yes |
| Policy failure: exception, invalid action, no answer within 5 s, or more than 64 MB written to `TMPDIR` | `error` | yes | yes, up to the failure |
| Evaluation exceeded 90 minutes | `timeout` | yes | no |
| Target-side infrastructure error | `error` | no | no |

`status` reports the error message and whether an `error` was charged. Identical resubmissions are charged.

## 4. Standard Feedback (`fetch`)

`fetch sNN` returns the stored feedback of a finished rollout:

```text
<experiment>_sNN/
├── feedback.json
├── calibration.json
├── logs/trial_0.npz
├── video/   top.mp4  left.mp4  right.mp4  frames.json  video.json
├── sensor/  sensor_report.json  sensor_tracks.npz
└── masks/   top.npz  left.npz  right.npz  masks.json
```

File contents, uncertainty, and timestamps: `FEEDBACK.md`.

## 5. Optional Queries

Queries read the stored record of a finished rollout. They are not charged and never change official results.

| Command | Returns | Limits |
|---|---|---|
| `frames sNN VIEW TIMES [depth]` | PNG frames from the same cameras at any instant (s, up to 3 decimals; nearest 1 ms), optional 16-bit depth, and `frames/frames.json` | ≤ 8 times per call; ≤ 240 frames (times × views) per submission |
| `masks sNN VIEW FRAMES` | Masks as PNG (255 = object) with `masks/masks.json`; `FRAMES`: `i0:i1[:step]` (end excluded) or `i,j,...` indices of `video/frames.json` | ≤ 60 masks (frames × views) per call |
| `history` | Every submission and the best evaluated policy (section 6) | — |
| `note sNN` | Appends your research note to a submission (section 6) | ≤ 16 KB per note |
| `package sNN` | The exact archive you submitted; its SHA-256 equals `archive_sha256` in `history` | — |

## 6. Research Records

`history` lists every submission with its hashes (`policy_sha256`, `archive_sha256`, `feedback_sha256`), `state`, `official` results with versions, your notes, `role`, `keep`, and `gate`:

- **`gate`:** `first`, `improved`, `equal`, `regressed`, or `not_comparable` (different evaluation versions), against the best comparable earlier submission.
- **`best_evaluated`:** ranked by official results only: valid run, then no hardware violation, then `success`, then score, then score lower bound; ties go to the earlier submission.
- **`latest_candidate`:** the latest submission not labelled `diagnostic` or `experimental`.

`note sNN` appends one record (append-only and hash-chained; corrections are new notes). Required fields: `kind`, `hypothesis`, `change`, `evidence`, `decision`; other fields are optional:

```json
{"kind": "improvement | diagnostic | experimental", "hypothesis": "...", "change": "...", "evidence": "...",
 "decision": "...", "keep": "keep | reject | undecided", "source_revision": "git commit",
 "code_change": "summary or diff stat", "sim_config": {"...": "your simulation configuration, ≤ 8 KB"},
 "checkpoint": "your checkpoint reference", "analysis": "...",
 "local": {"...": "your local-simulation result, ≤ 4 KB"}, "parent": "sNN"}
```

Notes cannot carry or change official results; unknown fields are refused. `r2s2r-harness` (`TOOLS.md`) wraps these commands.

## 7. Versions

| Component | Current | Where it appears |
|---|---|---|
| Policy interface | `v1` | `manifest.json` `contract_version` (`PACKAGE.md`) |
| Feedback protocol | `r2s2r-feedback/2` | `feedback.json` `protocol` |
| Official evaluation | `sv-2.2` (rubric `rubric-1.3`, camera rig `rig-1.1`) | `sensor_report.json` `version`, `rubric_version`, `rig_version` |
| Hardware specification | `hwspec-1.0` | `hardware/hardware_spec.json`; `sensor_report.json` `hardware.spec_version` |

The components are versioned separately; all three tasks currently use the same versions. Every record keeps the versions it was produced with, and `gate` and `best_evaluated` compare only submissions whose evaluation, rubric, rig, and hardware-spec versions match.
