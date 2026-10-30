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

Observations and actions: `CONTRACT.md` (contract `v2`). Optional action keys may be omitted or set to `None`.

## 2. Runtime Requirements

| Requirement | Limit |
|---|---|
| Python | 3.12 (3.12.3 on the target) |
| Libraries | Python standard library, NumPy 2.5.4, PyTorch 2.14.1 (CPU build); nothing else (no SciPy) |
| CPU threads | 1 (BLAS and Torch thread pools are set to 1; up to 64 additional threads may be created) |
| GPU | Not available |
| Address space | ≤ 8 GB (allocation beyond it fails with `MemoryError`) |
| Total CPU time | ≤ 600 s per trial |
| `act()` inference time | 2 ms target |
| Hard policy-call timeout | 5 s per `act()`; 60 s for `load_policy()` and `reset()` |
| Writable temporary storage | `TMPDIR`, ≤ 64 MB in total; a single file ≤ 64 MB |
| Open files | ≤ 256 |

The 2 ms target matches the 500 Hz control rate; a slower mean is reported as a warning by `validate` and `submit`. The 5 s timeout is a hard failure limit, not an acceptable inference rate.

## 3. Sandbox (as enforced)

Your package runs in a confined process on the target. The rules below are enforced by the operating system before any of your code runs; a package that probes them simply sees the operation fail.

- **Files:** the package directory is read-only (your own files included); the policy runtime and the system libraries are readable; everything else of the target is unreadable. The only writable place is the private scratch directory named by `TMPDIR` (created per trial, deleted afterwards). The working directory and `HOME` are the package directory.
- **Scratch size:** writing more than 64 MB in total to `TMPDIR` during a trial stops the policy and ends the trial as a policy failure (charged); a single file larger than 64 MB fails with an error inside the policy.
- **Network and processes:** no sockets (TCP or local), no subprocesses, no `fork`/`exec`, no signals to other processes, no tracing or cross-process memory access. Threads within the process are allowed.
- **Compute:** CPU only (`CUDA_VISIBLE_DEVICES` is empty); the resource limits of section 2 (address space, CPU time, open files, file size; core dumps disabled).
- **Environment:** a clean environment (`PATH=/usr/bin:/bin`, thread-pool variables set to 1); `PYTHONPATH` is unset; only the package directory is on the import path besides the runtime's libraries. No compiled extensions or native libraries can be loaded from the package.
- **Interface:** the policy host calls `load_policy(path)`, `reset()` and `act(obs)` as `CONTRACT.md` describes and converts your action arrays to `float64`; it has no access to target internals beyond the observation.

A violation of these rules is not a separate offence: the affected operation fails inside your policy, and the trial continues or ends according to `CONTRACT.md` section 4 (an exception in `act()` is a policy failure).

## 4. Validation

Check locally before submitting:

```bash
r2s2r-preflight my_policy/
```

The remote `validate` command (`REMOTE_API.md`) is authoritative and is never charged. It checks: manifest, SHA-256 hashes and the declared contract version, Python 3.12 syntax, no compiled code, `load_policy()` and `reset()` in the sandbox, five `act()` calls on synthetic observations with exactly this task's keys, shapes and dtypes (`CONTRACT.md` section 3), each returning a valid action dictionary (section 4 of `CONTRACT.md`), determinism (`reset()` and replay give bit-identical actions), and inference time. `submit` runs the same checks first; a rejected package is not charged.

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
- `contract_version` names the policy interface (`CONTRACT.md`); the current value is `"v2"`. A package declaring another value (for example the joint-only contract `"v1"`) is refused by `validate` and `submit` before anything runs. It is independent of the feedback and evaluation versions (`REMOTE_API.md` section 7).

## 6. Submission

```bash
tar -C my_policy -czf my_policy.tgz .
```

Archive rules, submission, and feedback retrieval: `REMOTE_API.md`. A working example (a hold policy for the fingers and the wrist): `example_package/`.
