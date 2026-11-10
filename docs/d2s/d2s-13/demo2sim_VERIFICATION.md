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
- **Measurable in simulation.** Each criterion is computed from your simulation's state: object and hand poses, contacts, timing. State the exact quantity and threshold, and, for each stage, the standard measurements that check it (section 3).
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

The gate decides whether a change is kept. It runs your own evaluation, frozen, on fixed starts, checks every stage against the standard measurements, and compares the candidate with the best policy so far. It runs on this machine under another account, and it records its own results.

**Suites**
- A suite is your evaluation program, a fixed set of dev seeds and the ordered stages it reports. Register one with `r2s2r-d2s suite register suite.json` (fields in `demo2sim/RECORDS.md`).
- Every run has one **task suite**: the whole task in its deployment setting, judged by your recorded criteria, with the pass rate they require. It lists the task's **primitives**: the contact-rich motions the task depends on (for example an in-hand reorientation, a regrasp, a turn of a part), the ones a policy is least likely to discover by itself.
- Each primitive has a **feasibility suite** (`kind` `feasibility`, `primitive` its name): starts in which the motion begins, stages that end with the motion done, and a pass rate of at least 0.25. Any controller may pass it (`demo2sim/LEARNING.md` section 2). A primitive is **proven** when the incumbent of a feasibility suite for it meets that suite's pass rate. **The task suite's gates run only after every primitive it lists is proven.**
- Each separately learned skill has its own **skill suite**: its starts, its pass condition and the pass rate you require (`demo2sim/LEARNING.md` section 2).

**What your evaluation writes**
- For every seed it is given, deterministically: `results.json` (which stages were completed, whether the episode stayed within the hardware limits) and the episode's **state log** `states/<seed>.npz`, in the standard format of `/usr/local/lib/r2s2r-v3/tools/d2s_measures.py` (wrist and object states, hand–object, per-finger and object–environment contacts, finger joint positions).
- Its `render_command` renders given seeds into `videos/<seed>/top.mp4`, `left.mp4` and `right.mp4`.
- Registering copies the program's directory and, if you name one, its Python environment. The evaluation runs on these copies without network access and sees nothing else of your workspace, so keep the program and its files in its directory. Later edits to your copies do not change the suite.
- A changed suite is a new version with a reason; its first gate is a new baseline, and earlier gate results are not re-labelled.

**Stages are checked against the standard measurements**
- Every stage of a suite has **predicates** on the measurements of `d2s_measures.py` (meas-2), for example how long an object is held in an opposed grip (thumb and another finger), how far it turns relative to the hand within one such grip, how much of that turning happens while the finger joints are almost still (slipping), how high it rises, its final orientation against a goal you give, how long it rests at the end.
- A stage counts only where your evaluation reports it **and** all its predicates hold. The gate computes the measurements itself from your state logs and reports where they overrule your evaluation.
- Choose predicates that separate the motion from what only looks like it: an in-hand reorientation is a rotation relative to the hand in an opposed grip with little passive rotation, not a rotation of the wrist or a slip. Take the thresholds from your criteria and the measured demonstration.
- The same code measures the target's trials (`measurements.json`, where your task has target rounds), so your stages and the target's numbers are comparable.

**The gate**
- `r2s2r-d2s gate <suite> <candidate> --hypothesis "..." --predicts <stage> --method "..." --observed "..."` runs the frozen evaluation on the suite's dev seeds and compares the candidate, seed by seed, with the suite's **incumbent**: the last accepted candidate. The first gate of a suite version becomes its incumbent.
- **Accepted** when the predicted stage (or `success`) is completed in at least m more episodes than the incumbent, no stage loses more than m episodes, and hardware violations do not increase; m = max(2, 5% of the dev seeds). Otherwise **rejected**, and the incumbent stays.
- **Hardware re-draw:** a candidate rejected only because its hardware violations rose by at most m is evaluated again, together with the incumbent, on as many fresh seeds as the dev set; it is accepted if over both sets its hardware violations do not exceed the incumbent's.
- The gate re-runs two episodes; a candidate whose results do not reproduce is rejected.
- **Failure review:** after each dev gate, the gate renders two episodes that failed at the stage with the largest loss and returns frame montages (top, left and right rows, time left to right) in `failures/` of the gate's output. From the second gate of a suite version on, `--observed` is required: the first failure you saw in a montage that your change addresses (gate, seed, time, what happens), stated as your inference.
- The gate records its result: per-stage counts with 95% Wilson intervals, the funnel (the first failed stage of every episode), where the measurements overruled your evaluation, the change against the incumbent, your hypothesis and observation, and the montages. Its time counts toward your budget.

**The final verdict**
- `r2s2r-d2s gate <suite> <candidate> --final` runs fresh seeds drawn by the gate, once per candidate, for a candidate that has been an incumbent of the current suite version.
- Choose the candidate on dev results only; never select by comparing final results.
- Your `verify` record names this gate (`final_gate`); its `passed` is whether the final gate met your task suite's pass rate.
