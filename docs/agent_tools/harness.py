#!/usr/bin/env python3
"""Research harness client: experiment records, best-policy preservation, regression gate (bookkeeping only).

Official results (status, success, progress, criteria version, hardware, runtime validity, rankability, gate, ...) come from
the target environment's ground-truth evaluation and are only DISPLAYED here, each as the target reports it: nothing in this
tool computes, changes or replaces them, treats a missing progress as 0, ranks anything itself or mixes version groups. Your
research decisions (what to try next, what to keep) stay yours.

Standard research cycle: hypothesis -> change -> local validation -> `submit` (records your intent, then submits) ->
feedback -> mandatory sim-to-target calibration (`r2s2r-calib`, TOOLS.md) -> `reflect` (diagnosis, evidence, keep / reject /
undecided, next hypothesis) -> next iteration. The target binds each intent to the submission with the same archive SHA-256
and keeps best policy and comparisons in `history` automatically; this tool captures objective facts (git revision, diff,
archive hash) and keeps local copies.

Calibration rule (TOOLS.md section 3; EXPERIMENT.md): after every target evaluation and before the next submission, the
calibration of the previous rollout must be recorded on your machine with `r2s2r-calib record DIR --hypothesis ... --notes ...
--config cfg.json --files ...`, where cfg.json names the submission and states the outcome: {"status": "completed",
"submission_id": "sNN", "experiment": ..., "archive_sha256": ..., "feedback_sha256": "<the submission's feedback hash>",
"simulator_revision": ..., "replay_mode": "commanded" | "executed", optional "calib_mode": "action" | "state-step" |
"state-segment", "simulator_changes" or "no_change_reason": ..., "local_validation": ...} with the metrics.json of the comparison among --files; or, only when the feedback is unavailable /
sealed or replay is genuinely infeasible, {"status": "exception", "submission_id": "sNN", "feedback_sha256": "<hash>" |
"unavailable", "exception_reason_class": "feedback_unavailable" | "feedback_sealed" | "replay_infeasible", "explanation": ...,
"alternative_diagnosis": ...} with the failed tool output / fetch error among --files (self-declared, evidence required, never
"completed"). `reflect sNN --calibration DIR` cites the record (directory, record.json SHA-256, feedback hash) in the
reflection's evidence and analysis (an exception goes to limitation). `submit` REFUSES by default when the previous finished
submission has neither a valid completed record (with feedback) nor a valid exception record; the first submission is exempt;
there is no option or environment variable that skips this check, and no server-side gate (the target never blocks a
submission for a missing research record). Records are looked up under --calib-records DIR, else $R2S2R_CALIB_RECORDS, else
<records>/<api>/calibration.

Usage (API = your target-environment API command, e.g. r2s2r-pen; or set R2S2R_API):
  r2s2r-harness --api r2s2r-pen submit DIR|ARCHIVE [--hypothesis ...] [--change ...] [--rationale ...] [--parent sMM]
                [--kind improvement|diagnostic|experimental] [--repo DIR] [--local result.json] [--sim-config cfg.json]
                [--checkpoint REF] [--records DIR] [--dry-run]
  r2s2r-harness --api r2s2r-pen reflect sNN [--worked ...] [--failed ...] [--diagnosis ...] [--evidence ...]
                [--keep keep|reject|undecided] [--decision ...] [--next ...] [--limitation ...] [--analysis ...]
                [--calibration DIR]   cite the r2s2r-calib record of sNN (completed: evidence / analysis; exception: limitation)
  r2s2r-harness [--calib-records DIR] ...          where local r2s2r-calib records are looked up (default $R2S2R_CALIB_RECORDS,
                                                   else <records>/<api>/calibration); any command
  r2s2r-harness --api r2s2r-pen summary [--json]
  r2s2r-harness --api r2s2r-pen result sNN [--json]   the official result of one submission as the target reports it
  r2s2r-harness --api r2s2r-pen record sNN --kind improvement|diagnostic|experimental --hypothesis ... --change ...
                --evidence ... --decision ... [--keep keep|reject|undecided] [--repo DIR] [--sim-config cfg.json]
                [--checkpoint REF] [--analysis TEXT] [--local result.json] [--parent sMM]
                                                   a plain research note (REMOTE_API.md section 5), appended to sNN
  r2s2r-harness --api r2s2r-pen archive DIR        write-once local copy: history, feedback bundles, packages, manifest
  r2s2r-harness --api r2s2r-pen best [--download DIR]   the best evaluated policy (official rule) and its exact package
  r2s2r-harness --api r2s2r-pen gate sNN           official regression gate of sNN against the best comparable before it
  r2s2r-harness verify DIR                         check an archive against its manifest
  r2s2r-harness --api r2s2r-pen video sNN VIDEO --package DIR|ARCHIVE [--simulator NAME] [--local-run ID]
                                                   link a video of your own training-simulation rollout of the policy
                                                   submitted as sNN (MP4 or WebM, <= 64 MB; display only, not charged)
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tarfile
import time
from pathlib import Path

VERSION = "r2s2r-harness 4"
UNDEFINED = "criteria not defined"


def api(cmd: str, args: list[str], stdin: bytes | None = None) -> bytes:
    r = subprocess.run(shlex.split(cmd) + args, input=stdin, capture_output=True)
    if r.returncode != 0:
        try:
            raise SystemExit("API error: " + json.loads(r.stdout).get("error", r.stdout.decode()[:300]))
        except ValueError:
            raise SystemExit(f"API error (exit {r.returncode}): {r.stderr.decode()[-300:]}") from None
    return r.stdout


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def history(a) -> dict:
    return json.loads(api(a.api, ["history"]))


def _outcome(c):
    return "-" if not c else f"{c['outcome']}({c['submission_id']})"


NOT_COMPUTED = "N/A (not computed)"
FINISHED = ("done", "error", "timeout")


def _official(s: dict) -> dict:
    return s.get("official") or {}


def _progress(o: dict) -> str:
    """The official progress exactly as the target reports it: a number (0.000 is a number), 'N/A (not computed)' when the
    target reports no progress for an evaluated rollout, 'criteria not defined' / 'not evaluable' for those statuses, '-'
    while there is no result. Never derived or defaulted here."""
    if not o:
        return "-"
    vs = o.get("verifier_status") or o.get("status")
    if vs == "criteria_undefined":
        return UNDEFINED
    if vs == "not_evaluable":
        return "not evaluable"
    sc = o.get("score")
    if sc is None:
        return NOT_COMPUTED if vs == "evaluated" else "-"
    return f"{sc:.3f}"


def _success(o: dict) -> str:
    if not o:
        return "-"
    vs = o.get("verifier_status") or o.get("status")
    if vs != "evaluated":
        return "n/a"
    return {"success": "yes", "failure": "no"}.get(o.get("status"), str(o.get("status")))


def _criteria(o: dict) -> str:
    c = (o or {}).get("criteria") or {}
    v = ((o or {}).get("versions") or {}).get("verifier")
    if not c:
        return "-"
    return f"{c.get('id') or 'none'}/{c.get('status') or '-'}" + (f" {v}" if v else "")


def _ranked(s: dict) -> str:
    """Rankability and gate as the target reports them: the gate for a ranked record, else why it is not ranked."""
    o = _official(s)
    if not o:
        return "-"
    if o.get("rankable"):
        return str(s.get("gate") or "ranked")
    return f"not ranked ({o.get('unranked_reason') or 'target: rankable false'})"


def _versions_diff(a: dict, b: dict) -> list:
    return sorted(k for k in set(a or {}) | set(b or {}) if (a or {}).get(k) != (b or {}).get(k))


def _calibration_text(c: dict) -> str:
    """The calibration column (local check, never an official value): the status of the valid record found (completed /
    exception, +reflection when a reflection cites it), INVALID when records name the submission but none validates, MISSING
    when a later submission exists without evidence, 'due' while it is the latest finished submission, '-' before the result."""
    if not c or not c.get("applicable"):
        return "-"
    if c.get("satisfied"):
        return c["status"] + ("+reflection" if c.get("reflection") else "")
    if c.get("invalid_records"):
        return "INVALID"
    return "MISSING" if c.get("overdue") else "due"


def row_view(s: dict, calib: dict | None = None) -> dict:
    """One submission as the harness displays it (every official value taken from the target's history row; `calibration` is
    the local evidence check, see calibration_status)."""
    o = _official(s)
    rs = s.get("research") or {}
    return {"submission_id": s["submission_id"], "role": s.get("role"), "keep": s.get("keep"), "state": s.get("state"),
            "status": o.get("status"), "verifier_status": o.get("verifier_status"), "success": _success(o), "progress": _progress(o), "score": o.get("score"),
            "criteria": o.get("criteria"), "verifier": (o.get("versions") or {}).get("verifier"), "runtime": o.get("runtime"), "hardware": o.get("hardware"),
            "rankable": o.get("rankable"), "unranked_reason": o.get("unranked_reason"), "gate": s.get("gate"),
            "vs_previous": (s.get("comparison") or {}).get("vs_previous"), "intent": bool(rs.get("intent")), "reflection": bool(rs.get("current_reflection")),
            "calibration": calib, "needs": rs.get("needs") or [], "versions": o.get("versions")}


def cmd_summary(a):
    h = history(a)
    root = _calib_root(a)
    if getattr(a, "json", False):
        print(json.dumps({"submissions": [row_view(s, calibration_status(h, s, root)) for s in h["submissions"]], "best_evaluated": h.get("best_evaluated"), "best_by_versions": h.get("best_by_versions"),
                          "latest_candidate": h.get("latest_candidate"), "rules": {"best": h.get("best_rule"), "gate": h.get("gate_rule"), "comparison": h.get("comparison_rule")}}, indent=1))
        return
    print(f"{'sub':5s} {'role':12s} {'keep':9s} {'state':7s} {'status':18s} {'succ':4s} {'progress':18s} {'criteria/verifier':28s} {'runtime':8s} {'hardware':9s} "
          f"{'ranked / gate':36s} {'vs previous':20s} {'intent':6s} {'refl':7s} calibration")
    for s in h["submissions"]:
        o = _official(s)
        rs = s.get("research") or {}
        cmp_ = s.get("comparison") or {}
        refl = "yes" if rs.get("current_reflection") else ("-" if s.get("state") not in FINISHED else "MISSING")
        print(f"{s['submission_id']:5s} {str(s.get('role')):12s} {str(s.get('keep') or '-'):9s} {str(s.get('state')):7s} {str(o.get('status', '-')):18s} {_success(o):4s} "
              f"{_progress(o):18s} {_criteria(o):28s} {str(o.get('runtime', '-')):8s} {str(o.get('hardware', '-')):9s} {_ranked(s):36s} "
              f"{_outcome(cmp_.get('vs_previous')):20s} {('yes' if rs.get('intent') else 'MISSING'):6s} {refl:7s} {_calibration_text(calibration_status(h, s, root))}")
    be = h.get("best_evaluated") or {}
    groups = h.get("best_by_versions") or []
    if be.get("official"):
        bo = be["official"]
        print("best evaluated:", be.get("submission_id"), f"(status {bo.get('status')}, success {_success(bo)}, progress {_progress(bo)}, criteria {_criteria(bo)}, "
                                                           f"target model {(be.get('versions') or {}).get('target_model')}; the version group of the latest ranked submission)",
              "| latest candidate:", h.get("latest_candidate"))
        others = [g for g in groups if g.get("submission_id") != be.get("submission_id")]
        for g in others:
            print(f"  other version group (not comparable with it; differs in {', '.join(_versions_diff(g.get('versions'), be.get('versions')))}): "
                  f"best {g.get('submission_id')} ({_criteria(g.get('official') or {})}, progress {_progress(g.get('official') or {})})")
    else:
        reasons = sorted({str(_official(s).get("unranked_reason")) for s in h["submissions"] if _official(s) and not _official(s).get("rankable")})
        print("best evaluated: none" + (f" (nothing ranked: {', '.join(reasons)})" if reasons else ""), "| latest candidate:", h.get("latest_candidate"))
    print("rule:", h["best_rule"])
    rsum = h.get("research_summary")
    if rsum:
        print(f"research records: {rsum['with_intent']}/{rsum['submissions']} with intent, {rsum['with_reflection']}/{rsum['submissions']} with reflection")
        for x in rsum["incomplete"]:
            print(f"  INCOMPLETE {x['submission_id']}: " + "; ".join(x["needs"]))
        for x in rsum.get("unbound_intents", []):
            print(f"  intent {x['intent_id']} ({x['recorded']}) not bound: {x['reason']}")
    overdue = [s["submission_id"] for s in h["submissions"] if calibration_status(h, s, root).get("overdue")]
    if overdue:
        print("  CALIBRATION MISSING (TOOLS.md section 3; local check): " + ", ".join(overdue) + " — r2s2r-calib record DIR --hypothesis ... --config cfg.json --files metrics.json ..., then r2s2r-harness reflect sNN --calibration DIR")


def _find(h: dict, sid: str) -> dict:
    s = next((x for x in h["submissions"] if x["submission_id"] == sid), None)
    if s is None:
        raise SystemExit("unknown submission")
    return s


def cmd_result(a):
    """The official result of one submission, field by field as recorded in history (the full report is in the fetched feedback)."""
    h = history(a)
    s = _find(h, a.sid)
    o = _official(s)
    calib = calibration_status(h, s, _calib_root(a))
    if getattr(a, "json", False):
        print(json.dumps(row_view(s, calib) | {"official": o, "comparison": s.get("comparison"), "research": s.get("research")}, indent=1))
        return
    if not o:
        print(f"{a.sid}: state {s.get('state')}, no official result yet" + (f" ({s.get('error')})" if s.get("error") else ""))
        return
    vs = o.get("verifier_status") or o.get("status")
    print(f"{a.sid}: result {o.get('status')} (verifier status {vs}); criteria {_criteria(o)}")
    print(f"  success: {_success(o)}")
    print(f"  progress: {_progress(o)}" + (f" ({o.get('confidence')})" if o.get("confidence") and o.get("score") is not None else ""))
    if vs == "criteria_undefined":
        print(f"  ({UNDEFINED}: nothing is scored or ranked until the task's criteria are published)")
    print(f"  runtime validity: {o.get('runtime')}; hardware compliance: {o.get('hardware')}")
    print(f"  rankable: {o.get('rankable')}" + (f" ({o['unranked_reason']})" if o.get("unranked_reason") else "") + f"; gate: {s.get('gate') if s.get('gate') is not None else 'none'}")
    stages = o.get("stages") or {}
    if stages:
        print("  stages (target names): " + ", ".join(f"{k}={v}" for k, v in stages.items()))
    ms = o.get("milestones") or []
    if ms:
        print("  milestones reached: " + (", ".join(f"{m['stage']}: {m['label']}" for m in ms if m.get("reached")) or "none"))
        print("  milestones not reached: " + (", ".join(f"{m['stage']}: {m['label']}" for m in ms if not m.get("reached")) or "none"))
    cmp_ = s.get("comparison") or {}
    if cmp_:
        print(f"  vs previous: {_outcome(cmp_.get('vs_previous'))}; vs best before: {_outcome(cmp_.get('vs_best_before'))}"
              + (f"; not comparable with: {', '.join(cmp_['earlier_not_comparable'])}" if cmp_.get("earlier_not_comparable") else ""))
    print("  versions:", json.dumps(o.get("versions")))
    if calib.get("applicable"):
        print(f"  calibration (local check): {_calibration_text(calib)}; reflection citing it: {calib.get('reflection') or 'none'}; "
              f"valid records: {', '.join(r['dir'] for r in calib['valid_records']) or 'none'}")
        for r in calib.get("invalid_records") or []:
            print(f"    invalid record {r['dir']}: " + "; ".join(r["problems"]))
    print("  evidence:", ((s.get("research") or {}).get("evidence") or {}).get("rollout"), "| feedback:", s.get("feedback_sha256"))
    needs = (s.get("research") or {}).get("needs") or []
    if needs:
        print("  needs: " + "; ".join(needs))


def cmd_record(a):
    d = {"kind": a.kind, "hypothesis": a.hypothesis, "change": a.change, "evidence": a.evidence, "decision": a.decision}
    if a.keep:
        d["keep"] = a.keep
    if a.repo:
        rev = subprocess.run(["git", "-C", a.repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", a.repo, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
        stat = subprocess.run(["git", "-C", a.repo, "diff", "--stat", "HEAD~1..HEAD"], capture_output=True, text=True).stdout.strip()
        d["source_revision"] = (rev or "unknown") + (" (uncommitted changes)" if dirty else "")
        if stat:
            d["code_change"] = stat[-3900:]
    for key, path in (("sim_config", a.sim_config), ("local", a.local)):
        if path:
            d[key] = json.loads(Path(path).read_text())
    for key in ("checkpoint", "analysis", "parent"):
        if getattr(a, key):
            d[key] = getattr(a, key)
    print(api(a.api, ["note", a.sid], json.dumps(d).encode()).decode().strip())


def _git(repo: str, *args) -> tuple[int, str]:
    r = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True)
    return r.returncode, r.stdout


def capture_git(repo: str, base_hint: str | None = None) -> tuple[dict, str]:
    """Objective facts about the source tree (captured, never authored): revision, uncommitted changes, diff against the
    parent submission's revision (else the previous commit). Returns (auto fields, full diff text)."""
    code, inside = _git(repo, "rev-parse", "--is-inside-work-tree")
    if code != 0 or inside.strip() != "true":
        return {"git": f"not a git repository: {os.path.abspath(repo)} (source revision not captured)"}, ""
    rev = _git(repo, "rev-parse", "HEAD")[1].strip() or None
    porcelain = _git(repo, "status", "--porcelain")[1]
    base = None
    if base_hint and _git(repo, "cat-file", "-e", base_hint + "^{commit}")[0] == 0:
        base = base_hint
    elif _git(repo, "rev-parse", "--verify", "-q", "HEAD~1")[0] == 0:
        base = "HEAD~1"
    diff = _git(repo, "diff", base)[1] if base else (_git(repo, "diff", "HEAD")[1] if rev else "")
    stat = _git(repo, "diff", "--stat", base)[1] if base else ""
    untracked = [ln[3:] for ln in porcelain.splitlines() if ln.startswith("??")]
    summary = stat.strip() + (("\nuntracked: " + ", ".join(untracked)) if untracked else "")
    auto = {"source_revision": rev, "source_dirty": bool(porcelain.strip()), "diff_base": base or "none (first commit)",
            "code_diff_sha256": hashlib.sha256(diff.encode()).hexdigest(), "code_change": summary[-3900:] or "no changes against the base"}
    if not rev:
        auto["git"] = "repository has no commits"
    return auto, diff


def build_archive(path: Path) -> bytes:
    """A directory becomes a deterministic .tar.gz of its contents (sorted, fixed metadata, like `tar -C DIR -czf - .`);
    an existing .tar / .tar.gz is used byte for byte."""
    if path.is_file():
        return path.read_bytes()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for f in sorted(path.rglob("*")):
            rel = f.relative_to(path).as_posix()
            if f.is_symlink():
                raise SystemExit(f"links are not allowed in a package: {rel}")
            ti = tarfile.TarInfo(rel + ("/" if f.is_dir() else ""))
            ti.mtime, ti.uid, ti.gid, ti.uname, ti.gname = 0, 0, 0, "", ""
            if f.is_dir():
                ti.type, ti.mode = tarfile.DIRTYPE, 0o755
                tf.addfile(ti)
            else:
                data = f.read_bytes()
                ti.size, ti.mode = len(data), 0o644
                tf.addfile(ti, io.BytesIO(data))
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", mtime=0) as gz:
        gz.write(buf.getvalue())
    return out.getvalue()


def _records_dir(a) -> Path:
    base = Path(getattr(a, "records", None) or os.environ.get("R2S2R_RECORDS") or Path.home() / "r2s2r_records")
    return base / (Path(a.api.split()[-1]).name if a.api else "dry-run")  # the API command's name, never its path


def _keep_local(root: Path, rel: str, data: bytes):
    p = root / rel
    if p.exists():
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    os.chmod(p, 0o444)


def _manifest_contract(path: Path) -> str | None:
    """contract_version declared by a package directory's manifest (None if unreadable); the target refuses anything but v2."""
    if not path.is_dir():
        return None
    try:
        return str(json.loads((path / "manifest.json").read_text()).get("contract_version"))
    except (OSError, ValueError, AttributeError):
        return None


# ------------------------------------------------------------------ mandatory calibration (TOOLS.md): local evidence and the target's record
def _calib_root(a) -> Path:
    v = getattr(a, "calib_records", None) or os.environ.get("R2S2R_CALIB_RECORDS")
    return Path(v) if v else _records_dir(a) / "calibration"


CALIB_STATUS = ("completed", "exception")
EXCEPTION_CLASSES = ("feedback_unavailable", "feedback_sealed", "replay_infeasible")
REPLAY_MODES = ("commanded", "executed")
CALIB_MODES = ("action", "state-step", "state-segment")  # optional: the r2s2r-calib replay --mode used
CALIB_CONFIG = ("status", "submission_id", "experiment", "archive_sha256", "policy_sha256", "feedback_sha256", "simulator_revision", "simulator_config",
                "replay_mode", "calib_mode", "simulator_changes", "no_change_reason", "local_validation", "exception_reason_class", "explanation", "alternative_diagnosis")


def calibration_due(h: dict) -> dict | None:
    """The latest finished submission: the rollout whose calibration (or documented exception) must exist before the next
    submission. None before the first finished submission (the first submission is exempt)."""
    cands = [s for s in h["submissions"] if s.get("state") in FINISHED]
    return cands[-1] if cands else None


def load_calibration_record(d: Path) -> dict | None:
    """An r2s2r-calib record directory as the harness reads it: record.json plus its SHA-256 (the record's identity)."""
    rj = Path(d) / "record.json"
    try:
        raw = rj.read_bytes()
        r = json.loads(raw)
    except (OSError, ValueError):
        return None
    if not isinstance(r, dict):
        return None
    cfg = r.get("config") if isinstance(r.get("config"), dict) else {}
    return {"dir": str(Path(d).resolve()), "record_sha256": sha(raw), "config": cfg, "files": r.get("files") or {}, "hypothesis": r.get("hypothesis") or "",
            "notes": r.get("notes") or "", "summary": r.get("summary"), "recorded_utc": r.get("recorded_utc")}


def local_calibration_records(root: Path, sid: str) -> list:
    """The r2s2r-calib records under root whose configuration names the submission sid, oldest first."""
    out = []
    if not Path(root).is_dir():
        return out
    for rj in sorted(Path(root).glob("*/record.json")):
        r = load_calibration_record(rj.parent)
        if r and r["config"].get("submission_id") == sid:
            out.append(r)
    return out


def _text_ok(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def validate_calibration_record(r: dict, s: dict) -> list:
    """Why record r is not valid calibration evidence for submission row s (empty = valid). status completed: the feedback
    hash, replay mode, simulator revision, a metrics.json made from that feedback, and the simulator changes or the reason
    for none; status exception: an allowed reason class, at least one evidence file, an explanation and an alternative
    diagnosis. Nothing is inferred: missing evidence is reported, never assumed."""
    cfg, sid, fsha = r["config"], s["submission_id"], s.get("feedback_sha256")
    problems = []
    status = cfg.get("status")
    if status not in CALIB_STATUS:
        return [f'config.status must be "completed" or "exception" (got {status!r})']
    if cfg.get("submission_id") != sid:
        problems.append(f"config.submission_id {cfg.get('submission_id')!r} is not {sid}")
    unknown = sorted(set(cfg) - set(CALIB_CONFIG))
    if unknown:
        problems.append("unknown config keys: " + ", ".join(unknown))
    if "calib_mode" in cfg and cfg["calib_mode"] not in CALIB_MODES:
        problems.append('config.calib_mode, when given, must be "action", "state-step" or "state-segment" (the r2s2r-calib replay --mode)')
    if status == "completed":
        if not fsha:
            problems.append("a completed calibration cannot refer to a submission without accessible feedback: record an exception (feedback_unavailable / feedback_sealed)")
        elif cfg.get("feedback_sha256") != fsha:
            problems.append(f"config.feedback_sha256 {str(cfg.get('feedback_sha256'))[:12]}... is not this submission's feedback hash {fsha[:12]}...")
        if cfg.get("replay_mode") not in REPLAY_MODES:
            problems.append('config.replay_mode must be "commanded" or "executed" (what was replayed)')
        if not _text_ok(cfg.get("simulator_revision")):
            problems.append("config.simulator_revision is required (the simulator code revision / configuration used for the replay)")
        if not (_text_ok(cfg.get("simulator_changes")) or _text_ok(cfg.get("no_change_reason"))):
            problems.append("config.simulator_changes or config.no_change_reason is required (what was changed, or why nothing was)")
        mp = Path(r["dir"]) / "metrics.json"
        if "metrics.json" not in r["files"] or not mp.is_file():
            problems.append("no metrics.json among the record's files (the r2s2r-calib compare / diagnose output of this feedback)")
        else:
            try:
                m = json.loads(mp.read_text())
                tgt = (m.get("target") or {}).get("feedback_sha256")
            except (OSError, ValueError, AttributeError):
                tgt = None
            if fsha and tgt != fsha:
                problems.append(f"metrics.json was not made from this submission's feedback (target.feedback_sha256 {str(tgt)[:12]}... is not {fsha[:12]}...)")
    else:
        cls = cfg.get("exception_reason_class")
        if cls not in EXCEPTION_CLASSES:
            problems.append("config.exception_reason_class must be one of " + ", ".join(EXCEPTION_CLASSES))
        if fsha and cfg.get("feedback_sha256") not in (fsha, "unavailable"):
            problems.append("config.feedback_sha256 must be this submission's feedback hash or \"unavailable\"")
        if not fsha and cls == "replay_infeasible":
            problems.append("replay_infeasible presumes accessible feedback; this submission has none: use feedback_unavailable or feedback_sealed")
        if not r["files"]:
            problems.append("an exception record needs at least one evidence file (--files: the failed tool output, the fetch error, ...)")
        for k in ("explanation", "alternative_diagnosis"):
            if not _text_ok(cfg.get(k)):
                problems.append(f"config.{k} is required (non-empty text)")
    return problems


def reflection_calibration(s: dict) -> dict | None:
    """The reflection of submission s that cites its calibration, from the notes the target lists for it: evidence or
    analysis naming a calibration record and the submission's feedback hash (what `reflect --calibration DIR` writes), or a
    limitation recording a calibration exception."""
    fsha = s.get("feedback_sha256")
    for n in reversed(s.get("notes") or []):
        if n.get("record") != "reflection":
            continue
        cited = (n.get("evidence") or "") + " " + (n.get("analysis") or "")
        if "calibration record" in cited and (not fsha or fsha in cited):
            return {"entry_sha256": n.get("entry_sha256"), "kind": "completed", "recorded": n.get("recorded")}
        if "calibration exception" in (n.get("limitation") or "").lower():
            return {"entry_sha256": n.get("entry_sha256"), "kind": "exception", "recorded": n.get("recorded")}
    return None


def calibration_status(h: dict, s: dict, root: Path) -> dict:
    """The local calibration check of one submission (never an official value): applicable once it finished; the records
    under root naming it are validated for it (valid / invalid with problems); `reflection` = the reflection citing the
    calibration; `overdue` when a later submission exists and no valid record does."""
    applicable = s.get("state") in FINISHED
    if not applicable:
        return {"submission_id": s["submission_id"], "applicable": False}
    recs = local_calibration_records(root, s["submission_id"])
    valid, invalid = [], []
    for r in recs:
        problems = validate_calibration_record(r, s)
        (invalid if problems else valid).append((r, problems))
    ids = [x["submission_id"] for x in h["submissions"]]
    later = ids[ids.index(s["submission_id"]) + 1:]
    return {"submission_id": s["submission_id"], "applicable": True, "feedback_sha256": s.get("feedback_sha256"), "satisfied": bool(valid),
            "status": valid[-1][0]["config"]["status"] if valid else None, "reflection": reflection_calibration(s),
            "valid_records": [{"dir": r["dir"], "status": r["config"]["status"], "record_sha256": r["record_sha256"]} for r, _ in valid],
            "invalid_records": [{"dir": r["dir"], "problems": pr} for r, pr in invalid],
            "overdue": bool(later) and not valid}


def _calibration_howto(sid: str, fsha: str | None, root: Path) -> str:
    cfg = (f'{{"status": "completed", "submission_id": "{sid}", "experiment": ..., "archive_sha256": ..., "feedback_sha256": "{fsha}", "simulator_revision": ..., '
           f'"replay_mode": "commanded" | "executed", "simulator_changes" or "no_change_reason": ..., "local_validation": ...}}') if fsha else None
    exc = (f'{{"status": "exception", "submission_id": "{sid}", "feedback_sha256": "{fsha or "unavailable"}", "exception_reason_class": '
           f'"{"feedback_unavailable" if not fsha else "feedback_unavailable | feedback_sealed | replay_infeasible"}", "explanation": ..., "alternative_diagnosis": ...}}')
    how = (f"To complete it: r2s2r-calib extract / replay / compare / diagnose on the feedback of {sid}, then `r2s2r-calib record {root} --hypothesis TEXT "
           f"--notes TEXT --config cfg.json --files .../metrics.json ...` with cfg.json {cfg}, then `r2s2r-harness reflect {sid} --calibration DIR`. " if fsha else
           f"{sid} has no accessible feedback: ")
    how += (f"{'Only when' if fsha else 'Record the exception, since'} the feedback is unavailable / sealed{' or replay is genuinely infeasible' if fsha else ''}: "
            f"`r2s2r-calib record {root} --hypothesis TEXT --notes TEXT --config cfg.json --files <tool error log / fetch output>` with cfg.json {exc} "
            f"(self-declared; the evidence files and texts are checked; it is never a completed calibration), then `r2s2r-harness reflect {sid} --calibration DIR`.")
    return how


def check_calibration_before_submit(a, h: dict) -> dict | None:
    """The local calibration gate (TOOLS.md section 3): the latest finished submission must have a
    valid completed calibration record (with accessible feedback) or a valid exception record on this machine, else the
    submission is refused with what to run. Returns the evidence of that submission (None before the first finished one). No
    option or environment variable skips it."""
    due = calibration_due(h)
    if due is None:
        return None
    root = _calib_root(a)
    ev = calibration_status(h, due, root)
    if ev["satisfied"]:
        return ev
    sid = due["submission_id"]
    found = (f"no record under {root} names {sid}" if not ev["invalid_records"] else
             f"{len(ev['invalid_records'])} record(s) name {sid} but none is valid evidence: " + " | ".join(f"{r['dir']}: " + "; ".join(r["problems"]) for r in ev["invalid_records"]))
    raise SystemExit(f"refused: calibration of {sid} not recorded (TOOLS.md section 3: mandatory after every target evaluation, before the next submission; "
                     f"the first submission is exempt). {found}. " + _calibration_howto(sid, due.get("feedback_sha256"), root))


def _reflection_from_record(r: dict, sid: str) -> dict:
    """What `reflect --calibration DIR` adds to the reflection from a valid r2s2r-calib record: a completed calibration is cited
    in evidence (directory, record.json SHA-256, feedback hash, replay mode, simulator revision, metrics summary) and summarized
    in analysis (simulator changes or the no-change reason, local validation, notes); an exception goes to limitation (reason
    class, explanation, record) with its evidence files and alternative diagnosis in evidence."""
    cfg, path, rsha = r["config"], r["dir"], r["record_sha256"]
    if cfg.get("status") == "exception":
        return {"limitation": f"calibration exception ({cfg.get('exception_reason_class')}): {cfg.get('explanation')} (calibration record {path}, record.json sha256 {rsha})",
                "evidence": (f"calibration exception record {path} (record.json sha256 {rsha}) for {sid}, feedback {cfg.get('feedback_sha256')}; evidence files: "
                             + ", ".join(f"{k} sha256 {v[:12]}" for k, v in r["files"].items()) + f"; alternative diagnosis: {cfg.get('alternative_diagnosis')}")}
    ev = (f"calibration record {path} (record.json sha256 {rsha}) for {sid}, feedback {cfg.get('feedback_sha256')}, status completed: replay {cfg.get('replay_mode')}"
          + (f" ({cfg['calib_mode']} mode)" if cfg.get("calib_mode") else "") + f", simulator {cfg.get('simulator_revision')}, metrics summary {json.dumps(r.get('summary'), sort_keys=True)}")
    parts = []
    if _text_ok(cfg.get("simulator_changes")):
        parts.append("simulator changes: " + cfg["simulator_changes"])
    if _text_ok(cfg.get("no_change_reason")):
        parts.append("simulator unchanged: " + cfg["no_change_reason"])
    if _text_ok(cfg.get("local_validation")):
        parts.append("local validation: " + cfg["local_validation"])
    if _text_ok(r.get("hypothesis")):
        parts.append("hypothesis: " + r["hypothesis"])
    if _text_ok(r.get("notes")):
        parts.append("notes: " + r["notes"])
    return {"evidence": ev, "analysis": f"calibration of {sid}: " + "; ".join(parts)}


def cmd_submit(a):
    cv = _manifest_contract(Path(a.package))
    if cv is not None and cv != "v2":
        print(f'WARNING: manifest.json declares contract_version {cv!r}; this experiment accepts "v2" only (sim2target/PACKAGE.md) and will refuse the package')
    data = build_archive(Path(a.package))
    digest = sha(data)
    parent_rev = None
    if a.parent and not a.dry_run:
        par = next((x for x in history(a)["submissions"] if x["submission_id"] == a.parent), None)
        parent_rev = ((((par or {}).get("research") or {}).get("intent") or {}).get("auto") or {}).get("source_revision")
    auto, diff = capture_git(a.repo or ".", parent_rev)
    auto.update({"captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "captured_by": VERSION})
    intent = {"package_sha256": digest, "auto": auto}
    for k in ("hypothesis", "change", "rationale", "parent", "kind", "checkpoint"):
        if getattr(a, k):
            intent[k] = getattr(a, k)
    for key, path in (("sim_config", a.sim_config), ("local", a.local)):
        if path:
            intent[key] = json.loads(Path(path).read_text())
    missing = [k for k in ("hypothesis", "change") if k not in intent]
    if a.dry_run:
        print(json.dumps({"archive_bytes": len(data), "package_sha256": digest, "intent": intent, "missing": missing}, indent=1))
        return
    root = _records_dir(a)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    cal_ev = check_calibration_before_submit(a, history(a))
    try:
        ir = json.loads(api(a.api, ["intent"], json.dumps(intent).encode()))
    except SystemExit as e:  # a failed research record never blocks a valid submission; history shows the gap
        ir = {"intent_id": None, "error": str(e)}
        print(f"WARNING: intent not recorded ({e}); submitting anyway, history will list the intent as missing")
    receipt = json.loads(api(a.api, ["submit"], data))
    if receipt.get("archive_sha256") and receipt["archive_sha256"] != digest:
        print("WARNING: the target's archive SHA-256 differs from the one sent; the intent will not bind")
    sid = receipt.get("submission_id", "unknown")
    _keep_local(root, f"submissions/{sid}/intent.json", json.dumps({"intent": intent, "response": ir}, indent=1).encode())
    _keep_local(root, f"submissions/{sid}/receipt.json", json.dumps(receipt, indent=1).encode())
    _keep_local(root, f"submissions/{sid}/source.diff", diff.encode())
    _keep_local(root, f"submissions/{sid}/package_{digest[:12]}.tar.gz", data)
    print(json.dumps({"submission": receipt, "intent": ir, "missing_agent_fields": missing, "calibration_of_previous": cal_ev,
                      "local_copy": str(root / "submissions" / sid), "submitted_at": stamp}, indent=1))


def cmd_reflect(a):
    h = history(a)
    s = next((x for x in h["submissions"] if x["submission_id"] == a.sid), None)
    if s is None:
        raise SystemExit("unknown submission")
    if s.get("state") not in ("done", "error", "timeout"):
        raise SystemExit(f"{a.sid} is {s.get('state')}: its result is not available yet; reflect after the evaluation finishes")
    d = {"record": "reflection"}
    for k, field in (("worked", "what_worked"), ("failed", "what_failed"), ("diagnosis", "diagnosis"), ("evidence", "evidence"),
                     ("keep", "keep"), ("decision", "decision"), ("next", "next_hypothesis"), ("limitation", "limitation"),
                     ("analysis", "analysis")):
        if getattr(a, k):
            d[field] = getattr(a, k)
    if getattr(a, "calibration", None):
        r = load_calibration_record(Path(a.calibration))
        if r is None:
            raise SystemExit(f"{a.calibration}: no record.json (make it with r2s2r-calib record DIR --hypothesis ... --config cfg.json --files ...)")
        if r["config"].get("submission_id") != a.sid:
            raise SystemExit(f"the calibration record names submission {r['config'].get('submission_id')!r}, not {a.sid}")
        problems = validate_calibration_record(r, s)
        if problems:
            raise SystemExit(f"{a.calibration} is not valid calibration evidence for {a.sid}: " + "; ".join(problems))
        limits = {"evidence": 4000, "analysis": 8000, "limitation": 4000}
        for k, text in _reflection_from_record(r, a.sid).items():
            d[k] = (d.get(k, "") + ("\n" if d.get(k) else "") + text)[:limits[k]]
    if len(d) == 1:
        raise SystemExit("nothing to record: give at least one of --diagnosis --evidence --keep --worked --failed --decision --next --limitation --analysis --calibration DIR")
    rollout = ((s.get("research") or {}).get("evidence") or {}).get("rollout", "")
    if rollout.startswith("none") and "limitation" not in d:
        print(f"note: {a.sid} has no rollout evidence ({rollout}); consider --limitation")
    print(api(a.api, ["note", a.sid], json.dumps(d).encode()).decode().strip())


def _write_once(path: Path, data: bytes, manifest: dict, rel: str):
    if path.exists():
        if sha(path.read_bytes()) != sha(data):
            print(f"CONFLICT: {rel} exists with different content; kept the existing file")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    os.chmod(path, 0o444)
    manifest[rel] = sha(data)


def cmd_archive(a):
    """Write-once local archive (EXPERIMENT.md section 1): files are never rewritten and manifest entries never change; a run
    only adds a history snapshot and the packages / feedback not archived yet. An archive whose files no longer match its
    manifest is refused (nothing added, the manifest kept) so that a tampered archive cannot re-manifest itself."""
    root = Path(a.dir)
    root.mkdir(parents=True, exist_ok=True)
    mf_path = root / "manifest.json"
    manifest = json.loads(mf_path.read_text()) if mf_path.exists() else {}
    bad = [rel for rel, h in manifest.items() if not (root / rel).exists() or sha((root / rel).read_bytes()) != h]
    if bad:
        raise SystemExit(f"refused: archive {root} does not match its manifest (MODIFIED OR MISSING: {', '.join(bad)}); nothing added, manifest.json kept as it is")
    before = dict(manifest)
    raw = api(a.api, ["history"])
    h = json.loads(raw)
    _write_once(root / "history" / f"{time.strftime('%Y%m%dT%H%M%S')}.json", raw, manifest, f"history/{time.strftime('%Y%m%dT%H%M%S')}.json")
    for s in h["submissions"]:
        sid = s["submission_id"]
        if s.get("state") not in ("done", "error", "timeout"):
            continue
        pk = root / "packages" / f"{sid}.tar"
        if not pk.exists():
            data = api(a.api, ["package", sid])
            if s.get("archive_sha256") and sha(data) != s["archive_sha256"]:
                print(f"{sid}: package hash differs from the official record; not archived")
            else:
                _write_once(pk, data, manifest, f"packages/{sid}.tar")
        fb = root / "feedback" / f"{sid}.tgz"
        if not fb.exists() and s.get("feedback_sha256"):
            _write_once(fb, api(a.api, ["fetch", sid]), manifest, f"feedback/{sid}.tgz")
    if any(manifest[k] != v for k, v in before.items()):
        raise SystemExit("internal error: a manifest entry would change; nothing written")
    if manifest != before:
        if mf_path.exists():
            mf_path.chmod(0o644)
        mf_path.write_text(json.dumps(manifest, indent=1, sort_keys=True))
        mf_path.chmod(0o444)
    print(f"archive {root}: {len(manifest)} files in the manifest ({len(manifest) - len(before)} added)")


def cmd_best(a):
    h = history(a)
    b = h.get("best_evaluated")
    groups = h.get("best_by_versions") or []
    if not b:
        reasons = sorted({str(_official(s).get("unranked_reason")) for s in h["submissions"] if _official(s) and not _official(s).get("rankable")})
        print("no ranked submission yet" + (f" (the target ranks nothing: {', '.join(reasons)})" if reasons else ""))
        print("rule:", h["best_rule"])
        return
    s = _find(h, b["submission_id"])
    o = s["official"]
    others = [{"submission_id": g.get("submission_id"), "versions": g.get("versions"), "differs_in": _versions_diff(g.get("versions"), b.get("versions")),
               "progress": _progress(g.get("official") or {}), "status": (g.get("official") or {}).get("status")} for g in groups if g.get("submission_id") != b["submission_id"]]
    print(json.dumps({"best_evaluated": b["submission_id"], "status": o.get("status"), "success": _success(o), "progress": _progress(o), "criteria": o.get("criteria"),
                      "versions": b.get("versions"), "scope": "the version group of the latest ranked submission; other groups are not comparable with it",
                      "other_version_groups": others, "official": o,
                      "policy_sha256": s["policy_sha256"], "archive_sha256": s["archive_sha256"], "feedback_sha256": s.get("feedback_sha256"),
                      "rule": h["best_rule"]}, indent=1))
    if a.download:
        data = api(a.api, ["package", b["submission_id"]])
        if sha(data) != s["archive_sha256"]:
            raise SystemExit("downloaded package does not match the official archive hash")
        out = Path(a.download) / f"best_{b['submission_id']}.tar"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        print("saved", out, "(sha256 verified)")


def cmd_gate(a):
    h = history(a)
    s = _find(h, a.sid)
    o = _official(s)
    cmp_ = s.get("comparison") or {}
    out = {"submission": a.sid, "gate": s.get("gate"), "rankable": o.get("rankable"), "unranked_reason": o.get("unranked_reason"), "comparison": cmp_, "official": o,
           "rule": h["gate_rule"], "comparison_rule": h.get("comparison_rule")}
    if o and not o.get("rankable"):
        out["note"] = f"not ranked by the target ({o.get('unranked_reason')}): no gate, never the best evaluated submission" + (
            "; listed and compared (score delta null)" if cmp_ else "; no comparison")
    elif s.get("gate") == "not_comparable":
        earlier = [x for x in h["submissions"] if x["submission_id"] in (cmp_.get("earlier_not_comparable") or [])]
        out["not_comparable_with"] = [{"submission_id": x["submission_id"], "differs_in": _versions_diff(_official(x).get("versions"), o.get("versions"))} for x in earlier]
        out["note"] = "first ranked submission of its version group: no earlier comparable submission (version fields that differ are listed per earlier submission)"
    print(json.dumps(out, indent=1))


def cmd_video(a):
    h = history(a)
    s = next((x for x in h["submissions"] if x["submission_id"] == a.sid), None)
    if s is None:
        raise SystemExit("unknown submission")
    digest = sha(build_archive(Path(a.package)))
    if digest != s["archive_sha256"]:
        raise SystemExit(f"--package is not the archive submitted as {a.sid} (its SHA-256 differs from archive_sha256 in history); "
                         "a training video must show the submitted policy")
    data = Path(a.video).read_bytes()
    if len(data) > 64 << 20:
        raise SystemExit("video larger than 64 MB")
    if a.local_run and not re.fullmatch(r"[A-Za-z0-9._:+-]{1,80}", a.local_run):
        raise SystemExit("--local-run: 1-80 characters of A-Z a-z 0-9 . _ : + -")
    args = ["training-video", a.sid, digest] + ([a.simulator] if a.simulator else []) + ([f"run={a.local_run}"] if a.local_run else [])
    out = api(a.api, args, data).decode().strip()
    print(out)
    if json.loads(out).get("sha256") != sha(data):
        raise SystemExit("the target stored a video with a different SHA-256 than the local file; check the upload")


def cmd_verify(a):
    root = Path(a.dir)
    manifest = json.loads((root / "manifest.json").read_text())
    bad = [rel for rel, h in manifest.items() if not (root / rel).exists() or sha((root / rel).read_bytes()) != h]
    print("archive intact" if not bad else "MODIFIED OR MISSING: " + ", ".join(bad))
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="research harness client (bookkeeping only)")
    ap.add_argument("--api", default=os.environ.get("R2S2R_API"))
    ap.add_argument("--calib-records", dest="calib_records", metavar="DIR",
                    help="where local r2s2r-calib records are looked up (default $R2S2R_CALIB_RECORDS, else <records>/<api>/calibration)")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("summary").add_argument("--json", action="store_true")
    rs_ = sp.add_parser("result"); rs_.add_argument("sid"); rs_.add_argument("--json", action="store_true")
    su = sp.add_parser("submit", description="submit a package (records your intent first). Calibration gate (TOOLS.md section 3, on your machine): refused "
                                             "unless the latest finished submission has a valid completed calibration record (r2s2r-calib record with a cfg.json "
                                             "naming it and its feedback hash, metrics.json among the files) or a valid self-declared exception record (feedback "
                                             "unavailable / sealed, replay infeasible: evidence files, explanation, alternative diagnosis); the first submission "
                                             "is exempt; nothing skips the gate")
    su.add_argument("package")
    for k in ("hypothesis", "change", "rationale", "parent", "kind", "repo", "local", "sim_config", "checkpoint", "records"):
        su.add_argument("--" + k.replace("_", "-"), dest=k)
    su.add_argument("--dry-run", action="store_true")
    rf = sp.add_parser("reflect")
    rf.add_argument("sid")
    for k in ("worked", "failed", "diagnosis", "evidence", "decision", "next", "analysis"):
        rf.add_argument("--" + k)
    rf.add_argument("--limitation", help="an evaluation without rollout evidence, or what the calibration could not cover")
    rf.add_argument("--calibration", metavar="DIR", help="an r2s2r-calib record directory whose cfg.json names sNN: a completed calibration is cited in evidence "
                                                         "and summarized in analysis; an exception record (feedback unavailable / sealed, replay infeasible) goes "
                                                         "to limitation with its evidence; the record is validated first")
    rf.add_argument("--keep", choices=("keep", "reject", "undecided"))
    r = sp.add_parser("record")
    r.add_argument("sid")
    for k in ("kind", "hypothesis", "change", "evidence", "decision"):
        r.add_argument("--" + k, required=True)
    for k in ("keep", "repo", "sim_config", "local", "checkpoint", "analysis", "parent"):
        r.add_argument("--" + k.replace("_", "-"), dest=k)
    sp.add_parser("archive").add_argument("dir")
    b = sp.add_parser("best")
    b.add_argument("--download")
    sp.add_parser("gate").add_argument("sid")
    sp.add_parser("verify").add_argument("dir")
    v = sp.add_parser("video")
    v.add_argument("sid")
    v.add_argument("video")
    v.add_argument("--package", required=True)
    v.add_argument("--simulator")
    v.add_argument("--local-run")
    for sub_ in (su, rf, rs_, b, sp.choices["summary"], sp.choices["gate"]):  # the same option after the command, for convenience
        sub_.add_argument("--calib-records", dest="calib_records", metavar="DIR", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.cmd == "submit" and a.kind and a.kind not in ("improvement", "diagnostic", "experimental"):
        raise SystemExit("--kind must be improvement, diagnostic or experimental")
    if a.cmd not in ("verify",) and not a.api and not (a.cmd == "submit" and a.dry_run):
        raise SystemExit("give --api (your target-environment API command, e.g. r2s2r-pen) or set R2S2R_API")
    return {"summary": cmd_summary, "result": cmd_result, "record": cmd_record, "archive": cmd_archive, "best": cmd_best, "gate": cmd_gate,
            "verify": cmd_verify, "submit": cmd_submit, "reflect": cmd_reflect, "video": cmd_video}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
