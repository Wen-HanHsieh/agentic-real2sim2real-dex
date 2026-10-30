#!/usr/bin/env python3
"""Kinematic reference adapter for r2s2r-calib (NumPy only; no physics). The hand follows its targets ideally: the fingers
sit at the clipped q_target, the wrist at the executed wrist target (or at the commanded one through the public command
limiter when the replay feeds commanded targets); the objects keep the state they were reset to (frozen, zero velocity);
no contacts. It is a reference, not a simulator: compared with a target rollout it shows the target's own controller
tracking error (wrist, fingers) and, for the objects, the whole motion the target produced. Use it to test the pipeline,
as a baseline for your own adapter, or as the in-process adapter example.

Driver use:  r2s2r-calib replay target.npz --driver tools/calib/calib_kinematic_adapter.py -o sim.npz
Subprocess:  r2s2r-calib replay target.npz --adapter-cmd "python3 tools/calib/calib_kinematic_adapter.py" -o sim.npz
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import calib_adapter as A  # noqa: E402

# URDF joint limits, vendor order (hardware/SPECS.md section 2)
LOWER = np.array([-1.187, -1.484, -1.047, -1.047] + [-1.047, -0.698, -1.047, -1.047] * 4)
UPPER = np.array([1.291, 0.698, 1.570, 1.570] + [1.570, 0.698, 2.094, 1.570] * 4)


class KinematicAdapter(A.SimAdapter):
    capabilities = {"set_state": True, "contacts": False, "parts": True}

    def __init__(self, meta: dict):
        self.meta = meta
        self.dt = float(meta.get("dt", 0.002))
        self.limiter = None
        self.state = None

    def _lim(self, p, q):
        try:
            from preflight import CommandLimiter, WORKSPACE  # the public limiter, if the tool ships beside preflight
            lo, hi = WORKSPACE.get(self.meta.get("task"), ((-10, -10, -10), (10, 10, 10)))
            lim = CommandLimiter(lo, hi, self.dt)
        except ImportError:
            return None
        lim.reset(p, q)
        return lim

    def reset(self, initial_state: dict) -> dict:
        s = {k: np.array(v, dtype=float) if not str(k).endswith("_contact") and k != "cube_configuration" else np.array(v) for k, v in initial_state.items()}
        s["q"] = np.clip(np.asarray(s.get("q", np.zeros(20)), dtype=float).reshape(20), LOWER, UPPER)
        s["qd"] = np.zeros(20)
        for k in ("wrist_linear_velocity", "wrist_angular_velocity"):
            s[k] = np.zeros(3)
        for k in ("object_linear_velocity", "object_angular_velocity", "part_linear_velocity", "part_angular_velocity"):
            if k in s:
                s[k] = np.zeros_like(s[k])
        for k in list(s):
            if k.endswith("_contact"):
                del s[k]  # no contact model: the keys are left out, so compare does not score them
        self.state = s
        self.limiter = self._lim(s["wrist_position"], s["wrist_orientation"])
        return self.read_state()

    def set_state(self, state: dict) -> None:
        for k, v in state.items():
            if k in ("q", "qd") or k in self.state:
                self.state[k] = np.array(v)
        self.state["q"] = np.asarray(self.state["q"], dtype=float).reshape(20)
        if self.limiter is not None:
            self.limiter.reset(self.state["wrist_position"], self.state["wrist_orientation"])

    def apply(self, action: dict) -> None:
        q_t = np.clip(np.asarray(action["q_target"], dtype=float).reshape(20), LOWER, UPPER)
        self.state["qd"] = (q_t - self.state["q"]) / self.dt
        self.state["q"] = q_t
        p, q = np.asarray(action["wrist_position_target"], float), np.asarray(action["wrist_orientation_target"], float)
        q = q / np.linalg.norm(q)
        if action.get("targets") == "commanded" and self.limiter is not None:
            ex = self.limiter(p, q, action.get("wrist_linear_velocity_target"), action.get("wrist_angular_velocity_target"))
            p, q = np.array(ex["position"]), np.array(ex["orientation"])
        self.state["wrist_linear_velocity"] = (p - self.state["wrist_position"]) / self.dt
        self.state["wrist_position"], self.state["wrist_orientation"] = p, q
        self.state["wrist_angular_velocity"] = np.zeros(3)

    def read_state(self) -> dict:
        return {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in self.state.items()}


def make(meta: dict) -> KinematicAdapter:
    return KinematicAdapter(meta)


if __name__ == "__main__":
    sys.exit(A.serve(make))
