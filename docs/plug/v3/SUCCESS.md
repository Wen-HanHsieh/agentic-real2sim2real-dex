# SUCCESS.md — Plug Manipulation

## Task Objective

Reproduce the demonstrated plug manipulation task using the Wuji Hand 2:

Pick Up White → Place White → Pick Up Black → Place Black

## Success Criteria

Complete all four stages in order:

1. Pick Up White: Grasp and lift the white plug from the right side of the table.
2. Place White: Move the white plug to the left side of the table and place it standing upright, with its blades pointing upward.
3. Pick Up Black: Grasp and lift the black plug from the right side of the table.
4. Place Black: Move the black plug to the left side of the table and place it standing upright, with its blades pointing upward.

Requirements:

* Both plugs must remain on the table.
* The white plug must remain upright while manipulating the black plug.
* Both plugs must remain upright on the left side of the table at the end of the episode.

## Task Progress

* Progress ranges from `0.0` to `1.0`.
* Each completed stage contributes `0.25`.
* Stages are credited sequentially; incomplete stages receive no credit.
* `success = true` requires all four stages, the final placement requirements, hardware compliance, and a valid rollout.

## Evaluation Rules

* Episode: 20 s (10,000 steps at 500 Hz).
* Verifier: Uses exact object positions, orientations, velocities, robot states, and contact information from the target environment.
* Research freedom: The agent may independently design training rewards, curricula, and optimization methods.
* Integrity: The agent must not modify or bypass the verifier or evaluation constraints.
