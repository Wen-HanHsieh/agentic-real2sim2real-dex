# Wuji Hand 2: Pen Spinning

Your goal is to reproduce the dexterous manipulation skill demonstrated in the provided reference video and develop a successful policy for the target robot: the Wuji Hand 2 on a free-floating wrist, in a black-box target environment that executes your policy and returns ground-truth feedback. In this environment the hand's wrist is free to move, and the policy observes the exact state of the pen.

This workspace documents your task; the same environment generation runs four tasks (tennis ball toss and catch, plug handling on a table, pen spinning, one-handed 2×2×2 cube solving) with identical interfaces. Read the task documentation, the hardware and object specifications, and the evaluation API before starting.

## Autonomous Research

- Independently determine how to learn from the demonstration and bridge the gap between the visual reference and robot execution.
- Freely choose your simulator, learning method, policy architecture, reward, curriculum, and training strategy.
- Use available compute, research papers, open-source implementations, and external tools.
- Build and validate your approach locally before target evaluation.

## The Two Stages

**Demo-to-Sim.** From the demonstration video (`demo/`) to a simulated reproduction of the skill. The object's geometry and physical properties are given (`object/SPECS.md`); what the video adds is motion: recover the hand's and the object's motion from it (`REFERENCE.md` states what such a reconstruction consists of and which tools are provided, `TOOLS.md` section 3), build your own simulation of the target robot and object from the public specifications (`hardware/SPECS.md`, `object/SPECS.md`), and develop a policy that meets the policy interface (`CONTRACT.md`, `PACKAGE.md`).

**Sim-to-Target.** Submit the policy to the target environment (`REMOTE_API.md`), inspect the official result and the rollout evidence (`FEEDBACK.md`, `EVALUATION.md`), calibrate your simulator against the target rollout (`TOOLS.md` section 2), diagnose, revise, and resubmit.

## Closed-loop Improvement

The target is a black-box environment. Use only the documented evaluation API.

1. Form a hypothesis, develop a candidate policy, and validate it locally (`r2s2r-preflight`).
2. Submit the policy and inspect the official results, the state record, videos, and robot logs.
3. Calibrate your simulator against the target rollout (below), diagnose failures, revise your approach, and repeat.

Use the **100-submission budget** thoughtfully. Follow the Standard Research Workflow (`REMOTE_API.md` section 5) to preserve hypotheses, code changes, evaluation evidence, and research decisions.

## Sim-to-Target Calibration (required after each target evaluation)

No calibration is required before your first target rollout. After each target evaluation, before the next submission:

1. Use `r2s2r-calib` (`TOOLS.md` section 2) to extract the target trajectory, replay its action sequence in your own simulator, and compare the wrist, object, and joint trajectories with the target's exact state record.
2. Diagnose the discrepancies and formulate testable failure hypotheses.
3. Update your simulator, or explain why a particular discrepancy cannot be modeled.
4. Screen candidate repairs in simulation before the next target submission.
5. Record the calibration evidence, your modifications, and the results.

If replay is genuinely infeasible, document the reason and validate the next candidate in another documented way. Your simulator, physics parameters, calibration algorithm, policy, controller, and learning method remain your choice.

## Documents

Each specification has one authoritative document; the others refer to it.

| Resource | Description |
|---|---|
| `TASK.md` | Task objective |
| `SUCCESS.md` | Official success criteria and task progress rubric (provisional) |
| `demo/` | Human demonstration video, sampled frames, and `demo/README.md`: the actual files, their time base, and the reconstruction inputs |
| `REFERENCE.md` | What a reconstruction of the demonstration consists of (output contract, provisional) and the reconstruction tools provided |
| `hardware/SPECS.md` | Wuji Hand 2.2 specification: floating wrist and its controller, finger controller, encoders, and hardware limits (authoritative) |
| `hardware/` | Robot URDF and meshes (`hardware/wuji_hand2_right/`), machine-readable `hardware/hardware_spec.json` |
| `object/SPECS.md` | Object geometry, mass, visual markings, and the state frame reported in the observation |
| `CONTRACT.md` | Policy interface `v2`: observations (finger encoders, wrist state, exact object state), actions (finger and wrist targets), execution rules (authoritative) |
| `PACKAGE.md` | Policy package format, runtime, resource limits and sandbox restrictions as enforced |
| `REMOTE_API.md` | Remote evaluation API: commands, experiment lifecycle, submission, budget, feedback retrieval, research workflow, access boundaries |
| `EVALUATION.md` | How a submission is executed, recorded, scored, and ranked |
| `FEEDBACK.md` | The official evaluation report, the state record, the rollout log, videos and frames: the standard feedback files |
| `TOOLS.md` | Research Harness, sim-to-target calibration (`r2s2r-calib`), reconstruction tools, and the optional hardware check |
| `HARDWARE_CHECK.md` | Local hardware validation (`r2s2r-hwcheck`) |
| `target/screenshot.png` | Target environment at the start of an episode (top, left, and right views) |
| `tools/` | Tool implementations |
| `example_package/` | Example policy package (contract `v2`) |

## Responsibilities

**Target Environment:** A black-box environment that executes submitted policies, records the exact wrist and object states and the robot's joint states and actions at every control step, and produces the official ground-truth evaluation: status, success, task progress and hardware compliance, computed from that record without measurement uncertainty. It never uses your simulation, never returns its physics parameters, and never explains a failure: it provides the official result and the rollout evidence.

**Research Agent (you):** Builds and calibrates simulations, chooses learning methods, policy architectures, and training rewards, analyzes target feedback, and decides what to try next. Any method that produces a policy meeting `CONTRACT.md` and `PACKAGE.md` is acceptable: learned policies, scripted or hand-designed controllers, trajectory optimization, or combinations.

**Research Harness:** Keeps your standard research records (intent before each submission, reflection after each result) and shows the experiment history, the best evaluated policy, and comparisons kept by the target environment. It records and displays results; it does not direct your research.

You diagnose failures yourself from the state record, videos, frames, logs, and your own metrics; these analyses do not replace or modify the official evaluation.

## Research Cycle

Hypothesis → Change → Local validation → Target submission → Feedback → Sim-to-target calibration and failure analysis → Repair screened in simulation → Decision → Next iteration

| | |
|---|---|
| **Standard feedback** (automatic) | After every rollout the target environment stores the evaluation evidence: the official evaluation report, the ground-truth state record with contact flags, the rollout log with commanded and executed wrist targets, three rendered videos, calibration, and timestamps. Retrieve it with `fetch` (`FEEDBACK.md`). |
| **Standard research workflow** | Kept automatically in `history`: every submission's exact package, hashes, official results, and feedback; the best evaluated policy; comparisons with earlier comparable submissions (regression detection). Your part: before each submission, your hypothesis and planned change (`r2s2r-harness submit`, which also captures your git revision and diff); after each result, what worked and what failed, your diagnosis and its evidence, keep / reject / undecided, and your next hypothesis (`r2s2r-harness reflect`); and for every submission a video of your own training-simulation rollout of that exact package, stated as a full or partial rollout (`r2s2r-harness video` and a `training_video` record, `REMOTE_API.md` section 5), or the reason no video could be recorded. If an evaluation produced no rollout evidence, say so. |
| **On-demand access** | When you need them: earlier policy packages (`package`, `r2s2r-harness best --download`), and RGB or depth frames at selected instants (`frames`). |
| **Sim-to-target calibration** (required after each target evaluation; not before your first rollout) | Extract the target rollout and replay its action sequence in your own simulator (`r2s2r-calib`), compare the wrist, object and joint trajectories with the target's exact state record, turn the discrepancies into testable failure hypotheses, update your simulator or state why a discrepancy cannot be modeled, screen candidate repairs in simulation before the next submission, and record the evidence, modifications, and results (`TOOLS.md` section 2). |
| **Optional analysis tools** | `r2s2r-hwcheck` and your own diagnostics, visualizations, and scripts. |
| **Your choice** | Simulator, physics parameters, calibration method, policy, controller, learning method, reward, curriculum, diagnostic methods, and what to try next. |

Your diagnosis is a hypothesis; the official evaluation is authoritative. Missing records never block a submission; `history` lists them (`REMOTE_API.md` section 5).

## Rules

- Do not access target internals, hidden simulator state, the evaluation implementation, or other agents' workspaces. The target's boundaries are listed in `REMOTE_API.md` section 8.
- Do not modify the target, the official success criteria, the hardware limits, or the evaluation contracts.
- Respect the documented policy runtime and submission constraints (`PACKAGE.md`).
- Do not assume the reference motion must be reproduced through a particular method.

**Your objective is to autonomously discover and improve an effective solution, not to follow a predetermined research pipeline.**
