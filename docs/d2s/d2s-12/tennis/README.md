# Wuji Hand 2: Learning a Dexterous Skill from a Human Demonstration (Demo-to-Sim)

Your goal is to learn the dexterous manipulation skill shown in a human demonstration video, so that the Wuji Hand 2 on a free-floating wrist achieves the goal of `TASK.md` in its deployment setting. From the video (`demo/`) and the task instruction (`TASK.md`) you reconstruct the demonstration, build a training simulation of the robot and the task's objects, train a policy with reinforcement learning, and verify in your simulation that the policy achieves the goal in the deployment setting.

There are no official success criteria, no task score and no ranking. You decide from the demonstration and the instruction what achieving the goal means, write that down as your own verification criteria before you rely on them, and report your own verdict with its evidence. Where your task has target rounds (`TASK_CONFIG.md` section 1), you also deliver your verified policy to a target and improve it from the target's feedback (`DELIVERY.md`); otherwise there is no target environment and no submission. Your records are published on the research website as they are made.

This workspace documents one task. Everything specific to it is in three documents: `TASK.md` (the instruction), `TASK_CONFIG.md` (the hand variant, the scene and the objects) and `demo/README.md`. Read them first, then the hardware specification and the documents in `demo2sim/`.

## Autonomous Research

- Independently determine how to learn from the demonstration and bridge the gap between the human video and robot execution.
- Freely choose your simulator, reinforcement-learning algorithm, policy architecture, reward, curriculum, domain randomization and training strategy, within the learning rules of `demo2sim/LEARNING.md`.
- Use available compute, research papers, open-source implementations and external tools.

## Research Workflow (mandatory order)

1. **Reference reconstruction.** Reconstruct the demonstration into the outputs of `demo2sim/REFERENCE.md` (default workflow: `demo2sim/RECONSTRUCTION.md`) until `check_reference.py` reports VALID, then record it: `r2s2r-d2s recon` (`demo2sim/RECORDS.md`). Stage 1 lasts 60 minutes (`demo2sim/RECONSTRUCTION.md`). A reconstruction that cannot pass a check is recorded as an exception with its failed components; an exception is never a VALID reconstruction.
2. **Verification criteria.** From the demonstration, your reconstruction and `TASK.md`, write the criteria by which you will judge in simulation whether a policy performs the task, and record them: `r2s2r-d2s criteria` (`demo2sim/VERIFICATION.md`).
3. **Training simulation.** Only after the 60 minutes of step 1 are over: build your simulation of the robot and the objects from the public specifications, with the recorded reconstruction as the reference of the skill, and record it: `r2s2r-d2s sim` (`demo2sim/SIMULATION.md`). Then register your **task suite**: your evaluation of your criteria in this simulation, frozen on fixed starts (`r2s2r-d2s suite register`, `demo2sim/VERIFICATION.md` section 3).
4. **Training.** Train the policy with reinforcement learning (`demo2sim/LEARNING.md`). Record every training iteration you evaluate: `r2s2r-d2s iter` (its reward, domain randomization, training curves and rollout videos). Every change you keep goes through a gate (`r2s2r-d2s gate`, `demo2sim/LEARNING.md` sections 2 and 3).
5. **Self-verification.** Run the final gate of the policy you choose (`r2s2r-d2s gate <suite> <candidate> --final`) and record your verdict with its evidence: `r2s2r-d2s verify`.
6. **Delivery (tasks with target rounds).** Deliver your task suite's incumbent as soon as it passes `validate`, even when it often fails: `r2s2r-d2s submit` (`DELIVERY.md`). Judge every trial of the round from the feedback, record your judgment, improve your simulation and policy, and deliver again.

Then return to step 3 or 4. A better reconstruction may be recorded later as a new version, and the criteria may be revised as a new version with the reason; earlier versions stay in the record. Record your hypotheses, decisions and reflections as you go: `r2s2r-d2s note`.

**Order is audited.** Every record is timestamped when it is received. The research website shows the timeline of your records, and a simulation, training or verification record made before your first reconstruction record is flagged as out of order.

## Time Budget and Stopping Rule

- **Your time budget** is in `TASK_CONFIG.md` section 1, counted from the start of your run. `r2s2r-d2s time` shows the time used and left; its numbers are authoritative. Write the start time in your first note.
- **Check `r2s2r-d2s status` first**, after a restart and whenever you are unsure what to do next. It shows your time, suites, incumbents, skill library and deliveries, and a next step computed from your records and the gate. Counts come from `status`, not from your notes.
- **Keep `PROGRESS.md` current** (its headings are fixed: Current step, Confirmed results, Failed approaches and why, Working parameters, Skill library, Budget plan, Next step). After a restart or a context compaction, run `r2s2r-d2s status`, re-read `PROGRESS.md` and continue from the live state.
- **Tasks without target rounds:** stop when your own verification passes (a `r2s2r-d2s verify` record that names a final gate meeting your pass rate), when the time is used, or when the operator tells you to stop.
- **Tasks with target rounds:** the rules of `DELIVERY.md` section 7 apply.
- **When your time is up**, stop working: run the final gate of your best policy if it has none, record your final verification (`r2s2r-d2s verify`) and a final reflection (`r2s2r-d2s note --kind reflection`) with what worked, what failed and what you would try next, then end. Leave enough time before the limit to record them.
- **A failure is not a reason to stop.** When a gate rejects a change or a verification fails, diagnose why, record it (`r2s2r-d2s note`), change your approach (`demo2sim/LEARNING.md` section 3) and continue.
- Do not end your turn to report intermediate results or to ask for confirmation: your records are the report. Keep working until one of the stopping conditions holds.

## Documents

Each specification has one authoritative document; the others refer to it. Every path in these documents is relative to the root of this workspace.

| Resource | Description |
|---|---|
| `README.md` | This document |
| `TASK.md` | The task instruction |
| `PROGRESS.md` | Your current state, kept by you under fixed headings (Time Budget above) |
| `TASK_CONFIG.md` | The hand variant, the scene and the objects of your task, and your experiment's record ID |
| `DELIVERY.md` | What you deliver to the target, how a round runs, what you get back, and the rounds' time rules |
| `TOOLS.md` | The reconstruction tools and models, and the record tool `r2s2r-d2s` |
| `demo/` | Human demonstration video, sampled frames, and `demo/README.md`: the actual files, their time base, and the reconstruction inputs |
| `demo2sim/REFERENCE.md` | The required output contract of the reconstruction, its validation, and the tools and models provided |
| `demo2sim/RECONSTRUCTION.md` | The default reconstruction workflow: a starting point, not a fixed algorithm |
| `demo2sim/SIMULATION.md` | What your training simulation must model and what you record about it |
| `demo2sim/LEARNING.md` | The learning rules (reinforcement learning), building the policy from skills, changes and when to switch methods, and what you record for each training iteration |
| `demo2sim/VERIFICATION.md` | How you write your own verification criteria, your test suites and the gate, and how you report your verdict |
| `demo2sim/RECORDS.md` | The research records, the `r2s2r-d2s` commands and what the website shows |
| `hardware/SPECS.md` | Common Wuji Hand 2.2 specification: floating wrist, controllers, encoders, frames, finger hardware rules (authoritative) |
| `hardware/RIGHT_HAND.md` | Your hand variant (right): model files, joint names and order, axes, limits, actuator parameters |
| `hardware/` | Robot URDFs and meshes of both variants (`hardware/wuji_hand2_right/`, `hardware/wuji_hand2_left/`) |
| `tools/` | Tool implementations |

## Research Cycle

Reference reconstruction → Verification criteria → Training simulation and task suite → Training, each kept change through a gate → Final gate and self-verification → Diagnosis → Next iteration

## Rules

- The final policy is trained with reinforcement learning (`demo2sim/LEARNING.md`).
- Your verification criteria and verdicts are your own claims; state their evidence and limitations, and never present them as an official evaluation.
- Do not access other agents' workspaces or records.
- Work independently of earlier runs of this research: do not look at their records on the research website, in its source repository or in any other copy.
- Do not modify the hardware specification or the provided tools' installed copies; work on your own copies.

**Your objective is to autonomously discover and improve an effective solution, not to follow a predetermined research pipeline.**
