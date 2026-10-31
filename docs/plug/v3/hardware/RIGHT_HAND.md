# Right Wuji Hand 2.2: Model Specification

The right variant of the Wuji Hand 2.2. The common hardware (floating wrist, controllers, encoders, frames, hardware rules) is in `hardware/SPECS.md`; which variant your task uses is stated in `TASK_CONFIG.md` section 1.

## 1. Model Files

All paths are relative to `hardware/`.

- **URDF:** `wuji_hand2_right/urdf/right.urdf` (joint names, order, axes, position, speed, and effort limits; link masses and inertias).
- **Meshes:** `wuji_hand2_right/meshes/right/`
- **License:** `wuji_hand2_right/LICENSE`
- **Source:** wuji-technology/wuji-description, release v2026.10.12, commit `829c9aa`, `hand2/hand2_2/body/urdf/right.urdf` and `hand2/hand2_2/body/meshes/right/` (byte-identical copies). Armature values come from the vendor MJCF `hand2/hand2_2/body/mjcf/right.xml`.
- **Root link (wrist frame):** `r_mount`, the floating base of `hardware/SPECS.md` section 3; its axes: +x toward the thumb side, +y toward the palm, the fingers along −z.
- **Palm frame:** `r_wrist`, attached to `r_mount` by the fixed joint `r_wrist_fixed` at `xyz` `(0.003000, 0.000000, −0.028498)` m, `rpy` `(0, 0, 0.000016)` rad (URDF values, rounded).
- **Fingertip pads:** `r_thumb_tip_sensor_frame` (6.0 g), `r_index_finger_tip_sensor_frame`, `r_middle_finger_tip_sensor_frame`, `r_ring_finger_tip_sensor_frame`, `r_pinky_tip_sensor_frame` (2.9 g each), each fixed to its distal link.
- **Total mass:** 0.6878 kg (sum of all 27 URDF link masses).

## 2. Joints

Vendor URDF order; joint vectors of a task that uses this hand (observation, actions, feedback, `joint_names` in the rollout log) follow it. The axis is the URDF `<axis>` of the joint, expressed in the joint frame. Position, speed and effort limits come from the URDF; armature values from the vendor MJCF. The PD gains of each joint are in `hardware/SPECS.md` section 5; the initial configuration `q₀` of a task is in its `TASK_CONFIG.md` section 3.

| # | Joint | Axis | Lower (rad) | Upper (rad) | Max speed (rad/s) | Effort (N·m) | Armature (kg·m²) |
|---|---|---|---|---|---|---|---|
| 0 | r_thumb_cmc_flex | `+x` | -1.187 | 1.291 | 8.587 | 0.6 | 5e-4 |
| 1 | r_thumb_cmc_abd | `+y` | -1.484 | 0.698 | 11.1 | 0.6 | 5e-4 |
| 2 | r_thumb_mcp | `+x` | -1.047 | 1.570 | 12.86 | 0.3 | 2e-4 |
| 3 | r_thumb_ip | `+x` | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 |
| 4 | r_index_finger_mcp_flex | `+x` | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 |
| 5 | r_index_finger_mcp_abd | `+y` | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 |
| 6 | r_index_finger_pip | `+x` | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 |
| 7 | r_index_finger_dip | `+x` | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 |
| 8 | r_middle_finger_mcp_flex | `+x` | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 |
| 9 | r_middle_finger_mcp_abd | `+y` | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 |
| 10 | r_middle_finger_pip | `+x` | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 |
| 11 | r_middle_finger_dip | `+x` | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 |
| 12 | r_ring_finger_mcp_flex | `+x` | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 |
| 13 | r_ring_finger_mcp_abd | `+y` | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 |
| 14 | r_ring_finger_pip | `+x` | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 |
| 15 | r_ring_finger_dip | `+x` | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 |
| 16 | r_pinky_mcp_flex | `+x` | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 |
| 17 | r_pinky_mcp_abd | `+y` | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 |
| 18 | r_pinky_pip | `+x` | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 |
| 19 | r_pinky_dip | `+x` | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 |

## 3. Relation to the Left Hand

The left variant has its own model files; its joint axes, joint origins and palm offset are compared with this hand in `hardware/LEFT_HAND.md` section 3.
