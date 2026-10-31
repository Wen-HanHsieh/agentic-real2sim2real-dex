# Hardware Validation Tool

`r2s2r-hwcheck` checks finger joint trajectories against the hardware rules of `hardware/SPECS.md` section 7, using the machine-readable specification of the trajectory's hand: `hardware/hardware_spec.json` (right hand, `hwspec-1.1`) or `hardware/hardware_spec_left.json` (left hand, `hwspec-1.1L`). With `joint_names` in the input, the tool picks the specification of that hand (`r_*` right, `l_*` left) when both files are next to each other; the names must be those of one hand. The target environment's evaluation applies the same rules (`FEEDBACK.md` section 2). The tool is simulator-independent and needs only NumPy. The wrist has no hardware rule beyond its controller and is not checked.

Passing a local check does not guarantee compliance during target execution: the target rollout is a different trajectory.

## 1. Usage

```bash
r2s2r-hwcheck traj.npz                    # simulator state (exact)
r2s2r-hwcheck traj.npz --measured         # noisy encoder readings
r2s2r-hwcheck traj.npz --dt 0.001         # sample spacing when traj.npz has no t
r2s2r-hwcheck traj.npz --json report.json
python tools/hwcheck/hwcheck.py traj.npz --spec hardware/hardware_spec.json        # right hand
python tools/hwcheck/hwcheck.py traj.npz --spec hardware/hardware_spec_left.json   # left hand
```

Exit code 1 if a violation or an invalid action is found; otherwise 0, including for `uncertain` and `incomplete` results.

## 2. Input (`.npz`)

One row per sample:

| Key | Shape | Purpose |
|---|---|---|
| `q` | `(n, 20)` | Joint positions [rad] (required) |
| `qd` | `(n, 20)` | Joint velocities [rad/s] |
| `tau_applied` | `(n, 20)` | Torque applied by your actuator model [N·m], not the PD demand |
| `q_target`, `qd_target` | `(n, 20)` | Action validity and PD torque-demand estimate |
| `t` | `(n,)` | Sample times [s], or `--dt` |
| `joint_names` | `(20,)` | Column order and hand; default: the URDF order of the specification's hand |

Sample at your physics rate (for example 1 kHz) to cover every PD tick. Missing inputs are reported as not checked. The target's `logs/trial_0.npz` (`FEEDBACK.md` section 4) can be checked directly: its finger keys have these names.

## 3. Results

| Kind | Meaning |
|---|---|
| `simulated (exact)` | Simulator state; a value beyond a limit is a violation |
| `measured (noisy)` | With `--measured`: decided against encoder noise; may be `uncertain`; torque is not measurable |
| `estimated` | PD torque demand from the published gains; demand above the effort limit is saturation, reported but not a violation |
| `not checked` | The required input was not provided |

**Overall status:** `violation`, `compliant`, `uncertain` (measured data within noise of a limit), or `incomplete` (inputs missing).

How the target environment reports hardware compliance: `FEEDBACK.md` section 2.
