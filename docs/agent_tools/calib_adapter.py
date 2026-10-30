#!/usr/bin/env python3
"""Simulator adapter interface of r2s2r-calib: how your own simulator is driven during a replay.

You implement ONE of the two forms; the tool never imports a simulator itself.

1. Python class (in-process): a module that defines `make(meta) -> SimAdapter`, where the adapter object has

       reset(initial_state) -> state      start an episode at the target's step-0 state; returns your state at step 0
       apply(action) -> None              apply ONE control step (2 ms): hold the finger and wrist targets for the step
       read_state() -> state              the state after the last apply() (same instant as the target's next row)
       set_state(state) -> None           optional: teleport to a given state (needed for the state-replay modes)
       close() -> None                    optional

   and is used with `r2s2r-calib replay ... --driver my_adapter.py`.

2. Subprocess (any language, any interpreter): a command that reads one JSON object per line on stdin and writes one
   JSON object per line on stdout, used with `--adapter-cmd "python my_adapter.py ..."`. Requests and replies:

       {"cmd": "hello", "meta": {...}}                  -> {"ok": true, "capabilities": {"set_state": true, "contacts": true, "parts": false}}
       {"cmd": "reset", "state": {...}}                 -> {"ok": true, "state": {...}}
       {"cmd": "set_state", "state": {...}}             -> {"ok": true}
       {"cmd": "apply", "action": {...}}                -> {"ok": true}
       {"cmd": "read_state"}                            -> {"ok": true, "state": {...}}
       {"cmd": "close"}                                 -> {"ok": true}
       any failure                                      -> {"ok": false, "error": "..."}

   A Python adapter class can be served over this protocol with `serve(adapter_factory)` (bottom of this file), which
   lets it run in a different interpreter than the tool (for example the one your simulator is installed in).

`meta` is the trajectory file's metadata (task, dt, joint and object names, versions, the replay mode). A `state` is a
dict of the target's state record at one instant (lists, `(w, x, y, z)` quaternions, world frame; `FEEDBACK.md` section 3):

    q (20,), qd (20,)                                          finger joints, vendor URDF order (q, qd may be absent in set_state)
    wrist_position (3,), wrist_orientation (4,), wrist_linear_velocity (3,), wrist_angular_velocity (3,)
    object_position (O, 3), object_orientation (O, 4), object_linear_velocity (O, 3), object_angular_velocity (O, 3)
    optional: part_* (P, .), cube_relative_orientation (8, 4), cube_configuration (8,),
              hand_object_contact (O,), object_environment_contact (O,), object_object_contact (O, O)   (bools)

Your reset()/read_state() return the same keys (at least the robot and object blocks; optional blocks are compared when
present). An `action` is the dict of CONTRACT.md section 4 as lists: q_target (20,), qd_target (20,) or null,
wrist_position_target (3,), wrist_orientation_target (4,), wrist_linear_velocity_target (3,) or null,
wrist_angular_velocity_target (3,) or null, plus "targets": "executed" | "commanded" telling whether the wrist targets
are the target's executed ones (after its command limits) or the commands the policy sent (apply the limits yourself,
e.g. with tools/preflight/preflight.py CommandLimiter).
"""

from __future__ import annotations

import importlib.util
import json
import shlex
import subprocess
import sys
from pathlib import Path

CAPABILITIES = ("set_state", "contacts", "parts")


class AdapterError(RuntimeError):
    pass


class SimAdapter:
    """Base class (documentation only; duck typing is enough)."""

    capabilities = {"set_state": False, "contacts": False, "parts": False}

    def reset(self, initial_state: dict) -> dict:
        raise NotImplementedError

    def apply(self, action: dict) -> None:
        raise NotImplementedError

    def read_state(self) -> dict:
        raise NotImplementedError

    def set_state(self, state: dict) -> None:
        raise AdapterError("this adapter does not support set_state (state replay)")

    def close(self) -> None:
        pass


def _jsonable(x):
    if hasattr(x, "tolist"):
        return x.tolist()
    if isinstance(x, dict):
        return {k: _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if hasattr(x, "item"):
        return x.item()
    return x


class SubprocessAdapter(SimAdapter):
    """Drives an adapter process over the JSON-lines protocol."""

    def __init__(self, cmd: str, meta: dict, timeout: float = 600.0):
        self.proc = subprocess.Popen(shlex.split(cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.timeout = timeout
        r = self._call({"cmd": "hello", "meta": _jsonable(meta)})
        self.capabilities = {k: bool((r.get("capabilities") or {}).get(k, False)) for k in CAPABILITIES}

    def _call(self, msg: dict) -> dict:
        if self.proc.poll() is not None:
            raise AdapterError(f"adapter process exited with code {self.proc.returncode}")
        try:
            self.proc.stdin.write(json.dumps(msg) + "\n")
            self.proc.stdin.flush()
            line = self.proc.stdout.readline()
        except (BrokenPipeError, OSError) as e:
            raise AdapterError(f"adapter process broke the pipe ({e}); see its stderr") from None
        if not line:
            raise AdapterError("adapter process closed stdout (crashed?); see its stderr")
        try:
            r = json.loads(line)
        except ValueError:
            raise AdapterError(f"adapter wrote a non-JSON line: {line[:200]!r}") from None
        if not r.get("ok"):
            raise AdapterError(f"adapter refused {msg.get('cmd')}: {r.get('error', 'no reason given')}")
        return r

    def reset(self, initial_state: dict) -> dict:
        return self._call({"cmd": "reset", "state": _jsonable(initial_state)})["state"]

    def set_state(self, state: dict) -> None:
        self._call({"cmd": "set_state", "state": _jsonable(state)})

    def apply(self, action: dict) -> None:
        self._call({"cmd": "apply", "action": _jsonable(action)})

    def read_state(self) -> dict:
        return self._call({"cmd": "read_state"})["state"]

    def close(self) -> None:
        try:
            if self.proc.poll() is None:
                self._call({"cmd": "close"})
        except AdapterError:
            pass
        finally:
            try:
                self.proc.stdin.close()
            except OSError:
                pass
            self.proc.wait(timeout=10)


def load_python_adapter(path: Path, meta: dict) -> SimAdapter:
    """Import a driver module and build its adapter: `make(meta) -> adapter`."""
    spec = importlib.util.spec_from_file_location("r2s2r_calib_driver", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "make"):
        raise AdapterError(f"{path}: must define make(meta) -> adapter with reset/apply/read_state (calib_adapter.py)")
    ad = mod.make(meta)
    for fn in ("reset", "apply", "read_state"):
        if not callable(getattr(ad, fn, None)):
            raise AdapterError(f"{path}: adapter lacks {fn}()")
    caps = dict(getattr(ad, "capabilities", {}) or {})
    caps.setdefault("set_state", callable(getattr(type(ad), "set_state", None)) and type(ad).set_state is not SimAdapter.set_state)
    ad.capabilities = {k: bool(caps.get(k, False)) for k in CAPABILITIES}
    return ad


def serve(factory, stdin=None, stdout=None) -> int:
    """Serve an adapter over the JSON-lines protocol: `factory(meta) -> adapter`. Call from your adapter script's main."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    ad = None
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            cmd = msg.get("cmd")
            if cmd == "hello":
                ad = factory(msg.get("meta") or {})
                caps = {k: bool((getattr(ad, "capabilities", {}) or {}).get(k, False)) for k in CAPABILITIES}
                out = {"ok": True, "capabilities": caps}
            elif ad is None:
                out = {"ok": False, "error": "hello first"}
            elif cmd == "reset":
                out = {"ok": True, "state": _jsonable(ad.reset(msg["state"]))}
            elif cmd == "set_state":
                ad.set_state(msg["state"])
                out = {"ok": True}
            elif cmd == "apply":
                ad.apply(msg["action"])
                out = {"ok": True}
            elif cmd == "read_state":
                out = {"ok": True, "state": _jsonable(ad.read_state())}
            elif cmd == "close":
                ad.close()
                stdout.write(json.dumps({"ok": True}) + "\n")
                stdout.flush()
                return 0
            else:
                out = {"ok": False, "error": f"unknown cmd {cmd!r}"}
        except Exception as e:  # report, never die silently: the tool shows the message
            import traceback
            sys.stderr.write(traceback.format_exc())
            out = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        stdout.write(json.dumps(out) + "\n")
        stdout.flush()
    return 0
