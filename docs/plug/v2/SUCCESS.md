# Target Environment: Success Criteria and Task Progress Rubric

**Task:** Reorient → Upright → Hold

The target environment evaluates each rollout against these criteria. The total score ranges from **0 to 1.0**.

- **Episode:** 12 s (6,000 control steps at 500 Hz).
- **Stage dependency:** Later-stage progress is credited only after the preceding stage is fully completed.
- **Rubric version:** `rubric-1.5` (2026-10-28: the first rubric version of this task).
- **Official success:** the official evaluation reports `status: success`. This requires a score of 1.0 even when every unobservable moment counts against the policy, hardware compliance (`hardware/SPECS.md` section 6), and a valid run (all 6,000 steps executed without a policy failure).

**Angle** is the angle between the plug's blade axis (body centre → blades, `object/SPECS.md`) and world +Z: 0° is upright, 90° is lying on a side. The plug is **upright** while the angle is at most 20°. The angle at step 0 is the start angle (about 90°).

## 1. Reorient (0–0.40)

| Score | Milestone |
|---|---|
| 0.40 × (start angle − smallest angle reached) / (start angle − 20°) | Partial credit, linear in the best reduction of the angle from the start angle down to the 20° threshold |
| 0.40 | The angle reaches 20° or less |

## 2. Upright (0–0.35)

| Score | Milestone |
|---|---|
| 0.35 × (longest upright run / 0.2 s) | Partial credit, linear in the longest continuous time the plug stays upright |
| 0.35 | The plug stays upright for at least 0.2 s continuously |

## 3. Hold (0–0.25)

| Score | Milestone |
|---|---|
| 0.25 × (final run / 1.0 s) | Partial credit, linear in the length of the continuous run ending at the final step in which the plug is upright, its angular speed is below 0.5 rad/s, and it touches the hand and nothing else |
| 0.25 | That run lasts at least 1.0 s: throughout the final 1.0 s the plug is upright, its angular speed is below 0.5 rad/s, and it touches the hand at every step |

**Retention:** Every milestone requires the plug retained up to that moment: it touches nothing but the hand, contact interruptions are shorter than 0.10 s, its centre stays within 8 cm horizontally of its step-0 position and never drops more than 3 cm below it. Progress counts only until retention is first lost, after which the Hold stage scores 0.

**Scoring:** Each stage scores its partial credit until its milestone is complete and its full weight afterwards; the Hold stage requires the Upright stage complete. Rotation of the plug about its own blade axis is free and does not count. Insertion is not required.

## 4. Sensor-Based Evaluation

The target environment scores these criteria from sensor-observable evidence: cameras, the robot's joint log, and the public robot and object specifications. Measurements are estimates, not ground truth. Where the evidence cannot decide a milestone, the result is reported as uncertain, and the overall status may be `unknown` instead of `success` or `failure`. See `FEEDBACK.md` for results, measurements, and uncertainty.

## 5. Research Freedom

These criteria define the **official target evaluation**, not a required training reward. The target score (`score`, also reported as `progress` and `reward` in `sensor_report.json`) is an evaluation metric. You may design your own training rewards, intermediate objectives, curricula, optimization methods, simulators, and policy architectures; your training reward need not resemble the target score. Your own metrics do not replace official results.
