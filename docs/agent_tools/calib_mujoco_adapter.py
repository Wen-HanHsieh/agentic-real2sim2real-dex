#!/usr/bin/env python3
"""Example simulator adapter for r2s2r-calib built on MuJoCo (a real dynamics model; needs `pip install mujoco`).

It builds a scene from public information only: the vendor URDF of the hand (hardware/wuji_hand2_right/urdf/right.urdf,
or hardware/wuji_hand2_left/urdf/left.urdf for the left-hand environment) with its root link (`r_mount`, left `l_mount`) made a free body (the floating wrist of hardware/SPECS.md section 3), the finger PD
controller of section 5 (gains, effort saturation, armature of section 2), the wrist impedance controller of section 4
(gains, force/torque saturation, gravity compensation of the hand's own mass), the public command limiter when commanded
targets are replayed, and rigid objects with the dimensions and masses of object/SPECS.md:
  tennis  a sphere (r 0.0325 m, 57.7 g) above a floor plane at z = 0;
  pen     a capsule (length 0.195 m, radius 0.0045 m, 22 g) whose state frame +x is the long axis, floor at z = 0;
  plug    two boxes with the published body dimensions and masses (blades as two small boxes), the table block with its
          top at z = 0, a floor plane at z = -0.75 m;
  cube    ONE rigid 50 mm box of 60 g (no layer mechanism): the eight parts are reported rigidly attached at their home
          offsets and cube_configuration stays at its reset value. This adapter cannot reproduce layer turns.
Contact parameters (friction, stiffness) are MuJoCo defaults unless overridden through the scene JSON (`--scene`), since the
target's are not published: calibrating them is exactly the agent's task. Physics 1 kHz, two substeps per control step.

Usage:  python calib_mujoco_adapter.py --urdf PATH/right.urdf [--scene scene.json] [--selftest]
        r2s2r-calib replay target.npz --adapter-cmd "python calib_mujoco_adapter.py --urdf hardware/wuji_hand2_right/urdf/right.urdf" -o sim.npz
The adapter speaks the JSON-lines protocol of calib_adapter.py on stdin/stdout (any interpreter with mujoco installed).
Capabilities: set_state (state replay), contacts (instantaneous contact flags from MuJoCo's contact list), parts (cube only, rigid).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import calib_adapter as A  # noqa: E402

DT_CONTROL, DT_PHYSICS = 0.002, 0.001
GRAVITY = np.array([0.0, 0.0, -9.81])
# hardware/SPECS.md: joints in vendor order with effort limits and armature (section 2), PD gains (section 5)
EFFORT = np.array([0.6, 0.6, 0.3, 0.3] + [2.0, 0.2, 0.3, 0.3] * 4)
ARMATURE = np.array([5e-4, 5e-4, 2e-4, 2e-4] + [5e-4, 2e-4, 2e-4, 2e-4] * 4)
KP = np.array([4.0, 4.0, 2.0, 2.0] + [10.0, 2.0, 2.0, 2.0] * 4)
KD = np.array([0.04, 0.04, 0.02, 0.02] + [0.10, 0.02, 0.02, 0.02] * 4)
# section 4 (wrist-1)
WRIST = {"kp_lin": 2000.0, "kd_lin": 60.0, "kp_rot": 20.0, "kd_rot": 0.4, "f_max": 30.0, "t_max": 2.0}
SCENES = {
    "tennis": {"floor_z": 0.0, "objects": [{"name": "tennis_ball", "shape": "sphere", "size": [0.0325], "mass": 0.0577}]},
    "pen": {"floor_z": 0.0, "objects": [{"name": "pen", "shape": "capsule_x", "size": [0.0045, 0.195], "mass": 0.022}]},
    "plug": {"floor_z": -0.75, "table": {"center": [0.10, 0.0, -0.015], "size": [1.20, 1.20, 0.03]},
             "objects": [{"name": "plug_white", "shape": "plug", "size": [0.029, 0.0431, 0.0585], "blade": [0.00635, 0.0015, 0.016], "mass": 0.075},
                         {"name": "plug_black", "shape": "plug", "size": [0.0318, 0.0358, 0.0645], "blade": [0.00635, 0.0015, 0.018], "mass": 0.055}]},
    "cube": {"floor_z": 0.0, "objects": [{"name": "cube", "shape": "box", "size": [0.05, 0.05, 0.05], "mass": 0.060, "parts": 8}]},
}
CUBE_HOME = np.array([[1, 1, -1], [-1, 1, -1], [1, -1, -1], [-1, -1, -1], [1, 1, 1], [-1, 1, 1], [1, -1, 1], [-1, -1, 1]], float) * 0.0125  # e/4 slots (object/SPECS.md)
FRICTION_DEFAULT = 1.0
MOUNTS = ("r_mount", "l_mount")  # wrist frame = the URDF root link: right hand, left hand


def _quat_mul(a, b):
    aw, ax, ay, az = a; bw, bx, by, bz = b
    return np.array([aw * bw - ax * bx - ay * by - az * bz, aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw])


def _rotvec(q):
    q = q if q[0] >= 0 else -q
    s = np.linalg.norm(q[1:])
    return 2.0 * q[1:] if s < 1e-12 else q[1:] * (2.0 * math.atan2(s, q[0]) / s)


def _clip_norm(x, m):
    n = np.linalg.norm(x)
    return x * (m / n) if n > m else x


class MujocoAdapter(A.SimAdapter):
    capabilities = {"set_state": True, "contacts": True, "parts": True}

    def __init__(self, meta: dict, urdf: Path, scene: dict | None = None):
        import mujoco
        self.mj = mujoco
        self.task = meta.get("task")
        if self.task not in SCENES:
            raise A.AdapterError(f"no example scene for task {self.task!r}")
        self.scene = json.loads(json.dumps(SCENES[self.task]))
        if scene:
            self.scene.update(scene)
        self.joint_names = list((meta.get("replay") or {}).get("joint_names") or [])
        self.object_names = list(meta.get("object_names") or [o["name"] for o in self.scene["objects"]])
        self._build(Path(urdf))
        self.target = None
        self.limiter = None

    # ------------------------------------------------------------------ model
    def _build(self, urdf: Path):
        mj = self.mj
        if not urdf.is_file():
            raise A.AdapterError(f"URDF not found: {urdf}")
        spec = mj.MjSpec.from_file(str(urdf))
        spec.option.timestep = DT_PHYSICS
        spec.option.gravity = GRAVITY.tolist()
        self.mount_name = next((n for n in MOUNTS if spec.body(n) is not None), None)
        if self.mount_name is None:
            raise A.AdapterError(f"URDF has no root link {' or '.join(MOUNTS)}")
        mount = spec.body(self.mount_name)
        mount.add_freejoint(name="wrist_free")
        fz = float(self.scene.get("floor_z", 0.0))
        spec.worldbody.add_geom(name="floor", type=mj.mjtGeom.mjGEOM_PLANE, size=[3.0, 3.0, 0.1], pos=[0.0, 0.0, fz], friction=[FRICTION_DEFAULT, 0.005, 0.0001])
        if self.scene.get("table"):
            tb = self.scene["table"]
            spec.worldbody.add_geom(name="table", type=mj.mjtGeom.mjGEOM_BOX, size=[s / 2 for s in tb["size"]], pos=tb["center"], friction=[FRICTION_DEFAULT, 0.005, 0.0001])
        self.obj_bodies = []
        for o in self.scene["objects"]:
            b = spec.worldbody.add_body(name=o["name"], pos=[0.0, 0.0, 1.0])
            b.add_freejoint(name=o["name"] + "_free")
            fr = o.get("friction", FRICTION_DEFAULT)
            if o["shape"] == "sphere":
                b.add_geom(name=o["name"], type=mj.mjtGeom.mjGEOM_SPHERE, size=[o["size"][0], 0, 0], mass=o["mass"], friction=[fr, 0.005, 0.0001])
            elif o["shape"] == "capsule_x":  # MuJoCo capsule axis is z; the state frame's long axis is +x: rotate z -> x
                r, L = o["size"]
                b.add_geom(name=o["name"], type=mj.mjtGeom.mjGEOM_CAPSULE, size=[r, max(L / 2 - r, 1e-4), 0], quat=[math.sqrt(0.5), 0, math.sqrt(0.5), 0],
                           mass=o["mass"], friction=[fr, 0.005, 0.0001])
            elif o["shape"] == "box":
                b.add_geom(name=o["name"], type=mj.mjtGeom.mjGEOM_BOX, size=[s / 2 for s in o["size"]], mass=o["mass"], friction=[fr, 0.005, 0.0001])
            elif o["shape"] == "plug":  # body box (state frame = body centre, blades along +z) and two blade boxes at y = +-6.35 mm
                sx, sy, sz = o["size"]
                bw, bt, bl = o["blade"]
                b.add_geom(name=o["name"], type=mj.mjtGeom.mjGEOM_BOX, size=[sx / 2, sy / 2, sz / 2], mass=o["mass"] * 0.97, friction=[fr, 0.005, 0.0001])
                for k, yy in enumerate((-0.00635, 0.00635)):
                    b.add_geom(name=f"{o['name']}_blade{k}", type=mj.mjtGeom.mjGEOM_BOX, size=[bw / 2, bt / 2, bl / 2], pos=[0, yy, sz / 2 + bl / 2],
                               mass=o["mass"] * 0.015, friction=[fr, 0.005, 0.0001])
            else:
                raise A.AdapterError(f"unknown shape {o['shape']}")
            self.obj_bodies.append(o["name"])
        self.model = spec.compile()
        self.data = mj.MjData(self.model)
        m = self.model
        self.bid_mount = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, self.mount_name)
        self.bid_obj = [mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, n) for n in self.obj_bodies]
        self.jid_wrist = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, "wrist_free")
        self.qadr_wrist, self.vadr_wrist = int(m.jnt_qposadr[self.jid_wrist]), int(m.jnt_dofadr[self.jid_wrist])
        self.obj_q = [int(m.jnt_qposadr[mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, n + "_free")]) for n in self.obj_bodies]
        self.obj_v = [int(m.jnt_dofadr[mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, n + "_free")]) for n in self.obj_bodies]
        names = self.joint_names or [mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j) for j in range(m.njnt) if m.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE]
        self.joint_names = names
        jids = [mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, n) for n in names]
        if any(j < 0 for j in jids):
            raise A.AdapterError(f"joint names not in the URDF: {[n for n, j in zip(names, jids) if j < 0]} (the log's hand must be the "
                                 "URDF's hand: r_* joints = right.urdf, l_* joints = left.urdf)")
        self.fq = np.array([m.jnt_qposadr[j] for j in jids]); self.fv = np.array([m.jnt_dofadr[j] for j in jids])
        self.lower, self.upper = m.jnt_range[jids, 0].copy(), m.jnt_range[jids, 1].copy()
        m.dof_armature[self.fv] = ARMATURE
        # which bodies are hand links / objects / environment, for the contact flags
        self.hand_bodies = set()
        for bidx in range(m.nbody):
            r = bidx
            while r > 0:
                if r == self.bid_mount:
                    self.hand_bodies.add(bidx); break
                r = int(m.body_parentid[r])
        self.hand_mass = float(m.body_subtreemass[self.bid_mount])
        self.cube_parts = next((o.get("parts") for o in self.scene["objects"] if o.get("parts")), None)
        self.cube_cfg = self.cube_rel = None
        mj.mj_forward(m, self.data)

    # ------------------------------------------------------------------ state io
    def _set_free(self, qadr, vadr, p, q, v, w):
        d = self.data
        q = np.asarray(q, float); q = q / np.linalg.norm(q)
        d.qpos[qadr:qadr + 3] = p; d.qpos[qadr + 3:qadr + 7] = q
        # free joint: qvel = [linear velocity of the body frame origin, world frame; angular velocity, body frame]
        R = np.zeros(9); self.mj.mju_quat2Mat(R, q); R = R.reshape(3, 3)
        d.qvel[vadr:vadr + 3] = v; d.qvel[vadr + 3:vadr + 6] = R.T @ np.asarray(w, float)

    def _get_free(self, bid):
        mj, d = self.mj, self.data
        res = np.zeros(6)
        mj.mj_objectVelocity(self.model, d, mj.mjtObj.mjOBJ_XBODY, bid, res, 0)  # [angular, linear] at the body frame origin, world frame
        return d.xpos[bid].copy(), d.xquat[bid].copy(), res[3:6].copy(), res[0:3].copy()

    def set_state(self, state: dict) -> None:
        d = self.data
        if "q" in state:
            d.qpos[self.fq] = np.clip(np.asarray(state["q"], float).reshape(20), self.lower, self.upper)
        if "qd" in state:
            d.qvel[self.fv] = np.asarray(state["qd"], float).reshape(20)
        self._set_free(self.qadr_wrist, self.vadr_wrist, state["wrist_position"], state["wrist_orientation"], state["wrist_linear_velocity"], state["wrist_angular_velocity"])
        for i in range(len(self.obj_bodies)):
            self._set_free(self.obj_q[i], self.obj_v[i], np.asarray(state["object_position"])[i], np.asarray(state["object_orientation"])[i],
                           np.asarray(state["object_linear_velocity"])[i], np.asarray(state["object_angular_velocity"])[i])
        if self.cube_parts:
            if "cube_configuration" in state:
                self.cube_cfg = np.asarray(state["cube_configuration"], dtype=np.int64)
            if "cube_relative_orientation" in state:
                self.cube_rel = np.asarray(state["cube_relative_orientation"], float)
            if "part_position" in state and "part_orientation" in state:  # carry the recorded (scrambled) cubie placement rigidly
                p0, q0 = np.asarray(state["object_position"], float)[0], np.asarray(state["object_orientation"], float)[0]
                R = np.zeros(9); self.mj.mju_quat2Mat(R, q0 / np.linalg.norm(q0)); R = R.reshape(3, 3)
                self.part_off = (np.asarray(state["part_position"], float) - p0[None]) @ R  # offsets in the root frame
                qc = np.array([q0[0], -q0[1], -q0[2], -q0[3]]) / np.linalg.norm(q0)
                self.part_rel = np.array([_quat_mul(qc, qj / np.linalg.norm(qj)) for qj in np.asarray(state["part_orientation"], float)])
        self.mj.mj_forward(self.model, d)

    def reset(self, initial_state: dict) -> dict:
        self.mj.mj_resetData(self.model, self.data)
        self.data.qpos[self.fq] = np.clip(np.asarray(initial_state.get("q", np.zeros(20)), float).reshape(20), self.lower, self.upper)
        self.set_state(initial_state)
        p, q, _, _ = self._get_free(self.bid_mount)
        self.target = {"position": p, "orientation": q, "linear_velocity": np.zeros(3), "angular_velocity": np.zeros(3)}
        self.q_target, self.qd_target = self.data.qpos[self.fq].copy(), np.zeros(20)
        self.limiter = None
        return self.read_state()

    def read_state(self) -> dict:
        d = self.data
        self.mj.mj_forward(self.model, d)  # poses, velocities and contacts of the integrated state (xpos is stale after mj_step)
        p, q, v, w = self._get_free(self.bid_mount)
        s = {"q": d.qpos[self.fq].tolist(), "qd": d.qvel[self.fv].tolist(), "wrist_position": p.tolist(), "wrist_orientation": q.tolist(),
             "wrist_linear_velocity": v.tolist(), "wrist_angular_velocity": w.tolist()}
        P, Q, V, W = [], [], [], []
        for bid in self.bid_obj:
            p_, q_, v_, w_ = self._get_free(bid)
            P.append(p_.tolist()); Q.append(q_.tolist()); V.append(v_.tolist()); W.append(w_.tolist())
        s.update(object_position=P, object_orientation=Q, object_linear_velocity=V, object_angular_velocity=W)
        s.update(self._contacts())
        if self.cube_parts:
            s.update(self._parts(np.array(P[0]), np.array(Q[0]), np.array(V[0]), np.array(W[0])))
        return s

    def _parts(self, p, q, v, w):
        """Rigid parts: the cubie placement recorded at reset/set_state (or the solved home slots) carried with the root body."""
        R = np.zeros(9); self.mj.mju_quat2Mat(R, q); R = R.reshape(3, 3)
        off = getattr(self, "part_off", CUBE_HOME)
        rel = getattr(self, "part_rel", np.tile([1.0, 0, 0, 0], (8, 1)))
        pp = p[None] + off @ R.T
        vv = v[None] + np.cross(w[None], pp - p[None])
        qq = np.array([_quat_mul(q, r) for r in rel])
        cfg = self.cube_cfg if self.cube_cfg is not None else np.full(8, 23, dtype=np.int64)
        crel = getattr(self, "cube_rel", np.tile([1.0, 0, 0, 0], (8, 1)))
        return {"part_position": pp.tolist(), "part_orientation": qq.tolist(), "part_linear_velocity": vv.tolist(),
                "part_angular_velocity": np.tile(w, (8, 1)).tolist(), "cube_relative_orientation": crel.tolist(), "cube_configuration": cfg.tolist()}

    def _contacts(self) -> dict:
        m, d = self.model, self.data
        O = len(self.bid_obj)
        hc, ec, oo = np.zeros(O, bool), np.zeros(O, bool), np.zeros((O, O), bool)
        which = {bid: i for i, bid in enumerate(self.bid_obj)}
        for c in d.contact[:d.ncon]:
            b1, b2 = int(m.geom_bodyid[c.geom1]), int(m.geom_bodyid[c.geom2])
            for a, b in ((b1, b2), (b2, b1)):
                if a in which:
                    i = which[a]
                    if b in self.hand_bodies:
                        hc[i] = True
                    elif b in which:
                        oo[i, which[b]] = oo[which[b], i] = True
                    elif b == 0:
                        ec[i] = True
        return {"hand_object_contact": hc.tolist(), "object_environment_contact": ec.tolist(), "object_object_contact": oo.tolist()}

    # ------------------------------------------------------------------ control
    def apply(self, action: dict) -> None:
        mj, m, d = self.mj, self.model, self.data
        q_t = np.clip(np.asarray(action["q_target"], float).reshape(20), self.lower, self.upper)
        qd_t = np.zeros(20) if action.get("qd_target") is None else np.asarray(action["qd_target"], float).reshape(20)
        p_c, q_c = np.asarray(action["wrist_position_target"], float), np.asarray(action["wrist_orientation_target"], float)
        q_c = q_c / np.linalg.norm(q_c)
        v_c = np.zeros(3) if action.get("wrist_linear_velocity_target") is None else np.asarray(action["wrist_linear_velocity_target"], float)
        w_c = np.zeros(3) if action.get("wrist_angular_velocity_target") is None else np.asarray(action["wrist_angular_velocity_target"], float)
        if action.get("targets") == "commanded":
            if self.limiter is None:
                from preflight import CommandLimiter, WORKSPACE
                lo, hi = WORKSPACE[self.task]
                self.limiter = CommandLimiter(lo, hi, DT_CONTROL)
                self.limiter.reset(self.target["position"], self.target["orientation"])
            ex = self.limiter(p_c, q_c, v_c, w_c)
            p_c, q_c, v_c, w_c = np.array(ex["position"]), np.array(ex["orientation"]), np.array(ex["linear_velocity"]), np.array(ex["angular_velocity"])
        self.target = {"position": p_c, "orientation": q_c, "linear_velocity": v_c, "angular_velocity": w_c}
        for _ in range(int(round(DT_CONTROL / DT_PHYSICS))):
            mj.mj_step1(m, d)  # kinematics and velocities of the current state; forces below; mj_step2 integrates
            q, qd = d.qpos[self.fq], d.qvel[self.fv]
            tau = np.clip(KP * (q_t - q) + KD * (qd_t - qd), -EFFORT, EFFORT)
            d.qfrc_applied[:] = 0.0
            d.qfrc_applied[self.fv] = tau
            p, qw, v, w = self._get_free(self.bid_mount)
            g_up = -GRAVITY * self.hand_mass
            com = d.subtree_com[self.bid_mount]
            F = WRIST["kp_lin"] * (p_c - p) + WRIST["kd_lin"] * (v_c - v) + g_up
            e_R = _rotvec(_quat_mul(q_c, np.array([qw[0], -qw[1], -qw[2], -qw[3]])))
            T = WRIST["kp_rot"] * e_R + WRIST["kd_rot"] * (w_c - w) + np.cross(com - p, g_up)
            F, T = _clip_norm(F, WRIST["f_max"]), _clip_norm(T, WRIST["t_max"])
            d.xfrc_applied[:] = 0.0
            d.xfrc_applied[self.bid_mount, :3] = F
            d.xfrc_applied[self.bid_mount, 3:] = T + np.cross(p - d.xipos[self.bid_mount], F)  # wrench moved from the frame origin to the body CoM
            mj.mj_step2(m, d)
        self.q_target, self.qd_target = q_t, qd_t


def selftest(urdf: Path) -> int:
    """Numerical checks of the conventions this adapter relies on (run on your installation before trusting replays)."""
    import mujoco
    meta = {"task": "tennis", "object_names": ["tennis_ball"], "replay": {"joint_names": []}}
    ad = MujocoAdapter(meta, urdf)
    q0 = [0.6, -0.3, 0.3, 0.2] + [0.6, 0.0, 1.4, 0.3] * 4
    wp, wq = ([0.02761, 0.001998, 0.307144], [0.555339, -0.420012, 0.441195, -0.566159]) if ad.mount_name == "l_mount" else \
        ([0.027681, -0.00208, 0.307114], [0.553986, 0.421314, 0.439445, 0.567875])  # initial wrist pose (hardware/SPECS.md section 3)
    st = {"q": q0, "qd": [0.0] * 20, "wrist_position": wp, "wrist_orientation": wq,
          "wrist_linear_velocity": [0.1, -0.2, 0.05], "wrist_angular_velocity": [0.3, 0.1, -0.2],
          "object_position": [[0.2, 0.2, 0.5]], "object_orientation": [[1.0, 0, 0, 0]], "object_linear_velocity": [[0.0, 0.0, 0.0]], "object_angular_velocity": [[0.0, 0.0, 0.0]]}
    ad.reset(st)
    s = ad.read_state()
    ok = True
    print(f"hand mass (subtree of {ad.mount_name}):", round(ad.hand_mass, 4), "(hardware/SPECS.md: 0.6878)")
    ok &= abs(ad.hand_mass - 0.6878) < 1e-3
    ev = np.abs(np.array(s["wrist_linear_velocity"]) - st["wrist_linear_velocity"]).max(); ew = np.abs(np.array(s["wrist_angular_velocity"]) - st["wrist_angular_velocity"]).max()
    print("velocity round trip set->read: linear err", ev, "angular err", ew)
    ok &= ev < 1e-9 and ew < 1e-9
    # finite-difference check of the reported linear velocity (free fall of the ball, no controller forces on it)
    p0 = np.array(s["object_position"][0])
    ad.data.qvel[ad.obj_v[0]:ad.obj_v[0] + 3] = [0.3, 0.0, 0.0]
    mujoco.mj_forward(ad.model, ad.data)
    v_rep = np.array(ad.read_state()["object_linear_velocity"][0])
    mujoco.mj_step(ad.model, ad.data)
    p1 = np.array(ad.read_state()["object_position"][0])
    fd = (p1 - p0) / DT_PHYSICS
    print("ball reported v", v_rep.round(4).tolist(), "finite difference", fd.round(4).tolist())
    ok &= np.abs(fd[:2] - v_rep[:2]).max() < 1e-3
    # the wrist holds its pose under gravity compensation (hold the initial target for 0.5 s)
    ad.reset(dict(st, wrist_linear_velocity=[0, 0, 0], wrist_angular_velocity=[0, 0, 0]))
    act = {"q_target": q0, "qd_target": None, "wrist_position_target": st["wrist_position"], "wrist_orientation_target": st["wrist_orientation"],
           "wrist_linear_velocity_target": None, "wrist_angular_velocity_target": None, "targets": "executed"}
    for _ in range(250):
        ad.apply(act)
    s2 = ad.read_state()
    dp = np.linalg.norm(np.array(s2["wrist_position"]) - st["wrist_position"])
    print("wrist hold for 0.5 s: position drift", round(dp * 1e3, 3), "mm; finger rmse vs q0", round(float(np.sqrt(np.mean((np.array(s2["q"]) - q0) ** 2))), 4), "rad; ball z", round(s2["object_position"][0][2], 3))
    ok &= dp < 0.002
    # a 5 cm step command: the wrist moves and arrives (executed targets would be rate-limited by the target; here applied directly)
    act2 = dict(act, wrist_position_target=[st["wrist_position"][0], st["wrist_position"][1], st["wrist_position"][2] + 0.05])
    for _ in range(500):
        ad.apply(act2)
    s3 = ad.read_state()
    print("5 cm step after 1 s: remaining error", round(abs(s3["wrist_position"][2] - st["wrist_position"][2] - 0.05) * 1e3, 2), "mm; ball on floor:", s3["object_environment_contact"])
    ok &= abs(s3["wrist_position"][2] - st["wrist_position"][2] - 0.05) < 0.005
    print("SELFTEST", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--urdf", required=True)
    ap.add_argument("--scene", help="JSON file overriding the task scene (objects, friction, table, floor_z)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest(Path(a.urdf))
    scene = json.loads(Path(a.scene).read_text()) if a.scene else None
    return A.serve(lambda meta: MujocoAdapter(meta, Path(a.urdf), scene))


if __name__ == "__main__":
    sys.exit(main())
