# Experiment Records

This document lists where the records of your experiments are kept and how they refer to each other: the records the target environment keeps for every submission, the local copies the tools write on your machine, and the calibration records.

The commands and their limits are specified in `sim2target/REMOTE_API.md` section 5 (target) and `TOOLS.md` sections 1–3 (tools, research harness and calibration); the official results are specified in `sim2target/EVALUATION.md` and `sim2target/FEEDBACK.md`.

Research records never change official evaluation results. Missing optional records, including research notes or training-simulation videos, do not independently block Remote API submissions.

**Mandatory calibration:** After each target evaluation with accessible rollout feedback, the research agent must complete and record the sim-to-target calibration workflow defined in `TOOLS.md` section 3 before its next target submission. If feedback is unavailable or replay is infeasible, the agent must document the blocker and follow the documented exception procedure. This is a research-workflow requirement, not a new server-side API gate.

## 1. What Is Recorded Where

| Record | Kept by | Written with | Contents |
|---|---|---|---|
| Submission record | Target environment, automatically | `submit` | The package exactly as submitted, `policy_sha256`, `archive_sha256`, timestamps, state, official results with their versions, standard feedback (`feedback_sha256`), comparisons and the best evaluated policy; read with `history`, `fetch`, `package` |
| Research intent | Target environment | `intent` (or `r2s2r-harness submit`) | Before a submission: hypothesis, planned change, rationale, kind, parent, checkpoint, local evidence, simulator configuration, and the source revision and code diff captured on your machine; bound to the first later submission whose `archive_sha256` equals its `package_sha256` |
| Reflection and notes | Target environment | `note sNN` (or `r2s2r-harness reflect`, `record`) | After the result: what worked and failed, diagnosis, evidence, keep / reject / undecided, decision, next hypothesis, limitation and analysis; append-only, with later records amending earlier ones |
| Training-simulation video | Target environment | `training-video` (or `r2s2r-harness video`) plus a `training_video` note | A rollout of the submitted package in your own simulator, with the simulator label and local run identifier, and the statement full / partial / none; expected as a research artifact but non-blocking |
| Local submission copy | Your machine | `r2s2r-harness submit` | Write-once files under `<records>/<api>/submissions/sNN/`: `intent.json` (the intent and the target's answer), `receipt.json`, `source.diff`, `package_<sha256 prefix>.tar.gz`; `<records>` is `--records`, else `$R2S2R_RECORDS`, else `~/r2s2r_records` |
| Local archive | Your machine | `r2s2r-harness archive DIR`, checked with `r2s2r-harness verify DIR` | Write-once: `history/<time>.json` snapshots, `packages/sNN.tar` (kept only if its SHA-256 equals `archive_sha256`), `feedback/sNN.tgz`, and `manifest.json` with the SHA-256 of every file |
| Calibration record | Your machine | `r2s2r-calib record DIR --hypothesis ... [--notes ...] [--config cfg.json] [--files ...]` | One directory `<UTC time>_<hypothesis>/` per record with `record.json` (hypothesis, notes, configuration, copies of the provided evidence files with their SHA-256, and a summary of a `metrics.json` among them) and one line per record in `DIR/index.jsonl`. Each calibration must be traceable to its source submission, feedback and simulator revision through the existing record fields or associated evidence |

### Required Calibration Evidence

For every evaluation with accessible feedback, preserve enough information to identify:

- The target `submission_id` (`sNN`) and its experiment.
- The submitted package's `archive_sha256` or `policy_sha256`, as applicable.
- The source feedback, identified by `feedback_sha256` or an equivalent verified feedback reference.
- The local simulator configuration and code revision used for replay.
- Whether commanded actions or executed targets were replayed.
- The comparison metrics and diagnostic evidence.
- Simulator changes made, or the reason for making no changes.
- The local validation result of the proposed repair.

Use the existing `r2s2r-calib record` arguments, configuration, notes and attached evidence files to preserve these references.

**Do not introduce new mandatory `record.json` fields unless the existing tool cannot reliably preserve the required association and a schema change is explicitly approved.**

The calibration record must represent actual tool outputs. Missing, failed or incomplete calibration steps must be reported rather than fabricated.

## 2. How the Records Refer to Each Other

- **Package.** A submission, its intent and its training-simulation video are tied by the archive's SHA-256: the intent's `package_sha256`, the submission's `archive_sha256` and the video's `PACKAGE_SHA256` are the same value. `policy_sha256` identifies the unpacked package.

- **Lineage.** The intent's `parent` names the submission the change starts from; `auto.source_revision` and `auto.diff_base` name your code revision and the base of the recorded diff.

- **Your local evidence.** The intent's `local` (≤ 4 KB) and `sim_config` (≤ 8 KB) carry your local result and simulator configuration; `checkpoint` names your checkpoint. The training-video upload carries your simulator label and `run=LOCAL_RUN`.

- **Official evidence.** `feedback_sha256` in `history` is the SHA-256 of the fetched `feedback.json`, which lists the SHA-256 of every file of the standard feedback (`sim2target/FEEDBACK.md` section 6). Official scores and validity findings remain associated with the original submission and its evaluation versions.

- **Calibration.** A calibration record must identify the submission and feedback it analyzes. The reflection's `evidence` and `analysis` fields cite the calibration record directory, comparison metrics, relevant failures and simulator changes. `next_hypothesis` describes the proposed repair screened in simulation (`sim2target/REMOTE_API.md` section 5; `TOOLS.md` section 3).

- **Next experiment.** The next submission's research intent records its hypothesis, parent submission, source revision, simulator configuration and local evidence. This makes it possible to determine which calibration findings motivated the subsequent experiment.

### Evidence Chain

Every target evaluation with accessible feedback should produce the following traceable chain:

```text
Submission sNN
  archive_sha256
  policy_sha256
        |
        v
Official Target Feedback
  feedback_sha256
  trajectory / actions / videos
  verifier result / validity
        |
        v
Sim-to-Target Calibration
  simulator revision / configuration
  extracted target trajectory
  replay results
  comparison metrics
  diagnosis
        |
        v
Research Reflection
  calibration evidence reference
  what worked / failed
  keep / reject / undecided
  simulator changes
  next hypothesis
        |
        v
Next Experiment
  parent submission
  updated simulator / policy
  local validation
  research intent
```

The chain is represented using existing identifiers, record fields, notes and evidence files. The diagram does not define a new JSON schema.

### Mandatory Calibration and Missing Evidence

After an evaluation with accessible rollout feedback:

1. Retrieve and verify the feedback.
2. Run `r2s2r-calib extract`.
3. Replay the target actions in the agent's simulator.
4. Compare the resulting trajectories.
5. Diagnose discrepancies.
6. Record calibration evidence.
7. Validate the next candidate locally.
8. Link the calibration findings in the research reflection before the next submission.

The detailed commands and permitted replay modes are defined in `TOOLS.md` section 3.

If feedback is sealed, missing or unusable, record the limitation and its evidence.

If replay is genuinely infeasible, preserve the attempted commands, failure evidence and diagnosis, and follow the documented exception procedure before proceeding without completed replay-based calibration.

A missing calibration record must not be silently interpreted as completed calibration.

**Remote API versus research workflow:** The existing Remote API does not independently reject a submission merely because optional research records are missing. Mandatory calibration is enforced by the agent's approved research workflow, subject to its documented exception procedure. Do not introduce a new server-side gate without explicit approval.

### Record Completeness

`history` lists every submission with its bound intent, reflections, training-video status and `research.needs`, identifying parts of the research record that are still missing (`sim2target/REMOTE_API.md` section 5). `r2s2r-harness summary` shows the same information.

Missing research artifacts must be represented as missing, not populated with placeholder evidence.

A missing training-simulation video does not block a submission and does not change official results.

Calibration is a separate mandatory research-workflow requirement when accessible target feedback exists.

### Immutable Evidence

- Target evaluation records are sealed after creation.
- Research intents and notes are append-only.
- Later corrections are new records or amendments; earlier records remain available.
- Local submission copies and archives preserve the original package and evidence hashes.
- Calibration evidence preserves its associated inputs and checksums.
- Historical official results are not retroactively re-scored when verifier or criteria versions change.

## 3. Best Policy and Comparisons

The best evaluated policy, regression gate and comparisons with earlier submissions are computed by the target environment from official results only (`sim2target/EVALUATION.md` section 6; `sim2target/REMOTE_API.md` section 5).

Your research intents, reflections, calibration records, notes and training-simulation videos never enter the official scoring or ranking.

### Rankability

Only officially rankable evaluations participate in best-policy selection.

- A technically valid successful rollout is rankable.
- A technically valid rollout with partial progress is rankable.
- A technically valid rollout with `progress = 0.0` is rankable.
- A technically valid rollout that physically failed early but completed without technical failure is rankable.
- A policy-invalid, hardware-invalid, runtime-invalid or otherwise technically invalid rollout is unranked.
- A result with genuinely uncomputed progress (`progress = null`) is unranked.
- When criteria are undefined, nothing is ranked.

**Zero progress is a valid score, not missing evidence.**

The official verifier determines progress and rankability. Research tools must preserve these values rather than recalculate or override them.

### Ranking and Comparisons

Within a compatible evaluation version group, eligible submissions are ranked by:

1. Official success.
2. Official progress.
3. Earlier submission wins an exact tie.

Comparisons are restricted to compatible versions of:

- Policy contract.
- Verifier.
- Criteria ID and status.
- Rubric.
- Hardware specification.
- Target model.
- Environment.

A change in any of these dimensions starts a new comparison group.

`best_evaluated` and `best_by_versions` report the official best eligible policies.

An unranked record may retain diagnostic evidence or comparisons where supported by the API, but it must not become the best evaluated policy or produce a ranking gate.

A missing progress score must not be converted into zero for comparisons.

Historical evaluations retain their original versions and are not retroactively rescored.

### Research Tools

`r2s2r-harness best --download DIR` retrieves the official best policy's exact package after checking its SHA-256.

When multiple version groups exist, inspect the official `history` and `best_by_versions` records to identify the intended compatible group. Do not assume that policies from different environment or verifier versions are directly comparable. Follow the actual supported `best` command semantics.

`r2s2r-harness gate sNN` shows the official gate and comparisons of one submission.

These tools display or retrieve official results. They must not substitute local simulation scores, researcher preferences or calibration metrics for the official ranking.

Research decisions such as `keep`, `reject` or `undecided` remain part of the research record and do not modify the target's official best-policy selection.
