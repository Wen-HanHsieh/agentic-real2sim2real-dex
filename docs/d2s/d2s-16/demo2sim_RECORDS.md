# Research Records (Demo-to-Sim)

Your research is recorded as a sequence of records in your experiment (`TASK_CONFIG.md` section 1). Records are append-only: each is timestamped when the record store receives it, never changed afterwards, and published on the research website's "Demo-to-Sim test" page. Keep your own copies of everything you record in your workspace.

## 1. Record Types

| Record | Command | When | Content |
|---|---|---|---|
| Reconstruction | `r2s2r-d2s recon` | Step 1, and each later improved version | Summary, per-component method and status, validation numbers, limitations, comparison video, 3D viewer |
| Criteria | `r2s2r-d2s criteria` | Step 2, and each revision | Your verification criteria (`demo2sim/VERIFICATION.md`) |
| Simulation | `r2s2r-d2s sim` | Step 3, and each changed simulation | `demo2sim/SIMULATION.md` section 3 |
| Suite | `r2s2r-d2s suite register` | Each test suite and each new version | Written by the gate (`demo2sim/VERIFICATION.md` section 3) |
| Gate | `r2s2r-d2s gate` | Each gate | Written by the gate: decision, per-stage counts, funnel, where the measurements overruled your evaluation, change against the incumbent, failure montages |
| Iteration | `r2s2r-d2s iter` | Each evaluated training iteration | `demo2sim/LEARNING.md` section 4 |
| Verification | `r2s2r-d2s verify` | Each verdict | `demo2sim/VERIFICATION.md` section 2 |
| Judgment | `r2s2r-d2s judge` | After each target round (tasks with target rounds) | Your judgment of every trial of the round (`DELIVERY.md` section 6) |
| Replay | `r2s2r-d2s replay` | After each target round (tasks with target rounds) | Your simulated replay of every trial of the round and what makes it differ (`DELIVERY.md` section 8) |
| Note | `r2s2r-d2s note` | Any time | A hypothesis, decision, reflection or blocker |

`r2s2r-d2s status` shows a summary (time, suites, incumbents, the chain with its proven and mastered links, skill library, deliveries), the next step and every record. `r2s2r-d2s time` shows the time used and left. Every command prints the record ID it created.

## 2. Commands

```bash
# 1. Reconstruction: runs check_reference.py; refused unless VALID, or recorded as an exception
r2s2r-d2s recon <recon_dir> --summary "..." --components components.json --video demo/<file> \
    [--limitation "..."]... [--exception "reason"] [--viewer <build_viewer.py output dir>]

# 2. Criteria: a Markdown file
r2s2r-d2s criteria criteria.md [--reason "why this revision"]

# 3. Simulation: a JSON record (fields of SIMULATION.md section 3) plus files
r2s2r-d2s sim sim.json [--file scene.xml]... [--image initial.png] [--video replay.mp4]

# Test suite and gate (demo2sim/VERIFICATION.md section 3): the gate records them itself
r2s2r-d2s suite register suite.json [--reason "why this new version"]
r2s2r-d2s gate <suite> <candidate_dir> --hypothesis "..." --predicts <stage|success> --method "..." --observed "..." [--gpus 0,1]
r2s2r-d2s gate <suite> <candidate_dir> --final
r2s2r-d2s gate --wait <request> | gate --list

# 4. Iteration: a JSON record (fields of LEARNING.md section 4), the curves and the three views
r2s2r-d2s iter iter.json --curves curves.csv --video top=top.mp4 --video left=left.mp4 --video right=right.mp4

# 5. Verification: a JSON record (fields of VERIFICATION.md section 2) and its evidence
r2s2r-d2s verify verify.json [--video top_success=ok_top.mp4]... [--file metrics.json]...

# 6. Judgment and replay of a target round (tasks with target rounds)
r2s2r-d2s judge judge.json
r2s2r-d2s replay <round> replay.json --sim trial_0=replay_0.npz --sim trial_1=replay_1.npz ...

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
| Iteration | `sim_version`: integer, a recorded simulation version; `reward_terms`: list, one object per term (for example `{"name": ..., "formula": ..., "weight": ...}`); `domain_randomization`: list, one object per randomized quantity (`[]` = none); `policy_observations`: `"deployable"` or `"privileged"` (`demo2sim/LEARNING.md` section 1) | `demo2sim/LEARNING.md` section 2 |
| Verification | `iteration`: the record ID of a recorded iteration (for example `"r0012"`); `criteria_version`: integer, a recorded criteria version; `passed`: true or false, whether the policy meets your recorded criteria; `final_gate`: the record ID of this policy's final gate (`passed` must equal its result); for a package, `package_sha256`: the SHA-256 of its `manifest.json` | `demo2sim/VERIFICATION.md` section 2 |
| Judgment | `round`: integer, a delivered round; `criteria_version`: integer, a recorded criteria version; `trials`: list, one object per trial of the round in order, each with `trial` (integer), `success` (true or false) and `evidence` (text: which of your criteria, and what the logs and the video show); `next`: text, what you will change | `DELIVERY.md` section 6 |
| Replay | Written by `r2s2r-d2s replay`: `replay.json` gives `simulation_version` (integer, the recorded simulation you replayed in), `observation_mismatch`, `dynamics_mismatch` and `changes` (text); the command adds the residual of every trial | `DELIVERY.md` section 8 |
| Note | Written by `r2s2r-d2s note` | — |

Versions count the records of each kind in your experiment: your first simulation record is simulation version 1.

**`suite.json` (`r2s2r-d2s suite register`).** The gate checks these fields and records the suite itself.

| Field | Content |
|---|---|
| `name` | Short name, `[a-z][a-z0-9_-]*` (for example `task`, `grasp`) |
| `kind` | `task` (the whole task; one per run), `skill` or `feasibility` |
| `chain` | Task suite: its 1 to 12 links from the deployment start to the goal, in order: `[{"primitive": name, "follows": ["start" or links listed before it]}, ...]`; each link must be proven by a feasibility suite before the task suite gates (`demo2sim/VERIFICATION.md` section 3) |
| `start_check` | Task suite, and suites of a link that follows `start`: `{"hold_policy": candidate directory whose actions keep the hand at its start pose, "support": "hand" or "environment" or {object name: one of them}}` |
| `primitive` | Feasibility suite: the link of the chain it proves (its `pass_rate` is at least 0.25). Skill suite (optional): the link it learns with a deployable policy (mastered at 0.8) |
| `follows`, `handoff_fraction` | Suites that name a primitive: the links it follows, exactly as in the chain (`start` for an entry link), and the share of its starts (at least 0.5) the gate gives as handoff states |
| `primitive_spec` | Feasibility suites and skill suites that name a primitive: `motion` (`reorientation`: the object turns relative to the hand; `articulation`: a part moves relative to the rest; `other`), `support` (`none`, or `environment` if the demonstration uses the table or another support), `angle_deg` (the rotation the motion achieves), `demo_interval_s` ([t0, t1] in seconds of the demonstration video), `video_evidence` (what you see there: which fingers, where they touch, how the object moves; 20–2000 characters), `reference` (`{"states": "<file>.npz" inside the evaluator directory, "object": name, "interval_s": [t0, t1], "axis_object": [x, y, z]}`, a reference log of your reconstruction; or `{"unavailable": "why"}`, not for a reorientation), `task_condition` (the condition of `TASK.md` it serves), `deviations` (where and why the robot does it differently; `none` if it does not) |
| `criteria_version` | The recorded criteria version the suite evaluates |
| `stages` | The ordered stage names your evaluation reports (not `success`) |
| `stage_predicates` | For every stage, 1 to 8 predicates `{"measure": ..., "op": ">=" or "<=" or ">" or "<", "value": number, "objects": "each" or "any" or k, "args": {...}}` on the measurements of `d2s_measures.py` (its `OBJECT_MEASURES` and `WRIST_MEASURES` list them; `objects` defaults to `each`; `args` only for the measures that take them) |
| `pass_rate`, `pass_rate_reason` | The success rate your criteria require, and why |
| `max_hardware_violations` | Episodes with a hardware violation a pass allows (default 0) |
| `evaluator` | The directory of your evaluation program (copied when you register) |
| `environment` | Optional: the Python virtual environment it runs in (copied when you register) |
| `python` | The interpreter: inside `environment`, or an installed one under `/opt` or `/usr` |
| `command` | The command as a list, with the placeholders `{python}`, `{policy}` (the candidate directory), `{seeds}` (a JSON file `{"seeds": [...]}`, with `"handoff": {"<seed>": "<file>.npz"}` for a suite of a chain link) and `{out}` (the directory for `results.json`, `states/<seed>.npz` and optional `videos/top.mp4`, `left.mp4`, `right.mp4`) |
| `render_command` | The same placeholders: renders the given seeds into `{out}/videos/<seed>/top.mp4`, `left.mp4`, `right.mp4` (the gate's failure review) |
| `dev_seeds` | 32 to 4096 distinct integers |
| `final_episodes` | Episodes of a final gate (default: as many as `dev_seeds`) |
| `timeout_min` | Longest run of one evaluation, 1 to 180 minutes (default 60) |
| `description` | What the suite tests |
| `precondition`, `postcondition`, `starts_from` | Skill suites: where the skill starts, what completes it, where its starts come from |

**`results.json`** (written by your evaluation into `{out}`): `{"episodes": [{"seed": 1234, "stages": {"<stage>": true, ...}, "hardware_ok": true, "metrics": {"<name>": 0.12}}, ...]}`, one entry per given seed; `metrics` is optional (at most 32 numbers). **`states/<seed>.npz`**: one state log per given seed, in the format described at the top of `/usr/local/lib/r2s2r-v3/tools/d2s_measures.py` (you may import that file to check your own logs: `python d2s_measures.py episode <file.npz>`). For a goal-conditioned motion, the state log gives each episode's goal: `goal_rel_orientation`, the object's goal orientation relative to the hand. **Handoff state** (`handoff` in the seeds file): one row of a state log, every per-row key with one row; start the episode from it (`d2s_measures.py`, top of the file). **Reference log** (`primitive_spec.reference.states`): your reconstruction in the same format, with at least `t`, `wrist_position`, `wrist_orientation`, `object_names` and `object_orientation`; check it with `python d2s_measures.py reference <file.npz> <object> <t0> <t1>`.

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
- **Gates:** every gate with its decision, its per-stage counts and funnel, your hypothesis and observation, and its failure montages.
- **Replays:** for tasks with target rounds, your replay of each round and its residuals.
- **Iterations:** per iteration the three rollout views, the training curves, the reward terms and weights, the domain randomization and the evaluation against your criteria.
- **Verification:** your verdicts with their evidence, labelled as the agent's own claims.
- **Target rounds:** your judgment of each trial, labelled as the agent's own claims.
- **Notes:** your hypotheses, decisions and reflections.

Text you record is published; do not include credentials, host names or personal information.
