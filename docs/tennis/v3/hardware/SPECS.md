# Wuji Hand 2.2: Common Hardware and Control Specification

This document covers what every task's robot has in common: the hand family and its configuration, the floating wrist, the controllers and their rates, the encoders, the frame conventions, and the hardware rules. The two hand variants have their own files: `hardware/RIGHT_HAND.md` and `hardware/LEFT_HAND.md` (model files, joint names and order, axes, limits, actuator parameters). Your task uses the variant named in `TASK_CONFIG.md` section 1; its initial wrist pose, initial finger configuration and wrist workspace are in `TASK_CONFIG.md` section 3.

## 1. Robot

- **Robot:** Wuji Hand 2.2 (Beta), 20 actuated revolute joints, carried by a free-floating 6-DoF wrist (section 3). The hand exists as a right and a left variant; each task uses one of them (`TASK_CONFIG.md` section 1).
- **Hand variants:**

| Variant | Specification | Model files (in `hardware/`) |
|---|---|---|
| Right hand | `hardware/RIGHT_HAND.md` | `wuji_hand2_right/` |
| Left hand | `hardware/LEFT_HAND.md` | `wuji_hand2_left/` |

- **Actuation:** Direct-drive, back-drivable motors with field-oriented control (FOC); no gearbox.
- **Fingertip pads:** passive soft rubber pads, modelled as rigid links fixed to each distal link (link names in the hand files). The link name `*_tip_sensor_frame` is the vendor's; there is no tactile sensing.
- **Source:** wuji-technology/wuji-description, release v2026.10.12, commit `829c9aa`, `hand2/hand2_2` (both variants).
- **Torque–speed curve:** Not published.

## 2. Joints

Each hand has 20 joints in the vendor URDF order: the thumb (`thumb_cmc_flex`, `thumb_cmc_abd`, `thumb_mcp`, `thumb_ip`), then the index, middle and ring fingers (`*_mcp_flex`, `*_mcp_abd`, `*_pip`, `*_dip` each) and the little finger (`pinky_mcp_flex`, `pinky_mcp_abd`, `pinky_pip`, `pinky_dip`). The full joint names carry the variant's prefix (`r_` right, `l_` left). Joint vectors in the observation, the actions and the feedback follow the joint order of your task's hand file. Position, speed and effort limits come from the URDF and armature values from the vendor MJCF; they are tabulated in the hand files. The initial finger configuration `q₀` of your task is in `TASK_CONFIG.md` section 3.

## 3. Floating Wrist and World Frame

- **World frame:** X forward, Y left, Z up. Where the origin lies and what the hand can touch (floor, table) depends on the task's scene: `TASK_CONFIG.md` section 3.
- **Gravity:** `(0, 0, -9.81)` m/s².
- **Wrist frame:** the hand is not attached to a fixed mount and has no arm. The root link of the hand's URDF (`r_mount` or `l_mount`, the *wrist frame*) is a free rigid body with 6 degrees of freedom, positioned and oriented by an ideal 6-axis wrist actuator (section 4). The URDF's own root has no joint to the world; treat the root link as a floating base.
- **Palm frame** (`r_wrist` or `l_wrist`) follows from the URDF's fixed joint between the root link and the palm (hand files).
- **Initial wrist pose** (every trial), **wrist workspace** (the box the executed wrist position target is kept in, world frame) and the palm frame's initial pose: `TASK_CONFIG.md` section 3.

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

`M` = 0.6878 kg is the total mass of the hand (all URDF links; equal for both variants), `c` its current centre of mass (fingers included), `g_up = (0, 0, 9.81)` m/s²: the controller compensates the hand's own weight, not the weight of held objects. The force `F` and the torque `T` (about the wrist-frame origin) act on the root link; the fingers are driven only by their own joint controllers (section 5).

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

Measured tracking on the target with the right hand holding its task object, no contact with the environment: steady-state offset ≈ 0.3 mm and 0.2° (the unsupported object weight), ≤ 1.0 mm and 0.5° while following a 2 cm, 1 Hz circle with a ±10° yaw oscillation and matching feed-forward velocities. The same controller and gains drive the left hand; its tracking has not been measured separately.

## 5. Finger Joint Controller

A joint-space PD controller runs at 1 kHz. Policy commands arrive at 500 Hz and are held for two controller ticks:

```text
tau_demand = kp (q_target − q) + kd (qd_target − qd)
```

| Joints (both variants) | kp (N·m/rad) | kd (N·m·s/rad) |
|---|---|---|
| Four long-finger `*_mcp_flex` | 10.0 | 0.10 |
| `*_thumb_cmc_flex`, `*_thumb_cmc_abd` | 4.0 | 0.04 |
| All other joints | 2.0 | 0.02 |

The applied torque is `tau_demand` saturated at each joint's effort limit (hand files). Motor speed limits apply. The finger controller is unchanged by the floating wrist: the wrist's motion back-drives the finger joints only through their inertia and contacts.

## 6. Encoder Observations

Joint encoders at 500 Hz with independent Gaussian noise:

| Measurement | Standard deviation |
|---|---|
| Joint position | 0.002 rad |
| Joint velocity | 0.05 rad/s |

The wrist state and the object state in the observation are exact (`CONTRACT.md` section 3). The policy receives no tactile, force, motor-current, or camera observations.

## 7. Hardware Compliance (authoritative)

This section is the single hardware specification. The target environment's evaluation (`FEEDBACK.md`) and the local tool `r2s2r-hwcheck` (`HARDWARE_CHECK.md`) apply it; its machine-readable form is `hardware/hardware_spec.json` for the right hand (`hwspec-1.1`) and `hardware/hardware_spec_left.json` for the left hand (`hwspec-1.1L`): the same rules, limits and gains, each with its hand's joint names. The rules concern the 20 finger joints of either variant, with the limits of its hand file, and are unchanged from the fixed-wrist environment; the wrist has no rule beyond its controller (section 4): wrist commands are limited, never rejected, and the wrist's motion is never a violation.

| Quantity | Requirement (every joint, every step) | Notes |
|---|---|---|
| Joint position | `lower − 0.02 ≤ q ≤ upper + 0.02` rad | Joint stops are compliant: pressing into a stop deflects slightly past the URDF limit; travel beyond the allowance is a violation |
| Joint velocity | `abs(qd) ≤` URDF max speed, no allowance | Also applies to joints back-driven by contact or by the wrist's motion |
| Applied torque | `abs(tau_applied) ≤` URDF effort, no allowance | The actuator saturates the PD torque at the effort limit, so the applied torque never exceeds it on the target; demand above the limit is saturation, reported but not a violation |
| Actions | `q_target`: finite `(20,)`; `qd_target`: `None` or finite `(20,)`; wrist targets as in `CONTRACT.md` section 4 | Position targets are clipped to the URDF limits; a missing, non-finite or wrongly shaped action value, a policy error, or no answer within 5 s ends the trial |

Nothing else is enforced; no torque–speed envelope is specified. If your simulator's actuator model can exceed the effort limit, check your trajectories with `HARDWARE_CHECK.md`.
