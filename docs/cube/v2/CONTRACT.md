# Policy Interface

## 1. Control

- **Robot:** Wuji Hand 2, 20 joints in vendor URDF order (`hardware/SPECS.md`).
- **Policy frequency:** 500 Hz (2 ms per step).
- **PD controller frequency:** 1 kHz, holding each command for two controller ticks.
- **Episode:** 40 s (20,000 policy steps). The episode is not ended by task events such as dropping the object; it ends early only on a policy failure (section 3).
- **Units:** SI (m, kg, s, rad, N·m).

## 2. Observations

At each step, `act(obs)` receives a dictionary:

| Key | Shape | Description |
|---|---|---|
| `q` | `(20,)` | Joint positions [rad], with encoder noise |
| `qd` | `(20,)` | Joint velocities [rad/s], with encoder noise |
| `prev_q_target` | `(3, 20)` | Previous three position targets, oldest first |
| `prev_qd_target` | `(3, 20)` | Previous three velocity targets, oldest first |
| `step` | int | Control step, 0–19999 |
| `scramble` | `(3, 2)` | The scramble, rows `[face, quarter_turns]` (`TASK.md`); float64 with integer values, identical at every step |

Previous targets are recorded before clipping; `None` velocity targets are recorded as zeros. At step 0, `prev_q_target` holds three copies of the initial configuration `q₀` (`hardware/SPECS.md`) and `prev_qd_target` holds zeros. Measured `q` may differ from `q₀` because of settling and encoder noise.

The policy receives **joint-only observations**: no camera images, object state, contacts, or forces. Camera data and sensor-estimated object tracks are available only after the rollout (`FEEDBACK.md`).

The policy may keep internal state; `reset()` initializes it.

## 3. Actions

`act(obs)` returns `(q_target, qd_target)`:

- `q_target`: `(20,)` absolute joint position targets [rad], clipped to the URDF joint limits before execution.
- `qd_target`: `(20,)` joint velocity targets [rad/s], or `None` (zero).
- Values must be finite `float32` or `float64`, in vendor URDF joint order.

The target environment initializes the hand and the scrambled cube, calls `reset()`, then calls `act(obs)` once per step and applies each command for 2 ms. A non-finite or wrongly shaped action, an exception, or no answer within 5 s is a policy failure and ends the trial. Motor speed and effort limits apply, also to joints back-driven by contact; the hardware rules are in `hardware/SPECS.md` section 6.

## 4. Determinism

For identical observation histories after `reset()`, `act()` must return bit-identical actions.

See `PACKAGE.md` for packaging, sandbox, and runtime requirements.
