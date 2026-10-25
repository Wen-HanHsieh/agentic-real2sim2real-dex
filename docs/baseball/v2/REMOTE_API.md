# Remote Evaluation API

The target environment executes submitted policies and stores sensor-based feedback after each rollout. Feedback contents: `FEEDBACK.md`. Packaging: `PACKAGE.md`.

## 1. Commands

```bash
# Package check, submission, and budget
r2s2r-baseball budget
r2s2r-preflight my_policy/
tar -C my_policy -czf - . | r2s2r-baseball validate
tar -C my_policy -czf - . | r2s2r-baseball submit
r2s2r-baseball status

# Standard feedback
r2s2r-baseball fetch sNN > sNN.tgz

# Standard research workflow
r2s2r-baseball history
r2s2r-baseball intent < intent.json
r2s2r-baseball note sNN < note.json

# On-demand access
r2s2r-baseball package sNN > sNN_package.tgz
r2s2r-baseball frames sNN <top|left|right|all> <t1,t2,...> [depth] > frames.tgz
r2s2r-baseball masks sNN <top|left|right|all> <i0:i1[:step] | i,j,...> > masks.tgz

# Optional: your training-simulation video of a submitted policy (display only)
r2s2r-baseball training-video sNN PACKAGE_SHA256 [SIMULATOR] [run=LOCAL_RUN] < my_rollout.mp4
```

`r2s2r-harness submit` and `r2s2r-harness reflect` (`TOOLS.md`) wrap `intent`, `submit`, and `note` (section 5); `r2s2r-harness video` wraps `training-video` (section 6). Responses are JSON, except `fetch`, `frames`, and `masks` (`.tar.gz`) and `package` (the archive exactly as submitted). Errors return `{"error": "..."}` with a non-zero exit code. `r2s2r-preflight` is a local check (`PACKAGE.md`).

## 2. Submission

- **Archive:** `.tar` or `.tar.gz`, ≤ 500 MB, ≤ 2000 files; `policy.py` at the archive root or inside one top-level directory; no links, absolute paths, or `..` paths.
- **Checks:** `validate` and `submit` run the same package checks (`PACKAGE.md`). A rejected package is not recorded and not charged.
- **Receipt:** `submit` returns `submission_id`, `policy_sha256`, `archive_sha256`, `state: queued`, `research_intent` (the intent bound to this submission, section 5), and the check's inference timing and warnings.
- One evaluation runs at a time.

## 3. Evaluation and Budget

- **Trial:** one trial per submission, 10 s (5,000 steps at 500 Hz), from fixed initial conditions.
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
├── sensor/  sensor_report.json  sensor_tracks.npz
└── masks/   top.npz  left.npz  right.npz  masks.json
```

File contents, uncertainty, and timestamps: `FEEDBACK.md`.

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

Use `limitation` when an evaluation ended without rollout evidence. A later reflection on the same submission is an amendment; earlier records remain.

**`history`** lists every submission with its hashes (`policy_sha256`, `archive_sha256`, `feedback_sha256`), `state`, `official` results (status, score and bounds, stages, milestones, versions), notes with `timing` (`before_result` / `after_result`), `role`, `keep`, `gate`, and:

- **`research`:** the bound intent, the rollout evidence (`complete rollout`, `partial rollout` up to a policy failure, or `none`), reflections, current decision and next hypothesis, and `needs`: every missing part (for example `reflection: missing`). Missing parts are listed, never filled in, and never block a submission.
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

## 6. On-demand Access

Stored data of earlier submissions, retrieved only when you need it. Not charged; never changes official results. `frames` and `masks` complement `fetch`: frames at any instant (also between video frames) with optional depth, and selected masks as PNG without downloading the whole bundle.

| Command | Returns | Limits |
|---|---|---|
| `package sNN` | The exact archive you submitted; its SHA-256 equals `archive_sha256` in `history` | — |
| `frames sNN VIEW TIMES [depth]` | PNG frames from the same cameras at any instant (s, up to 3 decimals; nearest 1 ms), optional 16-bit depth, and `frames/frames.json` | ≤ 8 times per call; ≤ 240 frames (times × views) per submission |
| `masks sNN VIEW FRAMES` | Masks as PNG (255 = object) with `masks/masks.json`; `FRAMES`: `i0:i1[:step]` (end excluded) or `i,j,...` indices of `video/frames.json` | ≤ 60 masks (frames × views) per call |

**Optional: training-simulation video (display only).** `training-video sNN PACKAGE_SHA256 [SIMULATOR] [run=LOCAL_RUN]` links a video (on stdin) of your own training-simulation rollout of the policy submitted as `sNN`, so that it can be shown publicly next to the target rollout of the same submission. It is never evaluated, never charged, and never changes official results, `history`, or your research records; uploading one is entirely optional.

| Field | Meaning | Limits |
|---|---|---|
| `PACKAGE_SHA256` | SHA-256 of the exact archive submitted as `sNN`; must equal its `archive_sha256` in `history`, otherwise the video is refused | 64 lowercase hex digits |
| `SIMULATOR` | Optional label of your simulator | 1–40 characters `A-Z a-z 0-9 . _ + -` |
| `run=LOCAL_RUN` | Optional identifier of your local run, checkpoint, or experiment | 1–80 characters `A-Z a-z 0-9 . _ : + -` |
| Video | MP4 or WebM of a rollout of that exact package in your simulator | ≤ 64 MB; ≤ 4 per submission (the latest is shown; earlier ones are kept) |

The response confirms the stored video's SHA-256 and the package match. `r2s2r-harness video` (`TOOLS.md`) computes the package hash from the directory or archive for you and checks it against `history` before uploading.

## 7. Versions

| Component | Current | Where it appears |
|---|---|---|
| Policy interface | `v1` | `manifest.json` `contract_version` (`PACKAGE.md`) |
| Feedback protocol | `r2s2r-feedback/2` | `feedback.json` `protocol` |
| Official evaluation | `sv-2.3` (rubric `rubric-1.3`, camera rig `rig-1.1`) | `sensor_report.json` `version`, `rubric_version`, `rig_version` |
| Hardware specification | `hwspec-1.1` | `hardware/hardware_spec.json`; `sensor_report.json` `hardware.spec_version` |
| Target model | `tm-2` (Wuji Hand 2.2) | `feedback.json` `target_model_version`, `robot`; `history` `official.versions.target_model` |

The components are versioned separately; all three tasks currently use the same versions. The target model version names the simulated robot revision and physics configuration of the target environment; earlier records ran `tm-1` (Wuji Hand 2 Beta 1). Every record keeps the versions it was produced with, and `gate` and `best_evaluated` compare only submissions whose evaluation, rubric, rig, hardware-spec, and target model versions match.
