# Policy Interface (contract v2)

## 1. Control

- **Robot:** Wuji Hand 2 on a free-floating 6-DoF wrist (`hardware/SPECS.md`): 20 finger joints in vendor URDF order plus the wrist pose.
- **Policy frequency:** 500 Hz (2 ms per step).
- **Controller frequency:** 1 kHz. The finger PD controller and the wrist controller hold each command for two controller ticks.
- **Episode:** 15 s (7,500 policy steps). The episode is not ended by task events such as dropping an object; it ends early only on a policy failure (section 4).
- **Units:** SI (m, kg, s, rad, N, N·m). Quaternions are `(w, x, y, z)`.
- **Contract version:** `v2`. Packages must declare `"contract_version": "v2"` (`PACKAGE.md`); packages written for an earlier contract are refused.

## 2. Frames and Time

- **World frame:** X forward, Y left, Z up; gravity `(0, 0, −9.81)` m/s². The tabletop is the plane z = 0; the origin lies on it at the midpoint between the two plugs' initial body centres (`object/SPECS.md`). The table is a 1.20 × 1.20 m block, 0.03 m thick, centred at (0.10, 0.00) with its top face at z = 0; the floor is at z = −0.75 m.
- **Wrist frame:** the URDF root link `r_mount` of the hand (`hardware/SPECS.md` section 3).
- **Object state frames:** a geometric frame fixed to each object, defined in `object/SPECS.md`. Object positions refer to that frame's origin, never implicitly to the centre of mass.
- **Orientation:** unit quaternion `(w, x, y, z)` that rotates frame vectors into the world frame. Every quaternion stream in the observation is sign-continuous: at step 0 `w ≥ 0`, afterwards each value takes the sign with a non-negative dot product with the previous step's value. Both signs describe the same rotation; canonicalize yourself if you need a unique sign.
- **Velocities:** linear velocity of the frame origin and angular velocity, both in the world frame.
- **Time:** step `k` is at `t = 0.002 k` s; `t = 0` is the first policy step (after the target's 1 s settle phase, which the policy does not control). All state in the observation of step `k` is sampled at the same instant: after the last controller tick of command `k − 1` (for `k = 0`: at the end of the settle phase).

## 3. Observations

At each step, `act(obs)` receives a dictionary. Arrays are NumPy `float64` unless stated otherwise.

**Robot**

| Key | Shape | Description |
|---|---|---|
| `q` | `(20,)` | Finger joint positions [rad], with encoder noise (`hardware/SPECS.md` section 6) |
| `qd` | `(20,)` | Finger joint velocities [rad/s], with encoder noise |
| `prev_q_target` | `(3, 20)` | Previous three finger position targets as commanded, oldest first |
| `prev_qd_target` | `(3, 20)` | Previous three finger velocity targets, oldest first (`None` recorded as zeros) |
| `wrist_position` | `(3,)` | Wrist-frame origin in the world [m] |
| `wrist_orientation` | `(4,)` | Wrist-frame orientation `(w, x, y, z)` |
| `wrist_linear_velocity` | `(3,)` | Velocity of the wrist-frame origin, world frame [m/s] |
| `wrist_angular_velocity` | `(3,)` | Wrist angular velocity, world frame [rad/s] |
| `prev_wrist_position_target` | `(3, 3)` | Previous three **executed** wrist position targets (after the limits of section 4), oldest first [m] |
| `prev_wrist_orientation_target` | `(3, 4)` | Previous three executed wrist orientation targets `(w, x, y, z)`, oldest first |
| `step` | int | Control step, 0–7499 |

At step 0, `prev_q_target` holds three copies of the initial finger configuration `q₀`, `prev_qd_target` holds zeros, and the wrist target histories hold three copies of the initial wrist pose. The wrist state is exact (no noise); the finger encoders keep their noise.

**Objects** (two objects: the white plug (index 0) and the black plug (index 1); order and state frames in `object/SPECS.md`)

| Key | Shape | Description |
|---|---|---|
| `object_position` | `(2, 3)` | State-frame origin of each object in the world [m] |
| `object_orientation` | `(2, 4)` | State-frame orientation `(w, x, y, z)` |
| `object_linear_velocity` | `(2, 3)` | Velocity of the state-frame origin, world frame [m/s] |
| `object_angular_velocity` | `(2, 3)` | Angular velocity, world frame [rad/s] |
| `goal_defined` | `(2,)` int64 | 1 if a goal is defined for the object, else 0; constant |
| `goal_position` | `(2, 3)` | Goal position of the object's state-frame origin [m]; NaN where undefined or unconstrained; constant |
| `goal_orientation` | `(2, 4)` | Goal orientation `(w, x, y, z)`; NaN where undefined; constant |
| `goal_free_axis` | `(2, 3)` | State-frame axis about which rotation is ignored for the goal; zeros = none; constant |

Object values are the target's exact simulation state (no noise). The leading object axis is present even for a single object.

**Not observed:** camera images or depth, estimated object states, contacts or contact forces, joint torques or motor currents, physical parameters (mass, friction, inertia, damping, stiffness) of the target, the evaluation's results, scores or rewards. Contact flags, videos and the official evaluation are available after the rollout (`FEEDBACK.md`). You may use any subset of the observation.

The policy may keep internal state; `reset()` initializes it.

## 4. Actions

`act(obs)` returns a dictionary:

| Key | Shape | Required | Description |
|---|---|---|---|
| `q_target` | `(20,)` | yes | Absolute finger joint position targets [rad], clipped to the URDF joint limits before execution |
| `qd_target` | `(20,)` | no (`None` = zero) | Finger joint velocity targets [rad/s] |
| `wrist_position_target` | `(3,)` | yes | Wrist-frame origin target in the world [m] |
| `wrist_orientation_target` | `(4,)` | yes | Wrist-frame orientation target `(w, x, y, z)`; norm within [0.9, 1.1], normalized before use; either sign |
| `wrist_linear_velocity_target` | `(3,)` | no (`None` = zero) | Feed-forward velocity of the wrist-frame origin, world frame [m/s] |
| `wrist_angular_velocity_target` | `(3,)` | no (`None` = zero) | Feed-forward angular velocity, world frame [rad/s] |

Values must be finite `float32` or `float64`; finger arrays in vendor URDF joint order. Unknown keys are refused.

**Wrist command limits** (applied at every step, `hardware/SPECS.md` section 4): the executed position target moves from the previous executed target toward `wrist_position_target` by at most 1.0 m/s × 2 ms and is then clipped to the wrist workspace box; the executed orientation target rotates toward `wrist_orientation_target` along the shortest arc by at most 3.0 rad/s × 2 ms; the feed-forward velocities are clipped to norms of 1.0 m/s and 3.0 rad/s. A command is never applied instantaneously: the wrist moves only through the saturated wrist controller. Commands beyond the limits are not a failure; the executed targets and limit flags are in the rollout log (`FEEDBACK.md`).

The target environment initializes the hand and the two plugs on the table, calls `reset()`, then calls `act(obs)` once per step and applies each command for 2 ms. A missing, non-finite or wrongly shaped value, a wrist orientation that is not a unit quaternion, an exception, or no answer within 5 s is a policy failure and ends the trial. Finger motor speed and effort limits apply, also to joints back-driven by contact; the hardware rules are in `hardware/SPECS.md` section 7.

## 5. Determinism

For identical observation histories after `reset()`, `act()` must return bit-identical actions.

See `PACKAGE.md` for packaging, sandbox, and runtime requirements.
