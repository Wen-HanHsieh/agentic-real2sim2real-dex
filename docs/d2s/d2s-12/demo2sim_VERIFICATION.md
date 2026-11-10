# Self-Verification (Demo-to-Sim)

There are no official success criteria in this stage. You determine, from the demonstration, your reconstruction and the instruction in `TASK.md`, what performing the task means, and you verify your policy against that in your simulation.

## 1. Writing the Criteria (`r2s2r-d2s criteria`)

Write your criteria before you use them to judge a policy, and record them.

**Judge the goal and the skill in the deployment setting, and keep the criteria strict.** Your criteria have two parts:
- **Goal:** whether the goal of `TASK.md` is achieved from any starting situation its deployment setting describes, not only from the one in the video. State it so it applies to every such situation (for example to however many objects there are and wherever they start).
- **Skill:** whether each object is handled the way the demonstration does it (`TASK.md`, The Demonstration). State it relative to each object and its phase, not to the video's fixed positions, so it applies to every deployment start.

**Quantify the demonstration first.** Analyze the video and measure every quantity your criteria use, for example:
- the duration of each phase (how long an object rests, is held, carried or in flight);
- how far and how high each object moves, and its rotation angles;
- when and with which fingers contact is made and broken;
- the wrist pose in each phase;
- the final pose of each object and how long it stays there.

**Keep the thresholds honest.**
- Write the measured value next to every threshold that comes from it.
- A tolerance needs a stated physical reason; never relax a criterion to let a policy pass.
- If a measured quantity cannot be reached within the hardware specification, prove it with a calculation in a note instead of lowering the threshold silently.

**Every set of criteria is**
- **Derived from evidence.** Each criterion states which part of the demonstration, the instruction or the deployment setting it comes from (video time range, reconstruction quantity, instruction phrase).
- **Measurable in simulation.** Each criterion is computed from your simulation's state: object and hand poses, contacts, timing. State the exact quantity and threshold.
- **Thresholds justified.** Give the reason for every number (measured in the reconstruction, a physical argument, or an explicit assumption).
- **Ordered into stages.** Name the stages in order (for example the subgoals of your decomposition) and what completes each one. Your evaluation reports, for every episode, which stages were completed; the last stage is success.
- **Success and pass rate.** State what success means (all criteria met, in order) and the success rate over many episodes that a policy needs to pass, with the reason for that number.
- **Ambiguities.** List what the demonstration and the instruction leave open and the assumption you made.

**Revisions.**
- You may revise the criteria; record each revision as a new version with the reason.
- A verdict always names the criteria version it was judged against, and earlier verdicts are not re-labelled.

## 2. Reporting a Verdict (`r2s2r-d2s verify`)

| Item | Content |
|---|---|
| Policy | The iteration record it comes from and the checkpoint |
| Final gate | The ID of this policy's final gate (section 3): the verdict's numbers are the gate's |
| Criteria | The criteria version used |
| Episodes | Number of evaluation episodes, their initial conditions and randomization |
| Result | Success rate and, per criterion, the measured values and whether they are met |
| Evidence | Rollout videos (top, left, right) of a successful and of a failed episode where there is one, and the metric files |
| Limitations | What the verification cannot show (for example simulation effects you could not model) |

A verdict is your claim about your simulation; it is shown on the research website as the agent's own result, never as an official evaluation.

## 3. Test Suites and the Gate (`r2s2r-d2s suite`, `r2s2r-d2s gate`)

The gate decides whether a change is kept. It runs your own evaluation, frozen, on fixed starts, and compares the candidate with the best policy so far. It runs on this machine under another account, and it records its own results.

**Suites**
- A suite is your evaluation program, a fixed set of dev seeds and the ordered stages it reports. Register one with `r2s2r-d2s suite register suite.json` (fields in `demo2sim/RECORDS.md`).
- Every run has one **task suite**: the whole task in its deployment setting, judged by your recorded criteria, with the pass rate they require.
- Each separately learned skill has its own **skill suite**: its starts, its pass condition and the pass rate you require (`demo2sim/LEARNING.md` section 2).
- The evaluation program must run any seed it is given, deterministically, and write `results.json`: for every seed, which stages were completed and whether the episode stayed within the hardware limits. Success is the last stage completed without a hardware violation.
- Registering copies the program's directory and, if you name one, its Python environment. The evaluation runs on these copies without network access and sees nothing else of your workspace, so keep the program and its files in its directory. Later edits to your copies do not change the suite.
- A changed suite is a new version with a reason; its first gate is a new baseline, and earlier gate results are not re-labelled.

**The gate**
- `r2s2r-d2s gate <suite> <candidate> --hypothesis "..." --predicts <stage> --method "..."` runs the frozen evaluation on the suite's dev seeds and compares the candidate, seed by seed, with the suite's **incumbent**: the last accepted candidate. The first gate of a suite version becomes its incumbent.
- **Accepted** when the predicted stage (or `success`) is completed in at least m more episodes than the incumbent, no stage loses more than m episodes, and hardware violations do not increase; m = max(2, 5% of the dev seeds). Otherwise **rejected**, and the incumbent stays.
- The gate re-runs two episodes; a candidate whose results do not reproduce is rejected.
- The gate records its result: per-stage counts with 95% Wilson intervals, the funnel (the first failed stage of every episode), the change against the incumbent, and your hypothesis. Its time counts toward your budget.

**The final verdict**
- `r2s2r-d2s gate <suite> <candidate> --final` runs fresh seeds drawn by the gate, once per candidate, for a candidate that has been an incumbent of the current suite version.
- Choose the candidate on dev results only; never select by comparing final results.
- Your `verify` record names this gate (`final_gate`); its `passed` is whether the final gate met your task suite's pass rate.
