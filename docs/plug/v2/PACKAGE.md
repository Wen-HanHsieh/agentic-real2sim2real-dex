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
policy.act(obs)  # returns (q_target, qd_target) or (q_target, None)
```

Observations and actions: `CONTRACT.md`.

## 2. Runtime Requirements

| Requirement | Limit |
|---|---|
| Python | 3.12 |
| Libraries | Python standard library, NumPy 2.5.4, PyTorch 2.14.1 (CPU) |
| CPU threads | 1 |
| GPU | Not available |
| Address space | ≤ 8 GB |
| Total CPU time | ≤ 600 s |
| `act()` inference time | 2 ms target |
| Hard policy-call timeout | 5 s |
| Writable temporary storage | `TMPDIR`, ≤ 64 MB |
| Open files | ≤ 256 |

The runtime is sandboxed: no network access or subprocesses; no compiled extensions or native libraries; package files are read-only. It has no access to target internals or privileged state.

The 2 ms target matches the 500 Hz control rate; a slower mean is reported as a warning. The 5 s timeout is a hard failure limit, not an acceptable inference rate.

## 3. Validation

Check locally before submitting:

```bash
r2s2r-preflight my_policy/
```

The remote `validate` command (`REMOTE_API.md`) is authoritative and is never charged. It checks: manifest and SHA-256 hashes, Python 3.12 syntax, no compiled code, `load_policy()` and `reset()` in the sandbox, five `act()` calls with valid outputs, determinism (`reset()` and replay give bit-identical actions), and inference time. `submit` runs the same checks first; a rejected package is not charged.

Passing validation does not guarantee a successful rollout.

## 4. Manifest

```json
{
  "name": "my_policy",
  "contract_version": "v1",
  "entry": "policy.py:load_policy",
  "files": {
    "policy.py": "<sha256 hex>",
    "weights.npz": "<sha256 hex>"
  }
}
```

- `entry` must be `policy.py:load_policy`.
- `files` must list every package file except `manifest.json`, each with its correct SHA-256.
- `contract_version` names the policy interface (`CONTRACT.md`); the current value is `"v1"`. It is independent of the feedback and evaluation versions (`REMOTE_API.md` section 7).

## 5. Submission

```bash
tar -C my_policy -czf my_policy.tgz .
```

Archive rules, submission, and feedback retrieval: `REMOTE_API.md`. A working example: `example_package/`.
