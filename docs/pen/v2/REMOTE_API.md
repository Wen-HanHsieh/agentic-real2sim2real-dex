# Remote Evaluation API

The target environment executes submitted policies and stores sensor-based feedback after each rollout. Feedback contents: `FEEDBACK.md`. Packaging: `PACKAGE.md`.

## 1. Commands

```bash
# Package check, submission, and budget
r2s2r-pen budget
r2s2r-preflight my_policy/
tar -C my_policy -czf - . | r2s2r-pen validate
tar -C my_policy -czf - . | r2s2r-pen submit
r2s2r-pen status

# Standard feedback
r2s2r-pen fetch sNN > sNN.tgz

# Standard research workflow
r2s2r-pen history
r2s2r-pen intent < intent.json
r2s2r-pen note sNN < note.json
r2s2r-pen training-video sNN PACKAGE_SHA256 [SIMULATOR] [run=LOCAL_RUN] < my_rollout.mp4

# On-demand access
r2s2r-pen package sNN > sNN_package.tgz
r2s2r-pen frames sNN <top|left|right|all> <t1,t2,...> [depth] > frames.tgz
```

`r2s2r-harness submit` and `r2s2r-harness reflect` (`TOOLS.md`) wrap `intent`, `submit`, and `note` (section 5); `r2s2r-harness video` wraps `training-video` (section 5). Responses are JSON, except `fetch` and `frames` (`.tar.gz`) and `package` (the archive exactly as submitted). Errors return `{"error": "..."}` with a non-zero exit code. `r2s2r-preflight` is a local check (`PACKAGE.md`).

## 2. Submission

- **Archive:** `.tar` or `.tar.gz`, ≤ 500 MB, ≤ 2000 files; `policy.py` at the archive root or inside one top-level directory; no links, absolute paths, or `..` paths.
- **Checks:** `validate` and `submit` run the same package checks (`PACKAGE.md`). A rejected package is not recorded and not charged.
- **Receipt:** `submit` returns `submission_id`, `policy_sha256`, `archive_sha256`, `state: queued`, `research_intent` (the intent bound to this submission, section 5), and the check's inference timing and warnings.
- One evaluation runs at a time.

## 3. Evaluation and Budget

- **Trial:** one trial per submission, 12 s (6,000 steps at 500 Hz), from fixed initial conditions.
- **Budget:** 100 charged submissions; `budget` returns the used and total count.
- **States:** `queued` → `running` → `done`, or `error` / `timeout`. Results are not available during a rollout.

| Outcome | State | Charged | Standard feedback |
|---|---|---|---|
| Rollout completed | `done` | yes | yes |
| Policy failure: exception, invalid action, no answer within 5 s, or more than 64 MB written to `TMPDIR` | `error` | yes | yes, up to the failure |
| Evaluation exceeded 45 minutes | `timeout` | yes | no |
| Target-side infrastructure error | `error` | no | no |

`status` reports the error message and whether an `error` was charged. Identical resubmissions are charged.

## 4. Standard Feedback (`fetch`)

Standard feedback is the evaluation evidence the target environment stores automatically after every rollout (after a policy failure: up to the failure). It is not pushed to you; `fetch sNN` returns it:

```text
<experiment>_sNN/
├── feedback.json
├── calibration.json
├── logs/trial_0.npz
├── video/   top.mp4  left.mp4  right.mp4  frames.json  video.json
└── sensor/  sensor_report.json  sensor_tracks.npz
```

The feedback contains task scores and observable evidence in three categories: verifier results, rollout observations, and hardware diagnostics (`FEEDBACK.md` section 4). It does not explain failures and contains no segmentation masks. `feedback.json` lists the SHA-256 of every returned file; `feedback_sha256` in `history` is the SHA-256 of that `feedback.json`. File contents, uncertainty, and timestamps: `FEEDBACK.md`.

## 5. Standard Research Workflow

Every submission keeps an auditable chain: research intent → code and policy revision → submission → official evidence → your diagnosis → your decision.

The target environment keeps the history, the best evaluated policy, and the comparisons automatically; the intent and the reflection are your part of the record. These commands are not charged and never change official results.

| Command | Returns or records | Limits |
|---|---|---|
| `history` | Every submission with its research record and comparisons, and the best evaluated policy | — |
| `intent` | Records your research intent before a submission | ≤ 16 KB per intent |
| `note sNN` | Appends your reflection or note to a submission | ≤ 16 KB per note |

| Part | Recorded by | Command |
|---|---|---|
| Package, hashes, timestamps, state, official results with versions, feedback; best evaluated policy; comparisons | Target environment, automatically | `history` |
| Research intent: hypothesis, planned change, rationale, parent, local evidence | You, before submitting | `intent` |
| Source revision and code diff (`auto`) | `r2s2r-harness submit`, on your machine (not verified by the target) | `intent` |
| Reflection: what worked and failed, diagnosis, evidence, keep / reject / undecided, next hypothesis | You, after the result | `note sNN` |

**Intent (before submitting).** One JSON object; `package_sha256`, the SHA-256 of the exact archive you will submit, is required:

```json
{"package_sha256": "64 hex digits", "hypothesis": "...", "change": "...", "rationale": "...",
 "kind": "improvement | diagnostic | experimental", "parent": "sNN", "checkpoint": "...",
 "local": {"...": "≤ 4 KB"}, "sim_config": {"...": "≤ 8 KB"},
 "auto": {"source_revision": "...", "source_dirty": false, "diff_base": "...", "code_diff_sha256": "...",
          "code_change": "...", "git": "...", "captured_utc": "...", "captured_by": "..."}}
```

The target binds an intent to the first later submission whose `archive_sha256` equals `package_sha256` (if several intents name the same archive, the latest one before the submission); an intent recorded after a submission never binds to it.

**Reflection (after the result).** `note sNN` with `"record": "reflection"`:

```json
{"record": "reflection", "what_worked": "...", "what_failed": "...", "diagnosis": "...", "evidence": "...",
 "keep": "keep | reject | undecided", "decision": "...", "next_hypothesis": "...", "limitation": "...", "analysis": "..."}
```

Use `limitation` when an evaluation ended without rollout evidence. After each target evaluation, the reflection also carries the sim-to-target calibration outcome (`TOOLS.md` section 2): discrepancies and simulator changes in `analysis` and `evidence`, the repair screened in simulation in `next_hypothesis`. A later reflection on the same submission is an amendment; earlier records remain.

**`history`** lists every submission with its hashes (`policy_sha256`, `archive_sha256`, `feedback_sha256`), `state`, `official` results (status, score and bounds, stages, milestones, versions), notes with `timing` (`before_result` / `after_result`), `role`, `keep`, `gate`, and:

- **`research`:** the bound intent, the rollout evidence (`complete rollout`, `partial rollout` up to a policy failure, or `none`), reflections, current decision and next hypothesis, `training_video`, and `needs`: every missing part (for example `reflection: missing`). Missing parts are listed, never filled in, and never block a submission.
- **`comparison`:** `vs_previous` (the previous comparable submission) and `vs_best_before` (the best comparable earlier submission): `improved`, `regressed`, `tied`, or `inconclusive` (score bounds overlap, or an unknown status), with score delta, stage deltas, and milestones gained or lost. One trial per submission: success is compared as a status, not a rate.
- **`gate`:** `first`, `improved`, `equal`, `regressed`, or `not_comparable` (different evaluation or target model versions), against the best comparable earlier submission.
- **`best_evaluated`:** ranked by official results only: valid run, then no hardware violation, then `success`, then score, then score lower bound; ties go to the earlier submission. `best_by_versions` gives the best of each version group.
- **`latest_candidate`:** the latest submission not labelled `diagnostic` or `experimental`.
- **`research_summary`:** records with intent and reflection, incomplete records, intents not bound to a submission, and the record-chain check.

Comparisons and the best policy are evidence; they never select, restore, or reject a policy.

A plain `note sNN` (without `"record"`) keeps the original schema. Required fields: `kind`, `hypothesis`, `change`, `evidence`, `decision`; other fields are optional:

```json
{"kind": "improvement | diagnostic | experimental", "hypothesis": "...", "change": "...", "evidence": "...",
 "decision": "...", "keep": "keep | reject | undecided", "source_revision": "git commit",
 "code_change": "summary or diff stat", "sim_config": {"...": "your simulation configuration, ≤ 8 KB"},
 "checkpoint": "your checkpoint reference", "analysis": "...",
 "local": {"...": "your local-simulation result, ≤ 4 KB"}, "parent": "sNN"}
```

All records are append-only and hash-chained (corrections are new records); they cannot carry or change official results, and unknown fields are refused. `r2s2r-harness` (`TOOLS.md`) wraps these commands.

**Training-simulation video (standard research artifact).** For every target submission, record a representative rollout of the submitted policy in your own training simulator and link it to the submission, so that it can be compared with the target rollout of the same package (the public research dashboard shows both). Prefer a full episode from the documented initial condition, and keep the local experiment and simulator details. The video must show your own local simulation of that exact package: never a human demonstration, a target evaluation video, another policy's rollout, an upstream repository demonstration, or reconstructed footage.

1. **Upload** the video for the exact package: `r2s2r-harness video sNN my_rollout.mp4 --package my_policy/ --simulator NAME --local-run ID` (`TOOLS.md`), or `training-video sNN PACKAGE_SHA256 [SIMULATOR] [run=LOCAL_RUN]` with the video on stdin. The target refuses a video unless `PACKAGE_SHA256` equals the submission's `archive_sha256`.
2. **State the rollout** with `note sNN` and `"record": "training_video"`, naming the `sha256` of the uploaded video (in the upload response):

```json
{"record": "training_video", "video_sha256": "...", "rollout": "full"}
{"record": "training_video", "video_sha256": "...", "rollout": "partial", "start_state": "...", "duration_s": 12.5, "limitations": "..."}
{"record": "training_video", "rollout": "none", "reason": "why no simulator rollout could be recorded"}
```

| Field | Meaning | Limits |
|---|---|---|
| `PACKAGE_SHA256` | SHA-256 of the exact archive submitted as `sNN`; must equal its `archive_sha256` in `history`, otherwise the video is refused | 64 lowercase hex digits |
| `SIMULATOR` | Label of your simulator | 1–40 characters `A-Z a-z 0-9 . _ + -` |
| `run=LOCAL_RUN` | Identifier of your local experiment, run, or checkpoint | 1–80 characters `A-Z a-z 0-9 . _ : + -` |
| Video | MP4 or WebM of a rollout of that exact package in your simulator | ≤ 64 MB; ≤ 4 per submission (the latest is shown; earlier ones are kept) |
| `video_sha256` | SHA-256 of a video already registered for this submission | 64 lowercase hex digits |
| `rollout` | `full` (a whole episode), `partial`, or `none` (no video) | — |
| `start_state`, `duration_s`, `limitations` | Required for `partial`: where the shown rollout starts, how long it is, and what it does not show | ≤ 1000 characters; (0, 3600] s; ≤ 2000 characters |
| `reason` | Required for `none`: why no simulator rollout could be recorded | ≤ 2000 characters |

The video is never evaluated or charged and never changes official results, comparisons, or the best policy; a missing or failed video never blocks a submission, and it can be added before or after the result without a new submission. In `history`, `research.training_video` shows whether it is expected for the submission, the number of videos, the latest video's SHA-256, and the rollout label; a missing video or rollout statement is listed in `research.needs`. Do not rerun earlier experiments only to produce videos for earlier submissions.

## 6. On-demand Access

Stored data of earlier submissions, retrieved only when you need it. Not charged; never changes official results. `frames` complements `fetch`: RGB frames at any instant (also between video frames), optionally with depth.

| Command | Returns | Limits |
|---|---|---|
| `package sNN` | The exact archive you submitted; its SHA-256 equals `archive_sha256` in `history` | — |
| `frames sNN VIEW TIMES [depth]` | PNG frames from the same cameras at any instant (s, up to 3 decimals; nearest 1 ms), optional 16-bit depth, and `frames/frames.json` | ≤ 8 times per call; ≤ 240 frames (times × views) per submission |

## 7. Versions

| Component | Current | Where it appears |
|---|---|---|
| Policy interface | `v1` | `manifest.json` `contract_version` (`PACKAGE.md`) |
| Feedback protocol | `r2s2r-feedback/2` | `feedback.json` `protocol` |
| Feedback contents | `agent-view-1` | `feedback.json` `feedback_view`; `sensor_report.json` `feedback_view` |
| Official evaluation | `sv-2.3` (rubric `rubric-1.3`, camera rig `rig-1.1`) | `sensor_report.json` `version`, `rubric_version`, `rig_version` |
| Hardware specification | `hwspec-1.1` | `hardware/hardware_spec.json`; `sensor_report.json` `hardware.spec_version` |
| Target model | `tm-2` (Wuji Hand 2.2) | `feedback.json` `target_model_version`, `robot`; `history` `official.versions.target_model` |

The components are versioned separately; all three tasks currently use the same versions. The target model version names the simulated robot revision and physics configuration of the target environment; earlier records ran `tm-1` (Wuji Hand 2 Beta 1). Every record keeps the versions it was produced with, and `gate` and `best_evaluated` compare only submissions whose evaluation, rubric, rig, hardware-spec, and target model versions match.

## 8. Access Boundaries

The target environment provides task scores and observable evidence. Diagnosing failures and improving the policy is your task.

| Available to you | Not available |
|---|---|
| Task definition, success criteria, robot and object specifications, demonstration (this bundle) | The target environment's simulator, its physics parameters, and its internal state during a rollout |
| Official results: status, score with bounds, stage scores, milestones (`fetch`, `history`) | Ground-truth object and contact states |
| Rollout observations: camera videos, RGB and depth frames on demand (`frames`), sensor-estimated object tracks, joint states and actions (`logs/trial_0.npz`) | Explanations of failures or suggested fixes |
| Hardware and runtime diagnostics: joint position and speed limits, action validity, estimated torque demand, policy errors, run validity | Segmentation masks |
| Your own packages, research records, and training-simulation videos | The verifier's implementation and configuration, and operator diagnostics |

- Your key reaches only the commands in section 1, for this task's experiment; anything else is refused and no shell is started.
- No command changes success criteria, scoring rules, official results, or the budget; your records and videos never change official results.
- The deployed policy receives joint-only observations (`CONTRACT.md`) and runs in a sandbox (`PACKAGE.md`).
