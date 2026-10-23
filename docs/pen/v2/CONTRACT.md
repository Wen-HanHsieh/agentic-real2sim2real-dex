# Policy Interface

## 1. Control

- **Robot:** Wuji Hand 2, 20 joints in vendor URDF order (`hardware/SPECS.md`).
- **Frequency:** Policy 500 Hz (2 ms/step); PD controller 1 kHz with zero-order hold.
- **Episode:** 12 s (6000 steps), no early termination.
- **Units:** SI (m, kg, s, rad, N·m).

## 2. Observations

`obs` is a dictionary containing:

| Key | Shape | Description |
|---|---|---|
| `q` | `(20,)` | Joint positions [rad], with encoder noise |
| `qd` | `(20,)` | Joint velocities [rad/s], with encoder noise |
| `prev_q_target` | `(3, 20)` | Previous 3 position targets, oldest first |
| `prev_qd_target` | `(3, 20)` | Previous 3 velocity targets, oldest first |
| `step` | int | Current step (0–5999) |

Previous targets are recorded before clipping; `None` velocity targets are recorded as zeros.

The task-specific initial joint configuration `q₀` is defined in `hardware/SPECS.md`. At step 0, `prev_q_target` contains three exact copies of `q₀`, and `prev_qd_target` contains zeros. Measured `q` may differ due to passive settling and encoder noise.

No camera, object state, force, or contact observations are available. The policy may maintain internal state, initialized by `reset()`.

## 3. Actions

`policy.act(obs)` returns:

| Output | Shape | Description |
|---|---|---|
| `q_target` | `(20,)` | Absolute joint position targets [rad], clipped to URDF limits |
| `qd_target` | `(20,)` or `None` | Joint velocity targets [rad/s]; `None` means zero |

Joint vectors accept `float64` or `float32` and follow vendor URDF order.

The environment initializes the hand and object before calling `policy.reset()`. It then calls `policy.act(obs)` once per step and applies each command for 2 ms.

Actions must be finite and correctly shaped. Motor speed and effort limits apply, including to back-driven joints (`hardware/SPECS.md`).

## 4. Determinism

For the same observation sequence after `reset()`, `act()` must return bit-identical actions.

Runtime and packaging requirements are defined in `PACKAGE.md`.
