# Wuji Hand 2: Learning a Dexterous Skill from a Human Demonstration (Demo-to-Sim)

Your goal is to reproduce the dexterous manipulation skill shown in a human demonstration video with the Wuji Hand 2 on a free-floating wrist, in a simulation that you build. From the video (`demo/`) and the task instruction (`TASK.md`) you reconstruct the demonstration, build a training simulation of the robot and the task's objects, train a policy with reinforcement learning, and verify in your simulation that the policy performs the task.

This stage has no target environment: there are no submissions, no official success criteria, no task score and no ranking. You decide from the demonstration and the instruction what performing the task means, write that down as your own verification criteria before you rely on them, and report your own verdict with its evidence. Your records are published on the research website as they are made.

This workspace documents one task. Everything specific to it is in four documents: `TASK.md` (the instruction), `TASK_CONFIG.md` (the hand variant, the scene and the objects), `object/SPECS.md` and `demo/README.md`. Read them first, then the hardware specification and the documents in `demo2sim/`.

## Autonomous Research

- Independently determine how to learn from the demonstration and bridge the gap between the human video and robot execution.
- Freely choose your simulator, reinforcement-learning algorithm, policy architecture, reward, curriculum, domain randomization and training strategy, within the learning rules of `demo2sim/LEARNING.md`.
- Use available compute, research papers, open-source implementations and external tools.

## Research Workflow (mandatory order)

1. **Reference reconstruction.** Reconstruct the demonstration into the outputs of `demo2sim/REFERENCE.md` (default workflow: `demo2sim/RECONSTRUCTION.md`) until `check_reference.py` reports VALID, then record it: `r2s2r-d2s recon` (`demo2sim/RECORDS.md`). A reconstruction that cannot pass a check is recorded as an exception with its failed components; an exception is never a VALID reconstruction.
2. **Verification criteria.** From the demonstration, your reconstruction and `TASK.md`, write the criteria by which you will judge in simulation whether a policy performs the task, and record them: `r2s2r-d2s criteria` (`demo2sim/VERIFICATION.md`).
3. **Training simulation.** Only after step 1 is recorded: build your simulation of the robot and the objects from the public specifications, with the recorded reconstruction as the reference of the skill, and record it: `r2s2r-d2s sim` (`demo2sim/SIMULATION.md`).
4. **Training.** Train the policy with reinforcement learning (`demo2sim/LEARNING.md`). Record every training iteration you evaluate: `r2s2r-d2s iter` (its reward, domain randomization, training curves and rollout videos).
5. **Self-verification.** Evaluate the policy against your recorded criteria in your simulation and record the verdict with its evidence: `r2s2r-d2s verify`.

Then return to step 3 or 4. A better reconstruction may be recorded later as a new version, and the criteria may be revised as a new version with the reason; earlier versions stay in the record. Record your hypotheses, decisions and reflections as you go: `r2s2r-d2s note`.

**Order is audited.** Every record is timestamped when it is received. The research website shows the timeline of your records, and a simulation, training or verification record made before your first reconstruction record is flagged as out of order.

## Documents

Each specification has one authoritative document; the others refer to it. Every path in these documents is relative to the root of this workspace.

| Resource | Description |
|---|---|
| `README.md` | This document |
| `TASK.md` | The task instruction |
| `TASK_CONFIG.md` | The hand variant, the scene and the objects of your task, and your experiment's record ID |
| `TOOLS.md` | The reconstruction tools and models, and the record tool `r2s2r-d2s` |
| `demo/` | Human demonstration video, sampled frames, and `demo/README.md`: the actual files, their time base, and the reconstruction inputs |
| `object/SPECS.md` | The task's objects: geometry, mass, appearance, mechanism where there is one, and their state frames |
| `demo2sim/REFERENCE.md` | The required output contract of the reconstruction, its validation, and the tools and models provided |
| `demo2sim/RECONSTRUCTION.md` | The default reconstruction workflow: a starting point, not a fixed algorithm |
| `demo2sim/SIMULATION.md` | What your training simulation must model and what you record about it |
| `demo2sim/LEARNING.md` | The learning rules (reinforcement learning) and what you record for each training iteration |
| `demo2sim/VERIFICATION.md` | How you write your own verification criteria and report your verdict |
| `demo2sim/RECORDS.md` | The research records, the `r2s2r-d2s` commands and what the website shows |
| `hardware/SPECS.md` | Common Wuji Hand 2.2 specification: floating wrist, controllers, encoders, frames, finger hardware rules (authoritative) |
| `hardware/RIGHT_HAND.md`, `hardware/LEFT_HAND.md` | The two hand variants: model files, joint names and order, axes, limits, actuator parameters (your variant: `TASK_CONFIG.md` section 1) |
| `hardware/` | Robot URDFs and meshes of both variants (`hardware/wuji_hand2_right/`, `hardware/wuji_hand2_left/`) |
| `tools/` | Tool implementations |

## Research Cycle

Reference reconstruction → Verification criteria → Training simulation → Training → Self-verification → Diagnosis → Next iteration

## Rules

- The final policy is trained with reinforcement learning (`demo2sim/LEARNING.md`).
- Build the simulation only after a reconstruction is recorded, and use it as the reference of the skill.
- The manipulation should resemble the demonstration, especially the wrist pose (`TASK.md`).
- Your verification criteria and verdicts are your own claims; state their evidence and limitations, and never present them as an official evaluation.
- Do not access other agents' workspaces or records.
- Do not modify the hardware specification, the object specifications or the provided tools' installed copies; work on your own copies.

**Your objective is to autonomously discover and improve an effective solution, not to follow a predetermined research pipeline.**
