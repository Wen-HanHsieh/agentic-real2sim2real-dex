# Left Wuji Hand 2.2: Model Specification

The left variant of the Wuji Hand 2.2. The common hardware (floating wrist, controllers, encoders, frames, hardware rules) is in `hardware/SPECS.md`; which variant your task uses is stated in `TASK_CONFIG.md` section 1.

## 1. Model Files

All paths are relative to `hardware/`.

- **URDF:** `wuji_hand2_left/urdf/left.urdf` (joint names, order, axes, position, speed, and effort limits; link masses and inertias).
- **Meshes:** `wuji_hand2_left/meshes/left/`
- **License:** `wuji_hand2_left/LICENSE`
- **Source:** wuji-technology/wuji-description, release v2026.10.12, commit `829c9aa`, `hand2/hand2_2/body/urdf/left.urdf` and `hand2/hand2_2/body/meshes/left/` (byte-identical copies). Armature values come from the vendor MJCF `hand2/hand2_2/body/mjcf/left.xml`.
- **Root link (wrist frame):** `l_mount`, the floating base of `hardware/SPECS.md` section 3; its axes: +x toward the thumb side, +y toward the back of the hand, the fingers along −z.
- **Palm frame:** `l_wrist`, attached to `l_mount` by the fixed joint `l_wrist_fixed` at `xyz` `(0.003001, 0.000000, −0.028502)` m, `rpy` `(0, 0, −0.000016)` rad (URDF values, rounded).
- **Fingertip pads:** `l_thumb_tip_sensor_frame` (6.0 g), `l_index_finger_tip_sensor_frame`, `l_middle_finger_tip_sensor_frame`, `l_ring_finger_tip_sensor_frame`, `l_pinky_tip_sensor_frame` (2.9 g each), each fixed to its distal link.
- **Total mass:** 0.6878 kg (sum of all 27 URDF link masses).

## 2. Joints

Vendor URDF order; joint vectors of a task that uses this hand (observation, actions, feedback, `joint_names` in the rollout log) follow it. The axis is the URDF `<axis>` of the joint, expressed in the joint frame. Position, speed and effort limits come from the URDF; armature values from the vendor MJCF. The PD gains of each joint are in `hardware/SPECS.md` section 5; the initial configuration `q₀` of a task is in its `TASK_CONFIG.md` section 3.

| # | Joint | Axis | Lower (rad) | Upper (rad) | Max speed (rad/s) | Effort (N·m) | Armature (kg·m²) |
|---|---|---|---|---|---|---|---|
| 0 | l_thumb_cmc_flex | `−x` | -1.187 | 1.291 | 8.587 | 0.6 | 5e-4 |
| 1 | l_thumb_cmc_abd | `+y` | -1.484 | 0.698 | 11.1 | 0.6 | 5e-4 |
| 2 | l_thumb_mcp | `−x` | -1.047 | 1.570 | 12.86 | 0.3 | 2e-4 |
| 3 | l_thumb_ip | `−x` | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 |
| 4 | l_index_finger_mcp_flex | `−x` | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 |
| 5 | l_index_finger_mcp_abd | `+y` | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 |
| 6 | l_index_finger_pip | `−x` | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 |
| 7 | l_index_finger_dip | `−x` | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 |
| 8 | l_middle_finger_mcp_flex | `−x` | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 |
| 9 | l_middle_finger_mcp_abd | `+y` | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 |
| 10 | l_middle_finger_pip | `−x` | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 |
| 11 | l_middle_finger_dip | `−x` | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 |
| 12 | l_ring_finger_mcp_flex | `−x` | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 |
| 13 | l_ring_finger_mcp_abd | `+y` | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 |
| 14 | l_ring_finger_pip | `−x` | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 |
| 15 | l_ring_finger_dip | `−x` | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 |
| 16 | l_pinky_mcp_flex | `−x` | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 |
| 17 | l_pinky_mcp_abd | `+y` | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 |
| 18 | l_pinky_pip | `−x` | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 |
| 19 | l_pinky_dip | `−x` | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 |

## 3. Differences from the Right Hand

From the two vendor models (URDF, MJCF and meshes).

| Item | Right (`hardware/RIGHT_HAND.md`) | Left (this file) |
|---|---|---|
| Joint and link names | prefix `r_` | prefix `l_` |
| Joint order | vendor URDF order | the same order |
| Axis of the flexion joints (`*_cmc_flex`, `*_mcp_flex`, `thumb_mcp`, `*_pip`, `*_dip`, `thumb_ip`) | `+x` | `−x` |
| Axis of the abduction joints (`thumb_cmc_abd`, `*_mcp_abd`) | `+y` | `+y` |
| Joint origins (URDF `<origin>`, every joint except the IMU frame) | as in its URDF | the right values with `y`, roll and yaw negated, to within 3.3 µm and 1.1 × 10⁻⁹ rad |
| Palm offset `*_wrist_fixed` | `(0.003000, 0.000000, −0.028498)` m | `(0.003001, 0.000000, −0.028502)` m |
| Wrist-frame axes (root link) | +x toward the thumb side, +y toward the palm, the fingers along −z | +x toward the thumb side, +y toward the back of the hand, the fingers along −z |
| IMU frame `*_wrist_imu_frame` (no observation uses it) | as in its URDF | not the mirror image of the right one: 1.5 mm and a different orientation away from it |
| Meshes | as shipped | the right meshes reflected to within 1 mm, except the wrist housing (3.3 mm) and the mount (5.2 mm) |
| Position, speed and effort limits, armature | as in its URDF / MJCF | identical, joint by joint |
| Link masses and inertias | as in its URDF | the same masses (0.6878 kg in total); inertia tensors reflected |

Kinematically the left hand is therefore the mirror image of the right one about the hand's x–z plane: a flexion axis `−x` is the mirror image of the right hand's `+x`, an abduction axis `+y` that of `+y`, so the same joint angles give mirror-image finger postures (forward kinematics agree with the reflected right hand to within 0.02 mm). The wrist frame is not mirrored: both root links are right-handed frames, and their `y` axes point to opposite sides of the hand, so a left-hand wrist orientation is not the reflected right-hand quaternion. Build the left hand from its own URDF and meshes.
