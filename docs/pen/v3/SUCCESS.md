# SUCCESS.md — Pen Spinning

## Task Objective

Reproduce the demonstrated pen-spinning skill using the Wuji Hand 2:

Spin 1 → Spin 2 → Spin 3 → Spin 4 → Hold

## Success Criteria

Complete all five stages in order:

1. Spin 1: Rotate the pen 180° clockwise, transferring it from index–middle to middle–ring.
2. Spin 2: Rotate another 180° clockwise, transferring it from middle–ring to ring–pinky.
3. Spin 3: Rotate another 180° clockwise, transferring it from ring–pinky to middle–ring.
4. Spin 4: Rotate another 180° clockwise, transferring it from middle–ring to index–middle.
5. Hold: Retain the pen stably in the hand throughout the final 1.0 s.

Requirements:

* Rotation: Measured as net clockwise rotation of the pen's heading about the world Z-axis, viewed from above (looking along −Z).
* Cumulative rotation: −180°, −360°, −540°, −720° after Spins 1–4, respectively.
* Finger transfers: Each spin must complete its specified transition between finger pairs.
* Retention: The pen must not touch the environment. Brief losses of hand contact are allowed if the pen is recovered.
* Hold: Maintain stable hand contact throughout the final 1.0 s.

## Task Progress

* Progress ranges from `0.0` to `1.0`.
* Each completed stage contributes `0.20`.
* Stages are credited sequentially; incomplete stages receive no credit.
* `success = true` requires all five stages, hardware compliance, and a valid rollout.

## Evaluation Rules

* Episode: 12 s (6,000 steps at 500 Hz).
* Verifier: Uses exact object positions, orientations, velocities, robot states, and finger–object contact information from the target environment.
* Research freedom: The agent may independently design training rewards, curricula, and optimization methods.
* Integrity: The agent must not modify or bypass the verifier or evaluation constraints.
