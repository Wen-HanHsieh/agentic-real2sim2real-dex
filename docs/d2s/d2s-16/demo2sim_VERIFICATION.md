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
- Every run has one **task suite**: the whole task in its deployment setting, judged by your recorded criteria, with the pass rate they require.
- **The chain.** The task suite lists its `chain`: every link from the deployment start to the goal, in order. Every link is a **primitive**:
  - an **entry link** from the deployment start to where the first motion starts (for example a capture of the object, or a settle into a grip);
  - each contact-rich **motion** the task depends on (for example an in-hand reorientation, a regrasp, a turn of a part), the ones a policy is least likely to discover by itself;
  - a **transition** wherever one link ends in a state the next one does not start from.
  - Each link names the links it `follows`: `start` (the deployment start) or links listed before it. Alternatives (for example one of several requested moves) are links that follow the same link.
  - A chain with a gap (a link that follows neither `start` nor a link listed before it) is refused.
- Each link has a **feasibility suite** (`kind` `feasibility`, `primitive` its name, `follows` as in the chain): stages that end with the link done, and a pass rate of at least 0.25. Any controller may pass it (`demo2sim/LEARNING.md` section 2). A link is **proven** when the incumbent of such a suite meets that suite's pass rate. **The task suite's gates run only after every link of its chain is proven.**
- **Handoff starts: each link is tested from the states the links before it actually end in.**
  - A suite of a link gives `handoff_fraction` (at least 0.5): the share of its starts the gate takes from the **handoff states** of the links it follows. The rest of its starts are yours to choose (for example prepared grips to learn from).
  - For a link that follows `start`, the handoff states are the deployment starts of your task suite that passed its start check (below). For any other link, they are the end states of the successful episodes of the best incumbent of each link it follows (mastered before proven), counting only episodes that themselves started from handoff states.
  - Registering freezes the handoff states into the suite version, so every gate of that version uses the same ones. When a link before it improves, register a new version to take its new end states.
  - The gate lists them in the seeds file: `{"seeds": [...], "handoff": {"<seed>": "<file>.npz"}}`. Your evaluation starts each listed seed from its file (one row of a state log, `d2s_measures.py`) and may then randomize it as it does its other starts.
  - The gate checks the first row of each such episode against its file: object pose relative to the wrist within 5 mm and 5°, wrist orientation within 5°, finger joints within 0.05 rad. A gate whose episodes do not start from their handoff states is an error.
  - Keys you add to your state log travel with the handoff state (for example your simulator's full state per row, `sim_state`, or the state of an articulated object's parts), so the next link can restart exactly.
  - A suite of a link registers only once each link it follows has an incumbent with at least 8 such successful episodes: prove the chain from its start.
- **What the primitive is** comes from three sources together, in the suite's `primitive_spec` (fields in `demo2sim/RECORDS.md`): the interval of the demonstration video where it happens and what you see there; the motion measured in your reconstruction (the object's rotation relative to the hand over that interval, about which axis); the condition of `TASK.md` it serves; and where and why the robot must deviate. Registering measures your reference log and refuses a spec whose angle or axis does not match it. Where the reconstruction cannot show the motion (for example a part hidden in the hand), say why; a reorientation always needs it.
- A **skill suite that names a primitive** (`primitive`, with the same `primitive_spec`, `follows` and `handoff_fraction`) gates a deployable policy for the link. The link is **mastered** when that suite's incumbent meets a pass rate of at least 0.8.
- **Primitives first:** during the first 60% of your budget, the task suite gates only when every link of its chain is mastered; after that, proven is enough.
- Only suites whose `follows` match the current chain count (for example, after a new task suite version inserts a transition, the suites of the link after it no longer do). `r2s2r-d2s status` shows the chain, which links are unproven or unmastered, and why a suite does not count.
- Each separately learned skill has its own **skill suite**: its starts, its pass condition and the pass rate you require (`demo2sim/LEARNING.md` section 2).

**Start check: the starts must be physically possible**
- When you register the task suite, and a suite of a link that follows `start`, the gate checks that every object starts at rest and supported, not already falling or out of the hand.
- `start_check` in `suite.json`:
  - `hold_policy`: a candidate directory your evaluation runs like any policy, whose actions keep the hand at its start pose;
  - `support`: what holds each object at the start: `hand`, or `environment` (a table or another fixed support) where the deployment in `TASK.md` places it there; or one of them per object name.
- The gate runs the suite's `command` with the hold policy on 64 fresh seeds and measures the first 1 s of every episode (`d2s_measures.py`, `start_check`):
  - the hand stays at its start pose (wrist within 5 mm and 3°, finger joints within 0.15 rad);
  - every object moves at most 2 cm and 20° from its first-row pose, and slower than 0.05 m/s and 0.5 rad/s over the last 0.2 s;
  - at 1 s, every object touches the hand and not the environment (`hand`), or touches the environment (`environment`; the hand may touch it too).
- Registration is refused unless at least 95% of the starts pass. The per-start numbers are in `start_check.json` in the request's output directory.
- A start that fails is not a start your deployment can have: change the hand's start pose or where the object starts, not the support you declare.
- Check your starts before you register: run your hold policy and `python d2s_measures.py start <states/seed.npz> hand` (or `environment`).
- The task suite's passing starts become the handoff states of the links that follow `start`.

**What your evaluation writes**
- For every seed it is given (from its handoff state where the seeds file lists one), deterministically: `results.json` (which stages were completed, whether the episode stayed within the hardware limits) and the episode's **state log** `states/<seed>.npz`, in the standard format of `/usr/local/lib/r2s2r-v3/tools/d2s_measures.py` (wrist and object states, hand–object, per-finger and object–environment contacts, finger joint positions).
- Its `render_command` renders given seeds into `videos/<seed>/top.mp4`, `left.mp4` and `right.mp4`.
- Registering copies the program's directory and, if you name one, its Python environment. The evaluation runs on these copies without network access and sees nothing else of your workspace, so keep the program and its files in its directory. Later edits to your copies do not change the suite.
- A changed suite is a new version with a reason; its first gate is a new baseline, and earlier gate results are not re-labelled. Versions 1 and 2 register at any time; from version 3 on, a new version needs 60 minutes since the previous one. Improve the policy against the current version rather than changing the suite.

**Stages are checked against the standard measurements**
- Every stage of a suite has **predicates** on the measurements of `d2s_measures.py` (meas-2), for example how long an object is held in an opposed grip (thumb and another finger), how far it turns relative to the hand within one such grip, how much of that turning happens while the finger joints are almost still (slipping), how high it rises, its final orientation against a goal you give, how long it rests at the end.
- A stage counts only where your evaluation reports it **and** all its predicates hold. The gate computes the measurements itself from your state logs and reports where they overrule your evaluation.
- Choose predicates that separate the motion from what only looks like it: an in-hand reorientation is a rotation relative to the hand in an opposed grip with little passive rotation, not a rotation of the wrist or a slip. Take the thresholds from your criteria and the measured demonstration.
- **The gate adds its own predicates** to the last stage of a suite with a `primitive_spec`: the object touches nothing but the hand (unless `support` is `environment`); for a `reorientation`, it turns relative to the hand by at least 75% of `angle_deg` within one opposed grip, at most max(15°, 35% of `angle_deg`) of that rotation is passive, and its final orientation relative to the hand is within 25° of the episode's goal, which your state log gives (`goal_rel_orientation`).
- The same code measures the target's trials (`measurements.json`, where your task has target rounds), so your stages and the target's numbers are comparable.

**The gate**
- `r2s2r-d2s gate <suite> <candidate> --hypothesis "..." --predicts <stage> --method "..." --observed "..."` runs the frozen evaluation on the suite's dev seeds and compares the candidate, seed by seed, with the suite's **incumbent**: the last accepted candidate. The first gate of a suite version becomes its incumbent.
- **Accepted** when the predicted stage (or `success`) is completed in at least m more episodes than the incumbent, no stage loses more than m episodes, and hardware violations do not increase; m = max(2, 5% of the dev seeds). Otherwise **rejected**, and the incumbent stays.
- **Hardware re-draw:** a candidate rejected only because its hardware violations rose by at most m is evaluated again, together with the incumbent, on as many fresh seeds as the dev set; it is accepted if over both sets its hardware violations do not exceed the incumbent's.
- The gate re-runs two episodes; a candidate whose results do not reproduce is rejected.
- **Failure review:** after each dev gate, the gate renders two episodes that failed at the stage with the largest loss and returns frame montages (top, left and right rows, time left to right) in `failures/` of the gate's output; for a suite with a `primitive_spec`, the first row shows the demonstration over its `demo_interval_s`, so you can compare what your policy does with what the human hand does. From the second gate of a suite version on, `--observed` is required: the first failure you saw in a montage that your change addresses (gate, seed, time, what happens), stated as your inference.
- **Failure analysis** (`TOOLS.md` section 3): treat it as a hypothesis. Confirm its first observable failure yourself in the montages and the gate's numbers before you act on it. Your `--observed` stays your own observation; if you agree with the analysis, say what you checked. If you act on its proposed change, put it in `--hypothesis` and predict the stage or number it names. The gate decides on the measurements alone.
- The gate records its result: per-stage counts with 95% Wilson intervals, the funnel (the first failed stage of every episode), where the measurements overruled your evaluation, the change against the incumbent, your hypothesis and observation, and the montages. Its time counts toward your budget.

**The final verdict**
- `r2s2r-d2s gate <suite> <candidate> --final` runs fresh seeds drawn by the gate, once per candidate, for a candidate that has been an incumbent of the current suite version.
- Choose the candidate on dev results only; never select by comparing final results.
- Your `verify` record names this gate (`final_gate`); its `passed` is whether the final gate met your task suite's pass rate.
