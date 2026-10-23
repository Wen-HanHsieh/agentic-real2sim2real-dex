# Policy Package

## 1. Format

```text
policy.py
manifest.json
weights / configs (optional)
```

`policy.py` defines `load_policy(path)`, returning an object with `reset()` and `act(obs) -> (q_target, qd_target or None)`. See `CONTRACT.md`.

## 2. Deployment Runtime

- **Python:** 3.12; standard library, NumPy 2.5.4, PyTorch 2.14.1 (CPU).
- **Resources:** 1 CPU thread, no GPU, 8 GB virtual address space, 600 s CPU time.
- **Restrictions:** No network, subprocesses, or compiled extensions; read-only package, writable `TMPDIR` (≤ 64 MB), ≤ 256 open files.
- **Inference:** 2 ms per `act()` target; 5 s hard timeout.
- **Determinism:** Identical observation histories must produce bit-identical actions.

## 3. Sandbox Validation

Policies run in an isolated sandbox without access to target internals or privileged state.

Validation checks package integrity, dependencies, policy interface, action validity, determinism, and runtime limits.

Before submission, run the local preflight check:

```bash
r2s2r-preflight my_policy/
```

The remote `validate` command performs the authoritative package check. See `REMOTE_API.md`.

Invalid packages are rejected with clear errors without consuming evaluation budget.

## 4. Manifest

`manifest.json` contains SHA256 hashes of all package files except itself.

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

## 5. Submission

```bash
tar -C my_policy -czf my_policy.tgz .
```

Submit through `REMOTE_API.md`. See `example_package/` for a reference package.
