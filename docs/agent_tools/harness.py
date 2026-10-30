#!/usr/bin/env python3
"""Research harness client: experiment records, best-policy preservation, regression gate (bookkeeping only).

Official results (status, success, progress, hardware, ...) come from the target environment's ground-truth evaluation and are
only displayed here; nothing in this tool computes, changes or replaces them. Your research decisions (what to try next, what
to keep) stay yours. While a task's success criteria are undefined, the target scores and ranks nothing; this tool then shows
"criteria not defined" where a score would be.

Standard research cycle: hypothesis -> change -> local validation -> `submit` (records your intent, then submits) ->
feedback -> failure analysis -> `reflect` (diagnosis, evidence, keep / reject / undecided, next hypothesis) -> next iteration.
The target binds each intent to the submission with the same archive SHA-256 and keeps best policy and comparisons in
`history` automatically; this tool captures objective facts (git revision, diff, archive hash) and keeps local copies.

Usage (API = your target-environment API command, e.g. r2s2r-pen; or set R2S2R_API):
  r2s2r-harness --api r2s2r-pen submit DIR|ARCHIVE [--hypothesis ...] [--change ...] [--rationale ...] [--parent sMM]
                [--kind improvement|diagnostic|experimental] [--repo DIR] [--local result.json] [--sim-config cfg.json]
                [--checkpoint REF] [--records DIR] [--dry-run]
  r2s2r-harness --api r2s2r-pen reflect sNN [--worked ...] [--failed ...] [--diagnosis ...] [--evidence ...]
                [--keep keep|reject|undecided] [--decision ...] [--next ...] [--limitation ...] [--analysis ...]
  r2s2r-harness --api r2s2r-pen summary
  r2s2r-harness --api r2s2r-pen result sNN        the official result of one submission (status, criteria, success, progress, stages, validity)
  r2s2r-harness --api r2s2r-pen record sNN --kind improvement|diagnostic|experimental --hypothesis ... --change ...
                --evidence ... --decision ... [--keep keep|reject|undecided] [--repo DIR] [--sim-config cfg.json]
                [--checkpoint REF] [--analysis TEXT] [--local result.json] [--parent sMM]
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

VERSION = "r2s2r-harness 3"
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


def _progress(o: dict) -> str:
    """The official progress of a submission as text: a number, 'criteria not defined', or '-' while not evaluated."""
    if not o:
        return "-"
    vs = o.get("verifier_status") or o.get("status")
    if vs == "criteria_undefined":
        return UNDEFINED
    if vs == "not_evaluable":
        return "n/a"
    s = o.get("score")
    return "-" if s is None else f"{s:.3f}"


def _criteria(o: dict) -> str:
    c = (o or {}).get("criteria") or {}
    if not c:
        return "-"
    return f"{c.get('id') or 'none'}/{c.get('status') or '-'}"


def cmd_summary(a):
    h = history(a)
    print(f"{'sub':5s} {'role':12s} {'keep':9s} {'state':7s} {'status':18s} {'progress':20s} {'criteria':22s} {'hardware':9s} {'gate':14s} "
          f"{'vs previous':20s} {'intent':6s} reflection")
    for s in h["submissions"]:
        o = s.get("official") or {}
        rs = s.get("research") or {}
        cmp_ = s.get("comparison") or {}
        refl = "yes" if rs.get("current_reflection") else ("-" if s.get("state") not in ("done", "error", "timeout") else "MISSING")
        print(f"{s['submission_id']:5s} {s['role']:12s} {str(s.get('keep') or '-'):9s} {str(s.get('state')):7s} {str(o.get('status', '-')):18s} "
              f"{_progress(o):20s} {_criteria(o):22s} {str(o.get('hardware', '-')):9s} "
              f"{str(s.get('gate', '-')):14s} {_outcome(cmp_.get('vs_previous')):20s} {('yes' if rs.get('intent') else 'MISSING'):6s} {refl}")
    be = h.get("best_evaluated") or {}
    if be.get("official"):
        bo = be["official"]
        print("best evaluated:", be.get("submission_id"), f"(status {bo.get('status')}, progress {_progress(bo)}, criteria {_criteria(bo)}, "
                                                           f"target model {(be.get('versions') or {}).get('target_model')})",
              "| latest candidate:", h.get("latest_candidate"))
    else:
        undefined = any(((s.get("official") or {}).get("verifier_status") == "criteria_undefined") for s in h["submissions"])
        print("best evaluated: none" + (f" ({UNDEFINED}: nothing is ranked)" if undefined else ""), "| latest candidate:", h.get("latest_candidate"))
    print("rule:", h["best_rule"])
    rsum = h.get("research_summary")
    if rsum:
        print(f"research records: {rsum['with_intent']}/{rsum['submissions']} with intent, {rsum['with_reflection']}/{rsum['submissions']} with reflection")
        for x in rsum["incomplete"]:
            print(f"  INCOMPLETE {x['submission_id']}: " + "; ".join(x["needs"]))
        for x in rsum.get("unbound_intents", []):
            print(f"  intent {x['intent_id']} ({x['recorded']}) not bound: {x['reason']}")


def cmd_result(a):
    """The official result of one submission, as recorded in history (the full report is in the fetched feedback)."""
    h = history(a)
    s = next((x for x in h["submissions"] if x["submission_id"] == a.sid), None)
    if s is None:
        raise SystemExit("unknown submission")
    o = s.get("official")
    if not o:
        print(f"{a.sid}: state {s.get('state')}, no official result yet")
        return
    vs = o.get("verifier_status") or o.get("status")
    print(f"{a.sid}: status {o.get('status')} (verifier status {vs}); criteria {_criteria(o)}")
    if vs == "criteria_undefined":
        print(f"success: {UNDEFINED}; progress: {UNDEFINED} (nothing is scored or ranked until the task's criteria are published)")
    elif vs == "evaluated" or o.get("score") is not None:
        print(f"success: {o.get('status') == 'success'}; progress: {_progress(o)} ({o.get('confidence') or 'exact'})")
        for name, sc in (o.get("stages") or {}).items():
            print(f"  stage {name}: {sc}")
        ms = o.get("milestones") or []
        if ms:
            print("  milestones reached: " + (", ".join(f"{m['stage']}: {m['label']}" for m in ms if m.get("reached")) or "none"))
    else:
        print(f"success: n/a; progress: n/a (verifier status {vs})")
    print(f"hardware: {o.get('hardware')}; runtime: {o.get('runtime')}; rankable: {o.get('rankable')}")
    print("versions:", json.dumps(o.get("versions")))
    print("evidence:", ((s.get("research") or {}).get("evidence") or {}).get("rollout"), "| feedback:", s.get("feedback_sha256"))


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
    base = Path(a.records or os.environ.get("R2S2R_RECORDS") or Path.home() / "r2s2r_records")
    return base / (a.api.split()[-1] if a.api else "dry-run")


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


def cmd_submit(a):
    cv = _manifest_contract(Path(a.package))
    if cv is not None and cv != "v2":
        print(f'WARNING: manifest.json declares contract_version {cv!r}; this experiment accepts "v2" only (PACKAGE.md) and will refuse the package')
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
    print(json.dumps({"submission": receipt, "intent": ir, "missing_agent_fields": missing,
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
    if len(d) == 1:
        raise SystemExit("nothing to record: give at least one of --diagnosis --evidence --keep --worked --failed --decision --next --limitation --analysis")
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
    root = Path(a.dir)
    root.mkdir(parents=True, exist_ok=True)
    mf_path = root / "manifest.json"
    manifest = json.loads(mf_path.read_text()) if mf_path.exists() else {}
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
    mf_path.chmod(0o644) if mf_path.exists() else None
    mf_path.write_text(json.dumps(manifest, indent=1, sort_keys=True))
    print(f"archive {root}: {len(manifest)} files in the manifest")


def cmd_best(a):
    h = history(a)
    b = h.get("best_evaluated")
    if not b:
        undefined = any(((s.get("official") or {}).get("verifier_status") == "criteria_undefined") for s in h["submissions"])
        print("no evaluated submission yet" + (f" ({UNDEFINED}: the target ranks nothing)" if undefined else ""))
        print("rule:", h["best_rule"])
        return
    s = next(x for x in h["submissions"] if x["submission_id"] == b["submission_id"])
    o = s["official"]
    print(json.dumps({"best_evaluated": b["submission_id"], "status": o.get("status"), "progress": _progress(o), "criteria": o.get("criteria"),
                      "versions": b.get("versions"), "official": o,
                      "policy_sha256": s["policy_sha256"], "archive_sha256": s["archive_sha256"], "feedback_sha256": s.get("feedback_sha256"),
                      "best_by_versions": [{"versions": x["versions"], "submission_id": x["submission_id"]} for x in h.get("best_by_versions", [])],
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
    s = next((x for x in h["submissions"] if x["submission_id"] == a.sid), None)
    if s is None:
        raise SystemExit("unknown submission")
    o = s.get("official") or {}
    out = {"submission": a.sid, "gate": s.get("gate"), "comparison": s.get("comparison"), "official": o,
           "rule": h["gate_rule"], "comparison_rule": h.get("comparison_rule")}
    if o.get("verifier_status") == "criteria_undefined":
        out["note"] = f"{UNDEFINED}: the target computes no gate and no comparison for this task until criteria are published"
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
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("summary")
    sp.add_parser("result").add_argument("sid")
    su = sp.add_parser("submit")
    su.add_argument("package")
    for k in ("hypothesis", "change", "rationale", "parent", "kind", "repo", "local", "sim_config", "checkpoint", "records"):
        su.add_argument("--" + k.replace("_", "-"), dest=k)
    su.add_argument("--dry-run", action="store_true")
    rf = sp.add_parser("reflect")
    rf.add_argument("sid")
    for k in ("worked", "failed", "diagnosis", "evidence", "decision", "next", "limitation", "analysis"):
        rf.add_argument("--" + k)
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
    a = ap.parse_args(argv)
    if a.cmd == "submit" and a.kind and a.kind not in ("improvement", "diagnostic", "experimental"):
        raise SystemExit("--kind must be improvement, diagnostic or experimental")
    if a.cmd not in ("verify",) and not a.api and not (a.cmd == "submit" and a.dry_run):
        raise SystemExit("give --api (your target-environment API command, e.g. r2s2r-pen) or set R2S2R_API")
    return {"summary": cmd_summary, "result": cmd_result, "record": cmd_record, "archive": cmd_archive, "best": cmd_best, "gate": cmd_gate,
            "verify": cmd_verify, "submit": cmd_submit, "reflect": cmd_reflect, "video": cmd_video}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
