# Wuji Hand 2: Learning a Dexterous Skill from a Human Demonstration

Your goal is to reproduce the dexterous manipulation skill demonstrated in the provided reference video and develop a successful policy for the target robot: the Wuji Hand 2 on a free-floating wrist, in a black-box target environment that executes your policy and returns ground-truth feedback. The policy observes the hand's joint encoders, the exact wrist state and the exact state of the task's objects.

This workspace documents one task. The same environment generation runs several tasks with identical interfaces: the shared documents describe those interfaces, and everything specific to your task is in five documents: `TASK.md` (the task, or, where no objective has been defined yet, what the environment supports), `SUCCESS.md` (the official criteria, or the statement that none are defined yet), `TASK_CONFIG.md` (the hand variant, episode length, initial configuration, objects, observation shapes, experiment and API command), `object/SPECS.md` and `demo/README.md`. Read them first, then the hardware specification and the evaluation API.

## Autonomous Research

- Independently determine how to learn from the demonstration and bridge the gap between the visual reference and robot execution.
- Freely choose your simulator, learning method, policy architecture, reward, curriculum, and training strategy.
- Use available compute, research papers, open-source implementations, and external tools.
- Build and validate your approach locally before target evaluation.

## The Two Stages

**Demo-to-Sim.** From the demonstration video (`demo/`) to a simulated reproduction of the skill, in two steps. First reconstruct the demonstration into the outputs of `demo2sim/REFERENCE.md` (required): the camera and time base, the objects' 6D motion, the demonstrator's 3D hand motion in the same metric world, the hand–object contact phases, the validation and a comparison video. `demo2sim/RECONSTRUCTION.md` is the default workflow and `TOOLS.md` section 4 lists the pre-installed reconstruction tools and models; how you reconstruct is your choice. The objects' geometry and physical properties are given (`object/SPECS.md`). Then build your training simulation (for example in MuJoCo, the format of the reconstruction's scene) of the target robot and objects from the public specifications (`hardware/SPECS.md`, the hand file of your task, `object/SPECS.md`, `TASK_CONFIG.md`), with your reconstruction as the reference of the skill, and develop a policy that meets the policy interface (`sim2target/CONTRACT.md`, `sim2target/PACKAGE.md`).

**Sim-to-Target.** Submit the policy to the target environment (`sim2target/REMOTE_API.md`), inspect the official result and the rollout evidence (`sim2target/FEEDBACK.md`, `sim2target/EVALUATION.md`), calibrate your simulator against the target rollout (`TOOLS.md` section 3), diagnose, revise, and resubmit.

## Closed-loop Improvement

The target is a black-box environment. Use only the documented evaluation API.

1. Form a hypothesis, develop a candidate policy, and validate it locally (`r2s2r-preflight`).
2. Submit the policy and inspect the official results, the state record, videos, and robot logs.
3. Calibrate your simulator against the target rollout (below), diagnose failures, revise your approach, and repeat.

Use the **100-submission budget** thoughtfully. Follow the Standard Research Workflow (`sim2target/REMOTE_API.md` section 5) to preserve hypotheses, code changes, evaluation evidence, and research decisions.

## Sim-to-Target Calibration (required after each target evaluation)

No calibration is required before your first target rollout. After each target evaluation, before the next submission:

1. Use `r2s2r-calib` (`TOOLS.md` section 3) to extract the target trajectory, replay its action sequence in your own simulator, and compare the wrist, object, and joint trajectories with the target's exact state record.
2. Diagnose the discrepancies and formulate testable failure hypotheses.
3. Update your simulator, or explain why a particular discrepancy cannot be modeled.
4. Screen candidate repairs in simulation before the next target submission.
5. Record the calibration evidence, your modifications, and the results.

If the feedback is unavailable or sealed, or replay is genuinely infeasible, record a calibration exception with its evidence instead (`TOOLS.md` section 3); an exception is never a completed calibration. Your simulator, physics parameters, calibration algorithm, policy, controller, and learning method remain your choice.

## Documents

Each specification has one authoritative document; the others refer to it. Every path in these documents is relative to the root of this workspace.

| Resource | Description |
|---|---|
| `README.md` | This document |
| `TASK.md` | The task objective, or, where none is defined yet, the demonstration and what the environment supports |
| `SUCCESS.md` | The official success criteria and progress rubric and their status, or the statement that none are defined yet |
| `TASK_CONFIG.md` | Runtime configuration of your task: hand variant, experiment and API command, episode length, scene and initial configuration, objects, observation and record shapes |
| `TOOLS.md` | The tools and where they are: research harness, sim-to-target calibration (`r2s2r-calib`), reconstruction tools and models, package and hardware checks |
| `demo/` | Human demonstration video, sampled frames, and `demo/README.md`: the actual files, their time base, and the reconstruction inputs |
| `object/SPECS.md` | The task's objects: geometry, mass, appearance, mechanism where there is one, and the state frames reported in the observation (scene items such as a table, and the initial arrangement: `TASK_CONFIG.md`) |
| `demo2sim/` | **Demo-to-Sim:** `demo2sim/REFERENCE.md`, the required output contract of the demonstration's reconstruction, its validation, and the reconstruction tools and models provided; `demo2sim/RECONSTRUCTION.md`, the default reconstruction workflow (scene analysis, known-geometry objects, camera and metric scale, 6D tracking, the hand fit against the object scene, physical and contact checks): a starting point, not a fixed algorithm |
| `sim2target/CONTRACT.md` | Policy interface `v2`: observations (finger encoders, wrist state, exact object state), actions (finger and wrist targets), execution rules (authoritative) |
| `sim2target/PACKAGE.md` | Policy package format, runtime, resource limits and sandbox restrictions as enforced |
| `sim2target/EVALUATION.md` | How a submission is executed, recorded, scored, and ranked |
| `sim2target/REMOTE_API.md` | Remote evaluation API: commands, experiment lifecycle, submission, budget, feedback retrieval, research workflow, access boundaries |
| `sim2target/FEEDBACK.md` | The official evaluation report, the state record, the rollout log, videos and frames: the standard feedback files |
| `sim2target/EXPERIMENT.md` | Where the records of your experiments are kept (target, local copies, calibration records) and how they refer to each other |
| `sim2target/HARDWARE_CHECK.md` | Local hardware validation (`r2s2r-hwcheck`) |
| `hardware/SPECS.md` | Common Wuji Hand 2.2 specification: floating wrist and its controller, finger controller, encoders, frames, and the hardware rules (authoritative) |
| `hardware/RIGHT_HAND.md`, `hardware/LEFT_HAND.md` | The two hand variants: model files, joint names and order, axes, limits, actuator parameters (your variant: `TASK_CONFIG.md` section 1) |
| `hardware/` | Robot URDFs and meshes of both variants (`hardware/wuji_hand2_right/`, `hardware/wuji_hand2_left/`) and the machine-readable hardware specification |
| `target/` | The target environment at the start of an episode: `target/screenshot.png` (the top, left and right views side by side) and each view alone |
| `tools/` | Tool implementations |
| `example_package/` | Example policy package (contract `v2`) |

## Responsibilities

**Target Environment:** A black-box environment that executes submitted policies, records the exact wrist and object states and the robot's joint states and actions at every control step, and produces the official ground-truth evaluation: status, success, task progress and hardware compliance, computed from that record without measurement uncertainty. It never uses your simulation, never returns its physics parameters, and never explains a failure: it provides the official result and the rollout evidence.

**Research Agent (you):** Builds and calibrates simulations, chooses learning methods, policy architectures, and training rewards, analyzes target feedback, and decides what to try next. Any method that produces a policy meeting `sim2target/CONTRACT.md` and `sim2target/PACKAGE.md` is acceptable: learned policies, scripted or hand-designed controllers, trajectory optimization, or combinations.

**Research Harness:** Keeps your standard research records (intent before each submission, reflection after each result) and shows the experiment history, the best evaluated policy, and comparisons kept by the target environment. It records and displays results; it does not direct your research.

You diagnose failures yourself from the state record, videos, frames, logs, and your own metrics; these analyses do not replace or modify the official evaluation.

## Research Cycle

Hypothesis → Change → Local validation → Target submission → Feedback → Sim-to-target calibration and failure analysis → Repair screened in simulation → Decision → Next iteration

| | |
|---|---|
| **Standard feedback** (automatic) | After every rollout the target environment stores the evaluation evidence: the official evaluation report, the ground-truth state record with contact flags, the rollout log with commanded and executed wrist targets, three rendered videos, calibration, and timestamps. Retrieve it with `fetch` (`sim2target/FEEDBACK.md`). |
| **Standard research workflow** | Kept automatically in `history`: every submission's exact package, hashes, official results, and feedback; the best evaluated policy; comparisons with earlier comparable submissions (regression detection). Your part: before each submission, your hypothesis and planned change (`r2s2r-harness submit`, which also captures your git revision and diff); after each result, what worked and what failed, your diagnosis and its evidence, keep / reject / undecided, and your next hypothesis (`r2s2r-harness reflect`); and for every submission a video of your own training-simulation rollout of that exact package, stated as a full or partial rollout (`r2s2r-harness video` and a `training_video` record, `sim2target/REMOTE_API.md` section 5), or the reason no video could be recorded. If an evaluation produced no rollout evidence, say so. |
| **On-demand access** | When you need them: earlier policy packages (`package`, `r2s2r-harness best --download`), and RGB or depth frames at selected instants (`frames`). |
| **Sim-to-target calibration** (required after each target evaluation; not before your first rollout) | Extract the target rollout and replay its action sequence in your own simulator (`r2s2r-calib`), compare the wrist, object and joint trajectories with the target's exact state record, turn the discrepancies into testable failure hypotheses, update your simulator or state why a discrepancy cannot be modeled, screen candidate repairs in simulation before the next submission, and record the evidence, modifications, and results (`TOOLS.md` section 3). |
| **Optional analysis tools** | `r2s2r-hwcheck` and your own diagnostics, visualizations, and scripts. |
| **Your choice** | Simulator, physics parameters, calibration method, policy, controller, learning method, reward, curriculum, diagnostic methods, and what to try next. |

Your diagnosis is a hypothesis; the official evaluation is authoritative. The target never blocks a submission for a missing record; `history` lists them (`sim2target/REMOTE_API.md` section 5). `r2s2r-harness submit` refuses the next submission while the calibration of the previous one is not recorded (`TOOLS.md` section 3).

## Rules

- Do not access target internals, hidden simulator state, the evaluation implementation, or other agents' workspaces. The target's boundaries are listed in `sim2target/REMOTE_API.md` section 8.
- Do not modify the target, the official success criteria, the hardware limits, or the evaluation contracts.
- Respect the documented policy runtime and submission constraints (`sim2target/PACKAGE.md`).
- Do not assume the reference motion must be reproduced through a particular method.

**Your objective is to autonomously discover and improve an effective solution, not to follow a predetermined research pipeline.**
