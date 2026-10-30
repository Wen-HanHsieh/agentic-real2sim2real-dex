# Task: One-handed 2×2×2 Rubik's Cube Solving

Reproduce the dexterous manipulation skill demonstrated in the human video using the Wuji Hand 2: **solve a scrambled 2×2×2 cube by turning its layers with the hand only, keep it in the hand throughout, and hold it solved**.

The hand starts palm up with the cube resting in it, and its wrist is free to move within the workspace of `hardware/SPECS.md` section 3. The policy observes the exact state of the cube and of each of its eight cubies, including the discrete configuration index of every cubie (`CONTRACT.md`, `object/SPECS.md`).

Develop your policy in your own simulation and evaluate it in the provided target environment.

- **Human demonstration:** `demo/`
- **Target environment:** `target/screenshot.png`
- **Success criteria:** `SUCCESS.md` (provisional)

## Cube Conventions

- **Faces at the start:** U faces world +Z (up), F faces the fingertips (world −X), R faces world −Y (little-finger side), L the thumb side, D the palm, B the wrist. Face names are fixed by this start orientation; the cube may be reoriented freely afterwards.
- **Solved colours:** U white, D yellow, F green, B blue, R red, L orange.
- **Moves (WCA):** X = 90° clockwise looking at face X from outside, X2 = 180°, X' = 90° counterclockwise. A 2×2×2 has no fixed centres: L equals R' plus a whole-cube rotation; likewise D = U' and B = F'.
- **Scramble:** fixed for every evaluation: **R' F U2**, encoded `[[1, 3], [2, 1], [0, 2]]` (face 0 = U, 1 = R, 2 = F; quarter_turns 1 = X, 2 = X2, 3 = X'). Applying the moves in order to a solved cube held in the start orientation gives the start state shown in `target/screenshot.png`. The policy receives it in every observation as `obs["scramble"]` (`CONTRACT.md`), and the observation's `cube_configuration` reports the resulting cubie orientations directly (`object/SPECS.md`).
