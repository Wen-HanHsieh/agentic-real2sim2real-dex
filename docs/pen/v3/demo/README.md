# Human Demonstration: Pen Spinning

The video demonstrates the skill to reproduce with the Wuji Hand 2: spin a pen around the fingers.

## Files

- **Video:** `penspinning_first6s.mp4`: the first 6.00 s of a longer published clip, 720 × 1280, 30 fps, 180 frames, at real time (uniform 33.3 ms frame spacing, no duplicated frames: frame `k` is at `t_real = k / 30` s). No original capture exists; this derivative is the source. It carries an on-screen caption unrelated to the task.
- **Sampled frames:** `frames/` (12 frames at `(k + 0.5) / 12` of the duration).

The pen in the video differs from the target pen (`object/SPECS.md`). The target hand starts palm up with the pen across its fingers and may move its wrist within its workspace (`TASK_CONFIG.md` section 3). The video illustrates the skill, not the exact target object or initial conditions.

## Reconstruction Inputs

This file is the only demonstration input (`REFERENCE.md`). Metric scale anchor: the pen length (`object/SPECS.md`); the demonstration pen's own length is unknown, so the anchor is the target pen's.

The demonstration is for offline analysis and policy development. During target execution the deployed policy receives only the observations in `../CONTRACT.md`.

## Reconstruction Notes

- **Provided tracking tool on this demonstration** (`REFERENCE.md` section 3): mask agreement 0.68 for the thin pen; roll about the long axis is unobservable; the tip and cap ends are told apart from the ring colours with a per-frame confidence; fast spins are flagged uncertain.
- **Not done for this demonstration:** pen spin hypotheses from the markings.
