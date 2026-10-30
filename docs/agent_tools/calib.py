#!/usr/bin/env python3
"""Sim-to-target calibration (local, simulator-independent): compare your own simulation with a target rollout.

Everything here works on the feedback you fetched (the ground-truth state record, the rollout log with the commanded and
executed finger and wrist targets, timestamps, videos) and on trajectories your simulator produced through an adapter
you write (calib_adapter.py). Nothing is sent to the target; nothing here changes official results. The target's state
record is exact: every discrepancy is a property of your simulator, controller or contact model. No calibration method
is prescribed; the tool aligns, compares and attributes where the evidence allows (calib_diagnose.py).

Usage:
  r2s2r-calib extract <bundle.tgz|dir> -o <target.npz>                       feedback bundle -> trajectory file (r2s2r-traj/3)
  r2s2r-calib replay <target.npz> (--driver adapter.py | --adapter-cmd "CMD") -o <sim.npz>
                     [--mode action|state-step|state-segment] [--targets executed|commanded] [--steps N]
  r2s2r-calib compare <target.npz> <sim.npz> -o <dir> [--lag N] [--threshold RAD]   metrics.json (+ SVG plots)
  r2s2r-calib diagnose <target.npz> <sim.npz> -o <dir>                              metrics.json + report.md + PNG plots
  r2s2r-calib video <target.mp4> <sim.mp4> -o <out.mp4> [--sim-offset S] [--height PX]
  r2s2r-calib record DIR --hypothesis TEXT [--notes TEXT] [--config cfg.json] [--files F ...]

Trajectory file `r2s2r-traj/3` (NumPy .npz, allow_pickle never needed). One time base: control step k at t = 0.002 k.
  Log block, N rows (row k = control step k): `step`, `t`, measured `q`, `qd` (N, 20) in the vendor order `joint_names`,
  the finger commands `q_target`, `qd_target` (N, 20), the wrist commands `wrist_position_command` (N, 3),
  `wrist_orientation_command` (N, 4), `wrist_linear_velocity_command`, `wrist_angular_velocity_command` (N, 3), the
  executed wrist targets `wrist_position_target`, `wrist_orientation_target`, `wrist_linear_velocity_target`,
  `wrist_angular_velocity_target`, and `wrist_command_limited` (N, 5) bool.
  State block, R = N + 1 rows (row k = the state observed at step k; row N after the last command): `state_step`,
  `state_t`, `wrist_position` (R, 3), `wrist_orientation` (R, 4), `wrist_linear_velocity`, `wrist_angular_velocity`
  (R, 3), `object_position` (R, O, 3), `object_orientation` (R, O, 4), `object_linear_velocity`,
  `object_angular_velocity` (R, O, 3); optional `part_position` (R, P, 3), `part_orientation` (R, P, 4),
  `part_linear_velocity`, `part_angular_velocity` (R, P, 3), `cube_relative_orientation` (R, 8, 4),
  `cube_configuration` (R, 8) int64; contact flags `hand_object_contact` (R, O), `object_environment_contact` (R, O),
  `object_object_contact` (R, O, O) bool (target: the control-interval flags of the feedback; adapters may provide
  instantaneous ones).
  Constants: `joint_names` (20,), `object_names` (O,), `part_names` (P,), `part_object` (P,), `goal_*` when present.
  `meta` (JSON string): schema, source (target | sim), task, dt, steps, state_rows, submission, versions, object_names,
  the replay settings of a simulated file, and the target's own wrist tracking summary.
Quaternions are (w, x, y, z), world frame, as in FEEDBACK.md; a sign flip is not a difference. Files of another schema
are refused with the reason.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import calib_adapter as A  # noqa: E402

SCHEMA = "r2s2r-traj/3"
PROTOCOL = "r2s2r-feedback/3"
STATE_SCHEMA = "objstate-1"
DT = 0.002  # target control step [s]
LOG_KEYS = {"q": 20, "qd": 20, "q_target": 20, "qd_target": 20, "wrist_position_command": 3, "wrist_orientation_command": 4,
            "wrist_linear_velocity_command": 3, "wrist_angular_velocity_command": 3, "wrist_position_target": 3, "wrist_orientation_target": 4,
            "wrist_linear_velocity_target": 3, "wrist_angular_velocity_target": 3}
LIMIT_FLAGS = ("translation_rate", "workspace", "rotation_rate", "linear_velocity", "angular_velocity")
STATE_REQUIRED = {"wrist_position": (3,), "wrist_orientation": (4,), "wrist_linear_velocity": (3,), "wrist_angular_velocity": (3,),
                  "object_position": ("O", 3), "object_orientation": ("O", 4), "object_linear_velocity": ("O", 3), "object_angular_velocity": ("O", 3)}
STATE_OPTIONAL = {"part_position": ("P", 3), "part_orientation": ("P", 4), "part_linear_velocity": ("P", 3), "part_angular_velocity": ("P", 3),
                  "cube_relative_orientation": (8, 4), "cube_configuration": (8,),
                  "hand_object_contact": ("O",), "object_environment_contact": ("O",), "object_object_contact": ("O", "O")}
CONST_KEYS = ("joint_names", "object_names", "part_names", "part_object", "goal_defined", "goal_position", "goal_orientation", "goal_free_axis")
ACTION_SOURCES = {"executed": {"wrist_position_target": "wrist_position_target", "wrist_orientation_target": "wrist_orientation_target",
                               "wrist_linear_velocity_target": "wrist_linear_velocity_target", "wrist_angular_velocity_target": "wrist_angular_velocity_target"},
                  "commanded": {"wrist_position_target": "wrist_position_command", "wrist_orientation_target": "wrist_orientation_command",
                                "wrist_linear_velocity_target": "wrist_linear_velocity_command", "wrist_angular_velocity_target": "wrist_angular_velocity_command"}}
MODES = ("action", "state-step", "state-segment")
POS_THRESHOLD, ANG_THRESHOLD = 0.01, np.radians(10.0)  # "first step over" thresholds of the wrist / object comparison


class CalibError(Exception):
    """A refused input, with the reason (the command line exits with code 2 and the message on stderr)."""


# ------------------------------------------------------------------ quaternions (w, x, y, z)
def qnormalize(q):
    q = np.asarray(q, dtype=np.float64)
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


def geodesic(qa: np.ndarray, qb: np.ndarray) -> np.ndarray:
    """Angle [rad] between orientations qa and qb (..., 4), sign-independent, exact 0 for identical rotations."""
    qa, qb = qnormalize(qa), qnormalize(qb)
    s = np.where(np.sum(qa * qb, axis=-1, keepdims=True) < 0, -1.0, 1.0)
    return 2.0 * np.arctan2(np.linalg.norm(qa - s * qb, axis=-1), np.linalg.norm(qa + s * qb, axis=-1))


def _interp_quat(t_src, q_src, t_dst):
    """Per-row normalized linear interpolation of a sign-continuous quaternion series (fine for small steps)."""
    q = np.asarray(q_src, dtype=np.float64)
    flat = q.reshape(len(q), -1)
    out = np.stack([np.interp(t_dst, t_src, flat[:, j]) for j in range(flat.shape[1])], 1).reshape((len(t_dst),) + q.shape[1:])
    return qnormalize(out)


# ------------------------------------------------------------------ trajectory files
def validate(d: dict, where: str = "trajectory file") -> dict:
    """Check schema, keys and shapes; returns the parsed meta. Raises CalibError with every problem listed."""
    probs = []
    if str(d.get("schema", d.get("format", ""))) != SCHEMA:
        raise CalibError(f"{where}: schema {str(d.get('schema', d.get('format', '?')))!r} is not {SCHEMA} (files of the fixed-wrist generation or of "
                         "another version cannot be compared here; re-run extract on a feedback bundle of this environment)")
    try:
        meta = json.loads(str(d["meta"]))
    except (KeyError, ValueError):
        raise CalibError(f"{where}: missing or invalid meta") from None
    for k in ("step", "t", "joint_names", "object_names", "state_step", "state_t"):
        if k not in d:
            probs.append(f"missing {k}")
    if probs:
        raise CalibError(f"{where}: " + "; ".join(probs))
    N, R, O = len(d["step"]), len(d["state_step"]), len(d["object_names"])
    P = len(d["part_names"]) if "part_names" in d else 0
    if len(d["joint_names"]) != 20:
        probs.append(f"joint_names has {len(d['joint_names'])} entries, not 20")
    for k, w in LOG_KEYS.items():
        if k in d and np.shape(d[k]) != (N, w):
            probs.append(f"{k}: shape {np.shape(d[k])} != {(N, w)}")
    if "wrist_command_limited" in d and np.shape(d["wrist_command_limited"]) != (N, 5):
        probs.append(f"wrist_command_limited: shape {np.shape(d['wrist_command_limited'])} != {(N, 5)}")
    dims = {"O": O, "P": P}
    for k, shp in STATE_REQUIRED.items():
        want = (R,) + tuple(dims.get(x, x) for x in shp)
        if k not in d:
            probs.append(f"missing {k}")
        elif np.shape(d[k]) != want:
            probs.append(f"{k}: shape {np.shape(d[k])} != {want}")
    for k, shp in STATE_OPTIONAL.items():
        if k in d:
            want = (R,) + tuple(dims.get(x, x) for x in shp)
            if np.shape(d[k]) != want:
                probs.append(f"{k}: shape {np.shape(d[k])} != {want}")
    if R != N + 1 and meta.get("source") == "target":
        probs.append(f"state rows {R} != steps + 1 ({N + 1})")
    if N > 1 and abs(float(d["t"][1] - d["t"][0]) - float(meta.get("dt", DT))) > 1e-9:
        probs.append("t spacing differs from meta dt")
    for k in ("wrist_orientation", "object_orientation"):
        if k in d and len(d[k]) and np.abs(np.linalg.norm(np.asarray(d[k], dtype=float), axis=-1) - 1).max() > 1e-3:
            probs.append(f"{k}: not unit quaternions")
    if probs:
        raise CalibError(f"{where}: " + "; ".join(probs))
    return meta


def load_traj(p: Path) -> dict:
    p = Path(p)
    if not p.is_file():
        raise CalibError(f"{p}: no such file")
    try:
        z = np.load(p, allow_pickle=False)
    except (OSError, ValueError) as e:
        raise CalibError(f"{p}: not a NumPy .npz file ({e})") from None
    d = {k: z[k] for k in z.files}
    validate(d, str(p))
    return d


def save_traj(p: Path, d: dict) -> None:
    validate(d, "trajectory to save")
    np.savez_compressed(p, **d)


# ------------------------------------------------------------------ extract
def _bundle_files(src: Path) -> dict:
    """Files of a fetched feedback bundle (tar.gz or extracted directory), keyed by path relative to the bundle root."""
    src = Path(src)
    if not src.exists():
        raise CalibError(f"{src}: no such bundle")
    if src.is_dir():
        root = src if (src / "feedback.json").is_file() else next((p.parent for p in src.rglob("feedback.json")), None)
        if root is None:
            raise CalibError(f"no feedback.json under {src}")
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file() and not p.name.endswith(".mp4")}
    try:
        with tarfile.open(src, "r:*") as tf:
            out = {}
            for m in tf.getmembers():
                if m.isfile() and not m.name.endswith(".mp4"):
                    out[m.name.split("/", 1)[1] if "/" in m.name else m.name] = tf.extractfile(m).read()
    except tarfile.TarError as e:
        raise CalibError(f"{src}: not a tar archive ({e})") from None
    if "feedback.json" not in out:
        raise CalibError(f"{src}: no feedback.json at the bundle root")
    return out


def wrist_tracking(d: dict) -> dict:
    """The target's own wrist tracking: executed target of step k versus the wrist state observed at step k + 1."""
    n = min(len(d["wrist_position_target"]), len(d["wrist_position"]) - 1)
    if n <= 0:
        return {}
    ep = np.linalg.norm(d["wrist_position"][1:n + 1] - d["wrist_position_target"][:n], axis=1)
    eq = geodesic(d["wrist_orientation"][1:n + 1], d["wrist_orientation_target"][:n])
    out = {"steps": int(n), "position_error_m": {"rmse": float(np.sqrt(np.mean(ep ** 2))), "max": float(ep.max()), "final": float(ep[-1])},
           "orientation_error_deg": {"rmse": float(np.degrees(np.sqrt(np.mean(eq ** 2)))), "max": float(np.degrees(eq.max())), "final": float(np.degrees(eq[-1]))}}
    lim = d.get("wrist_command_limited")
    if lim is not None and len(lim):
        out["commands_limited_steps"] = {k: int(lim[:, i].sum()) for i, k in enumerate(LIMIT_FLAGS)}
    return out


def finger_tracking(d: dict) -> dict:
    """Finger PD tracking in the record: measured q at step k + 1 versus the target commanded at step k (encoder noise included)."""
    n = min(len(d["q_target"]), len(d["q"]) - 1)
    if n <= 0:
        return {}
    e = d["q"][1:n + 1] - d["q_target"][:n]
    return {"steps": int(n), "rmse_rad": float(np.sqrt(np.mean(e ** 2))), "max_abs_rad": float(np.abs(e).max()),
            "worst_joint": str(d["joint_names"][int(np.argmax(np.sqrt(np.mean(e ** 2, axis=0))))])}


def extract(src: Path, out: Path) -> dict:
    f = _bundle_files(src)
    try:
        fb = json.loads(f["feedback.json"])
    except ValueError:
        raise CalibError("feedback.json is not JSON") from None
    if fb.get("protocol") != PROTOCOL:
        raise CalibError(f"feedback protocol {fb.get('protocol')!r} is not {PROTOCOL}: this bundle was produced by another environment generation "
                         "(for example sensor-based feedback without a state record); it cannot be extracted here")
    for need in ("logs/trial_0.npz", "state/trajectory.npz", "state/schema.json"):
        if need not in f:
            raise CalibError(f"bundle lacks {need}")
    schema = json.loads(f["state/schema.json"])
    if schema.get("schema") != STATE_SCHEMA:
        raise CalibError(f"state schema {schema.get('schema')!r} is not {STATE_SCHEMA}")
    log = np.load(io.BytesIO(f["logs/trial_0.npz"]), allow_pickle=False)
    st = np.load(io.BytesIO(f["state/trajectory.npz"]), allow_pickle=False)
    for k in list(LOG_KEYS) + ["joint_names", "wrist_command_limited"]:
        if k not in log.files:
            raise CalibError(f"logs/trial_0.npz lacks {k}")
    for k in list(STATE_REQUIRED) + ["step", "t", "object_names", "hand_object_contact", "object_environment_contact", "object_object_contact"]:
        if k not in st.files:
            raise CalibError(f"state/trajectory.npz lacks {k}")
    n, R = int(len(log["q"])), int(len(st["step"]))
    if R != n + 1:
        raise CalibError(f"state rows {R} and log rows {n} are not aligned (expected rows = steps + 1)")
    if not np.allclose(st["t"], st["step"] * DT, atol=1e-9):
        raise CalibError("state t is not 0.002 * step")
    d = {"schema": SCHEMA, "step": np.arange(n, dtype=np.int64), "t": np.arange(n) * DT, "joint_names": log["joint_names"],
         "state_step": np.asarray(st["step"], dtype=np.int64), "state_t": np.asarray(st["t"], dtype=np.float64)}
    for k in LOG_KEYS:
        d[k] = np.asarray(log[k], dtype=np.float64)
    d["wrist_command_limited"] = np.asarray(log["wrist_command_limited"], dtype=bool)
    for k in list(STATE_REQUIRED) + list(STATE_OPTIONAL):
        if k in st.files:
            a = st[k]
            d[k] = a.astype(bool) if k.endswith("_contact") else (a.astype(np.int64) if k == "cube_configuration" else np.asarray(a, dtype=np.float64))
    for k in CONST_KEYS[1:]:
        if k in st.files:
            d[k] = st[k]
    fr = json.loads(f["video/frames.json"]) if "video/frames.json" in f else {}
    rep = json.loads(f["verifier/report.json"]) if "verifier/report.json" in f else {}
    meta = {"schema": SCHEMA, "source": "target", "task": fb.get("task"), "submission_id": fb.get("submission_id"), "protocol": fb.get("protocol"),
            "policy_sha256": fb.get("policy_sha256"), "versions": fb.get("versions"), "criteria": fb.get("criteria"),
            "dt": DT, "steps": n, "state_rows": R, "duration_s": n * DT, "expected_steps": fb.get("expected_steps"),
            "object_names": [str(x) for x in st["object_names"]], "part_names": [str(x) for x in st["part_names"]] if "part_names" in st.files else [],
            "has_contacts": True, "video_fps": fr.get("fps"), "video_frames": fr.get("frames"),
            "official": {k: rep.get(k) for k in ("status", "success", "progress") if k in rep},
            "quaternions": "(w, x, y, z), world frame, sign-continuous; sign flips are not differences",
            "note": "q, qd measured (encoder noise); q_target, qd_target and wrist_*_command = the commands the policy sent; wrist_*_target = the "
                    "executed targets after the command limits; state rows = the exact state observed at each step (row N after the last command); "
                    "contact flags = any contact during the control interval ending at the row",
            "target_wrist_tracking": wrist_tracking(d), "target_finger_tracking": finger_tracking(d)}
    d["meta"] = json.dumps(meta)
    save_traj(Path(out), d)
    return meta


# ------------------------------------------------------------------ replay
def _state_row(d: dict, k: int) -> dict:
    s = {key: d[key][k] for key in list(STATE_REQUIRED) + list(STATE_OPTIONAL) if key in d}
    if "q" in d and len(d["q"]):
        kk = min(k, len(d["q"]) - 1)
        s["q"], s["qd"] = d["q"][kk], d["qd"][kk]
    return s


def _action(d: dict, k: int, targets: str) -> dict:
    a = {"q_target": d["q_target"][k], "qd_target": d["qd_target"][k], "targets": targets}
    for key, src in ACTION_SOURCES[targets].items():
        a[key] = d[src][k]
    return a


def contact_segments(d: dict, min_len: int = 10) -> list:
    """Contact phases from the target's flags: runs of identical (hand, environment) contact labels over all objects.
    Returns [{"start", "end", "label"}] with end exclusive on the state rows; runs shorter than min_len rows are merged
    into their predecessor."""
    R = len(d["state_step"])
    if "hand_object_contact" not in d:
        return [{"start": 0, "end": R, "label": "unknown (no contact flags)"}]
    hc, ec = np.asarray(d["hand_object_contact"], bool), np.asarray(d["object_environment_contact"], bool)
    O = hc.shape[1]
    names = [str(x) for x in d["object_names"]]

    def lab(k):
        parts = []
        for i in range(O):
            parts.append(f"{names[i]}:" + ("hand+env" if hc[k, i] and ec[k, i] else "hand" if hc[k, i] else "env" if ec[k, i] else "free"))
        return " ".join(parts)

    labels = [lab(k) for k in range(R)]
    segs = []
    s = 0
    for k in range(1, R + 1):
        if k == R or labels[k] != labels[s]:
            segs.append({"start": s, "end": k, "label": labels[s]})
            s = k
    merged = []
    for sg in segs:
        if merged and sg["end"] - sg["start"] < min_len:
            merged[-1]["end"] = sg["end"]
        else:
            merged.append(dict(sg))
    return merged


def replay(target: dict, adapter, mode: str = "action", targets: str = "executed", steps: int | None = None, source: str = "sim") -> dict:
    """Drive the adapter with the target's action sequence; returns a trajectory dict (same layout, source 'sim')."""
    if mode not in MODES:
        raise CalibError(f"unknown replay mode {mode!r}")
    if targets not in ACTION_SOURCES:
        raise CalibError(f"unknown targets {targets!r}")
    n = len(target["q_target"]) if steps is None else max(0, min(steps, len(target["q_target"])))
    caps = getattr(adapter, "capabilities", {}) or {}
    if mode != "action" and not caps.get("set_state"):
        raise CalibError(f"replay mode {mode} needs an adapter with set_state (state replay); this adapter declares none")
    seg_starts = set()
    if mode == "state-segment":
        seg_starts = {sg["start"] for sg in contact_segments(target)} - {0}
    rows = [adapter.reset(_state_row(target, 0))]
    resets = []
    for k in range(n):
        if (mode == "state-step" and k > 0) or (mode == "state-segment" and k in seg_starts):
            adapter.set_state(_state_row(target, k))
            resets.append(k)
        adapter.apply(_action(target, k, targets))
        rows.append(adapter.read_state())
    keys = [k for k in list(STATE_REQUIRED) + list(STATE_OPTIONAL) if all(k in r for r in rows)]
    missing = [k for k in STATE_REQUIRED if k not in keys]
    if missing:
        raise CalibError(f"adapter states lack required keys: {missing}")
    out = {"schema": SCHEMA, "step": np.arange(n, dtype=np.int64), "t": np.arange(n) * DT, "joint_names": target["joint_names"],
           "state_step": np.arange(n + 1, dtype=np.int64), "state_t": np.arange(n + 1) * DT}
    for k in keys:
        arr = np.stack([np.asarray(r[k]) for r in rows])
        out[k] = arr.astype(bool) if k.endswith("_contact") else (arr.astype(np.int64) if k == "cube_configuration" else np.asarray(arr, dtype=np.float64))
    if all("q" in r for r in rows):  # log convention: row k = the measurement at step k
        out["q"] = np.stack([np.asarray(r["q"], dtype=np.float64).reshape(20) for r in rows])[:n]
        out["qd"] = np.stack([np.asarray(r.get("qd", np.zeros(20)), dtype=np.float64).reshape(20) for r in rows])[:n]
    for k, src in ACTION_SOURCES[targets].items():  # what the adapter was fed (as executed targets of the sim file)
        out[k] = target[src][:n]
    for k in ("q_target", "qd_target"):
        out[k] = target[k][:n]
    for k in CONST_KEYS[1:]:
        if k in target:
            out[k] = target[k]
    tmeta = json.loads(str(target["meta"]))
    meta = {"schema": SCHEMA, "source": source, "task": tmeta.get("task"), "replay_of": tmeta.get("submission_id"), "dt": DT, "steps": n, "state_rows": n + 1,
            "object_names": tmeta.get("object_names"), "replay": {"mode": mode, "targets": targets, "state_resets_at_steps": resets, "adapter_capabilities": caps},
            "quaternions": tmeta.get("quaternions")}
    out["meta"] = json.dumps(meta)
    validate(out, "replayed trajectory")
    return out


# ------------------------------------------------------------------ align and compare
def align(tg: dict, sm: dict) -> tuple[dict, dict, dict]:
    """Common state rows at the target's instants. Same dt: truncate to the common length. Higher sim rate: resample the sim
    onto the target's rows. Lower sim rate: refused (the comparison needs a value at every target step)."""
    tm, sm_meta = json.loads(str(tg["meta"])), json.loads(str(sm["meta"]))
    dt_t, dt_s = float(tm.get("dt", DT)), float(sm_meta.get("dt", DT))
    info = {"target_dt": dt_t, "sim_dt": dt_s, "target_rows": int(len(tg["state_step"])), "sim_rows": int(len(sm["state_step"]))}
    if dt_s > dt_t + 1e-12:
        raise CalibError(f"the simulated file is sampled at {1 / dt_s:.0f} Hz, slower than the target's {1 / dt_t:.0f} Hz: record your simulator at the control rate "
                         "(or faster) so that every target step has a counterpart")
    if abs(dt_s - dt_t) < 1e-12:
        R = min(len(tg["state_step"]), len(sm["state_step"]))
        s2 = {k: v[:R] for k, v in sm.items() if k in STATE_REQUIRED or k in STATE_OPTIONAL}
        info["method"] = "same rate: truncated to the common length" if len(tg["state_step"]) != len(sm["state_step"]) else "same rate and length"
    else:
        t_t, t_s = tg["state_t"], sm["state_t"]
        R = int(np.sum(t_t <= t_s[-1] + 1e-9))
        t_dst = t_t[:R]
        s2 = {}
        for k in list(STATE_REQUIRED) + list(STATE_OPTIONAL):
            if k not in sm:
                continue
            a = sm[k]
            if k.endswith("orientation"):
                s2[k] = _interp_quat(t_s, a, t_dst)
            elif a.dtype == bool or k == "cube_configuration":
                idx = np.clip(np.searchsorted(t_s, t_dst, side="right") - 1, 0, len(t_s) - 1)
                s2[k] = a[idx]
            else:
                flat = a.reshape(len(a), -1)
                s2[k] = np.stack([np.interp(t_dst, t_s, flat[:, j]) for j in range(flat.shape[1])], 1).reshape((R,) + a.shape[1:])
        info["method"] = f"sim at {1 / dt_s:.0f} Hz resampled onto the target's {1 / dt_t:.0f} Hz rows (linear; quaternions normalized)"
    info["rows_compared"] = int(R)
    t2 = {k: v[:R] for k, v in tg.items() if k in STATE_REQUIRED or k in STATE_OPTIONAL}
    return t2, s2, info


def _series(e: np.ndarray, thr: float | None = None, scale: float = 1.0) -> dict:
    e = np.asarray(e, dtype=np.float64) * scale
    if e.size == 0:
        return {"rmse": None, "max": None, "mean": None, "final": None, "argmax_step": None}
    r = {"rmse": float(np.sqrt(np.mean(e ** 2))), "max": float(e.max()), "mean": float(e.mean()), "final": float(e[-1]), "argmax_step": int(np.argmax(e))}
    if thr is not None:
        over = np.where(e > thr * scale)[0]
        r["first_step_over"] = int(over[0]) if len(over) else None
        r["threshold"] = thr * scale
    return r


def _joint_metrics(a, b, names, thr):
    e = b - a
    per = []
    for j, nm in enumerate(names):
        per.append({"joint": str(nm), "rmse": float(np.sqrt(np.mean(e[:, j] ** 2))), "max_abs": float(np.max(np.abs(e[:, j]))),
                    "mean": float(np.mean(e[:, j])), "final": float(e[-1, j])})
    over = np.where(np.any(np.abs(e) > thr, axis=1))[0]
    return {"steps_compared": int(len(e)), "rmse_all": float(np.sqrt(np.mean(e ** 2))), "max_abs_all": float(np.max(np.abs(e))),
            "first_step_over_threshold": (int(over[0]) if len(over) else None), "threshold_rad": thr,
            "worst_joints": sorted(per, key=lambda r: -r["rmse"])[:5], "per_joint": per}


def compare(tg: dict, sm: dict, lag: int = 50, thr: float = 0.1) -> dict:
    names = [str(x) for x in tg["joint_names"]]
    if [str(x) for x in sm["joint_names"]] != names:
        raise CalibError("joint_names differ between the two files")
    if [str(x) for x in tg["object_names"]] != [str(x) for x in sm["object_names"]]:
        raise CalibError(f"object_names differ: target {[str(x) for x in tg['object_names']]} vs sim {[str(x) for x in sm['object_names']]}")
    t2, s2, info = align(tg, sm)
    R = info["rows_compared"]
    res = {"schema": SCHEMA, "alignment": info, "rows_compared": R, "time_s": [0.0, float((max(R, 1) - 1) * DT)]}
    # fingers (log convention, row k = step k)
    if "q" in tg and "q" in sm and len(tg["q"]) and len(sm["q"]):
        n = min(len(tg["q"]), len(sm["q"]), R)
        a, b = tg["q"][:n], sm["q"][:n]
        res["joints"] = _joint_metrics(a, b, names, thr)
        if lag > 0 and n > 20:
            best = None
            for s in range(-lag, lag + 1):
                if s >= 0:
                    L = min(n, len(sm["q"]) - s)
                    e = sm["q"][s:s + L] - a[:L] if L > 0 else np.zeros((0, 20))
                else:
                    L = n + s
                    e = sm["q"][:L] - a[-s:-s + L] if L > 0 else np.zeros((0, 20))
                if len(e) < 10:
                    continue
                r = float(np.sqrt(np.mean(e ** 2)))
                if best is None or r < best[1]:
                    best = (s, r)
            rm = res["joints"]["rmse_all"]
            res["joints"]["best_shift"] = ({"sim_steps_after_target": best[0], "rmse_at_shift": best[1], "search_steps": lag} if best and best[1] < 0.95 * rm
                                           else {"sim_steps_after_target": 0, "rmse_at_shift": rm, "search_steps": lag, "note": "no shift reduces the rmse by 5 % or more"})
    if "q_target" in sm:
        m = min(len(tg["q_target"]), len(sm["q_target"]))
        res["action_sequence_max_abs_diff"] = float(np.max(np.abs(tg["q_target"][:m] - sm["q_target"][:m]))) if m else None
    # wrist
    w = {"position_error_m": _series(np.linalg.norm(s2["wrist_position"] - t2["wrist_position"], axis=1), POS_THRESHOLD),
         "orientation_error_deg": _series(geodesic(s2["wrist_orientation"], t2["wrist_orientation"]), ANG_THRESHOLD, 180.0 / np.pi),
         "linear_velocity_error_mps": _series(np.linalg.norm(s2["wrist_linear_velocity"] - t2["wrist_linear_velocity"], axis=1)),
         "angular_velocity_error_radps": _series(np.linalg.norm(s2["wrist_angular_velocity"] - t2["wrist_angular_velocity"], axis=1))}
    res["wrist"] = w
    # objects
    objs = {}
    for i, nm in enumerate(str(x) for x in tg["object_names"]):
        o = {"position_error_m": _series(np.linalg.norm(s2["object_position"][:, i] - t2["object_position"][:, i], axis=1), POS_THRESHOLD),
             "orientation_error_deg": _series(geodesic(s2["object_orientation"][:, i], t2["object_orientation"][:, i]), ANG_THRESHOLD, 180.0 / np.pi),
             "linear_velocity_error_mps": _series(np.linalg.norm(s2["object_linear_velocity"][:, i] - t2["object_linear_velocity"][:, i], axis=1)),
             "angular_velocity_error_radps": _series(np.linalg.norm(s2["object_angular_velocity"][:, i] - t2["object_angular_velocity"][:, i], axis=1))}
        for k in ("hand_object_contact", "object_environment_contact"):
            if k in s2 and k in t2:
                o[k + "_agreement"] = float(np.mean(s2[k][:, i].astype(bool) == t2[k][:, i].astype(bool)))
        objs[nm] = o
    res["objects"] = objs
    if "object_object_contact" in s2 and "object_object_contact" in t2:
        res["object_object_contact_agreement"] = float(np.mean(s2["object_object_contact"].astype(bool) == t2["object_object_contact"].astype(bool)))
    # parts (cube)
    if "part_position" in s2 and "part_position" in t2:
        ep = np.linalg.norm(s2["part_position"] - t2["part_position"], axis=2)
        parts = {"n_parts": int(ep.shape[1]), "position_error_m_max_over_parts": _series(ep.max(axis=1), POS_THRESHOLD),
                 "position_error_m_per_part": [float(np.sqrt(np.mean(ep[:, j] ** 2))) for j in range(ep.shape[1])]}
        if "part_orientation" in s2:
            eq = geodesic(s2["part_orientation"], t2["part_orientation"])
            parts["orientation_error_deg_max_over_parts"] = _series(eq.max(axis=1), ANG_THRESHOLD, 180.0 / np.pi)
        if "cube_configuration" in s2 and "cube_configuration" in t2:
            same = np.all(s2["cube_configuration"] == t2["cube_configuration"], axis=1)
            parts["configuration_agreement"] = float(same.mean())
            parts["first_configuration_mismatch_step"] = int(np.argmin(same)) if not same.all() else None
        if "cube_relative_orientation" in s2 and "cube_relative_orientation" in t2:
            parts["relative_orientation_error_deg_max"] = _series(geodesic(s2["cube_relative_orientation"], t2["cube_relative_orientation"]).max(axis=1), None, 180.0 / np.pi)
        res["parts"] = parts
    elif "part_position" in t2:
        res["parts"] = {"note": "the target has parts (cube articulation) but the simulated file carries none: not compared"}
    try:
        tm = json.loads(str(tg["meta"]))
        res["target_wrist_tracking"] = tm.get("target_wrist_tracking")
        res["target_finger_tracking"] = tm.get("target_finger_tracking")
        res["replay"] = json.loads(str(sm["meta"])).get("replay")
    except (ValueError, KeyError):
        pass
    return res


# ------------------------------------------------------------------ plots (plain SVG, no plotting library needed)
def _svg_lines(series, title, w=360, h=160):
    xs = np.concatenate([np.asarray(s[1], float) for s in series]); ys = np.concatenate([np.asarray(s[2], float) for s in series])
    ys = ys[np.isfinite(ys)]
    if len(ys) == 0:
        return f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}'><text x='8' y='16' font-size='11'>{title}: no data</text></svg>"
    x0, x1 = float(xs.min()), float(xs.max()); y0, y1 = float(ys.min()), float(ys.max())
    if y1 - y0 < 1e-9:
        y0, y1 = y0 - 1, y1 + 1
    L, Rm, T, B = 40, 8, 18, 18
    sx = lambda x: L + (x - x0) / max(x1 - x0, 1e-9) * (w - L - Rm)
    sy = lambda y: T + (y1 - y) / (y1 - y0) * (h - T - B)
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' font-family='Helvetica,Arial,sans-serif' font-size='10'>",
           f"<text x='{L}' y='12' font-weight='bold'>{title}</text>",
           f"<line x1='{L}' y1='{T}' x2='{L}' y2='{h - B}' stroke='#999'/><line x1='{L}' y1='{h - B}' x2='{w - Rm}' y2='{h - B}' stroke='#999'/>",
           f"<text x='{L - 4}' y='{T + 4}' text-anchor='end'>{y1:.3g}</text><text x='{L - 4}' y='{h - B}' text-anchor='end'>{y0:.3g}</text>",
           f"<text x='{w - Rm}' y='{h - 4}' text-anchor='end'>{x1:.3g} s</text><text x='{L}' y='{h - 4}'>{x0:.3g}</text>"]
    for i, (lab, x, y, col) in enumerate(series):
        x = np.asarray(x, float); y = np.asarray(y, float)
        keep = np.isfinite(y)
        pts, runs = [], []
        for xi, yi, k in zip(x, y, keep):
            if k:
                pts.append(f"{sx(xi):.1f},{sy(yi):.1f}")
            elif pts:
                runs.append(pts); pts = []
        if pts:
            runs.append(pts)
        for r in runs:
            step = max(1, len(r) // 600)
            out.append(f"<polyline fill='none' stroke='{col}' stroke-width='1.2' points='{' '.join(r[::step])}'/>")
        out.append(f"<text x='{L + 6 + 90 * i}' y='{T + 10}' fill='{col}'>{lab}</text>")
    out.append("</svg>")
    return "\n".join(out)


def _grid(svgs, cols, w, h):
    rows = (len(svgs) + cols - 1) // cols
    body = "".join(f"<g transform='translate({(i % cols) * w} {(i // cols) * h})'>{s}</g>" for i, s in enumerate(svgs))
    return f"<svg xmlns='http://www.w3.org/2000/svg' width='{cols * w}' height='{rows * h}'>{body}</svg>"


def plots(tg: dict, sm: dict, res: dict, out: Path) -> list:
    names = [str(x) for x in tg["joint_names"]]
    written = []
    if "joints" in res:
        n = res["joints"]["steps_compared"]
        t = np.arange(n) * DT
        js = [_svg_lines([("target", t, tg["q"][:n, j], "#1f6f3f"), ("sim", t, sm["q"][:n, j], "#5b3a9e"), ("command", t, tg["q_target"][:n, j], "#bbbbbb")], names[j])
              for j in range(len(names))]
        (out / "joints.svg").write_text(_grid(js, 4, 360, 160)); written.append("joints.svg")
    t2, s2, info = align(tg, sm)
    R = info["rows_compared"]
    t = np.arange(R) * DT
    ws = [_svg_lines([("|p_sim - p_target| [m]", t, np.linalg.norm(s2["wrist_position"] - t2["wrist_position"], axis=1), "#b42318")], "wrist position error", 720, 160),
          _svg_lines([("angle [deg]", t, np.degrees(geodesic(s2["wrist_orientation"], t2["wrist_orientation"])), "#b42318")], "wrist orientation error", 720, 160)]
    for ax, lab in ((0, "x"), (1, "y"), (2, "z")):
        s = [("target", t, t2["wrist_position"][:, ax], "#1f6f3f"), ("sim", t, s2["wrist_position"][:, ax], "#5b3a9e")]
        if "wrist_position_target" in tg:
            m = min(R, len(tg["wrist_position_target"]))
            s.append(("executed target", np.arange(m) * DT, tg["wrist_position_target"][:m, ax], "#bbbbbb"))
        ws.append(_svg_lines(s, f"wrist position {lab} [m]", 720, 160))
    (out / "wrist.svg").write_text(_grid(ws, 1, 720, 160)); written.append("wrist.svg")
    os_ = []
    for i, nm in enumerate(str(x) for x in tg["object_names"]):
        os_.append(_svg_lines([("|p_sim - p_target| [m]", t, np.linalg.norm(s2["object_position"][:, i] - t2["object_position"][:, i], axis=1), "#b42318")], f"{nm}: position error", 720, 160))
        for ax, lab in ((0, "x"), (1, "y"), (2, "z")):
            os_.append(_svg_lines([("target", t, t2["object_position"][:, i, ax], "#1f6f3f"), ("sim", t, s2["object_position"][:, i, ax], "#5b3a9e")], f"{nm}: position {lab} [m]", 720, 160))
        os_.append(_svg_lines([("angle [deg]", t, np.degrees(geodesic(s2["object_orientation"][:, i], t2["object_orientation"][:, i])), "#b42318")], f"{nm}: orientation error", 720, 160))
        if "hand_object_contact" in s2 and "hand_object_contact" in t2:
            os_.append(_svg_lines([("target", t, t2["hand_object_contact"][:, i].astype(float), "#1f6f3f"), ("sim", t, s2["hand_object_contact"][:, i].astype(float) + 0.02, "#5b3a9e")],
                                  f"{nm}: hand contact", 720, 120))
    (out / "objects.svg").write_text(_grid(os_, 1, 720, 160)); written.append("objects.svg")
    return written


# ------------------------------------------------------------------ video, record
def video(target_mp4: Path, sim_mp4: Path, out: Path, sim_offset: float = 0.0, height: int = 480) -> None:
    if shutil.which("ffmpeg") is None:
        raise CalibError("ffmpeg not found")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(target_mp4), "-itsoffset", f"{sim_offset:.3f}", "-i", str(sim_mp4),
           "-filter_complex", f"[0:v]scale=-2:{height}[a];[1:v]scale=-2:{height}[b];[a][b]hstack=inputs=2:shortest=1[v]",
           "-map", "[v]", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def record(root: Path, hypothesis: str, notes: str, config: Path | None, files: list) -> Path:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = re.sub(r"[^a-z0-9]+", "-", hypothesis.lower())[:40].strip("-") or "calibration"
    d = root / f"{stamp}_{slug}"
    d.mkdir()
    rec = {"recorded_utc": stamp, "hypothesis": hypothesis, "notes": notes, "files": {}}
    if config:
        rec["config"] = json.loads(Path(config).read_text())
    for f in files:
        f = Path(f)
        shutil.copy2(f, d / f.name)
        rec["files"][f.name] = _sha(f)
        if f.name == "metrics.json":
            m = json.loads(f.read_text())
            rec["summary"] = {"joints_rmse_all": (m.get("joints") or {}).get("rmse_all"), "wrist_position_rmse_m": ((m.get("wrist") or {}).get("position_error_m") or {}).get("rmse"),
                              "objects": {k: (v.get("position_error_m") or {}).get("rmse") for k, v in (m.get("objects") or {}).items()}}
    (d / "record.json").write_text(json.dumps(rec, indent=1))
    with open(root / "index.jsonl", "a") as fh:
        fh.write(json.dumps({"dir": d.name, "hypothesis": hypothesis, "summary": rec.get("summary")}) + "\n")
    return d


# ------------------------------------------------------------------ CLI
def _fmt(s: dict | None, unit: str) -> str:
    if not s or s.get("rmse") is None:
        return "n/a"
    return f"rmse {s['rmse']:.4g} {unit}, max {s['max']:.4g} {unit} at step {s['argmax_step']}" + (
        f", first over {s['threshold']:.3g} {unit}: {s['first_step_over']}" if "threshold" in s else "")


def print_compare(res: dict, thr: float) -> None:
    print(f"alignment: {res['alignment']['method']}; {res['rows_compared']} state rows compared")
    if "joints" in res:
        j = res["joints"]
        print(f"joints: {j['steps_compared']} steps, rmse {j['rmse_all']:.4f} rad, max {j['max_abs_all']:.4f} rad, first step over {thr} rad: "
              f"{j['first_step_over_threshold']}; worst: " + ", ".join(f"{r['joint']} {r['rmse']:.3f}" for r in j["worst_joints"]))
        if j.get("best_shift"):
            print(f"best time shift: sim {j['best_shift']['sim_steps_after_target']} steps after target (rmse {j['best_shift']['rmse_at_shift']:.4f})")
    w = res["wrist"]
    print(f"wrist: position {_fmt(w['position_error_m'], 'm')}; orientation {_fmt(w['orientation_error_deg'], 'deg')}")
    for k, v in res["objects"].items():
        print(f"object {k}: position {_fmt(v['position_error_m'], 'm')}; orientation {_fmt(v['orientation_error_deg'], 'deg')}"
              + (f"; hand-contact agreement {v['hand_object_contact_agreement']:.2f}" if "hand_object_contact_agreement" in v else ""))
    if res.get("parts"):
        pr = res["parts"]
        if "note" in pr:
            print("parts:", pr["note"])
        else:
            print(f"parts ({pr['n_parts']}): position {_fmt(pr['position_error_m_max_over_parts'], 'm')}"
                  + (f"; orientation {_fmt(pr['orientation_error_deg_max_over_parts'], 'deg')}" if "orientation_error_deg_max_over_parts" in pr else "")
                  + (f"; configuration agreement {pr['configuration_agreement']:.2f}" if "configuration_agreement" in pr else ""))


def _open_adapter(a, meta: dict):
    if bool(a.driver) == bool(a.adapter_cmd):
        raise CalibError("give exactly one of --driver adapter.py (Python class) or --adapter-cmd \"...\" (subprocess protocol)")
    if a.driver:
        return A.load_python_adapter(Path(a.driver), meta)
    return A.SubprocessAdapter(a.adapter_cmd, meta)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="r2s2r-calib", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("extract"); p.add_argument("bundle"); p.add_argument("-o", "--out", required=True)
    p = sub.add_parser("replay"); p.add_argument("target"); p.add_argument("--driver"); p.add_argument("--adapter-cmd"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--mode", choices=MODES, default="action"); p.add_argument("--targets", choices=tuple(ACTION_SOURCES), default="executed"); p.add_argument("--steps", type=int)
    p = sub.add_parser("compare"); p.add_argument("target"); p.add_argument("sim"); p.add_argument("-o", "--out")
    p.add_argument("--lag", type=int, default=50); p.add_argument("--threshold", type=float, default=0.1); p.add_argument("--no-plots", action="store_true")
    p = sub.add_parser("diagnose"); p.add_argument("target"); p.add_argument("sim"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--lag", type=int, default=50); p.add_argument("--threshold", type=float, default=0.1); p.add_argument("--no-plots", action="store_true")
    p = sub.add_parser("video"); p.add_argument("target_mp4"); p.add_argument("sim_mp4"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--sim-offset", type=float, default=0.0); p.add_argument("--height", type=int, default=480)
    p = sub.add_parser("record"); p.add_argument("dir"); p.add_argument("--hypothesis", required=True); p.add_argument("--notes", default="")
    p.add_argument("--config"); p.add_argument("--files", nargs="*", default=[])
    a = ap.parse_args(argv)
    if a.cmd == "extract":
        meta = extract(Path(a.bundle), Path(a.out))
        print(json.dumps({"wrote": a.out, **{k: meta[k] for k in ("task", "submission_id", "steps", "state_rows", "object_names", "official", "target_wrist_tracking", "target_finger_tracking")}}, indent=1))
    elif a.cmd == "replay":
        tg = load_traj(Path(a.target))
        meta = json.loads(str(tg["meta"]))
        meta["replay"] = {"mode": a.mode, "targets": a.targets, "joint_names": [str(x) for x in tg["joint_names"]]}
        ad = _open_adapter(a, meta)
        try:
            sm = replay(tg, ad, a.mode, a.targets, a.steps)
        finally:
            try:
                ad.close()
            except Exception:
                pass
        save_traj(Path(a.out), sm)
        print(json.dumps({"wrote": a.out, "steps": int(sm["meta"] and json.loads(str(sm["meta"]))["steps"]), "mode": a.mode, "targets": a.targets,
                          "state_resets": len(json.loads(str(sm["meta"]))["replay"]["state_resets_at_steps"])}))
    elif a.cmd in ("compare", "diagnose"):
        tg, sm = load_traj(Path(a.target)), load_traj(Path(a.sim))
        res = compare(tg, sm, a.lag, a.threshold)
        if a.out:
            out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
            (out / "metrics.json").write_text(json.dumps(res, indent=1))
            res["plots"] = [] if a.no_plots else plots(tg, sm, res, out)
            res["written"] = str(out)
        print_compare(res, a.threshold)
        if a.cmd == "diagnose":
            import calib_diagnose as D  # noqa: PLC0415
            rep = D.diagnose(tg, sm, res, Path(a.out), plots=not a.no_plots)
            print(f"report: {rep['report']}" + (f"; plots: {', '.join(rep['plots'])}" if rep.get("plots") else "; plots: none (matplotlib not available)"))
        if a.out:
            print("written:", res["written"], "metrics.json", *res.get("plots", []))
    elif a.cmd == "video":
        video(Path(a.target_mp4), Path(a.sim_mp4), Path(a.out), a.sim_offset, a.height)
        print("wrote", a.out)
    elif a.cmd == "record":
        d = record(Path(a.dir), a.hypothesis, a.notes, Path(a.config) if a.config else None, a.files)
        print("recorded", d)
    return 0


def cli() -> int:
    try:
        return main()
    except (CalibError, A.AdapterError) as e:
        sys.stderr.write(f"r2s2r-calib: {e}\n")
        return 2


if __name__ == "__main__":
    sys.exit(cli())
