# Target Environment: Success Criteria and Task Progress Rubric

**Task:** 5 cm Toss → Catch → Spin → Hold

The target environment evaluates each rollout against these criteria. The total score ranges from **0 to 1.0**.

- **Episode:** 10 s (5,000 control steps at 500 Hz).
- **Stage dependency:** Later-stage progress is credited only after the preceding stage is fully completed.
- **Rubric version:** `rubric-1.4` (since 2026-10-26: toss apex at least 5 cm instead of 20 cm; nothing else changed). Earlier submissions keep their `rubric-1.3` results.
- **Official success:** the official evaluation reports `status: success`. This requires a score of 1.0 even when every unobservable moment counts against the policy, hardware compliance (`hardware/SPECS.md` section 6), and a valid run (all 5,000 steps executed without a policy failure).

## 1. Toss (0–0.25)

| Score | Milestone |
|---|---|
| 0.10 | Upward release with at least 0.05 s of contact-free flight |
| 0.25 | Upward release with at least 0.10 s of contact-free flight, an apex at least 5 cm above the release point, and a physically consistent free-fall arc |

## 2. Catch (0–0.30)

| Score | Milestone |
|---|---|
| 0.10 | The hand recontacts the ball before it touches anything else |
| 0.30 | The ball lands on the hand, touches nothing else afterwards, and stays below 0.02 m/s for at least 0.10 s while touching the hand; the first such moment is `t_rest` |

## 3. Spin (0–0.30)

After `t_rest`, the ball's signed net rotation about the **world +Z axis** is measured (counterclockwise from above is positive).

| Score | Milestone |
|---|---|
| 0.10 | At least 90° |
| 0.15 | At least 180° |
| 0.20 | At least 360° |
| 0.25 | At least 540° |
| 0.30 | At least 720° |

Every spin milestone requires contact gaps shorter than 0.10 s and the ball centre within 3 cm of its position at `t_rest`.

## 4. Hold (0–0.15)

| Score | Milestone |
|---|---|
| 0.05 | After the spin, hand contact and speed below 0.02 m/s for at least 0.10 s |
| 0.10 | Throughout the final 0.15 s: at least 720° net rotation, hand contact, and speed below 0.02 m/s |
| 0.15 | Throughout the final 0.30 s: at least 720° net rotation and speed below 0.02 m/s; hand contact at the final step |

**Scoring:** Each stage scores 0 until its first milestone and otherwise its highest satisfied milestone. Hops and regrasps before the qualifying toss are allowed.

## 5. Sensor-Based Evaluation

The target environment scores these criteria from sensor-observable evidence: cameras, the robot's joint log, and the public robot and object specifications. Measurements are estimates, not ground truth. Where the evidence cannot decide a milestone, the result is reported as uncertain, and the overall status may be `unknown` instead of `success` or `failure`. See `FEEDBACK.md` for results, measurements, and uncertainty.

## 6. Research Freedom

These criteria define the **official target evaluation**, not a required training reward. The target score (`score`, also reported as `progress` and `reward` in `sensor_report.json`) is an evaluation metric. You may design your own training rewards, intermediate objectives, curricula, optimization methods, simulators, and policy architectures; your training reward need not resemble the target score. Your own metrics do not replace official results.
