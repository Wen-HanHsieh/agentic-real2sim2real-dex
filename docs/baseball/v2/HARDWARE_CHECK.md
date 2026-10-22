# Hardware Validation Tool

`r2s2r-hwcheck` checks a joint trajectory from any simulator against the hardware requirements of
`hardware/SPECS.md` section 6 (`hardware/hardware_spec.json`, version `hwspec-1.0`). SuperDex judges its trials
with the same code, so a trajectory that passes here passes the same rules on the target. It needs only numpy and
does not depend on a simulator, learning method or controller.

## 0. The rules (copy of hardware/SPECS.md section 6)

These rules are the single hardware specification used by SuperDex to judge trials, by the sensor-based feedback
(`FEEDBACK.md`) and by the hardware validation tool (`HARDWARE_CHECK.md`). Machine-readable copy:
`hardware/hardware_spec.json` (version `hwspec-1.0`).

| Quantity | Requirement (every joint, every step) | Notes |
|---|---|---|
| Joint position | `lower − 0.02 ≤ q ≤ upper + 0.02` rad (URDF limits, section 2) | Joint stops are compliant: a joint that is pressed into its stop (by a target at or beyond the limit, by contact or by inertia) deflects slightly past the nominal URDF value. The allowance keeps pressing into a stop compliant; travel further past a stop is a violation. |
| Joint velocity | `|q̇| ≤` URDF max speed (section 2), no allowance | Applies to joints back-driven by contact. |
| Joint torque | `|τ_applied| ≤` URDF effort (section 2), no allowance | The actuator is current-limited: the PD torque kp (q_target - q) + kd (qd_target - qd) is saturated at the effort limit, so the applied torque never exceeds it on the target. A PD demand above the limit is saturation; it is reported, and it is not a violation. |
| Actions | `q_target`: shape (20,), finite; `qd_target`: `None` or shape (20,), finite | Targets outside the URDF limits are clipped. A non-finite or wrongly shaped action, a policy error, or no answer within 5 s ends the trial. |

Nothing else is enforced on the hardware. The torque–speed curve is not published; the applied torque never exceeds
the effort limit on the target, so a policy cannot violate the torque requirement there — check it in your own
simulator with `HARDWARE_CHECK.md` if your actuator model can exceed it.

## 1. Usage

```bash
r2s2r-hwcheck traj.npz                 # simulator state (exact)
r2s2r-hwcheck traj.npz --measured      # noisy encoder readings (sigma from SPECS.md section 5)
r2s2r-hwcheck traj.npz --json report.json
python tools/hwcheck/hwcheck.py traj.npz --spec hardware/hardware_spec.json   # the same tool from this bundle
```

Exit code 0 unless a violation or an invalid action is found.

## 2. Input (`.npz`, one row per sample)

| Key | Shape | Needed for |
|---|---|---|
| `q` | (n, 20) rad | position (required) |
| `qd` | (n, 20) rad/s | velocity |
| `tau_applied` | (n, 20) N·m | torque: the torque your actuator model applied (not the PD demand) |
| `q_target`, `qd_target` | (n, 20) | action validity; PD torque demand (estimate) |
| `t` | (n,) s | sample spacing (or `--dt`) |
| `joint_names` | (20,) | column order (default: URDF order, as in `hardware/SPECS.md`) |

Sample at your physics rate (e.g. 1 kHz) to see every PD tick.

## 3. Report

Each check is reported with how it was obtained:

- **simulated (exact)**: your simulator's state; a value beyond a limit is a violation.
- **measured (noisy)** with `--measured`: `violation` if a value, or the mean of 10 or 50 consecutive values, lies beyond
  a limit by more than k·σ/√window; `compliant` if every value lies inside by more than k·σ; otherwise `uncertain`
  (k makes a wrong clear decision at most 1 % likely). Torque is not measurable.
- **estimated**: the PD torque demand `kp (q_target − q) + kd (qd_target − qd)` from the published gains. A demand above the
  effort limit is saturation; it is reported, and it is not a violation.
- **not checked**: inputs you did not provide.

Overall status: `violation`, `compliant`, `uncertain` (measured data within noise of a limit) or `incomplete` (inputs missing).
