# Wuji Hand 2.2: Hardware Specification

## 1. Robot

- **Robot:** Wuji Hand 2.2 (Beta), right hand, 20 actuated revolute joints.
- **Actuation:** Direct-drive, back-drivable motors with field-oriented control (FOC); no gearbox.
- **Fingertip pads:** passive soft rubber pads, modelled as rigid links `r_*_tip_sensor_frame` fixed to each distal link (2.9 g fingers, 6.0 g thumb). The link name is the vendor's; there is no tactile sensing.
- **URDF:** `wuji_hand2_right/urdf/right.urdf` (joint names, order, axes, position, speed, and effort limits; link masses and inertias). Root link: `r_mount` (mounting flange); `r_wrist` is the palm frame.
- **Meshes:** `wuji_hand2_right/meshes/right/`
- **License:** `wuji_hand2_right/LICENSE`
- **Source:** wuji-technology/wuji-description, release v2026.10.12, commit `829c9aa`, `hand2/hand2_2`.
- **Torque–speed curve:** Not published.

## 2. Joint Specifications

Joint vectors follow the vendor URDF order. Position, speed, and effort limits come from the URDF; armature values come from the vendor MJCF. `q₀` is this task's nominal initial configuration [rad].

| # | Joint | Lower (rad) | Upper (rad) | Max speed (rad/s) | Effort (N·m) | Armature (kg·m²) | q₀ (rad) |
|---|---|---|---|---|---|---|---|
| 0 | r_thumb_cmc_flex | -1.187 | 1.291 | 8.587 | 0.6 | 5e-4 | 0.6 |
| 1 | r_thumb_cmc_abd | -1.484 | 0.698 | 11.1 | 0.6 | 5e-4 | -0.3 |
| 2 | r_thumb_mcp | -1.047 | 1.570 | 12.86 | 0.3 | 2e-4 | 0.3 |
| 3 | r_thumb_ip | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 | 0.2 |
| 4 | r_index_finger_mcp_flex | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 | 0.6 |
| 5 | r_index_finger_mcp_abd | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 | 0.0 |
| 6 | r_index_finger_pip | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 | 1.4 |
| 7 | r_index_finger_dip | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 | 0.3 |
| 8 | r_middle_finger_mcp_flex | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 | 0.6 |
| 9 | r_middle_finger_mcp_abd | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 | 0.0 |
| 10 | r_middle_finger_pip | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 | 1.4 |
| 11 | r_middle_finger_dip | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 | 0.3 |
| 12 | r_ring_finger_mcp_flex | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 | 0.6 |
| 13 | r_ring_finger_mcp_abd | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 | 0.0 |
| 14 | r_ring_finger_pip | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 | 1.4 |
| 15 | r_ring_finger_dip | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 | 0.3 |
| 16 | r_pinky_mcp_flex | -1.047 | 1.570 | 8.203 | 2.0 | 5e-4 | 0.6 |
| 17 | r_pinky_mcp_abd | -0.698 | 0.698 | 8.11 | 0.2 | 2e-4 | 0.0 |
| 18 | r_pinky_pip | -1.047 | 2.094 | 12.86 | 0.3 | 2e-4 | 1.4 |
| 19 | r_pinky_dip | -1.047 | 1.570 | 13.5 | 0.3 | 2e-4 | 0.3 |

`q₀` is the same in every trial. Measured initial positions may differ because of settling and encoder noise (`CONTRACT.md`).

## 3. Mount and World Frame

- **World frame:** X forward, Y left, Z up.
- **Gravity:** `(0, 0, -9.81)` m/s².
- **Fixed root link:** `r_mount` (URDF root), no wrist or arm motion.
- **Root position (m):** `(0.028496, -0.002080, 0.302200)`.
- **Root orientation (quaternion, wxyz):** `(0.513578, 0.469204, 0.486056, 0.528994)`.
- **Palm frame `r_wrist` in the world:** position `(0.000024, -0.000002, 0.299706)` m, orientation (wxyz) `(0.513573, 0.469208, 0.486052, 0.528998)`.

The hand is palm-up, with fingertips tilted downward by 5°. The root position and orientation are the complete transform from the `r_mount` frame to the world frame; apply them directly to the URDF root without an additional mount rotation. The `r_wrist` pose follows from the URDF joint `r_wrist_fixed` and is given for reference. The mount is the same in every trial.

## 4. Joint Controller

A joint-space PD controller runs at 1 kHz. Policy commands arrive at 500 Hz and are held for two controller ticks:

```text
tau_demand = kp (q_target − q) + kd (qd_target − qd)
```

| Joints | kp (N·m/rad) | kd (N·m·s/rad) |
|---|---|---|
| Four long-finger `*_mcp_flex` | 10.0 | 0.10 |
| `r_thumb_cmc_flex`, `r_thumb_cmc_abd` | 4.0 | 0.04 |
| All other joints | 2.0 | 0.02 |

The applied torque is `tau_demand` saturated at each joint's effort limit. Motor speed limits apply.

## 5. Encoder Observations

Joint encoders at 500 Hz with independent Gaussian noise:

| Measurement | Standard deviation |
|---|---|
| Joint position | 0.002 rad |
| Joint velocity | 0.05 rad/s |

The policy receives no tactile, force, motor-current, camera, or object-state observations (`CONTRACT.md`).

## 6. Hardware Compliance (authoritative)

This section is the single hardware specification. The target environment's evaluation (`FEEDBACK.md`) and the local tool `r2s2r-hwcheck` (`HARDWARE_CHECK.md`) apply it; `hardware/hardware_spec.json` (`hwspec-1.1`) is its machine-readable form.

| Quantity | Requirement (every joint, every step) | Notes |
|---|---|---|
| Joint position | `lower − 0.02 ≤ q ≤ upper + 0.02` rad | Joint stops are compliant: pressing into a stop deflects slightly past the URDF limit; travel beyond the allowance is a violation |
| Joint velocity | `abs(qd) ≤` URDF max speed, no allowance | Also applies to joints back-driven by contact |
| Applied torque | `abs(tau_applied) ≤` URDF effort, no allowance | The actuator saturates the PD torque at the effort limit, so the applied torque never exceeds it on the target; demand above the limit is saturation, reported but not a violation |
| Actions | `q_target`: finite `(20,)`; `qd_target`: `None` or finite `(20,)` | Position targets are clipped to the URDF limits; a non-finite or wrongly shaped action, a policy error, or no answer within 5 s ends the trial |

Nothing else is enforced; no torque–speed envelope is specified. If your simulator's actuator model can exceed the effort limit, check your trajectories with `HARDWARE_CHECK.md`.
