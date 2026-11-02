# Evaluation: How a Submission Is Executed, Recorded, and Ranked

This document describes what the target environment does with a submission, as implemented. The policy interface is `sim2target/CONTRACT.md`, the package rules are `sim2target/PACKAGE.md`, the API is `sim2target/REMOTE_API.md`, the returned files are `sim2target/FEEDBACK.md`, and the success criteria are `SUCCESS.md`.

## 1. One Trial per Submission

- Every accepted submission is executed **once**: one trial of the task's episode length (`N` control steps at 500 Hz, `TASK_CONFIG.md` section 2) in the nominal condition of the task, from the fixed initial state of `TASK_CONFIG.md` section 3 (including any fixed task setting stated in `TASK.md`). Object geometry, physical properties and state-frame conventions are defined in `object/SPECS.md`.
- The trial starts with a 1 s settle phase that the policy does not control (the hand holds its initial finger configuration and wrist pose while the object comes to rest), then `reset()` and `N` calls of `act(obs)`.
- There are no repetitions, no randomized initial conditions, and no alternative physical conditions in the evaluation of a submission. The target environment has other conditions for its own internal consistency tests (for example a halved physics step); they are never used to evaluate submissions and never appear in the feedback.
- The episode is not ended by physical task events such as dropping an object or failing a grasp; it ends early only on a policy execution failure (`sim2target/CONTRACT.md` section 4). The record then covers the steps up to the failure.

A physically valid rollout remains evaluable even if the task fails early or achieves zero progress. Task failure alone is not policy execution failure.

## 2. Determinism and Noise

- The finger encoder noise (`hardware/SPECS.md` section 6) is drawn from a seed derived from the package's SHA-256 and a fixed key of the target environment: the same package always sees the same noise sequence; a different package sees a different one. The seed is not published and cannot be chosen.
- Everything else is deterministic: identical packages produce identical state records, logs and reports (the target checks this with its own hashes).
- Your policy must be deterministic given its observation history (`sim2target/CONTRACT.md` section 5); `validate` and `submit` verify this before the trial.

## 3. Execution

1. **Checks before anything is charged** (`validate` or the first step of `submit`): archive rules, manifest and hashes, `"contract_version": "v2"`, syntax, no compiled code, `load_policy()`, `reset()`, five `act()` calls on synthetic observations with the task's exact key set, shapes and dtypes (`TASK_CONFIG.md` section 5), action validity, determinism replay, inference time. Synthetic observations follow the task-specific schema, including explicitly documented undefined values and validity indicators. A rejected package is not recorded and not charged.
2. **The trial:** the policy runs in the sandbox of `sim2target/PACKAGE.md` section 3 and is called once per control step; each command is held for 2 ms; the wrist command limits and controllers of `hardware/SPECS.md` apply.
3. **Policy failure:** a missing, non-finite or wrongly shaped action value, an unknown key, a wrist orientation target with norm outside `[0.9, 1.1]`, an exception, no answer within 5 s (60 s for `load_policy()` and `reset()`), or more than 64 MB written to the scratch directory ends the trial at that step. Accepted wrist orientation targets are normalized before execution. The submission's state is `error`, it is charged, and the feedback up to the failure is stored (`sim2target/REMOTE_API.md` section 3). A policy-failed rollout is technically invalid and unranked.
4. **Wall-clock limit:** an evaluation (trial, verifier and video rendering) that exceeds the task's wall-clock limit (`TASK_CONFIG.md` section 2) is stopped; the state is `timeout`, the submission is charged, and no feedback exists.
5. **Target-side error:** an infrastructure failure gives state `error` with `charged: false`; nothing is recorded against the budget.

The 5-second policy-call timeout is a hard watchdog, not the expected inference latency. The 2 ms inference target and package runtime requirements remain defined in `sim2target/PACKAGE.md`.

**Physical task failure is distinct from policy failure.** Dropping an object, failing to complete a task stage, or achieving zero progress does not by itself terminate the trial or make an otherwise valid evaluation unrankable.

## 4. The Record

Each submission's record is written once and then sealed: the package exactly as submitted, the receipt, the state record, the rollout log, the videos, the official report and `feedback.json` with the SHA-256 of every returned file (`sim2target/FEEDBACK.md` section 6). Records are never rewritten; a later change of the criteria never re-scores an earlier record (`SUCCESS.md`). `history` and `fetch` read the sealed record.

**Mandatory sim-to-target calibration.** After each evaluation with accessible rollout feedback, and before the next target submission, the research agent must complete the `r2s2r-calib` workflow defined in `TOOLS.md`. Calibration evidence must be recorded and linked to the corresponding submission through the research records. If feedback is sealed, unavailable, or unusable, record the blocker rather than fabricate calibration results; follow the documented exception procedure before proceeding without completed calibration.

Calibration is a research workflow requirement. It does not modify the sealed official result, target verifier score, or ranking.

## 5. The Official Result

The active Ground-Truth Verifier scores the sealed state record against the criteria identified in the official report (`sim2target/FEEDBACK.md` section 1). The report identifies the actual verifier and criteria versions used for the evaluation; these identifiers must not be inferred from the current software version or retroactively replaced.

The official result distinguishes:

- **`status: evaluated`** with `success` and `progress` when criteria exist and the record is evaluable. `success` requires the criteria fully met, hardware compliance (`hardware/SPECS.md` section 7), a run without policy failure, and the target's own run checks passed.
- **`status: criteria_undefined`** with `success` and `progress` `null` while the task has no criteria (the report's `criteria` field states the criteria id, rubric and status your submission was scored with).
- **`status: not_evaluable`** only when the record itself is unusable due to a target-side problem, not merely because the physical task failed.

A technically invalid rollout is not rankable. Its actual execution state, validity findings, and available feedback must be preserved without inventing an evaluation score.

### Stage-Based Task Progress

The four tasks use the stage-based progress criteria defined in their respective `SUCCESS.md` files.

| Task | Official Progress |
|---|---|
| Tennis | 9 sequential stages, each contributing 1/9 |
| Plug | 4 sequential stages, each contributing 0.25 |
| Pen | 5 sequential stages, each contributing 0.20 |
| Cube | 4 sequential stages, each contributing 0.25 |

Stage completion, ordering, success conditions, and physical thresholds are defined by the active `SUCCESS.md` criteria and their corresponding Ground-Truth Verifier.

For Cube, distance-to-solved measurements are diagnostics; they do not replace the approved four-stage progress rubric.

**The target verifier is the sole authority for official progress.** The harness displays the reported values and must not recalculate progress using a different formula.

### Progress, Success, and Validity

- **`success`:** Whether all required task criteria and validity conditions are satisfied.
- **`progress`:** Official task progress in [0, 1], computed by the active verifier.
- **`progress = 0.0`:** A valid measured result indicating that no progress milestones were achieved. It remains eligible for ranking when the rollout is otherwise valid.
- **`progress = null`:** Progress was not computed or is unavailable. It must not be silently converted to zero.
- **Rankability:** Whether the official evaluation is eligible for comparisons and best-policy selection, based on its result and validity status.

A physically unsuccessful but technically valid rollout should receive its actual progress, including `0.0`, regardless of how early the physical task failed.

`history` reports the result as `official.status` (`success`, `failure`, `criteria_undefined`, or `not_evaluable`) and `official.score` (the report's `progress`, exact). Any additional official validity, rankability, stage, or criteria metadata must be preserved according to the active result schema.

## 6. Ranking

- **Version groups:** Submissions are comparable only within the same version group: contract, verifier, criteria id and status, rubric, hardware specification, target model, and environment version (`sim2target/REMOTE_API.md` section 7). A change of any of them starts a new group; the best of every group is listed in `best_by_versions`.
- **Rankability:** Only officially rankable evaluations participate in best-policy selection. Valid rollouts with zero progress, partial progress, or early physical task failure remain rankable. Policy failures, hardware-invalid runs, runtime-invalid runs, and otherwise technically invalid evaluations are unranked.
- **Ranking order:** Within a compatible version group, `best_evaluated` ranks eligible submissions by official `success` first, then official `progress`; ties go to the earlier submission. An evaluated physical task failure with `progress = 0.0` is eligible for ranking.
- **Missing progress:** A failure whose progress could not be computed (`progress` `null`, shown as N/A) is listed with its evidence and comparisons where meaningful (`score_delta` `null`), but is not ranked: it has no ranking gate and is never `best_evaluated`. Missing progress is not equivalent to valid zero progress.
- **Regression comparisons:** `gate` and `comparison` compare each eligible submission with the best comparable one before it and with the previous comparable one (`sim2target/REMOTE_API.md` section 5). Incompatible or unrankable submissions must not affect best-policy selection.
- **Undefined criteria:** Nothing is ranked while the criteria are undefined: records are listed with their validity and evidence, and `gate`, `comparison` and `best_evaluated` stay empty.
- **Version preservation:** Earlier records retain their original verifier, criteria, and environment versions. New criteria never silently re-score or overwrite previous submissions.

One trial per submission: success is compared as a status, not as a rate. Your research records, calibration artifacts and training-simulation videos never influence the official ranking.
