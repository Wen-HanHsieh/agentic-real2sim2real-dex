# Target Environment: Success Criteria and Task Progress Rubric

**Task:** Spin-up → Sustain → Hold

The target environment evaluates each rollout against these criteria. The total score ranges from **0 to 1.0**.

- **Episode:** 12 s (6,000 control steps at 500 Hz).
- **Stage dependency:** Later-stage progress is credited only after the preceding stage is fully completed.
- **Official success:** the official evaluation reports `status: success`. This requires a score of 1.0 even when every unobservable moment counts against the policy, hardware compliance (`hardware/SPECS.md` section 6), and a valid run (all 6,000 steps executed without a policy failure).

**Rotation** is the signed cumulative change of the pen's heading (the direction from its back end to its red tip, projected on the horizontal plane) about world +Z, measured from step 0. Counterclockwise from above is positive; clockwise motion subtracts. Rotation of the pen about its own long axis does not change the heading and does not count.

## 1. Spin-up (0–0.30)

| Score | Milestone |
|---|---|
| 0.10 | Net rotation of at least 90° |
| 0.20 | Net rotation of at least 180° |
| 0.30 | First revolution: net rotation reaches +360° within 3.0 s of step 0 |

## 2. Sustain (0–0.45)

| Score | Milestone |
|---|---|
| 0.15 | Net rotation of at least +540° |
| 0.25 | Second revolution: +720° reached within 3.0 s of the first |
| 0.35 | Net rotation of at least +900° |
| 0.45 | Third revolution: +1080° reached within 3.0 s of the second |

## 3. Hold (0–0.25)

| Score | Milestone |
|---|---|
| 0.10 | After +1080°, the pen touches the hand with centre speed below 0.02 m/s and angular speed below 0.5 rad/s for at least 0.25 s |
| 0.15 | The same throughout the final 0.5 s |
| 0.25 | Throughout the final 1.0 s: net rotation of at least +1080° (the third revolution is never undone), centre speed below 0.02 m/s, angular speed below 0.5 rad/s, and hand contact at every step |

**Retention:** Every milestone requires the pen retained up to that moment: it touches nothing but the hand, contact interruptions are shorter than 0.10 s, its centre stays within 8 cm horizontally of its step-0 position and never drops more than 3 cm below it, and its long axis never tilts more than 45° from horizontal.

**Scoring:** Each stage scores 0 until its first milestone and otherwise its highest satisfied milestone. Back-and-forth motion nets to zero; a revolution that takes longer than 3.0 s after the previous one does not count toward the next milestone.

## 4. Sensor-Based Evaluation

The target environment scores these criteria from sensor-observable evidence: cameras, the robot's joint log, and the public robot and object specifications. Measurements are estimates, not ground truth. Where the evidence cannot decide a milestone, the result is reported as uncertain, and the overall status may be `unknown` instead of `success` or `failure`. See `FEEDBACK.md` for results, measurements, and uncertainty.

## 5. Research Freedom

These criteria define the **official target evaluation**, not a required training reward. You may design your own training rewards, intermediate objectives, curricula, optimization methods, simulators, and policy architectures. Your own metrics do not replace official results.
