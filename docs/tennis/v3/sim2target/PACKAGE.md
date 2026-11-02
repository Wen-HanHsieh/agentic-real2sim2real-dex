# Policy Package

## 1. Package Format

A policy package is a directory containing:

- `policy.py`: the policy implementation.
- `manifest.json`: package metadata and SHA-256 hashes.
- Optional weights and configuration files.

`policy.py` must define:

```python
def load_policy(path):
    return policy
```

The returned object implements:

```python
policy.reset()
policy.act(obs)  # returns a dict: q_target, wrist_position_target, wrist_orientation_target, and the optional keys
```

Observations and actions: `sim2target/CONTRACT.md` (contract `v2`). Optional action keys may be omitted or set to `None`.

## 2. Runtime Requirements

| Requirement | Limit |
|---|---|
| Python | 3.12 (3.12.3 on the target) |
| Libraries | Python standard library, NumPy 2.5.4, PyTorch 2.14.1 (CPU build); nothing else (no SciPy) |
| Numerical compute threads | BLAS and PyTorch thread pools are restricted to 1 thread. Up to 64 additional threads may be created within the sandbox; these do not increase the CPU-time budget |
| GPU | Not available |
| Address space | ≤ 8 GB; allocations exceeding the limit fail. The precise failure behavior depends on the allocation path and sandbox enforcement |
| Total CPU time | ≤ 600 s per trial |
| `act()` inference time | 2 ms target |
| Hard policy-call timeout | 5 s per `act()`; 60 s for `load_policy()` and `reset()` |
| Writable temporary storage | `TMPDIR`, ≤ 64 MB in total; a single file ≤ 64 MB |
| Open files | ≤ 256 |

The 2 ms inference target matches the 500 Hz control rate; a slower mean is reported as a warning by `validate` and `submit`. The 5 s timeout is a hard failure limit, not an acceptable inference rate.

Exceeding the enforced address-space or CPU-time limits can cause allocation failure or policy termination. Policies must remain within these limits throughout the trial.

## 3. Sandbox (as enforced)

Your package runs in a confined process on the target. The rules below are enforced by the operating system before any of your code runs; a package that probes them simply sees the operation fail.

- **Files:** the package directory is read-only (your own files included); the policy runtime and the system libraries are readable; everything else of the target is unreadable. The only writable place is the private scratch directory named by `TMPDIR` (created per trial, deleted afterwards). The working directory and `HOME` are the package directory.
- **Scratch size:** writing more than 64 MB in total to `TMPDIR` during a trial stops the policy and ends the trial as a policy failure (charged); a single file larger than 64 MB fails with an error inside the policy.
- **Network and processes:** no sockets (TCP or local), no subprocesses, no `fork`/`exec`, no signals to other processes, no tracing or cross-process memory access. Threads within the process are allowed.
- **Compute:** CPU only (`CUDA_VISIBLE_DEVICES` is empty); the resource limits of section 2 (address space, CPU time, open files, file size; core dumps disabled).
- **Environment:** a clean environment (`PATH=/usr/bin:/bin`, thread-pool variables set to 1); `PYTHONPATH` is unset; only the package directory is on the import path besides the runtime's libraries. No compiled extensions or native libraries can be loaded from the package.
- **Interface:** the policy host calls `load_policy(path)`, `reset()` and `act(obs)` as `sim2target/CONTRACT.md` describes and converts your action arrays to `float64`; it has no access to target internals beyond the observation.

A violation of these rules is not a separate offence: the affected operation fails inside your policy, and the trial continues or ends according to `sim2target/CONTRACT.md` section 4 (an exception in `act()` is a policy failure).

## 4. Validation

Check locally before submitting:

```bash
r2s2r-preflight my_policy/
```

For the Cube task, use the left-hand configuration defined in `TASK_CONFIG.md`:

```bash
r2s2r-preflight my_policy/ --hand left
```

Alternatively:

```bash
R2S2R_HAND=left r2s2r-preflight my_policy/
```

The local preflight must use the correct hand variant and vendor URDF joint ordering for the task.

The remote `validate` command (`sim2target/REMOTE_API.md`) is authoritative and is never charged. It checks: manifest, SHA-256 hashes and the declared contract version, Python 3.12 syntax, no compiled code, `load_policy()` and `reset()` in the sandbox, five `act()` calls on synthetic observations with exactly your task's keys, shapes and dtypes (`sim2target/CONTRACT.md` section 3, `TASK_CONFIG.md` section 5), each returning a valid action dictionary (section 4 of `sim2target/CONTRACT.md`), determinism (`reset()` and replay give bit-identical actions), and inference time. `submit` runs the same checks first; a rejected package is not charged.

**Task-specific observations.** Synthetic observations must follow the exact task-specific schema, including documented undefined values and their validity indicators. For example, Plug goal-position and goal-orientation values may contain `NaN` when `goal_defined` is false. Such documented observation values are permitted by `sim2target/CONTRACT.md`; action outputs must still contain only valid finite values.

For Cube, validation must use the left-hand joint order and the task-specific observation fields, including cubie states and configuration indices, defined in `TASK_CONFIG.md`.

### Validation Scope

Package validation confirms that the package can be loaded and that its interface, basic execution, determinism, and sandbox requirements are satisfied.

It does not establish:

- **Rollout validity:** Whether a complete target rollout satisfies all runtime and hardware requirements.
- **Task success:** Whether the policy completes the manipulation task defined in `SUCCESS.md`.
- **Evaluation rankability:** Whether the official evaluation is eligible for ranking and regression comparisons.

These outcomes are determined by the official evaluation system after the rollout.

A valid rollout with task progress `0.0` remains rankable. An otherwise valid early task failure does not automatically make the result unrankable. Technically invalid rollouts are handled according to the official validity rules.

Passing validation does not guarantee a successful rollout.

## 5. Manifest

```json
{
  "name": "my_policy",
  "contract_version": "v2",
  "entry": "policy.py:load_policy",
  "files": {
    "policy.py": "<sha256 hex>",
    "weights.npz": "<sha256 hex>"
  }
}
```

- `entry` must be `policy.py:load_policy`.
- `files` must list every package file except `manifest.json`, each with its correct SHA-256.
- `contract_version` names the policy interface (`sim2target/CONTRACT.md`); the current value is `"v2"`. A package declaring another value (for example the joint-only contract `"v1"`) is refused by `validate` and `submit` before anything runs. It is independent of the feedback and evaluation versions (`sim2target/REMOTE_API.md` section 7).

## 6. Submission

```bash
tar -C my_policy -czf my_policy.tgz .
```

macOS metadata is ignored: archive members whose name starts with `._` (AppleDouble files that macOS `tar` adds) and anything under `__MACOSX/` are dropped before the package is checked and are never unpacked. Do not use file names starting with `._` in your package; a manifest that lists one is refused. On macOS, `COPYFILE_DISABLE=1 tar …` avoids these members altogether. `r2s2r-preflight` applies the same rule to the package directory: it skips such files with a warning and refuses a manifest that lists one.

Archive rules, submission, and feedback retrieval: `sim2target/REMOTE_API.md`. A working example (a hold policy for the fingers and the wrist): `example_package/`.
