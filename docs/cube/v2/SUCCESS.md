# Target Environment: Success Criteria and Task Progress Rubric

**Task:** First turn → Turning → Solving → Hold

The target environment evaluates each rollout against these criteria. The total score ranges from **0 to 1.0**.

- **Episode:** 40 s (20,000 control steps at 500 Hz).
- **Stage dependency:** Stage scores are additive; see **Scoring** below for how the stages depend on each other.
- **Official success:** the official evaluation reports `status: success`. This requires a score of 1.0 even when every unobservable moment counts against the policy, hardware compliance (`hardware/SPECS.md` section 6), and a valid run (all 20,000 steps executed without a policy failure).

**Definitions.** A layer turn is complete when the turned layer is aligned again (within about 10°) a quarter or half turn from where it started. Distance to solved is the smallest number of face turns that solves the cube (a 180° turn counts as one); the start state is 3 turns from solved, and the policy receives the scramble in every observation (`CONTRACT.md`). Solved means every face shows one colour and every layer is aligned: any two cubies' orientations differ by less than 10°, whatever the whole cube's orientation.

## 1. First turn (0–0.15)

| Score | Milestone |
|---|---|
| 0.05 | A layer rotated at least 45° about its axis |
| 0.15 | One complete layer turn |

## 2. Turning (0–0.15)

| Score | Milestone |
|---|---|
| 0.05 | Two complete layer turns |
| 0.15 | Three or more complete layer turns |

## 3. Solving (0–0.50)

| Score | Milestone |
|---|---|
| 0.15 | Distance to solved reaches 2 |
| 0.30 | Distance to solved reaches 1 |
| 0.50 | The cube is solved at some moment |

## 4. Hold (0–0.20)

| Score | Milestone |
|---|---|
| 0.10 | Solved and touching the hand at the final step |
| 0.20 | Solved throughout the final 1.0 s and touching the hand at the final step |

**Retention:** Every milestone requires the cube retained and intact up to that moment: it touches nothing but the hand, its centre never drops more than 5 cm below its step-0 height, and the cubies are never forced more than 15° away from a configuration the mechanism allows (all layers aligned, or exactly one layer part-way through a turn).

**Scoring:** Each stage scores 0 until its first milestone and otherwise its highest satisfied milestone. Stages 1 and 2 count every complete layer turn, solving or not. Stage 3 requires Stage 1 complete but not Stage 2, and scores the smallest distance reached at any moment. Stage 4 requires Stage 3 complete. Reorienting the whole cube in the hand is allowed and is not a turn. Examples: one wrong turn 0.15; one correct turn 0.30; two correct turns 0.50; solved and held to the end 1.0.

## 5. Sensor-Based Evaluation

The target environment scores these criteria from sensor-observable evidence: cameras, the robot's joint log, and the public robot and object specifications. Measurements are estimates, not ground truth. Where the evidence cannot decide a milestone, the result is reported as uncertain, and the overall status may be `unknown` instead of `success` or `failure`. See `FEEDBACK.md` for results, measurements, and uncertainty.

## 6. Research Freedom

These criteria define the **official target evaluation**, not a required training reward. You may design your own training rewards, intermediate objectives, curricula, optimization methods, simulators, and policy architectures. Your own metrics do not replace official results.
