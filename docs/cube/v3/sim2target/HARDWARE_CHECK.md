# Hardware Validation Tool

`r2s2r-hwcheck` checks finger joint trajectories against the hardware rules of `hardware/SPECS.md` section 7, using the machine-readable specification of the trajectory's hand: `hardware/hardware_spec.json` (right hand, `hwspec-1.1`) or `hardware/hardware_spec_left.json` (left hand, `hwspec-1.1L`).

With `joint_names` in the input, the tool picks the specification of that hand (`r_*` right, `l_*` left) when both files are next to each other; the names must be those of one hand.

The target environment's evaluation applies the same rules (`sim2target/FEEDBACK.md` section 2).

The tool is simulator-independent and needs only NumPy. The wrist has no hardware rule beyond its controller and is not checked.

Passing a local check does not guarantee compliance during target execution: the target rollout is a different trajectory.

**Important:** Exit code 0 does not necessarily mean hardware compliant. Results marked `uncertain` or `incomplete` are not violations confirmed by the tool, but they are also not evidence of complete compliance. Automated research and submission gates must inspect the reported overall status and the completeness of individual checks.

## 1. Usage

```bash
r2s2r-hwcheck traj.npz                    # simulator state (exact)
r2s2r-hwcheck traj.npz --measured         # noisy encoder readings
r2s2r-hwcheck traj.npz --dt 0.001         # sample spacing when traj.npz has no t
r2s2r-hwcheck traj.npz --json report.json

python tools/hwcheck/hwcheck.py traj.npz --spec hardware/hardware_spec.json        # right hand
python tools/hwcheck/hwcheck.py traj.npz --spec hardware/hardware_spec_left.json   # left hand
```

**Exit codes:**

- `1`: a hardware violation or invalid action was found.
- `0`: no confirmed violation or invalid action was found, including results classified as `compliant`, `uncertain`, or `incomplete`.

The exit code indicates whether the checker found a violation; it does not independently certify full hardware compliance.

### Automated Validation

For automated research and submission decisions:

- **`compliant`:** All applicable required checks have sufficient evidence and pass.
- **`uncertain`:** Available measurements cannot establish whether a limit was exceeded.
- **`incomplete`:** One or more required checks lack sufficient input data.
- **`violation`:** At least one hardware limit or action-validity requirement was violated.

Only a complete `compliant` result may be treated as a passed local hardware check.

An `uncertain` or `incomplete` result must be reported explicitly and investigated before claiming compliance. Do not silently reinterpret either status as `compliant`.

Preserve the existing exit-code behavior for compatibility with scripts that use `r2s2r-hwcheck`.

### Hand Selection

Use the hardware specification for the task's hand variant:

- **Right hand:** `hardware/hardware_spec.json`, `hwspec-1.1`.
- **Left hand:** `hardware/hardware_spec_left.json`, `hwspec-1.1L`.

The current Cube task uses the left-hand variant. Tennis, Plug, and Pen use the right-hand variant, as specified by their respective `TASK_CONFIG.md`.

When `joint_names` is present, it must identify exactly one hand variant and match the corresponding specification.

If `joint_names` is absent, the caller must explicitly select or verify the correct hardware specification using the task configuration and documented tool behavior.

Do not infer that the right-hand specification is correct merely because it is the default.

The input joint-vector columns must follow the vendor URDF order of the selected hand.

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

Sample at your physics or controller rate (for example, 1 kHz) to cover every PD tick.

Missing inputs are reported as not checked.

### Sampling Requirements

The policy operates at 500 Hz, while the finger PD controller operates at 1 kHz.

Hardware compliance applies at every controller tick, including intermediate ticks between policy commands.

For local simulation:

- Prefer exact joint position, velocity, and applied torque sampled at 1 kHz or finer.
- Preserve the timestamps or specify the correct sampling interval with `--dt`.
- Include the actual applied torque, not only the PD torque demand.
- Include the executed joint trajectory, not only the policy command sequence.
- Ensure the selected joint ordering matches the correct hand specification.

A trajectory sampled only at 500 Hz may miss violations between consecutive policy steps.

A passing check on a lower-rate trajectory establishes compliance only for the samples checked; it does not certify compliance at unobserved controller ticks.

Do not interpolate missing samples and treat the interpolation as measured hardware evidence.

### Checking Target Rollout Logs

The target's `logs/trial_0.npz` (`sim2target/FEEDBACK.md` section 4) can be checked directly, but its finger `q` and `qd` values are noisy encoder observations.

When checking these logs, use:

```bash
r2s2r-hwcheck trial_0.npz --measured
```

The target rollout log does not expose the exact applied motor torque.

Consequently:

- Treat `q` and `qd` as noisy measurements, not exact ground-truth joint trajectories.
- Use the tool's measured-data uncertainty handling.
- Do not infer exact hardware compliance from these noisy observations alone.
- Missing `tau_applied` must remain `not checked`.
- Estimated PD torque demand is not a substitute for exact applied torque.
- The log's 500 Hz sampling may miss intermediate 1 kHz controller events.

The official target hardware verifier remains authoritative. It evaluates the target's exact joint states and applied torques at the controller rate (`sim2target/FEEDBACK.md` section 2).

The local checker is a diagnostic tool and does not override the official hardware result.

### Missing Inputs

The checker evaluates only the quantities supported by the input data.

If `qd`, `tau_applied`, or action-related fields are absent, the corresponding checks are reported as not checked according to the existing implementation.

A result with missing evidence must not be described as complete hardware compliance.

In particular, without exact applied torque, the checker cannot independently verify applied-torque compliance.

Do not replace missing applied torque with estimated PD demand and label it as measured or exact.

## 3. Results

| Kind | Meaning |
|---|---|
| `simulated (exact)` | Simulator state; a value beyond a limit is a violation |
| `measured (noisy)` | With `--measured`: decided against encoder noise; may be `uncertain`; torque is not measurable |
| `estimated` | PD torque demand from the published gains; demand above the effort limit is saturation, reported but not a violation |
| `not checked` | The required input was not provided |

**Overall status:** `violation`, `compliant`, `uncertain` (measured data within noise of a limit), or `incomplete` (inputs missing).

### Interpreting Hardware Compliance

| Overall status | Interpretation | Automated research decision |
|---|---|---|
| `compliant` | Available required checks are complete and pass | Passed local hardware check |
| `uncertain` | Measurement uncertainty prevents a definite compliance decision | Do not claim compliance; investigate |
| `incomplete` | Required evidence is missing | Do not claim compliance; obtain missing evidence |
| `violation` | A hardware or action-validity violation was detected | Failed local hardware check |

**A successful process exit is not the same as a successful hardware validation.**

Always inspect the structured result when making automated decisions.

If the checker reports `uncertain` or `incomplete`, preserve that status and the supporting evidence. Do not convert it to a pass merely because the command returned exit code 0.

### Authoritative Hardware Rules

The actual limits are defined by `hardware/SPECS.md` section 7 and the corresponding hand specification.

| Quantity | Compliance Rule |
|---|---|
| Joint position | `lower − 0.02 ≤ q ≤ upper + 0.02` rad |
| Joint velocity | `abs(qd) ≤ URDF max speed`, no allowance |
| Applied torque | `abs(tau_applied) ≤ URDF effort limit`, no allowance |
| Finger actions | `q_target` must be finite `(20,)`; `qd_target` must be `None` or finite `(20,)` |

The checks apply to every joint at every controller tick.

### Saturation Versus Violation

Distinguish requested actuator commands from executed hardware behavior.

**Finger position targets:**

`q_target` values outside the URDF joint limits are clipped to those limits by the target controller. An otherwise finite, correctly shaped out-of-range position target is not itself a hardware violation.

Actual joint position beyond the allowed `0.02` rad tolerance is a violation.

**PD torque demand:**

The finger controller computes:

```text
tau_demand = kp * (q_target - q) + kd * (qd_target - qd)
```

The target actuator saturates this demand at the joint's effort limit.

PD demand above the effort limit indicates torque saturation, not automatically a hardware violation.

Hardware compliance is determined by the actual applied torque.

**Joint velocity:**

Actual joint velocity beyond the URDF speed limit is a violation, including motion caused by contact or back-driving from wrist movement.

**Invalid actions:**

Missing, non-finite, or wrongly shaped finger actions are invalid according to `sim2target/CONTRACT.md` section 4.

These action-validity failures are distinct from ordinary clipping or torque saturation.

### Finger-Only Validation Boundary

`r2s2r-hwcheck` validates the documented finger-joint hardware limits and supported finger action fields.

It does not validate:

- The complete Contract v2 wrist action dictionary.
- Wrist position or orientation command validity.
- Wrist workspace and command-rate limiting.
- Wrist impedance-controller behavior.
- Task success or progress.
- Target rollout validity as a whole.

The wrist has no additional hardware compliance rule beyond its controller (`hardware/SPECS.md` section 4).

Wrist actions remain governed by `sim2target/CONTRACT.md`, and their execution is checked by the target runtime.

Passing `r2s2r-hwcheck` does not guarantee that a policy package passes preflight, that the target rollout will be valid, or that the task will succeed.

The official hardware result is reported in `sim2target/FEEDBACK.md` section 2.
