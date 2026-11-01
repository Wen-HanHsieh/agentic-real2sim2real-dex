# Experiment Records

This document lists where the records of your experiments are kept and how they refer to each other: the records the target environment keeps for every submission, the local copies the tools write on your machine, and the calibration records. The commands and their limits are specified in `sim2target/REMOTE_API.md` section 5 (target), `TOOLS.md` sections 1 and 2 (tools); the official results are specified in `sim2target/EVALUATION.md` and `sim2target/FEEDBACK.md`. Records never change official results, and a missing record never blocks a submission.

## 1. What Is Recorded Where

| Record | Kept by | Written with | Contents |
|---|---|---|---|
| Submission record | Target environment, automatically | `submit` | The package exactly as submitted, `policy_sha256`, `archive_sha256`, timestamps, state, official results with their versions, the standard feedback (`feedback_sha256`), comparisons and the best evaluated policy; read with `history`, `fetch`, `package` |
| Research intent | Target environment | `intent` (or `r2s2r-harness submit`) | Before a submission: hypothesis, planned change, rationale, kind, parent, checkpoint, local evidence, simulator configuration, and the source revision and code diff captured on your machine; bound to the first later submission whose `archive_sha256` equals its `package_sha256` |
| Reflection and notes | Target environment | `note sNN` (or `r2s2r-harness reflect`, `record`) | After the result: what worked and failed, diagnosis, evidence, keep / reject / undecided, decision, next hypothesis, limitation, analysis; append-only, a later record amends an earlier one |
| Training-simulation video | Target environment | `training-video` (or `r2s2r-harness video`) plus a `training_video` note | A rollout of the submitted package in your own simulator, with the simulator label and your local run identifier, and the statement full / partial / none |
| Local submission copy | Your machine | `r2s2r-harness submit` | Write-once files under `<records>/<api>/submissions/sNN/`: `intent.json` (the intent and the target's answer), `receipt.json`, `source.diff`, `package_<sha256 prefix>.tar.gz`; `<records>` is `--records`, else `$R2S2R_RECORDS`, else `~/r2s2r_records` |
| Local archive | Your machine | `r2s2r-harness archive DIR`, checked with `r2s2r-harness verify DIR` | Write-once: `history/<time>.json` snapshots, `packages/sNN.tar` (kept only if its SHA-256 equals `archive_sha256`), `feedback/sNN.tgz`, and `manifest.json` with the SHA-256 of every file |
| Calibration record | Your machine | `r2s2r-calib record DIR --hypothesis ... [--notes ...] [--config cfg.json] [--files ...]` | One directory `<UTC time>_<hypothesis>/` per record with `record.json` (hypothesis, notes, your configuration, copies of the given files with their SHA-256, and a summary of a `metrics.json` among them) and one line per record in `DIR/index.jsonl` |

## 2. How the Records Refer to Each Other

- **Package.** A submission, its intent and its training-simulation video are tied by the archive's SHA-256: the intent's `package_sha256`, the submission's `archive_sha256` and the video's `PACKAGE_SHA256` are the same value. `policy_sha256` identifies the unpacked package.
- **Lineage.** The intent's `parent` names the submission the change starts from; `auto.source_revision` and `auto.diff_base` name your code revision and the base of the recorded diff.
- **Your local evidence.** The intent's `local` (≤ 4 KB) and `sim_config` (≤ 8 KB) carry your local result and simulator configuration; `checkpoint` names your checkpoint. The training-video upload carries your simulator label and `run=LOCAL_RUN`.
- **Calibration.** A reflection's `evidence` and `analysis` fields are where you cite the calibration of that rollout (the calibration record directory and the comparison metrics) and the simulator changes it led to; `next_hypothesis` carries the repair you screened in simulation (`sim2target/REMOTE_API.md` section 5, `TOOLS.md` section 2).
- **Official evidence.** `feedback_sha256` in `history` is the SHA-256 of the fetched `feedback.json`, which lists the SHA-256 of every file of the standard feedback (`sim2target/FEEDBACK.md` section 6).

`history` lists every submission with its bound intent, its reflections, its training-video status and `research.needs`, the parts of the record that are still missing (`sim2target/REMOTE_API.md` section 5); `r2s2r-harness summary` shows the same.

## 3. Best Policy and Comparisons

The best evaluated policy, the regression gate and the comparisons with earlier submissions are computed by the target environment from official results only (`sim2target/EVALUATION.md` section 6, `sim2target/REMOTE_API.md` section 5). Your records, notes and videos never enter them. `r2s2r-harness best --download DIR` retrieves the best policy's exact package after checking its SHA-256; `r2s2r-harness gate sNN` shows the gate and the comparisons of one submission.
