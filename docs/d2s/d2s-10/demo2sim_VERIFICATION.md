# Self-Verification (Demo-to-Sim)

There are no official success criteria in this stage. You determine, from the demonstration, your reconstruction and the instruction in `TASK.md`, what performing the task means, and you verify your policy against that in your simulation.

## 1. Writing the Criteria (`r2s2r-d2s criteria`)

Write your criteria before you use them to judge a policy, and record them.

**Judge the goal in the deployment setting, and keep the criteria strict.** Your criteria decide whether the goal of `TASK.md` is achieved from any starting situation its deployment setting describes, not only from the one in the video, so state them in a form that applies to every such situation (for example to however many objects there are and wherever they start). Use the video to learn what achieving the goal looks like, and measure what it shows: for example the final pose of each object, how long it stays there, how high or how far an object moves. Write the measured value next to every threshold that comes from it. A tolerance needs a stated physical reason; never relax a criterion to let a policy pass. If a measured quantity cannot be reached within the hardware specification, prove it with a calculation in a note instead of lowering the threshold silently.

- **Derived from evidence.** Each criterion states which part of the demonstration, the instruction or the deployment setting it comes from (video time range, reconstruction quantity, instruction phrase).
- **Measurable in simulation.** Each criterion is computed from your simulation's state: object and hand poses, contacts, timing. State the exact quantity and threshold.
- **Thresholds justified.** Give the reason for every number (measured in the reconstruction, a physical argument, or an explicit assumption).
- **Ordered.** Where the task has stages, define them in order and say what completes each one.
- **Success.** State what success means (all criteria met, in order) and, if useful, a progress measure.
- **Ambiguities.** List what the demonstration and the instruction leave open and the assumption you made.

**Revisions.** You may revise the criteria; record each revision as a new version with the reason. A verdict always names the criteria version it was judged against, and earlier verdicts are not re-labelled.

## 2. Reporting a Verdict (`r2s2r-d2s verify`)

| Item | Content |
|---|---|
| Policy | The iteration record it comes from and the checkpoint |
| Criteria | The criteria version used |
| Episodes | Number of evaluation episodes, their initial conditions and randomization |
| Result | Success rate and, per criterion, the measured values and whether they are met |
| Evidence | Rollout videos (top, left, right) of a successful and of a failed episode where there is one, and the metric files |
| Limitations | What the verification cannot show (for example simulation effects you could not model) |

A verdict is your claim about your simulation; it is shown on the research website as the agent's own result, never as an official evaluation.
