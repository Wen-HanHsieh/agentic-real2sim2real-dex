# Self-Verification (Demo-to-Sim)

There are no official success criteria in this stage. You determine, from the demonstration, your reconstruction and the instruction in `TASK.md`, what performing the task means, and you verify your policy against that in your simulation.

## 1. Writing the Criteria (`r2s2r-d2s criteria`)

Write your criteria before you use them to judge a policy, and record them.

- **Derived from evidence.** Each criterion states which part of the demonstration or the instruction it comes from (video time range, reconstruction quantity, instruction phrase).
- **Measurable in simulation.** Each criterion is computed from your simulation's state: object and hand poses, contacts, timing. State the exact quantity and threshold.
- **Thresholds justified.** Give the reason for every number (measured in the reconstruction, a physical argument, or an explicit assumption).
- **Ordered.** Where the task has stages, define them in order and say what completes each one.
- **Demonstration similarity.** Include how closely the manipulation must resemble the demonstration, especially the wrist pose (`TASK.md`).
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
