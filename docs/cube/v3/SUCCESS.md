# SUCCESS.md — One-Handed 2×2×2 Rubik's Cube Solving

## Task Objective

Solve the scrambled 2×2×2 Rubik's Cube using the left Wuji Hand 2:

First Turn → Turning → Solve → Hold

## Success Criteria

Complete all four stages in order:

1. First Turn: Complete one valid cube layer turn.
2. Turning: Complete at least three valid layer turns in total.
3. Solve: Reach the fully solved cube configuration.
4. Hold: Keep the cube solved throughout the final 1.0 s, with hand contact at the end.

Requirements:

* Layer Turn: A valid 90° or 180° rotation of a cube layer, aligned within 10° of its intended position.
* Solved: All six faces have uniform colors and all layers are aligned. Whole-cube orientation does not matter.
* Retention: The cube must remain in the hand, never touch the environment, and remain mechanically intact.
* Manipulation: Whole-cube reorientation does not count as a layer turn.

## Task Progress

* Progress ranges from `0.0` to `1.0`.
* Each completed stage contributes `0.25`.
* Stages are credited sequentially; incomplete stages receive no credit.
* `success = true` requires all four stages, hardware compliance, and a valid rollout.

## Evaluation Rules

* Episode: 40 s (20,000 steps at 500 Hz).
* Verifier: Uses exact cubie configurations, object states, robot states, and contact information from the target environment.
* Research freedom: The agent may independently design training rewards, curricula, and optimization methods.
* Integrity: The agent must not modify or bypass the verifier or evaluation constraints.
