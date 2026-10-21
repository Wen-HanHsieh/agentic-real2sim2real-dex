# Hardware Specification: Wuji Hand 2 (Right, Beta 1)

## 1. Robot Model

- **URDF:** `wuji_hand2_right/urdf/right.urdf`
- **Meshes:** `wuji_hand2_right/meshes/right/`
- **License:** `wuji_hand2_right/LICENSE`
- **Source:** wuji-technology/wuji-description, release v2026.7.23, commit `1407bee`.
- **Robot:** 20 actuated revolute joints, direct-drive, back-drivable FOC motors, no gearbox.
- **Torque–speed curve:** Not published.

## 2. Joint Specifications

Joint vectors follow the vendor URDF order. Position, speed, and effort limits come from the URDF; armature values come from the vendor MJCF. Initial positions `q₀` are in radians.

| # | Joint | Lower (rad) | Upper (rad) | Max speed (rad/s) | Effort (N·m) | Armature (kg·m²) | q₀ (rad) |
|---|---|---|---|---|---|---|---|
| 0 | r_thumb_cmc_flex | -1.187 | 1.291 | 8.587 | 0.6 | 5e-4 | 0.0 |
| 1 | r_thumb_cmc_abd | -1.484 | 0.698 | 11.1 | 0.6 | 5e-4 | -1.4 |
| 2 | r_thumb_mcp | -1.047 | 1.570 | 12.86 | 0.3 | 2e-4 | 0.0 |
| 3 | r_thumb_ip | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 | 0.0 |
| 4 | r_index_finger_mcp_flex | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 | 0.0 |
| 5 | r_index_finger_mcp_abd | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 | 0.0 |
| 6 | r_index_finger_pip | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 | 1.2 |
| 7 | r_index_finger_dip | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 | 0.3 |
| 8 | r_middle_finger_mcp_flex | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 | 0.0 |
| 9 | r_middle_finger_mcp_abd | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 | 0.0 |
| 10 | r_middle_finger_pip | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 | 1.2 |
| 11 | r_middle_finger_dip | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 | 0.3 |
| 12 | r_ring_finger_mcp_flex | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 | 0.0 |
| 13 | r_ring_finger_mcp_abd | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 | 0.0 |
| 14 | r_ring_finger_pip | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 | 1.2 |
| 15 | r_ring_finger_dip | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 | 0.3 |
| 16 | r_pinky_mcp_flex | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 | 0.0 |
| 17 | r_pinky_mcp_abd | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 | 0.0 |
| 18 | r_pinky_pip | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 | 1.2 |
| 19 | r_pinky_dip | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 | 0.3 |

The initial configuration `q₀` is fixed across evaluation trials. At step 0, `prev_q_target` contains three exact copies of `q₀`; measured `q` may differ due to passive settling and encoder noise.

## 3. Robot Mount

The Wuji Hand 2 is fixed in the world with no wrist or arm motion.

- **World frame:** X forward, Y left, Z up.
- **Gravity:** `(0, 0, -9.81)` m/s².
- **Root link:** `r_wrist`.
- **Position (m):** `(0.0, 0.0, 0.30)`.
- **Orientation (quaternion, wxyz):** `(0.541675, 0.454520, 0.454520, 0.541675)`.

The hand is palm-up, with fingertips tilted downward by 10°. The mount is fixed across all evaluation trials.

The quaternion specifies the complete transform from the `r_wrist` frame to the world frame, including the fixed SuperDex frame offset. Apply it directly to the vendor URDF root; do not apply an additional mount rotation.

## 4. Joint Controller

MIT-style PD controller at 1 kHz:

\[
\tau = k_p(q_{\mathrm{target}} - q) + k_d(\dot q_{\mathrm{target}} - \dot q)
\]

Commands arrive at 500 Hz and are held for two PD ticks. Motor speed and effort limits apply.

| Joints | kp (N·m/rad) | kd (N·m·s/rad) |
|---|---|---|
| Four long-finger `*_mcp_flex` | 10.0 | 0.10 |
| `r_thumb_cmc_flex`, `r_thumb_cmc_abd` | 4.0 | 0.04 |
| All other joints | 2.0 | 0.02 |

## 5. Sensors

Joint encoders at 500 Hz with independent Gaussian noise:

- **Position:** σ = 0.002 rad
- **Velocity:** σ = 0.05 rad/s

No tactile, force, motor-current, camera, or object-state observations are provided to the policy. See `CONTRACT.md` for the observation and action interface.
