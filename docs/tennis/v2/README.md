# Wuji Hand 2: Tennis Ball Toss and Catch

Learn the dexterous manipulation skill demonstrated in the human video, develop a policy in your own simulation, and improve it iteratively with feedback from the target environment.

## Resources

| Resource | Description |
|---|---|
| `TASK.md` | Task objective |
| `SUCCESS.md` | Official success criteria and task progress rubric |
| `CONTRACT.md` | Policy observations, actions, and execution rules |
| `PACKAGE.md` | Policy packaging and runtime requirements |
| `hardware/SPECS.md` | Wuji Hand 2.2 specification: mount, controller, and hardware limits (authoritative) |
| `hardware/` | Robot URDF and meshes (`hardware/wuji_hand2_right/`), machine-readable `hardware/hardware_spec.json` |
| `object/SPECS.md` | Object geometry, mass, and surface |
| `demo/` | Human demonstration video and sampled frames |
| `target/screenshot.png` | Target environment at the start of an episode (top, left, and right cameras) |
| `REMOTE_API.md` | Remote evaluation API: submission, standard feedback, standard research workflow, on-demand access, limits, access boundaries |
| `FEEDBACK.md` | Cameras, official evaluation, object tracks, hardware diagnostics, and the standard feedback files |
| `HARDWARE_CHECK.md` | Local hardware validation |
| `TOOLS.md` | Research Harness (standard research workflow), sim-to-target calibration (required after each target evaluation), and the optional hardware check |
| `tools/` | Tool implementations |
| `example_package/` | Example policy package |

## Responsibilities

**Target Environment:** A black-box environment that executes submitted policies, records camera observations and the robot's joint states and actions, and produces the official sensor-based evaluation: status, task progress, hardware compliance, and their uncertainty. It never uses your simulation, never returns its internal state, and never explains a failure: it provides task scores and observable evidence.

**Research Agent (you):** Builds and calibrates simulations, chooses learning methods, policy architectures, and training rewards, analyzes target feedback, and decides what to try next. Any method that produces a policy meeting `CONTRACT.md` and `PACKAGE.md` is acceptable: learned policies, scripted or hand-designed controllers, trajectory optimization, or combinations.

**Research Harness:** Keeps your standard research records (intent before each submission, reflection after each result) and shows the experiment history, the best evaluated policy, and comparisons kept by the target environment. It records and displays results; it does not direct your research.

You diagnose failures yourself from videos, frames, object tracks, joint logs, and your own metrics; these analyses do not replace or modify the official evaluation.

## Research Cycle

Hypothesis → Change → Local validation → Target submission → Feedback → Sim-to-target calibration and failure analysis → Repair screened in simulation → Decision → Next iteration

| | |
|---|---|
| **Standard feedback** (automatic) | After every rollout the target environment stores the evaluation evidence: three camera videos, the joint log, the official evaluation, object tracks, hardware diagnostics, calibration, and timestamps. Retrieve it with `fetch` (`FEEDBACK.md`). |
| **Standard research workflow** | Kept automatically in `history`: every submission's exact package, hashes, official results, and feedback; the best evaluated policy; comparisons with earlier comparable submissions (regression detection). Your part: before each submission, your hypothesis and planned change (`r2s2r-harness submit`, which also captures your git revision and diff); after each result, what worked and what failed, your diagnosis and its evidence, keep / reject / undecided, and your next hypothesis (`r2s2r-harness reflect`); and for every submission a video of your own training-simulation rollout of that exact package, stated as a full or partial rollout (`r2s2r-harness video` and a `training_video` record, `REMOTE_API.md` section 5), or the reason no video could be recorded. If an evaluation produced no rollout evidence, say so. |
| **On-demand access** | When you need them: earlier policy packages (`package`, `r2s2r-harness best --download`), and RGB or depth frames at selected instants (`frames`). |
| **Sim-to-target calibration** (required after each target evaluation; not before your first rollout) | Extract the target rollout and replay its action sequence in your own simulator (`r2s2r-calib`), compare the observable behavior, turn the discrepancies into testable failure hypotheses, update your simulator or state why a discrepancy cannot be modeled, screen candidate repairs in simulation before the next submission, and record the evidence, modifications, and results (`TOOLS.md` section 2). |
| **Optional analysis tools** | `r2s2r-hwcheck` and your own diagnostics, visualizations, and scripts. |
| **Your choice** | Simulator, physics parameters, calibration method, policy, controller, learning method, reward, curriculum, diagnostic methods, and what to try next. |

Your diagnosis is a hypothesis; the official evaluation is authoritative. Missing records never block a submission; `history` lists them (`REMOTE_API.md` section 5).
