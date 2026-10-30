# Human Demonstration: Tennis Ball Toss and Catch

The video demonstrates the skill to reproduce with the Wuji Hand 2: toss a tennis ball from the palm, catch it, and repeat.

## Files

- **Video:** `tennis_IMG_0005_h264.mp4`: an H.264 copy (720 × 1280, no audio) of the original phone capture, 10.50 s, 30 fps, 315 frames, portrait orientation. The capture's frames are uniformly spaced: frame `k` is at `t_real = k / 30` s.
- **Sampled frames:** `frames/` (12 frames at `(k + 0.5) / 12` of the duration).

One hand, palm up, holds one tennis ball and performs three consecutive vertical toss-and-catch cycles with in-hand regrasps between the tosses; the ball leaves the top of the frame near each apex. The target task requires two complete cycles with a lower apex (`SUCCESS.md`), from a palm-up hand whose wrist is free to move within its workspace (`hardware/SPECS.md` section 3). The video illustrates the skill, not the exact target object or initial conditions.

## Reconstruction Inputs

This file is the only demonstration input (`REFERENCE.md`). Metric scale anchor: the ball diameter (`object/SPECS.md`). The ball's free flight gives a gravity check of a reconstruction's scale and time base.

The demonstration is for offline analysis and policy development. During target execution the deployed policy receives only the observations in `../CONTRACT.md`.
