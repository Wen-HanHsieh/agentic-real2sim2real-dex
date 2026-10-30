#!/usr/bin/env python3
"""Diagnosis of a target-vs-simulation comparison (r2s2r-calib diagnose): contact-phase segmentation, error growth per
segment, and an attribution of the discrepancies to the wrist controller / finger actuator model, free object motion or
contact phases WHERE THE EVIDENCE SUPPORTS IT, with an explicit "cannot determine" otherwise. Writes report.md (+ PNG
plots when matplotlib is installed) and extends metrics.json with the per-segment numbers. No calibration method is
prescribed: the report states what differs, when, and which part of your model the difference can be charged to.

Attribution rules (all thresholds are printed in the report):
- hand state is "close" in a segment when the wrist position error < WRIST_POS_OK, the wrist orientation error < WRIST_ANG_OK
  and the finger rmse < FINGER_OK over the segment;
- a "free" segment of an object (no hand and no environment contact in the target): object error growth is charged to
  free-body motion of your simulator (gravity, drag, integration) when the velocity error at the segment start is small,
  otherwise to the inherited velocity error (it came from an earlier segment);
- a contact segment (hand and/or environment contact): object error growth is charged to the contact model only when the
  hand state is close throughout the segment; otherwise it is "cannot determine" (the hand itself moved differently);
- wrist: the sim's wrist is compared with the target's wrist; both tracked the same executed targets in replay mode
  `executed`, so a difference is the wrist controller / hand dynamics model (plus contact reactions in contact segments);
  in mode `commanded` the command limiter is part of the difference;
- fingers: the sim's measured q is compared with the target's; both were commanded the same q_target, so a difference is
  the finger actuator / joint model (plus contact reactions in contact segments);
- state-step replay: the per-step errors are one-step prediction errors (no error accumulation), reported per segment.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import calib as C  # noqa: E402

WRIST_POS_OK, WRIST_ANG_OK, FINGER_OK = 0.002, np.radians(1.0), 0.02  # hand "close" thresholds
OBJ_POS_SMALL, OBJ_VEL_SMALL = 0.005, 0.01  # object errors considered small [m], [m/s]


def _seg_stat(e: np.ndarray, a: int, b: int) -> dict:
    x = np.asarray(e[a:b], dtype=np.float64)
    if x.size == 0:
        return {"start": None, "end": None, "max": None, "mean": None, "growth": None}
    return {"start": float(x[0]), "end": float(x[-1]), "max": float(x.max()), "mean": float(x.mean()), "growth": float(x[-1] - x[0])}


def diagnose(tg: dict, sm: dict, res: dict, out: Path, plots: bool = True) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    t2, s2, info = C.align(tg, sm)
    R = info["rows_compared"]
    tmeta, smeta = json.loads(str(tg["meta"])), json.loads(str(sm["meta"]))
    rp = smeta.get("replay") or {}
    mode, targets = rp.get("mode", "unknown"), rp.get("targets", "unknown")
    names = [str(x) for x in tg["object_names"]]
    O = len(names)
    # per-row error series
    e_wp = np.linalg.norm(s2["wrist_position"] - t2["wrist_position"], axis=1)
    e_wq = C.geodesic(s2["wrist_orientation"], t2["wrist_orientation"])
    e_op = np.stack([np.linalg.norm(s2["object_position"][:, i] - t2["object_position"][:, i], axis=1) for i in range(O)], 1)
    e_oq = np.stack([C.geodesic(s2["object_orientation"][:, i], t2["object_orientation"][:, i]) for i in range(O)], 1)
    e_ov = np.stack([np.linalg.norm(s2["object_linear_velocity"][:, i] - t2["object_linear_velocity"][:, i], axis=1) for i in range(O)], 1)
    nq = min(len(tg.get("q", [])), len(sm.get("q", [])), R)
    e_q = np.sqrt(np.mean((sm["q"][:nq] - tg["q"][:nq]) ** 2, axis=1)) if nq else np.zeros(0)
    # tracking of the same executed targets, target side and sim side (row k+1 vs target of step k)
    n_t = min(len(tg["wrist_position_target"]), R - 1)
    trk_t_p = np.linalg.norm(t2["wrist_position"][1:n_t + 1] - tg["wrist_position_target"][:n_t], axis=1)
    trk_s_p = np.linalg.norm(s2["wrist_position"][1:n_t + 1] - tg["wrist_position_target"][:n_t], axis=1)
    trk_t_q = C.geodesic(t2["wrist_orientation"][1:n_t + 1], tg["wrist_orientation_target"][:n_t])
    trk_s_q = C.geodesic(s2["wrist_orientation"][1:n_t + 1], tg["wrist_orientation_target"][:n_t])
    nf = min(len(tg["q_target"]), nq - 1) if nq > 1 else 0
    ftrk_t = np.sqrt(np.mean((tg["q"][1:nf + 1] - tg["q_target"][:nf]) ** 2, axis=1)) if nf else np.zeros(0)
    ftrk_s = np.sqrt(np.mean((sm["q"][1:nf + 1] - tg["q_target"][:nf]) ** 2, axis=1)) if nf else np.zeros(0)
    segs = C.contact_segments(tg)
    segs = [dict(sg, end=min(sg["end"], R)) for sg in segs if sg["start"] < R]
    hc_t = np.asarray(tg.get("hand_object_contact"), bool)[:R] if "hand_object_contact" in tg else None
    ec_t = np.asarray(tg.get("object_environment_contact"), bool)[:R] if "object_environment_contact" in tg else None
    rows = []
    for sg in segs:
        a, b = sg["start"], sg["end"]
        wp, wq = _seg_stat(e_wp, a, b), _seg_stat(np.degrees(e_wq), a, b)
        fq = _seg_stat(e_q, a, min(b, nq)) if nq else None
        hand_close = (wp["max"] is not None and wp["max"] < WRIST_POS_OK and wq["max"] < np.degrees(WRIST_ANG_OK)
                      and (fq is None or fq["max"] is None or fq["max"] < FINGER_OK))
        row = {"start_step": int(a), "end_step": int(b), "t_start": round(a * C.DT, 3), "t_end": round((b - 1) * C.DT, 3), "label": sg["label"],
               "wrist_position_error_m": wp, "wrist_orientation_error_deg": wq, "finger_rmse_rad": fq, "hand_close": bool(hand_close),
               "wrist_tracking_of_executed_target_m": {"target": _seg_stat(trk_t_p, a, min(b, n_t)), "sim": _seg_stat(trk_s_p, a, min(b, n_t))},
               "finger_tracking_of_q_target_rad": {"target": _seg_stat(ftrk_t, a, min(b, nf)), "sim": _seg_stat(ftrk_s, a, min(b, nf))} if nf else None,
               "objects": {}}
        for i, nm in enumerate(names):
            op, oq, ov = _seg_stat(e_op[:, i], a, b), _seg_stat(np.degrees(e_oq[:, i]), a, b), _seg_stat(e_ov[:, i], a, b)
            # the phase of this object in this segment is its part of the segment label (short runs merged into a segment keep its label)
            part = next((x.split(":", 1)[1] for x in sg["label"].split() if x.startswith(nm + ":")), None)
            in_hand = None if part is None else ("hand" in part)
            on_env = None if part is None else ("env" in part)
            if mode == "state-step":
                attribution = ("one-step prediction error (state replay): mean position error per step "
                               f"{op['mean'] * 1e3:.2f} mm; " + ("hand close" if hand_close else "hand state differs within the step too"))
                charge = "local model error (contact phase)" if (in_hand or on_env) else "local model error (free motion)"
            elif in_hand is None:
                attribution, charge = "no contact flags in the target record: phases unknown", "cannot determine"
            elif not in_hand and not on_env:
                if abs(op["growth"]) < OBJ_POS_SMALL:
                    attribution, charge = f"free segment, object error did not grow ({op['growth'] * 1e3:+.1f} mm)", "none (free motion reproduced)"
                elif ov["start"] is not None and ov["start"] > OBJ_VEL_SMALL:
                    attribution = (f"free segment: velocity error at the segment start {ov['start']:.3f} m/s already explains growth; the error was "
                                   "inherited from the previous (contact) segment")
                    charge = "inherited velocity error"
                else:
                    attribution = (f"free segment with a small velocity error at the start ({(ov['start'] or 0):.3f} m/s) and growth of "
                                   f"{op['growth'] * 1e3:+.1f} mm: free-body motion of your simulator (gravity, drag, integration, inertia)")
                    charge = "free-body dynamics"
            else:
                phase = "hand" if in_hand and not on_env else "environment" if on_env and not in_hand else "hand and environment"
                if hand_close:
                    if abs(op["growth"]) < OBJ_POS_SMALL and (oq["growth"] or 0) < 2.0:
                        attribution, charge = f"{phase} contact with the hand close; object error did not grow", "none (contact phase reproduced)"
                    else:
                        attribution = (f"{phase} contact while the hand stayed close (wrist < {WRIST_POS_OK * 1e3:.0f} mm / {np.degrees(WRIST_ANG_OK):.0f} deg, "
                                       f"fingers < {FINGER_OK} rad): object growth {op['growth'] * 1e3:+.1f} mm / {oq['growth']:+.1f} deg is charged to the contact model "
                                       "(friction, stiffness, geometry, object inertia)")
                        charge = "contact model"
                else:
                    attribution = (f"cannot determine: {phase} contact but the hand state itself differs (wrist up to {wp['max'] * 1e3:.1f} mm / {wq['max']:.2f} deg"
                                   + (f", fingers up to {fq['max']:.3f} rad rmse" if fq and fq["max"] is not None else "")
                                   + "); the object difference may stem from the hand motion, the contact model or both")
                    charge = "cannot determine"
            row["objects"][nm] = {"in_hand": in_hand, "on_environment": on_env, "position_error_m": op, "orientation_error_deg": oq,
                                  "linear_velocity_error_mps": ov, "charge": charge, "attribution": attribution}
        rows.append(row)
    # global attributions for the hand
    hand = {}
    if n_t:
        hand["wrist"] = {"sim_vs_target_position_rmse_m": float(np.sqrt(np.mean(e_wp[:R] ** 2))),
                         "target_tracking_rmse_m": float(np.sqrt(np.mean(trk_t_p ** 2))), "sim_tracking_rmse_m": float(np.sqrt(np.mean(trk_s_p ** 2))),
                         "target_tracking_rmse_deg": float(np.degrees(np.sqrt(np.mean(trk_t_q ** 2)))), "sim_tracking_rmse_deg": float(np.degrees(np.sqrt(np.mean(trk_s_q ** 2))))}
        w = hand["wrist"]
        if mode == "action" and targets == "executed":
            if w["sim_vs_target_position_rmse_m"] < WRIST_POS_OK:
                w["attribution"] = "the sim wrist follows the target wrist within the threshold: wrist controller / hand dynamics model consistent at this level"
            else:
                w["attribution"] = (f"both wrists tracked the same executed targets (target rmse {w['target_tracking_rmse_m'] * 1e3:.2f} mm, sim rmse "
                                    f"{w['sim_tracking_rmse_m'] * 1e3:.2f} mm): the difference is your wrist controller / hand dynamics model"
                                    + (" (plus contact reactions in contact segments)" if any(r["objects"][n]["in_hand"] for r in rows for n in names if r["objects"][n]["in_hand"]) else ""))
        elif mode == "action":
            w["attribution"] = "replay with commanded targets: the difference includes your command limiter; replay with --targets executed to isolate the controller"
        else:
            w["attribution"] = f"state replay ({mode}): per-step wrist prediction error {w['sim_vs_target_position_rmse_m'] * 1e3:.2f} mm rmse"
    if nq:
        fj = res.get("joints") or {}
        hand["fingers"] = {"sim_vs_target_rmse_rad": float(np.sqrt(np.mean(e_q ** 2))), "target_tracking_rmse_rad": float(np.sqrt(np.mean(ftrk_t ** 2))) if nf else None,
                           "sim_tracking_rmse_rad": float(np.sqrt(np.mean(ftrk_s ** 2))) if nf else None, "worst_joints": [x["joint"] for x in fj.get("worst_joints", [])[:3]]}
        f = hand["fingers"]
        if f["sim_vs_target_rmse_rad"] < FINGER_OK:
            f["attribution"] = "finger joints follow the target within the threshold (note: the target's q carries encoder noise of 0.002 rad)"
        elif nf and f["sim_tracking_rmse_rad"] is not None and f["target_tracking_rmse_rad"] is not None:
            f["attribution"] = (f"same q_target commands, different measured q (target tracking rmse {f['target_tracking_rmse_rad']:.4f} rad, sim "
                                f"{f['sim_tracking_rmse_rad']:.4f} rad): finger actuator / joint model (gains, effort limit, armature, joint friction)"
                                + " and contact reactions in contact segments")
    diag = {"replay": rp, "thresholds": {"wrist_position_ok_m": WRIST_POS_OK, "wrist_orientation_ok_deg": float(np.degrees(WRIST_ANG_OK)), "finger_ok_rad": FINGER_OK,
                                         "object_position_small_m": OBJ_POS_SMALL, "object_velocity_small_mps": OBJ_VEL_SMALL},
            "segments": rows, "hand": hand}
    res["diagnosis"] = diag
    (out / "metrics.json").write_text(json.dumps(res, indent=1))
    written = []
    if plots:
        written = _plots(tg, sm, t2, s2, R, names, rows, e_wp, e_wq, e_op, e_oq, e_q, out, res)
    rep_path = out / "report.md"
    rep_path.write_text(_report(tmeta, smeta, res, diag, names, written))
    return {"report": str(rep_path), "plots": written}


def _plots(tg, sm, t2, s2, R, names, rows, e_wp, e_wq, e_op, e_oq, e_q, out: Path, res: dict | None = None) -> list:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return []
    t = np.arange(R) * C.DT
    written = []

    def shade(ax):
        for i, sg in enumerate(rows):
            if i % 2:
                ax.axvspan(sg["t_start"], sg["t_end"], color="#000000", alpha=0.05, lw=0)

    fig, axs = plt.subplots(3 + len(names), 1, figsize=(10, 2.2 * (3 + len(names))), sharex=True)
    axs[0].plot(t, 1e3 * e_wp, color="#b42318"); axs[0].set_ylabel("wrist pos err [mm]"); shade(axs[0])
    axs[1].plot(t, np.degrees(e_wq), color="#b42318"); axs[1].set_ylabel("wrist ori err [deg]"); shade(axs[1])
    if len(e_q):
        axs[2].plot(np.arange(len(e_q)) * C.DT, e_q, color="#5b3a9e")
    axs[2].set_ylabel("finger rmse [rad]"); shade(axs[2])
    for i, nm in enumerate(names):
        ax = axs[3 + i]
        ax.plot(t, 1e3 * e_op[:, i], color="#1f6f3f", label="position [mm]")
        ax2 = ax.twinx(); ax2.plot(t, np.degrees(e_oq[:, i]), color="#999999", label="orientation [deg]"); ax2.set_ylabel("deg", color="#999999")
        ax.set_ylabel(f"{nm} err [mm]"); shade(ax)
        if "hand_object_contact" in tg:
            hc = np.asarray(tg["hand_object_contact"], bool)[:R, i]
            ax.fill_between(t, 0, 1e3 * e_op[:, i].max() if e_op[:, i].max() > 0 else 1, where=hc, color="#1f6f3f", alpha=0.08, lw=0, label="target hand contact")
    axs[-1].set_xlabel("t [s] (shaded bands: alternate contact segments)")
    axs[0].set_title("target vs simulation: errors over time")
    fig.tight_layout(); fig.savefig(out / "errors.png", dpi=110); plt.close(fig); written.append("errors.png")
    # wrist and object positions, components
    fig, axs = plt.subplots(3, 1 + len(names), figsize=(5 * (1 + len(names)), 7), sharex=True, squeeze=False)
    for ax_i, lab in enumerate("xyz"):
        ax = axs[ax_i, 0]
        ax.plot(t, t2["wrist_position"][:, ax_i], color="#1f6f3f", label="target")
        ax.plot(t, s2["wrist_position"][:, ax_i], color="#5b3a9e", label="sim", alpha=0.8)
        if "wrist_position_target" in tg:
            m = min(R, len(tg["wrist_position_target"]))
            ax.plot(np.arange(m) * C.DT, tg["wrist_position_target"][:m, ax_i], color="#bbbbbb", label="executed target", lw=0.8)
        ax.set_ylabel(f"wrist {lab} [m]")
        for i, nm in enumerate(names):
            axo = axs[ax_i, 1 + i]
            axo.plot(t, t2["object_position"][:, i, ax_i], color="#1f6f3f", label="target")
            axo.plot(t, s2["object_position"][:, i, ax_i], color="#5b3a9e", label="sim", alpha=0.8)
            axo.set_ylabel(f"{nm} {lab} [m]")
    axs[0, 0].legend(fontsize=8); axs[-1, 0].set_xlabel("t [s]")
    fig.tight_layout(); fig.savefig(out / "positions.png", dpi=110); plt.close(fig); written.append("positions.png")
    if len(e_q) and "q" in sm:
        worst = [x["joint"] for x in (res.get("joints") or {}).get("worst_joints", [])[:4]]
        jn = [str(x) for x in tg["joint_names"]]
        fig, axs = plt.subplots(len(worst), 1, figsize=(10, 2.0 * max(1, len(worst))), sharex=True, squeeze=False)
        n = len(e_q)
        for k, w in enumerate(worst):
            j = jn.index(w)
            ax = axs[k, 0]
            ax.plot(np.arange(n) * C.DT, tg["q"][:n, j], color="#1f6f3f", label="target q")
            ax.plot(np.arange(n) * C.DT, sm["q"][:n, j], color="#5b3a9e", label="sim q", alpha=0.8)
            ax.plot(np.arange(n) * C.DT, tg["q_target"][:n, j], color="#bbbbbb", label="q_target", lw=0.8)
            ax.set_ylabel(w, fontsize=7)
        axs[0, 0].legend(fontsize=8); axs[-1, 0].set_xlabel("t [s]")
        fig.tight_layout(); fig.savefig(out / "fingers.png", dpi=110); plt.close(fig); written.append("fingers.png")
    return written


def _f(x, scale=1.0, nd=2):
    return "n/a" if x is None else f"{x * scale:.{nd}f}"


def _report(tmeta, smeta, res, diag, names, plots) -> str:
    rp = diag["replay"]
    th = diag["thresholds"]
    L = ["# Sim-to-target calibration report", "",
         f"Task `{tmeta.get('task')}`, target submission `{tmeta.get('submission_id')}` (versions `{json.dumps(tmeta.get('versions'))}`), "
         f"{tmeta.get('steps')} control steps; replay mode `{rp.get('mode')}`, wrist targets `{rp.get('targets')}`"
         + (f", state resets at {len(rp.get('state_resets_at_steps', []))} steps" if rp.get("state_resets_at_steps") else "") + ".", "",
         f"Alignment: {res['alignment']['method']}; {res['rows_compared']} state rows compared.", "",
         "## Global errors (simulation minus target)", "", "| Quantity | rmse | max | at step | first step over threshold |", "|---|---|---|---|---|"]
    w = res["wrist"]
    L.append(f"| wrist position [mm] | {_f(w['position_error_m']['rmse'], 1e3, 3)} | {_f(w['position_error_m']['max'], 1e3, 3)} | {w['position_error_m']['argmax_step']} | {w['position_error_m'].get('first_step_over')} (10 mm) |")
    L.append(f"| wrist orientation [deg] | {_f(w['orientation_error_deg']['rmse'], 1, 3)} | {_f(w['orientation_error_deg']['max'], 1, 3)} | {w['orientation_error_deg']['argmax_step']} | {w['orientation_error_deg'].get('first_step_over')} (10 deg) |")
    if "joints" in res:
        j = res["joints"]
        L.append(f"| finger joints [rad] | {_f(j['rmse_all'], 1, 4)} | {_f(j['max_abs_all'], 1, 4)} | — | {j['first_step_over_threshold']} ({j['threshold_rad']} rad) |")
    for nm, o in res["objects"].items():
        L.append(f"| {nm} position [mm] | {_f(o['position_error_m']['rmse'], 1e3)} | {_f(o['position_error_m']['max'], 1e3)} | {o['position_error_m']['argmax_step']} | {o['position_error_m'].get('first_step_over')} (10 mm) |")
        L.append(f"| {nm} orientation [deg] | {_f(o['orientation_error_deg']['rmse'])} | {_f(o['orientation_error_deg']['max'])} | {o['orientation_error_deg']['argmax_step']} | {o['orientation_error_deg'].get('first_step_over')} (10 deg) |")
        if "hand_object_contact_agreement" in o:
            L.append(f"| {nm} hand-contact flag agreement | {o['hand_object_contact_agreement']:.3f} | | | |")
    if res.get("parts"):
        pr = res["parts"]
        if "note" in pr:
            L.append(f"| parts | {pr['note']} | | | |")
        else:
            L.append(f"| parts position, max over parts [mm] | {_f(pr['position_error_m_max_over_parts']['rmse'], 1e3)} | {_f(pr['position_error_m_max_over_parts']['max'], 1e3)} | {pr['position_error_m_max_over_parts']['argmax_step']} | |")
            if "configuration_agreement" in pr:
                L.append(f"| cube configuration agreement | {pr['configuration_agreement']:.3f} | | first mismatch step {pr['first_configuration_mismatch_step']} | |")
    L += ["", "## Hand: controller and actuator attribution", ""]
    h = diag["hand"]
    if "wrist" in h:
        hw = h["wrist"]
        L.append(f"- Wrist: sim-vs-target rmse {hw['sim_vs_target_position_rmse_m'] * 1e3:.3f} mm; tracking of the executed targets: target {hw['target_tracking_rmse_m'] * 1e3:.2f} mm / "
                 f"{hw['target_tracking_rmse_deg']:.2f} deg, sim {hw['sim_tracking_rmse_m'] * 1e3:.2f} mm / {hw['sim_tracking_rmse_deg']:.2f} deg. {hw.get('attribution', '')}")
    if "fingers" in h:
        hf = h["fingers"]
        L.append(f"- Fingers: sim-vs-target rmse {hf['sim_vs_target_rmse_rad']:.4f} rad (worst joints {', '.join(hf['worst_joints']) or 'n/a'}); tracking of q_target: target "
                 f"{_f(hf['target_tracking_rmse_rad'], 1, 4)} rad, sim {_f(hf['sim_tracking_rmse_rad'], 1, 4)} rad. {hf.get('attribution', '')}")
    L += ["", "## Contact-phase segments (from the target's contact flags)", "",
          f"Hand is 'close' when wrist error < {th['wrist_position_ok_m'] * 1e3:.0f} mm and < {th['wrist_orientation_ok_deg']:.0f} deg and finger rmse < {th['finger_ok_rad']} rad "
          f"over the segment; object growth below {th['object_position_small_m'] * 1e3:.0f} mm counts as reproduced.", "",
          "| # | t [s] | phase (per object) | hand close | wrist err max [mm] | finger rmse max [rad] | object | pos err start → end [mm] | ori err start → end [deg] | charge |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for k, sg in enumerate(diag["segments"]):
        for nm in names:
            o = sg["objects"][nm]
            L.append(f"| {k} | {sg['t_start']}–{sg['t_end']} | {sg['label']} | {'yes' if sg['hand_close'] else 'no'} | {_f(sg['wrist_position_error_m']['max'], 1e3)} | "
                     f"{_f((sg['finger_rmse_rad'] or {}).get('max'), 1, 3)} | {nm} | {_f(o['position_error_m']['start'], 1e3)} → {_f(o['position_error_m']['end'], 1e3)} | "
                     f"{_f(o['orientation_error_deg']['start'])} → {_f(o['orientation_error_deg']['end'])} | {o['charge']} |")
    L += ["", "## Attributions", ""]
    for k, sg in enumerate(diag["segments"]):
        for nm in names:
            L.append(f"- segment {k} ({sg['t_start']}–{sg['t_end']} s), {nm}: {sg['objects'][nm]['attribution']}.")
    L += ["", "## Plots", ""]
    L += [f"- `{p}`" for p in plots] if plots else ["- none (matplotlib not installed; the SVG plots of `compare` are in this directory if it was run)"]
    L += ["", "These attributions are evidence-based statements about where the difference arises, not a calibration recipe: which parameters you change, "
          "and how, is your decision. `metrics.json` carries every number of this report."]
    return "\n".join(L) + "\n"
