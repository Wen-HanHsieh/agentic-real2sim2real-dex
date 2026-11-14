# Human Demonstration: Plug Handling on a Table

The video shows the scene of this task: two two-blade charger plugs on a desk, handled by one hand.

## Files

- **Video:** `plug_IMG_0004_h264.mp4`: an H.264 copy (1280 × 720, no audio) of the original phone capture, 14.53 s, 30 fps, 436 frames, landscape orientation. The capture's frames are uniformly spaced: frame `k` is at `t_real = k / 30` s.
- **Sampled frames:** `frames/` (12 frames at `(k + 0.5) / 12` of the duration).

A white plug and a black plug lie on their sides on a white desk. A right hand enters from the near-right corner, palm down, picks up the white plug, reorients it in the hand until its blades point up, carries it about 25 cm to the left and stands it on the desk; it then does the same with the black plug and stands it beside the first. The simulated scene has a table (`TASK_CONFIG.md` section 2) and the hand on a free-floating wrist; the plugs start as `TASK.md` (Deployment) describes.

## Reconstruction Inputs

This file is the only demonstration input (`demo2sim/REFERENCE.md`). Metric scale anchor: no object dimension is given; choose the anchor from the objects you identify and look up, and record it. The tabletop is a plane that fixes the world frame's vertical.

The demonstration is for offline analysis and policy development.

## Reconstruction Notes

- **Provided tracking tool on this demonstration** (`demo2sim/REFERENCE.md` section 3): mask agreement 0.86 (white) and 0.88 (black); the white plug is occluded in the hand in 23 % of the frames (orientation weakly constrained there), the black plug fully covered in 11 % (pose extrapolated, `valid` false); the two plugs are tracked independently with the other plug as an occluder.
- **Hands:** the demonstrator's right hand.
