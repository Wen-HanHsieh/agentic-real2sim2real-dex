# Target Environment: Success Criteria and Task Progress Rubric

**Task:** Toss 1 → Catch 1 → Toss 2 → Catch 2 → Hold

The target environment evaluates each rollout against these criteria. The total score ranges from **0 to 1.0**.

- **Episode:** 10 s (5,000 control steps at 500 Hz).
- **Stage dependency:** Later-stage progress is credited only after the preceding stage is fully completed.
- **Rubric version:** `rubric-1.5` (2026-10-28: the first rubric version of this task).
- **Official success:** the official evaluation reports `status: success`. This requires a score of 1.0 even when every unobservable moment counts against the policy, hardware compliance (`hardware/SPECS.md` section 6), and a valid run (all 5,000 steps executed without a policy failure).

**Definitions.** A **release** is the moment the ball loses hand contact; it starts a **flight** if the ball then touches nothing (hand or environment) for at least 0.10 s. The **apex** is the highest point of the flight above the release height. A flight **lands on the hand** if the first contact after it is hand contact. **Retention** after a landing is the time the ball stays with the hand: it touches nothing else, and contact interruptions are shorter than 0.10 s (a longer interruption is the next release). Flights are counted in order; hops and regrasps shorter than 0.10 s are not releases. Success requires 2 complete toss-and-catch cycles (Toss 1 to Catch 2) and the final hold.

## 1. Toss 1 (0–0.25)

| Score | Milestone |
|---|---|
| 0.25 × (apex / 5 cm) | Partial credit, linear in the apex of the first flight |
| 0.25 | A flight with at least 0.10 s of contact-free flight and an apex at least 5 cm above the release point |

## 2. Catch 1 (0–0.25)

| Score | Milestone |
|---|---|
| 0.25 × (retention / 0.30 s) | Partial credit, linear in the retention time after the Toss 1 flight landed on the hand |
| 0.25 | The Toss 1 flight lands on the hand and the ball is retained for at least 0.30 s |

## 3. Toss 2 (0–0.20)

| Score | Milestone |
|---|---|
| 0.20 × (apex / 5 cm) | Partial credit, linear in the apex of the next flight after Catch 1 |
| 0.20 | A second flight with at least 0.10 s of contact-free flight and an apex at least 5 cm above its release point |

## 4. Catch 2 (0–0.20)

| Score | Milestone |
|---|---|
| 0.20 × (retention / 0.30 s) | Partial credit, linear in the retention time after the Toss 2 flight landed on the hand |
| 0.20 | The Toss 2 flight lands on the hand and the ball is retained for at least 0.30 s |

## 5. Hold (0–0.10)

| Score | Milestone |
|---|---|
| 0.10 × (contact fraction) | Partial credit: the fraction of the final 1.0 s with hand contact |
| 0.10 | Hand contact throughout the final 1.0 s (the ball never touched the environment or left the workspace) |

**Retention:** Every milestone requires the ball retained up to that moment: it never touches the environment, and its centre stays within 25 cm horizontally of its step-0 position. Flights released after the ball first touched the environment or left the workspace score nothing, and the Hold stage then scores 0.

**Scoring:** Each stage scores its partial credit until its milestone is complete and its full weight afterwards. A contact gap shorter than 0.10 s is a bobble, not a release; a flight that lands on the environment ends the cycle without a catch. The ball's rotation is not measured and does not count.

## 6. Sensor-Based Evaluation

The target environment scores these criteria from sensor-observable evidence: cameras, the robot's joint log, and the public robot and object specifications. Measurements are estimates, not ground truth. Where the evidence cannot decide a milestone, the result is reported as uncertain, and the overall status may be `unknown` instead of `success` or `failure`. See `FEEDBACK.md` for results, measurements, and uncertainty.

## 7. Research Freedom

These criteria define the **official target evaluation**, not a required training reward. The target score (`score`, also reported as `progress` and `reward` in `sensor_report.json`) is an evaluation metric. You may design your own training rewards, intermediate objectives, curricula, optimization methods, simulators, and policy architectures; your training reward need not resemble the target score. Your own metrics do not replace official results.
