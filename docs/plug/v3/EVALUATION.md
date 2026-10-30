# Evaluation: How a Submission Is Executed, Recorded, and Ranked

This document describes what the target environment does with a submission, as implemented. The policy interface is `CONTRACT.md`, the package rules are `PACKAGE.md`, the API is `REMOTE_API.md`, the returned files are `FEEDBACK.md`, and the success criteria are `SUCCESS.md`.

## 1. One Trial per Submission

- Every accepted submission is executed **once**: one trial of 15 s (7,500 control steps at 500 Hz) in the nominal condition of this task, from the fixed initial state of `hardware/SPECS.md` section 3 and `object/SPECS.md`.
- The trial starts with a 1 s settle phase that the policy does not control (the hand holds its initial finger configuration and wrist pose while the object comes to rest), then `reset()` and 7,500 calls of `act(obs)`.
- There are no repetitions, no randomized initial conditions, and no alternative physical conditions in the evaluation of a submission. The target environment has other conditions for its own internal consistency tests (for example a halved physics step); they are never used to evaluate submissions and never appear in the feedback.
- The episode is not ended by task events; it ends early only on a policy failure (`CONTRACT.md` section 4). The record then covers the steps up to the failure.

## 2. Determinism and Noise

- The finger encoder noise (`hardware/SPECS.md` section 6) is drawn from a seed derived from the package's SHA-256 and a fixed key of the target environment: the same package always sees the same noise sequence; a different package sees a different one. The seed is not published and cannot be chosen.
- Everything else is deterministic: identical packages produce identical state records, logs and reports (the target checks this with its own hashes).
- Your policy must be deterministic given its observation history (`CONTRACT.md` section 5); `validate` and `submit` verify this before the trial.

## 3. Execution

1. **Checks before anything is charged** (`validate` or the first step of `submit`): archive rules, manifest and hashes, `"contract_version": "v2"`, syntax, no compiled code, `load_policy()`, `reset()`, five `act()` calls on synthetic observations with this task's exact key set, shapes and dtypes, action validity, determinism replay, inference time. A rejected package is not recorded and not charged.
2. **The trial**: the policy runs in the sandbox of `PACKAGE.md` section 3 and is called once per control step; each command is held for 2 ms; the wrist command limits and controllers of `hardware/SPECS.md` apply.
3. **Policy failure**: a missing, non-finite or wrongly shaped action value, an unknown key, a wrist orientation that is not a unit quaternion, an exception, no answer within 5 s (60 s for `load_policy()` and `reset()`), or more than 64 MB written to the scratch directory ends the trial at that step. The submission's state is `error`, it is charged, and the feedback up to the failure is stored (`REMOTE_API.md` section 3).
4. **Wall-clock limit**: an evaluation (trial, verifier and video rendering) that exceeds 45 minutes is stopped; the state is `timeout`, the submission is charged, and no feedback exists.
5. **Target-side error**: an infrastructure failure gives state `error` with `charged: false`; nothing is recorded against the budget.

## 4. The Record

Each submission's record is written once and then sealed: the package exactly as submitted, the receipt, the state record, the rollout log, the videos, the official report and `feedback.json` with the SHA-256 of every returned file (`FEEDBACK.md` section 6). Records are never rewritten; a later change of the criteria never re-scores an earlier record (`SUCCESS.md`). `history` and `fetch` read the sealed record.

## 5. The Official Result

The official verifier (`gv-1`) scores the sealed state record against the criteria named in the report (`FEEDBACK.md` section 1):

- `status: evaluated` with `success` and `progress` when criteria exist for the task; `success` requires the criteria fully met, hardware compliance (`hardware/SPECS.md` section 7), a run without policy failure, and the target's own run checks passed.
- `status: criteria_undefined` with `success` and `progress` `null` while the task has no criteria (the case of this task until criteria are published, `SUCCESS.md`).
- `status: not_evaluable` only when the record itself is unusable (a target-side problem, not charged).

`history` reports the result as `official.status` (`success`, `failure`, `criteria_undefined`, or `not_evaluable`) and `official.score` (the report's `progress`, exact).

## 6. Ranking

- Submissions are comparable only within the same version group: contract, verifier, criteria id and status, rubric, hardware specification, target model, and environment version (`REMOTE_API.md` section 7). A change of any of them starts a new group; the best of every group is listed in `best_by_versions`.
- Within a group, `best_evaluated` ranks by official results only: valid run, then no hardware violation, then `success`, then `progress`; ties go to the earlier submission. `gate` and `comparison` compare each submission with the best comparable one before it and with the previous comparable one (`REMOTE_API.md` section 5).
- Nothing is ranked while the criteria are undefined: records are listed with their validity and evidence, and `gate`, `comparison` and `best_evaluated` stay empty.
- One trial per submission: success is compared as a status, not as a rate. Your research records and training-simulation videos never influence the ranking.
