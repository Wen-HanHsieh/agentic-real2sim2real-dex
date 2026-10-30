# Wuji Hand 2.2: Hardware Specification

## 1. Robot

- **Robot:** Wuji Hand 2.2 (Beta), right hand, 20 actuated revolute joints, carried by a free-floating 6-DoF wrist (section 3).
- **Actuation:** Direct-drive, back-drivable motors with field-oriented control (FOC); no gearbox.
- **Fingertip pads:** passive soft rubber pads, modelled as rigid links `r_*_tip_sensor_frame` fixed to each distal link (2.9 g fingers, 6.0 g thumb). The link name is the vendor's; there is no tactile sensing.
- **URDF:** `wuji_hand2_right/urdf/right.urdf` (joint names, order, axes, position, speed, and effort limits; link masses and inertias). Root link: `r_mount` (the wrist frame); `r_wrist` is the palm frame.
- **Meshes:** `wuji_hand2_right/meshes/right/`
- **License:** `wuji_hand2_right/LICENSE`
- **Source:** wuji-technology/wuji-description, release v2026.10.12, commit `829c9aa`, `hand2/hand2_2`.
- **Torque–speed curve:** Not published.

## 2. Joint Specifications

Joint vectors follow the vendor URDF order. Position, speed, and effort limits come from the URDF; armature values come from the vendor MJCF. `q₀` is this task's nominal initial configuration [rad].

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

`q₀` is the same in every trial. Measured initial positions may differ because of settling and encoder noise (`CONTRACT.md`).

## 3. Floating Wrist and World Frame

- **World frame:** X forward, Y left, Z up. The floor is the plane z = 0; the initial wrist pose (`hardware/SPECS.md` section 3) is about 0.31 m above it.
- **Gravity:** `(0, 0, -9.81)` m/s².
- **Wrist:** the hand is not attached to a fixed mount and has no arm. Its URDF root link `r_mount` (the *wrist frame*) is a free rigid body with 6 degrees of freedom, positioned and oriented by an ideal 6-axis wrist actuator (section 4). The URDF's own root has no joint to the world; treat `r_mount` as a floating base.
- **Initial wrist pose** (every trial): position `(0.028196, -0.002080, 0.304675)` m, orientation (wxyz) `(0.534290, 0.445683, 0.463192, 0.548957)`. Palm up, fingertips tilted downward by 10°: the pose of the fixed mount of this task's previous environment, with the object resting in the hand. The executed wrist target starts at this pose (the three entries of the target histories at step 0); the measured wrist state at step 0 differs from it by the controller's steady-state offset under the object's weight (section 4, about 0.3 mm).
- **Palm frame `r_wrist`** follows from the URDF joint `r_wrist_fixed`. In the world at the initial pose: position `(0.000050, -0.000002, 0.299709)` m, orientation (wxyz) `(0.534286, 0.445687, 0.463188, 0.548962)`.
- **Wrist workspace:** the executed wrist position target is kept inside the box `x ∈ [−0.30, 0.35]`, `y ∈ [−0.30, 0.30]`, `z ∈ [0.05, 0.65]` m (world frame). The hand itself collides with the floor and the object.

## 4. Wrist Controller (version `wrist-1`)

A Cartesian impedance controller runs at 1 kHz and holds each policy command for two ticks. With `p`, `q`, `v`, `ω` the wrist frame's world position, orientation, linear velocity (of the frame origin) and angular velocity, and `p*`, `q*`, `v*`, `ω*` the executed target (`CONTRACT.md` section 4):

```text
e_p = p* − p
e_R = rotation vector of q* ⊗ q⁻¹             (world frame, shortest rotation, |e_R| ≤ π)
F   = Kp_lin e_p + Kd_lin (v* − v) + M g_up
T   = Kp_rot e_R + Kd_rot (ω* − ω) + (c − p) × (M g_up)
F  ← F · min(1, F_max / |F|)
T  ← T · min(1, T_max / |T|)
```

`M` = 0.6878 kg is the total mass of the hand (all URDF links), `c` its current centre of mass (fingers included), `g_up = (0, 0, 9.81)` m/s²: the controller compensates the hand's own weight, not the weight of held objects. The force `F` and the torque `T` (about the wrist-frame origin) act on `r_mount`; the fingers are driven only by their own joint controllers (section 5).

| Parameter | Value |
|---|---|
| `Kp_lin` | 2000 N/m |
| `Kd_lin` | 60 N·s/m |
| `Kp_rot` | 20 N·m/rad |
| `Kd_rot` | 0.4 N·m·s/rad |
| `F_max` (force norm, gravity compensation included) | 30 N |
| `T_max` (torque norm) | 2.0 N·m |
| `V_MAX` (executed-target translation speed, linear feed-forward norm) | 1.0 m/s |
| `W_MAX` (executed-target rotation speed, angular feed-forward norm) | 3.0 rad/s |

Command limits (rate limits, workspace box, feed-forward clipping) are applied once per policy step before the controller sees the target (`CONTRACT.md` section 4). The wrist's acceleration is limited by `F_max` and `T_max`; its speed follows the executed target and can exceed `V_MAX` / `W_MAX` by a few percent during transients (measured: 1.05 m/s peak after a 20 cm step command). There is no other wrist hardware limit.

Measured tracking on the target (hand holding its task object, no contact with the environment): steady-state offset ≈ 0.3 mm and 0.2° (the unsupported object weight), ≤ 1.0 mm and 0.5° while following a 2 cm, 1 Hz circle with a ±10° yaw oscillation and matching feed-forward velocities.

## 5. Finger Joint Controller

A joint-space PD controller runs at 1 kHz. Policy commands arrive at 500 Hz and are held for two controller ticks:

```text
tau_demand = kp (q_target − q) + kd (qd_target − qd)
```

| Joints | kp (N·m/rad) | kd (N·m·s/rad) |
|---|---|---|
| Four long-finger `*_mcp_flex` | 10.0 | 0.10 |
| `r_thumb_cmc_flex`, `r_thumb_cmc_abd` | 4.0 | 0.04 |
| All other joints | 2.0 | 0.02 |

The applied torque is `tau_demand` saturated at each joint's effort limit. Motor speed limits apply. The finger controller is unchanged by the floating wrist: the wrist's motion back-drives the finger joints only through their inertia and contacts.

## 6. Encoder Observations

Joint encoders at 500 Hz with independent Gaussian noise:

| Measurement | Standard deviation |
|---|---|
| Joint position | 0.002 rad |
| Joint velocity | 0.05 rad/s |

The wrist state and the object state in the observation are exact (`CONTRACT.md` section 3). The policy receives no tactile, force, motor-current, or camera observations.

## 7. Hardware Compliance (authoritative)

This section is the single hardware specification. The target environment's evaluation (`FEEDBACK.md`) and the local tool `r2s2r-hwcheck` (`HARDWARE_CHECK.md`) apply it; `hardware/hardware_spec.json` (`hwspec-1.1`) is its machine-readable form. The rules concern the 20 finger joints and are unchanged from the fixed-wrist environment; the wrist has no rule beyond its controller (section 4): wrist commands are limited, never rejected, and the wrist's motion is never a violation.

| Quantity | Requirement (every joint, every step) | Notes |
|---|---|---|
| Joint position | `lower − 0.02 ≤ q ≤ upper + 0.02` rad | Joint stops are compliant: pressing into a stop deflects slightly past the URDF limit; travel beyond the allowance is a violation |
| Joint velocity | `abs(qd) ≤` URDF max speed, no allowance | Also applies to joints back-driven by contact or by the wrist's motion |
| Applied torque | `abs(tau_applied) ≤` URDF effort, no allowance | The actuator saturates the PD torque at the effort limit, so the applied torque never exceeds it on the target; demand above the limit is saturation, reported but not a violation |
| Actions | `q_target`: finite `(20,)`; `qd_target`: `None` or finite `(20,)`; wrist targets as in `CONTRACT.md` section 4 | Position targets are clipped to the URDF limits; a missing, non-finite or wrongly shaped action value, a policy error, or no answer within 5 s ends the trial |

Nothing else is enforced; no torque–speed envelope is specified. If your simulator's actuator model can exceed the effort limit, check your trajectories with `HARDWARE_CHECK.md`.
