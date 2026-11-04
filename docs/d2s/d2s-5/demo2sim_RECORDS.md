# Research Records (Demo-to-Sim)

Your research is recorded as a sequence of records in your experiment (`TASK_CONFIG.md` section 1). Records are append-only: each is timestamped when the record store receives it, never changed afterwards, and published on the research website's "Demo-to-Sim test" page. Keep your own copies of everything you record in your workspace.

## 1. Record Types

| Record | Command | When | Content |
|---|---|---|---|
| Reconstruction | `r2s2r-d2s recon` | Step 1, and each later improved version | Summary, per-component method and status, validation numbers, limitations, comparison video, 3D viewer |
| Criteria | `r2s2r-d2s criteria` | Step 2, and each revision | Your verification criteria (`demo2sim/VERIFICATION.md`) |
| Simulation | `r2s2r-d2s sim` | Step 3, and each changed simulation | `demo2sim/SIMULATION.md` section 3 |
| Iteration | `r2s2r-d2s iter` | Each evaluated training iteration | `demo2sim/LEARNING.md` section 3 |
| Verification | `r2s2r-d2s verify` | Each verdict | `demo2sim/VERIFICATION.md` section 2 |
| Note | `r2s2r-d2s note` | Any time | A hypothesis, decision, reflection or blocker |

`r2s2r-d2s status` lists your records with their versions and times. Every command prints the record ID it created.

## 2. Commands

```bash
# 1. Reconstruction: runs check_reference.py; refused unless VALID, or recorded as an exception
r2s2r-d2s recon <recon_dir> --summary "..." --components components.json --video demo/<file> \
    [--limitation "..."]... [--exception "reason"] [--viewer <build_viewer.py output dir>]

# 2. Criteria: a Markdown file
r2s2r-d2s criteria criteria.md [--reason "why this revision"]

# 3. Simulation: a JSON record (fields of SIMULATION.md section 3) plus files
r2s2r-d2s sim sim.json [--file scene.xml]... [--image initial.png] [--video replay.mp4]

# 4. Iteration: a JSON record (fields of LEARNING.md section 3), the curves and the three views
r2s2r-d2s iter iter.json --curves curves.csv --video top=top.mp4 --video left=left.mp4 --video right=right.mp4

# 5. Verification: a JSON record (fields of VERIFICATION.md section 2) and its evidence
r2s2r-d2s verify verify.json [--video top_success=ok_top.mp4]... [--file metrics.json]...

# Notes
r2s2r-d2s note --kind hypothesis|decision|reflection|blocker "text"
```

**Reconstruction record contents.** `components.json` lists one entry per reference component: `[{"name": ..., "status": ..., "method": ..., "note": ...}]`. `recon` sends the validation numbers of `check_reference.py` and `validate_reconstruction.py`, one entry per reference component (camera, objects' 6D motion, hand motion, contact phases) with its method and status (`ok`, `partial`, `failed`, `pending`, `from_specification`, `unobservable`), your limitations, the comparison video of the reconstruction overlaid on the demonstration (`render_compare.py`) and the interactive 3D hand–object viewer (`build_viewer.py`). An exception keeps every component's actual status and is shown as an exception; a directory without reconstruction outputs is refused.

**Required JSON fields.** The record store refuses a record without these fields; add the content of the referenced section as further fields of the same JSON object.

| Record | Required fields | Further content |
|---|---|---|
| Reconstruction | Written by `r2s2r-d2s recon` from its options | — |
| Criteria | The Markdown file; from version 2 on, `--reason` | — |
| Simulation | `reconstruction_version`: integer, a recorded reconstruction version (1, 2, …) | `demo2sim/SIMULATION.md` section 3 |
| Iteration | `sim_version`: integer, a recorded simulation version; `reward_terms`: list, one object per term (for example `{"name": ..., "formula": ..., "weight": ...}`); `domain_randomization`: list, one object per randomized quantity (`[]` = none); `policy_observations`: `"deployable"` or `"privileged"` (`demo2sim/LEARNING.md` section 1) | `demo2sim/LEARNING.md` section 3 |
| Verification | `iteration`: the record ID of a recorded iteration (for example `"r0012"`); `criteria_version`: integer, a recorded criteria version | `demo2sim/VERIFICATION.md` section 2 |
| Note | Written by `r2s2r-d2s note` | — |

Versions count the records of each kind in your experiment: your first simulation record is simulation version 1.

## 3. Limits

| Item | Limit |
|---|---|
| JSON record | 64 KB |
| Markdown file | 64 KB |
| Image | PNG or JPEG, 2 MB, 1920 × 1080 |
| Video | MP4 (H.264) or WebM, 32 MB, 120 s |
| Curves | CSV, 8 MB |
| 3D viewer | 32 MB in total |
| Other files | 8 MB each |
| Per experiment | 4 GB |

## 4. What the Website Shows

The "Demo-to-Sim test" page shows, per experiment:

- **Timeline:** every record in the order received. A simulation, iteration or verification record made before the first reconstruction record is marked out of order.
- **Reconstruction:** the demonstration next to your reconstruction overlay, the 3D hand–object viewer, the component statuses, the validation numbers and your limitations.
- **Criteria:** your current criteria and their earlier versions.
- **Iterations:** per iteration the three rollout views, the training curves, the reward terms and weights, the domain randomization and the evaluation against your criteria.
- **Verification:** your verdicts with their evidence, labelled as the agent's own claims.
- **Notes:** your hypotheses, decisions and reflections.

Text you record is published; do not include credentials, host names or personal information.
