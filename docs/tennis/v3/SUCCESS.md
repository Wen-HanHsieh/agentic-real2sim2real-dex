# SUCCESS.md — Tennis Ball Manipulation

## Task Objective

Reproduce the demonstrated tennis ball manipulation sequence using the Wuji Hand 2:

Toss 1 → Catch 1 → Spin 1 → Toss 2 → Catch 2 → Toss 3 → Catch 3 → Spin 2 → Hold

## Success Criteria

Complete all nine stages in order:

1. Toss 1: Toss the ball upward.
2. Catch 1: Catch and retain the ball.
3. Spin 1: Rotate the ball at least 360° about the world Z-axis while retaining it.
4. Toss 2: Toss the ball upward again.
5. Catch 2: Catch and retain the ball.
6. Toss 3: Toss the ball upward a third time.
7. Catch 3: Catch and retain the ball.
8. Spin 2: Rotate the ball at least 360° about the world Z-axis while retaining it.
9. Hold: Maintain hand contact throughout the final 1.0 s.

Requirements:

* Toss: At least 0.10 s of contact-free flight, with an apex at least 5 cm above release height.
* Catch: Ball lands on the hand and is retained for at least 0.30 s.
* Spin: At least 360° net rotation about the world Z-axis, measured using unwrapped angular displacement.
* Retention: The ball must never touch the environment or leave the permitted workspace.

## Task Progress

* Progress ranges from `0.0` to `1.0`.
* Each completed stage contributes `1/9`.
* Stages are credited sequentially; incomplete stages receive no credit.
* `success = true` requires all nine stages, hardware compliance, and a valid rollout.

## Evaluation Rules

* Episode: 15 s (7,500 steps at 500 Hz).
* Verifier: Uses exact object states, robot states, and contact information from the target environment.
* Research freedom: The agent may independently design training rewards, curricula, and optimization methods.
* Integrity: The agent must not modify or bypass the verifier or evaluation constraints.
