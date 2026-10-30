# Human Demonstration: One-handed 2×2×2 Rubik's Cube Solving

The video demonstrates the skill to reproduce with the Wuji Hand 2: solve a 2×2×2 cube in one hand.

## Files

- **Video:** `rubiks_2x2_0.5x.mp4`: a 2× slowed file, 720 × 1280, 15 fps in the file, 395 frames, 26.33 s of file time. No original capture exists; this derivative is the source. **Time base (an assumption):** the file is treated as 30 fps footage re-timed by a factor 2, so real time = file time / 2 (13.17 s of real time, frame `k` at `t_real = k / 30` s). The factor 2.000 is confirmed by the on-screen timer (8.0 s of timer time elapse over 240 file frames); the original frame rate itself cannot be verified. Velocities read from the file must be doubled.
- **Sampled frames:** `frames/` (12 frames at `(k + 0.5) / 12` of the file duration).

The cube in the video differs from the target cube (`object/SPECS.md`). The target hand starts palm up with the cube in it and may move its wrist within its workspace (`hardware/SPECS.md` section 3). The video illustrates the skill, not the exact target object, scramble, or initial conditions.

## Reconstruction Inputs

This file is the only demonstration input (`REFERENCE.md`). Metric scale anchor: the cube edge (`object/SPECS.md`); the demonstration cube's own edge is unknown, so the anchor is the target cube's.

The demonstration is for offline analysis and policy development. During target execution the deployed policy receives only the observations in `../CONTRACT.md`.
