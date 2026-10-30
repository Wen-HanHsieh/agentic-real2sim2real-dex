"""r2s2r-preflight: local pre-check of a policy package (contract v2) for the target environment. Nothing is sent anywhere.

Usage:  r2s2r-preflight [tennis|pen|plug|cube] <package_dir | package.tgz> [--steps N]
The task may be omitted: it is taken from $R2S2R_TASK, else from the one r2s2r-<task> command on PATH.
Run it with the Python you use for the policy (the target runs Python 3.12, numpy 2.5.4, torch 2.14.1 CPU).

Checks, in the order the target environment applies them:
  1. structure: policy.py at the root, manifest.json (entry, "contract_version": "v2", every file listed with its
     SHA256), Python 3.12 syntax, no compiled code, imports limited to the standard library, numpy, torch and the
     package's own modules. A manifest declaring another contract version (for example the joint-only "v1") is
     refused, as the target refuses it;
  2. sandboxed run, with restrictions like the target environment's: read-only package, private scratch TMPDIR, no network,
     no subprocesses, no signals to other processes, 8 GB address space, 600 s CPU, 256 open files, 64 MB per
     written file, 1 CPU thread, no GPU;
  3. load_policy(path), reset(), then act() for N steps (default: the full trial) on synthetic observations with
     exactly this task's keys, shapes and dtypes (CONTRACT.md section 3: float64 arrays, int64 for the integer
     fields, `step` an int). Each action must be a dict with the keys of CONTRACT.md section 4 (q_target (20,),
     wrist_position_target (3,), wrist_orientation_target (4,) with norm in [0.9, 1.1]; optional qd_target,
     wrist_linear_velocity_target, wrist_angular_velocity_target or None), all finite, no unknown keys; every call
     < 5 s; mean/max act() time against the 2 ms inference budget; total CPU time against 600 s;
  4. determinism: reset(), replay the first 200 observations, require bit-identical actions.
The synthetic observations hold the fingers at q0 with encoder noise and the objects near their initial state; the
wrist state follows the executed wrist target through the same command limiter as the target (CommandLimiter below:
rate limits, workspace box, feed-forward clipping), so the target histories in the observation are what the target
would record. No physics is simulated: a passing run shows that the package speaks the contract, nothing more.
Passing is necessary, not sufficient: the remote `validate` command runs the target environment's own check (never charged).
"""

import ast
import ctypes
import hashlib
import json
import math
import os
import resource
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import time

CONTRACT = "v2"
STEPS = {"tennis": 5000, "pen": 6000, "plug": 7500, "cube": 20000}  # 500 Hz x 10 s / 12 s / 15 s / 40 s
ALLOWED_THIRD_PARTY = {"numpy", "torch"}
COMPILED = (".so", ".pyd", ".dll", ".dylib")
ACT_TIMEOUT, BUDGET, CPU_LIMIT = 5.0, 0.002, 600
K_HIST = 3
DT = 0.002
NAN = float("nan")

# ---------------------------------------------------------------- the contract, per task (CONTRACT.md sections 3 and 4)
_ROBOT = {"q": ((20,), "float64"), "qd": ((20,), "float64"), "prev_q_target": ((3, 20), "float64"), "prev_qd_target": ((3, 20), "float64"),
          "prev_wrist_position_target": ((3, 3), "float64"), "prev_wrist_orientation_target": ((3, 4), "float64"),
          "wrist_position": ((3,), "float64"), "wrist_orientation": ((4,), "float64"), "wrist_linear_velocity": ((3,), "float64"),
          "wrist_angular_velocity": ((3,), "float64"), "step": ((), "int")}


def _objects(O):
    return {"object_position": ((O, 3), "float64"), "object_orientation": ((O, 4), "float64"),
            "object_linear_velocity": ((O, 3), "float64"), "object_angular_velocity": ((O, 3), "float64")}


OBS = {  # key -> (shape, dtype); exactly the observation key set of each task
    "tennis": {**_ROBOT, **_objects(1)},
    "pen": {**_ROBOT, **_objects(1)},
    "plug": {**_ROBOT, **_objects(2), "goal_defined": ((2,), "int64"), "goal_position": ((2, 3), "float64"),
             "goal_orientation": ((2, 4), "float64"), "goal_free_axis": ((2, 3), "float64")},
    "cube": {**_ROBOT, **_objects(1), "part_position": ((8, 3), "float64"), "part_orientation": ((8, 4), "float64"),
             "part_linear_velocity": ((8, 3), "float64"), "part_angular_velocity": ((8, 3), "float64"),
             "cube_relative_orientation": ((8, 4), "float64"), "cube_configuration": ((8,), "int64"), "scramble": ((3, 2), "float64")},
}
ACTION = {"q_target": ((20,), True), "qd_target": ((20,), False), "wrist_position_target": ((3,), True),
          "wrist_orientation_target": ((4,), True), "wrist_linear_velocity_target": ((3,), False),
          "wrist_angular_velocity_target": ((3,), False)}  # key: (shape, required)
# initial finger configuration q0 (vendor URDF order, hardware/SPECS.md section 2)
_CUPPED = [0.6, -0.3, 0.3, 0.2] + [0.6, 0.0, 1.4, 0.3] * 4
Q0 = {"tennis": _CUPPED, "cube": _CUPPED, "pen": [0.0, -1.4, 0.0, 0.0] + [0.0, 0.0, 1.2, 0.3] * 4,
      "plug": [0.3, -0.2, 0.2, 0.2] + [0.25, 0.0, 0.35, 0.15] * 4}
# initial wrist pose (hardware/SPECS.md section 3) and workspace box; wrist limits (section 4)
WRIST_INIT = {"tennis": ((0.027681, -0.002080, 0.307114), (0.553986, 0.421314, 0.439445, 0.567875)),
              "cube": ((0.027681, -0.002080, 0.307114), (0.553986, 0.421314, 0.439445, 0.567875)),
              "pen": ((0.028196, -0.002080, 0.304675), (0.534290, 0.445683, 0.463192, 0.548957)),
              "plug": ((-0.26, -0.08, 0.09), (0.35355339, -0.35355339, -0.61237244, 0.61237244))}
WORKSPACE = {"tennis": ((-0.30, -0.30, 0.05), (0.35, 0.30, 0.65)), "pen": ((-0.30, -0.30, 0.05), (0.35, 0.30, 0.65)),
             "cube": ((-0.30, -0.30, 0.05), (0.35, 0.30, 0.65)), "plug": ((-0.45, -0.40, 0.03), (0.35, 0.40, 0.50))}
V_MAX, W_MAX = 1.0, 3.0
# approximate initial object positions (plausible synthetic values only; the target's exact ones are in the observation)
OBJ_INIT = {"tennis": [(-0.071, 0.003, 0.318)], "pen": [(-0.109, 0.012, 0.287)], "cube": [(-0.075, 0.012, 0.318)],
            "plug": [(0.042, 0.031, 0.015), (-0.043, -0.041, 0.019)]}
SCRAMBLE = [[1.0, 3.0], [2.0, 1.0], [0.0, 2.0]]  # cube: TASK.md
CUBE_IDENTITY = 23  # object/rotations24.json identity_index


# ---------------------------------------------------------------- quaternions (w, x, y, z) and the command limiter
def qmul(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return [aw * bw - ax * bx - ay * by - az * bz, aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw]


def qnorm(q):
    n = math.sqrt(sum(x * x for x in q))
    return [x / n for x in q]


def rotvec_of(q):
    """Rotation vector (angle in [0, pi]) of a unit quaternion, shortest rotation."""
    q = q if q[0] >= 0 else [-x for x in q]
    s = math.sqrt(q[1] ** 2 + q[2] ** 2 + q[3] ** 2)
    if s < 1e-12:
        return [2.0 * x for x in q[1:]]
    f = 2.0 * math.atan2(s, q[0]) / s
    return [x * f for x in q[1:]]


def quat_of_rotvec(r):
    a = math.sqrt(sum(x * x for x in r))
    if a < 1e-12:
        return qnorm([1.0, 0.5 * r[0], 0.5 * r[1], 0.5 * r[2]])
    s = math.sin(a / 2) / a
    return [math.cos(a / 2), s * r[0], s * r[1], s * r[2]]


def _clip_norm(x, m):
    n = math.sqrt(sum(v * v for v in x))
    return ([v * (m / n) for v in x], True) if n > m else (list(x), False)


class CommandLimiter:
    """The target's wrist command limits (CONTRACT.md section 4): executed target from the commanded one.
    __call__(p_cmd, q_cmd, v_cmd=None, w_cmd=None) -> {"position", "orientation", "linear_velocity", "angular_velocity", "limited"}."""

    def __init__(self, workspace_lo, workspace_hi, dt=DT, v_max=V_MAX, w_max=W_MAX):
        self.lo, self.hi, self.dt, self.v_max, self.w_max = list(workspace_lo), list(workspace_hi), dt, v_max, w_max
        self.p = self.q = None

    def reset(self, p0, q0):
        self.p, self.q = list(map(float, p0)), qnorm(list(map(float, q0)))

    def __call__(self, p_cmd, q_cmd, v_cmd=None, w_cmd=None):
        dp, lim_p = _clip_norm([float(a) - b for a, b in zip(p_cmd, self.p)], self.v_max * self.dt)
        p_new = [a + b for a, b in zip(self.p, dp)]
        p_clip = [min(max(x, lo), hi) for x, lo, hi in zip(p_new, self.lo, self.hi)]
        ws = any(a != b for a, b in zip(p_clip, p_new))
        qc = qnorm(list(map(float, q_cmd)))
        r = rotvec_of(qmul(qc, [self.q[0], -self.q[1], -self.q[2], -self.q[3]]))
        r, lim_q = _clip_norm(r, self.w_max * self.dt)
        q_new = qnorm(qmul(quat_of_rotvec(r), self.q))
        if sum(a * b for a, b in zip(q_new, self.q)) < 0:  # keep the executed target's sign continuous
            q_new = [-x for x in q_new]
        v, lim_v = _clip_norm([0.0, 0.0, 0.0] if v_cmd is None else list(map(float, v_cmd)), self.v_max)
        w, lim_w = _clip_norm([0.0, 0.0, 0.0] if w_cmd is None else list(map(float, w_cmd)), self.w_max)
        self.p, self.q = p_clip, q_new
        return {"position": list(p_clip), "orientation": list(q_new), "linear_velocity": v, "angular_velocity": w,
                "limited": {"translation_rate": lim_p, "workspace": ws, "rotation_rate": lim_q, "linear_velocity": lim_v, "angular_velocity": lim_w}}


# ---------------------------------------------------------------- action validation (the target's rules)
def validate_action(a, np):
    """None if `a` is a valid contract v2 action, else the reason. Arrays are flattened as the target's policy host does."""
    if not isinstance(a, dict):
        return "act(obs) must return a dict (contract v2)"
    extra = set(a) - set(ACTION)
    if extra:
        return "unknown action keys: " + ", ".join(sorted(extra))
    out = {}
    for k, (shape, req) in ACTION.items():
        x = a.get(k)
        if x is None:
            if req:
                return f"missing {k}"
            out[k] = None
            continue
        try:
            x = np.asarray(x, dtype=np.float64).ravel()
        except (TypeError, ValueError):
            return f"{k} must be a finite {shape} array"
        if x.shape != shape or not np.all(np.isfinite(x)):
            return f"{k} must be a finite {shape} array (got shape {x.shape})"
        out[k] = x
    nq = float(np.linalg.norm(out["wrist_orientation_target"]))
    if not 0.9 <= nq <= 1.1:
        return f"wrist_orientation_target must be a unit quaternion (w, x, y, z); norm {nq:.3f}"
    return None


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def static_checks(pkg):
    errs, warns = [], []
    files = sorted(os.path.relpath(os.path.join(d, f), pkg).replace(os.sep, "/") for d, _, fs in os.walk(pkg) for f in fs)
    if "policy.py" not in files:
        return ["policy.py missing at the package root"], warns
    for f in files:
        with open(os.path.join(pkg, f), "rb") as fh:
            if f.lower().endswith(COMPILED) or fh.read(4) == b"\x7fELF":
                errs.append(f"{f}: compiled code is not allowed (Python source and data files only)")
    if "manifest.json" not in files:
        errs.append("manifest.json missing at the package root (PACKAGE.md)")
    else:
        try:
            man = json.load(open(os.path.join(pkg, "manifest.json")))
            assert isinstance(man, dict)
        except Exception:
            return errs + ["manifest.json is not a JSON object"], warns
        if man.get("entry") != "policy.py:load_policy":
            errs.append('manifest.json: "entry" must be "policy.py:load_policy"')
        cv = man.get("contract_version")
        if cv != CONTRACT:
            errs.append(f'manifest.json: "contract_version" must be "{CONTRACT}" (got {cv!r}): this experiment evaluates policies under policy '
                        f"contract {CONTRACT} (object-state and wrist observation, act() returning a dict of finger and wrist targets; see CONTRACT.md); "
                        "packages written for another contract are not accepted")
        listed = man.get("files")
        if not isinstance(listed, dict):
            errs.append('manifest.json: "files" must map every file except manifest.json to its SHA256')
        else:
            want = [f for f in files if f != "manifest.json"]
            for f in want:
                if f not in listed:
                    errs.append(f"manifest.json does not list {f}")
                elif str(listed[f]).lower() != sha(os.path.join(pkg, f)):
                    errs.append(f"SHA256 mismatch in manifest.json for {f} (recompute with sha256sum)")
            errs += [f"manifest.json lists {f}, which is not in the package" for f in listed if f not in want]
    local = {f[:-3].split("/")[0] for f in files if f.endswith(".py")} | {f.split("/")[0] for f in files if "/" in f}
    std = set(getattr(sys, "stdlib_module_names", ())) | set(sys.builtin_module_names)
    for f in files:
        if not f.endswith(".py"):
            continue
        try:
            tree = ast.parse(open(os.path.join(pkg, f), "rb").read(), filename=f, feature_version=(3, 12))
        except SyntaxError as e:
            errs.append(f"{f}:{e.lineno}: syntax error: {e.msg}")
            continue
        for n in ast.walk(tree):
            mods = [a.name for a in n.names] if isinstance(n, ast.Import) else \
                   [n.module] if isinstance(n, ast.ImportFrom) and n.module and n.level == 0 else []
            for m in mods:
                top = m.split(".")[0]
                if std and top not in std and top not in ALLOWED_THIRD_PARTY and top not in local:
                    errs.append(f"{f}:{n.lineno}: imports {m!r}, which is not installed on the target "
                                "(standard library, numpy and torch only)")
                if top in ("subprocess", "multiprocessing", "socket", "urllib", "http", "ctypes"):
                    warns.append(f"{f}:{n.lineno}: imports {top}; process creation and network are blocked on the target")
    return errs, warns


# ------------------------------------------------------------------ sandbox (child process)
def _landlock(pkg, scratch):
    libc = ctypes.CDLL(None, use_errno=True)
    abi = libc.syscall(444, None, ctypes.c_size_t(0), ctypes.c_uint32(1))
    if abi < 1:
        return "Landlock unavailable on this kernel: filesystem restrictions NOT emulated"

    class RS(ctypes.Structure):
        _fields_ = [("fs", ctypes.c_uint64), ("net", ctypes.c_uint64)]

    class PB(ctypes.Structure):
        _pack_ = 1
        _fields_ = [("allowed", ctypes.c_uint64), ("fd", ctypes.c_int32)]

    fs_all = (1 << (13 if abi == 1 else 14 if abi == 2 else 15)) - 1
    rs_attr = RS(fs_all, 3 if abi >= 4 else 0)
    size = ctypes.sizeof(RS) if abi >= 4 else 8
    rs = libc.syscall(444, ctypes.byref(rs_attr), ctypes.c_size_t(size), ctypes.c_uint32(0))
    if rs < 0:
        return "Landlock ruleset failed: filesystem restrictions NOT emulated"
    R = (1 << 2) | (1 << 3)  # read file, read dir
    W = R | (1 << 1) | (1 << 4) | (1 << 5) | (1 << 7) | (1 << 8) | ((1 << 14) if abi >= 3 else 0)
    roots = {os.path.realpath(p) for p in (sys.prefix, sys.base_prefix, sys.exec_prefix, os.path.dirname(os.path.realpath(sys.executable)))}
    roots |= {os.path.realpath(p) for p in sys.path if p and os.path.isdir(p)}
    rules = [(p, R) for p in sorted(roots) + ["/usr", "/lib", "/lib64", "/etc/ld.so.cache", "/proc/self",
                                              "/sys/devices/system/cpu", "/dev/urandom", pkg]]
    rules += [(scratch, W), ("/dev/null", R | (1 << 1) | ((1 << 14) if abi >= 3 else 0))]
    for path, acc in rules:
        try:
            fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
        except OSError:
            continue
        if not os.path.isdir(path):
            acc &= (1 << 0) | (1 << 1) | (1 << 2) | ((1 << 14) if abi >= 3 else 0)
        rule = PB(acc, fd)
        libc.syscall(445, ctypes.c_int(rs), ctypes.c_int(1), ctypes.byref(rule), ctypes.c_uint32(0))
        os.close(fd)
    if libc.syscall(446, ctypes.c_int(rs), ctypes.c_uint32(0)) != 0:
        return "Landlock restrict failed: filesystem restrictions NOT emulated"
    return None


def _seccomp():
    """Same intent as the target environment's sandbox: no sockets, ptrace, cross-process memory, bpf, io_uring; no exec/fork (threads ok);
    signals, prlimit, setpriority and sched_set* only on this process."""
    me = os.getpid()
    EPERM, ENOSYS, ALLOW, KILL = 0x00050001, 0x00050026, 0x7FFF0000, 0x80000000
    LD, JEQ, JSET, RET = 0x20, 0x15, 0x45, 0x06
    deny = [41, 101, 310, 311, 321, 425, 59, 322, 57, 58, 200, 424, 434]
    self_arg0, zero_ok = [62, 234, 129, 297, 302, 203, 144, 142], {302, 203, 144, 142}
    prog, fix, lab = [], [], {}

    def ins(c, k, jt=0, jf=0):
        prog.append([c, jt, jf, k])
    ins(LD, 4); ins(JEQ, 0xC000003E, 1, 0); ins(RET, KILL); ins(LD, 0)
    for nr in deny:
        fix.append((len(prog), "deny")); ins(JEQ, nr)
    fix.append((len(prog), "enosys")); ins(JEQ, 435)
    fix.append((len(prog), "clone")); ins(JEQ, 56)
    for nr in self_arg0:
        fix.append((len(prog), f"a{nr}")); ins(JEQ, nr)
    fix.append((len(prog), "prio")); ins(JEQ, 141)
    ins(RET, ALLOW)
    lab["deny"] = len(prog); ins(RET, EPERM)
    lab["enosys"] = len(prog); ins(RET, ENOSYS)
    lab["clone"] = len(prog); ins(LD, 16); ins(JSET, 0x10000, 1, 0); ins(RET, EPERM); ins(RET, ALLOW)
    for nr in self_arg0:
        lab[f"a{nr}"] = len(prog); ins(LD, 16); ins(JEQ, me); fix.append((len(prog) - 1, "ok"))
        if nr in zero_ok:
            ins(JEQ, 0); fix.append((len(prog) - 1, "ok"))
        ins(RET, EPERM)
    lab["prio"] = len(prog); ins(LD, 24); ins(JEQ, 0); fix.append((len(prog) - 1, "ok"))
    ins(JEQ, me); fix.append((len(prog) - 1, "ok")); ins(RET, EPERM)
    lab["ok"] = len(prog); ins(RET, ALLOW)
    for i, l in fix:
        prog[i][1] = lab[l] - i - 1
    buf = ctypes.create_string_buffer(b"".join(struct.pack("HBBI", *x) for x in prog))

    class FP(ctypes.Structure):
        _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.c_void_p)]
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0 or libc.prctl(22, 2, ctypes.byref(FP(len(prog), ctypes.cast(buf, ctypes.c_void_p))), 0, 0) != 0:
        return "seccomp unavailable: network/process restrictions NOT emulated"
    return None


# ------------------------------------------------------------------ synthetic observations
class SyntheticTarget:
    """Observations with the task's exact key set, shapes and dtypes; the wrist follows the executed target (no physics)."""

    def __init__(self, task, np, seed=0):
        self.task, self.np, self.spec = task, np, OBS[task]
        self.rng = np.random.default_rng(seed)
        self.q0 = np.array(Q0[task])
        p0, q0w = WRIST_INIT[task]
        self.lim = CommandLimiter(*WORKSPACE[task])
        self.lim.reset(p0, q0w)
        self.hq = [self.q0.copy() for _ in range(K_HIST)]
        self.hqd = [np.zeros(20) for _ in range(K_HIST)]
        self.hwp = [np.array(self.lim.p) for _ in range(K_HIST)]
        self.hwq = [np.array(self.lim.q) for _ in range(K_HIST)]
        self.wp, self.wq = np.array(self.lim.p), np.array(self.lim.q)
        O = len(OBJ_INIT[task])
        self.obj_p = np.array(OBJ_INIT[task], dtype=float)
        self.obj_q = np.tile(np.array([1.0, 0.0, 0.0, 0.0]), (O, 1))
        self.const = {}
        if task == "cube":
            self.const["scramble"] = np.array(SCRAMBLE)
            self.const["cube_relative_orientation"] = np.tile(np.array([1.0, 0.0, 0.0, 0.0]), (8, 1))
            self.const["cube_configuration"] = np.full(8, CUBE_IDENTITY, dtype=np.int64)
        if task == "plug":
            self.const["goal_defined"] = np.zeros(2, dtype=np.int64)
            self.const["goal_position"] = np.full((2, 3), NAN)
            self.const["goal_orientation"] = np.full((2, 4), NAN)
            self.const["goal_free_axis"] = np.zeros((2, 3))

    def observe(self, k):
        np, rng = self.np, self.rng
        O = len(self.obj_p)
        o = {"q": self.hq[-1] + 0.002 * rng.standard_normal(20), "qd": 0.05 * rng.standard_normal(20),
             "prev_q_target": np.array(self.hq), "prev_qd_target": np.array(self.hqd),
             "prev_wrist_position_target": np.array(self.hwp), "prev_wrist_orientation_target": np.array(self.hwq),
             "wrist_position": self.wp + 1e-4 * rng.standard_normal(3), "wrist_orientation": self.wq.copy(),
             "wrist_linear_velocity": 1e-3 * rng.standard_normal(3), "wrist_angular_velocity": 1e-3 * rng.standard_normal(3), "step": int(k),
             "object_position": self.obj_p + 1e-4 * rng.standard_normal((O, 3)), "object_orientation": self.obj_q.copy(),
             "object_linear_velocity": 1e-3 * rng.standard_normal((O, 3)), "object_angular_velocity": 1e-2 * rng.standard_normal((O, 3))}
        if self.task == "cube":
            o["part_position"] = np.repeat(self.obj_p, 8, 0) + 0.0125 * rng.standard_normal((8, 3))
            o["part_orientation"] = np.tile(np.array([1.0, 0.0, 0.0, 0.0]), (8, 1))
            o["part_linear_velocity"] = 1e-3 * rng.standard_normal((8, 3))
            o["part_angular_velocity"] = 1e-2 * rng.standard_normal((8, 3))
        for key, v in self.const.items():
            o[key] = v.copy()
        for key, (shape, dtype) in self.spec.items():  # exactly the contract's key set, shapes and dtypes
            if key == "step":
                continue
            o[key] = np.asarray(o[key], dtype=np.int64 if dtype == "int64" else np.float64).reshape(shape)
        assert set(o) == set(self.spec), set(o) ^ set(self.spec)
        return o

    def apply(self, a):
        """Record the finger targets and run the wrist command through the limiter (as the target does)."""
        np = self.np
        q_t = np.asarray(a["q_target"], dtype=np.float64).ravel()
        qd_t = np.zeros(20) if a.get("qd_target") is None else np.asarray(a["qd_target"], dtype=np.float64).ravel()
        ex = self.lim(np.asarray(a["wrist_position_target"], dtype=float).ravel(), np.asarray(a["wrist_orientation_target"], dtype=float).ravel(),
                      None if a.get("wrist_linear_velocity_target") is None else np.asarray(a["wrist_linear_velocity_target"], dtype=float).ravel(),
                      None if a.get("wrist_angular_velocity_target") is None else np.asarray(a["wrist_angular_velocity_target"], dtype=float).ravel())
        self.hq = self.hq[1:] + [q_t]
        self.hqd = self.hqd[1:] + [qd_t]
        self.hwp = self.hwp[1:] + [np.array(ex["position"])]
        self.hwq = self.hwq[1:] + [np.array(ex["orientation"])]
        self.wp, self.wq = np.array(ex["position"]), np.array(ex["orientation"])  # the wrist reaches its target (no physics)
        return ex


def _canon(a, np):
    """Flattened float64 copy of an action for the determinism comparison (as the target compares them)."""
    return {k: (None if v is None else np.asarray(v, dtype=np.float64).ravel().copy()) for k, v in a.items()}


def _same(a, b, np):
    if set(a) != set(b):
        return False
    for k in a:
        if (a[k] is None) != (b[k] is None):
            return False
        if a[k] is not None and not np.array_equal(a[k], b[k]):
            return False
    return True


def child(task, pkg, steps):
    out = sys.stdout
    sys.stdout = sys.stderr
    scratch = tempfile.mkdtemp(prefix="r2s2r_preflight_")
    os.environ.update({"TMPDIR": scratch, "HOME": pkg, "CUDA_VISIBLE_DEVICES": "", "OMP_NUM_THREADS": "1",
                       "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    tempfile.tempdir = scratch
    for r, v in ((resource.RLIMIT_AS, 8 << 30), (resource.RLIMIT_CPU, CPU_LIMIT), (resource.RLIMIT_NOFILE, 256),
                 (resource.RLIMIT_FSIZE, 64 << 20), (resource.RLIMIT_CORE, 0)):
        resource.setrlimit(r, (v, v))
    import numpy as np  # noqa: F401 (before the restrictions, like the target's policy host)
    ctypes.CDLL(None, use_errno=True).prctl(38, 1, 0, 0, 0)  # PR_SET_NO_NEW_PRIVS (Landlock and seccomp need it)
    notes = [n for n in (_landlock(pkg, scratch), _seccomp()) if n]
    rep = {"notes": notes}

    def emit(**kw):
        rep.update(kw)
        out.write(json.dumps(rep) + "\n")
        out.flush()
        os._exit(0)
    import importlib.util
    import traceback
    t0 = time.process_time()
    try:
        sys.path.insert(0, pkg)
        spec = importlib.util.spec_from_file_location("student_policy", os.path.join(pkg, "policy.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        pol = mod.load_policy(pkg)
        pol.reset()
    except BaseException:
        emit(ok=False, stage="load_policy/reset", error=traceback.format_exc(limit=6))
    tgt = SyntheticTarget(task, np)
    times, rec, limited = [], [], {}
    n_rec = min(steps, 200)
    for k in range(steps):
        obs = tgt.observe(k)
        t = time.perf_counter()
        try:
            a = pol.act(obs)
        except BaseException:
            emit(ok=False, stage=f"act() at step {k}", error=traceback.format_exc(limit=6))
        dt = time.perf_counter() - t
        times.append(dt)
        why = validate_action(a, np)
        if why:
            emit(ok=False, stage=f"act() at step {k}", error=f"invalid action: {why} (CONTRACT.md section 4)")
        if k < n_rec:
            rec.append((obs, _canon(a, np)))
        if dt > ACT_TIMEOUT:
            emit(ok=False, stage=f"act() at step {k}", error=f"act() took {dt:.2f} s (> {ACT_TIMEOUT} s: the trial would stop)")
        ex = tgt.apply(a)
        for f, on in ex["limited"].items():
            limited[f] = limited.get(f, 0) + int(on)
    try:
        pol.reset()
        for k, (obs, a0) in enumerate(rec):
            a = pol.act(obs)
            if not _same(_canon(a, np), a0, np):
                emit(ok=False, stage=f"determinism replay at step {k}",
                     error="after reset(), the same observations gave different actions (CONTRACT.md: bit-identical)")
    except BaseException:
        emit(ok=False, stage="determinism replay", error=traceback.format_exc(limit=6))
    emit(ok=True, steps=steps, replayed=len(rec), act_ms_mean=1e3 * float(np.mean(times)), act_ms_max=1e3 * float(np.max(times)),
         cpu_s=time.process_time() - t0, limited=limited)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        return child(sys.argv[2], sys.argv[3], int(sys.argv[4]))
    argv, steps = list(sys.argv[1:]), None
    if "--steps" in argv:
        i = argv.index("--steps")
        try:
            steps = int(argv[i + 1])
        except (IndexError, ValueError):
            print("--steps needs an integer")
            return 2
        del argv[i:i + 2]
    if len(argv) == 1:
        task = os.environ.get("R2S2R_TASK", "")
        if task not in STEPS:
            found = [t for t in STEPS if shutil.which(f"r2s2r-{t}")]
            task = found[0] if len(found) == 1 else ""
        if not task:
            print("cannot tell the task: give it explicitly, e.g. r2s2r-preflight tennis my_policy/")
            return 2
        argv = [task] + argv
    if len(argv) != 2 or argv[0] not in STEPS:
        print(__doc__)
        return 2
    task, src = argv
    steps = STEPS[task] if steps is None else max(1, steps)
    tmp = None
    if os.path.isfile(src):
        tmp = tempfile.mkdtemp(prefix="r2s2r_pkg_")
        try:
            with tarfile.open(src, "r:*") as tf:
                for m in tf.getmembers():
                    if not (m.isfile() or m.isdir()) or m.name.startswith("/") or ".." in m.name.split("/"):
                        print(f"FAIL archive: unsafe or non-regular member {m.name!r}")
                        return 1
                if hasattr(tarfile, "data_filter"):
                    tf.extractall(tmp, filter="data")
                else:
                    tf.extractall(tmp)
        except tarfile.TarError as e:
            print(f"FAIL archive: not a valid tar archive ({e})")
            return 1
        src = tmp
    pkg = os.path.realpath(src)
    print(f"r2s2r-preflight: task {task}, contract {CONTRACT}, package {src}, python {sys.version.split()[0]}")
    try:
        import numpy
        vers = f"numpy {numpy.__version__}"
    except ImportError:
        vers = "numpy missing"
    try:
        import importlib.metadata as md
        vers += f", torch {md.version('torch')}"
    except Exception:
        pass
    if not sys.version.startswith("3.12"):
        print(f"WARN  local Python {sys.version.split()[0]}; the target runs 3.12")
    print(f"INFO  local {vers}; the target has numpy 2.5.4, torch 2.14.1 (CPU)")
    errs, warns = static_checks(pkg)
    for w in warns:
        print("WARN ", w)
    if errs:
        for e in errs:
            print("FAIL ", e)
        print("RESULT: REJECT (the target environment would refuse this package; nothing would be charged)")
        return 1
    print(f"PASS  structure, manifest (contract_version {CONTRACT}), syntax, imports")
    t = time.time()
    try:
        r = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "--child", task, pkg, str(steps)],
                           capture_output=True, text=True, timeout=max(120, steps * ACT_TIMEOUT + 60), cwd=pkg)
        line = (r.stdout.strip().splitlines() or [""])[-1]
        rep = json.loads(line) if line.startswith("{") else {"ok": False, "stage": "sandbox", "error": (r.stderr or r.stdout)[-2000:] or f"exit code {r.returncode} (CPU or memory limit?)"}
    except subprocess.TimeoutExpired:
        rep = {"ok": False, "stage": "run", "error": "did not finish in time"}
    for n in rep.get("notes", []):
        print("WARN ", n)
    if not rep["ok"]:
        print(f"FAIL  {rep['stage']}:\n{rep['error']}")
        print("RESULT: REJECT")
        return 1
    print(f"PASS  load_policy(), reset(), act() x{rep['steps']} on synthetic {task} observations (exact key set, shapes, dtypes): "
          "valid action dict every step, < 5 s per call")
    print(f"PASS  determinism: reset() + replay of the first {rep['replayed']} steps gives bit-identical actions")
    print(f"INFO  act() mean {rep['act_ms_mean']:.3f} ms, max {rep['act_ms_max']:.3f} ms (budget 2 ms, reported); "
          f"CPU {rep['cpu_s']:.1f} s of {CPU_LIMIT} s for {rep['steps']} steps; wall {time.time() - t:.1f} s")
    lim = {k: v for k, v in rep.get("limited", {}).items() if v}
    if lim:
        print("INFO  wrist commands changed by the command limits (steps): " + ", ".join(f"{k} {v}" for k, v in lim.items())
              + " (not a failure; CONTRACT.md section 4)")
    if rep["act_ms_mean"] > 1e3 * BUDGET:
        print("WARN  mean act() time exceeds the 2 ms inference budget (reported, not enforced)")
    if rep["cpu_s"] > 0.8 * CPU_LIMIT * rep["steps"] / STEPS[task]:
        print("WARN  CPU time is close to the 600 s limit for a full trial on this machine")
    print("RESULT: OK locally. The remote `validate` command runs the target environment's own check (never charged).")
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
