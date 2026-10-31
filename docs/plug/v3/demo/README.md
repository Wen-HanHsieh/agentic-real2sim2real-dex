# Human Demonstration: Plug Handling on a Table

The video shows the scene the target environment reproduces: two two-blade charger plugs on a desk, handled by one hand.

## Files

- **Video:** `plug_IMG_0004_h264.mp4`: an H.264 copy (1280 × 720, no audio) of the original phone capture, 14.53 s, 30 fps, 436 frames, landscape orientation. The capture's frames are uniformly spaced: frame `k` is at `t_real = k / 30` s.
- **Sampled frames:** `frames/` (12 frames at `(k + 0.5) / 12` of the duration).

A white USB-C charger and a black USB-A charger lie on their sides on a white desk. A right hand enters from the near-right corner, palm down, picks up the white plug, reorients it in the hand until its blades point up, carries it about 25 cm to the left and stands it on the desk; it then does the same with the black plug and stands it beside the first (`TASK.md`). The target scene has the same two plugs on a table and the hand on a free-floating wrist starting palm down above the near-right side of the table (`object/SPECS.md`, `TASK_CONFIG.md` section 3). No task objective or success criteria are defined for the target yet (`SUCCESS.md`); the video documents the demonstrated behaviour, not a required one.

## Reconstruction Inputs

This file is the only demonstration input (`REFERENCE.md`). Metric scale anchor: the standard blade geometry of the plugs, 6.35 mm wide blades 12.7 mm apart (`object/SPECS.md`); the tabletop is a plane that fixes the world frame's vertical.

The demonstration is for offline analysis and policy development. During target execution the deployed policy receives only the observations in `../CONTRACT.md`.

## Reconstruction Notes

- **Provided tracking tool on this demonstration** (`REFERENCE.md` section 3): mask agreement 0.86 (white) and 0.88 (black); the white plug is occluded in the hand in 23 % of the frames (orientation weakly constrained there), the black plug fully covered in 11 % (pose extrapolated, `valid` false); the two plugs are tracked independently with the other plug as an occluder.
- **Symmetry:** the plugs: 180° about the blade axis; symmetric objects are tracked on one symmetry branch kept by continuity.
