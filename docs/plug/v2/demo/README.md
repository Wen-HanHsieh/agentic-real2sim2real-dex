# Human Demonstration: Plug Reorientation

The video demonstrates the skill to reproduce with the Wuji Hand 2: reorient a charger plug in the hand so that its blades point up.

## Files

- **Video:** `plug_IMG_0004_h264.mp4` (14.53 s, 30 fps, H.264, 1280 × 720).
- **Sampled frames:** `frames/` (12 frames).

Two two-blade charger plugs lie on their sides on a desk. The hand picks each one up, reorients it in-hand until the blades point up, and stands it upright on the desk, the second next to the first. The target hand is fixed-base and has no desk: the target task is the in-hand part of this skill only. The plug starts lying on a side face in the palm and must be reoriented blades-up and held there (`TASK.md`, `SUCCESS.md`); picking up from and placing on a surface are not part of the target task, and the target has one plug. The video illustrates the skill, not the exact target object or initial conditions.

The demonstration is for offline analysis and policy development. During target execution the deployed policy receives only the observations in `../CONTRACT.md`.
