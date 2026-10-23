# Wuji Hand 2: Ball Toss, Catch, and Spin

Learn the dexterous manipulation skill demonstrated in the human video, develop a policy in your own simulation, and improve it iteratively with feedback from the target environment.

## Resources

| Resource | Description |
|---|---|
| `TASK.md` | Task objective |
| `SUCCESS.md` | Official success criteria and task progress rubric |
| `CONTRACT.md` | Policy observations, actions, and execution rules |
| `PACKAGE.md` | Policy packaging and runtime requirements |
| `hardware/SPECS.md` | Robot specification, mount, controller, and hardware limits (authoritative) |
| `hardware/` | Robot URDF and meshes (`hardware/wuji_hand2_right/`), machine-readable `hardware/hardware_spec.json` |
| `object/SPECS.md` | Object geometry and mass |
| `demo/` | Human demonstration video and sampled frames |
| `target/screenshot.png` | Target environment at the start of an episode (top, left, and right cameras) |
| `REMOTE_API.md` | Remote evaluation API: submission, standard feedback, optional queries, limits |
| `FEEDBACK.md` | Cameras, official evaluation, object tracks, masks, and standard feedback files |
| `HARDWARE_CHECK.md` | Local hardware validation |
| `TOOLS.md` | Optional research tools and the Research Harness |
| `tools/` | Tool implementations |
| `example_package/` | Example policy package |

## Responsibilities

**Target Environment:** A black-box environment that executes submitted policies, records camera observations and the robot's joint states and actions, and produces the official sensor-based evaluation: status, task progress, hardware compliance, and their uncertainty. It never uses your simulation and never returns its internal state.

**Research Agent (you):** Builds simulations, chooses learning methods, policy architectures, and training rewards, analyzes target feedback, and decides what to try next.

**Research Harness:** Keeps experiment records, preserves the best evaluated policy, compares submissions, and provides optional diagnostic tools. It records and displays results; it does not direct your research.

You may analyze videos, object tracks, masks, and your own metrics to diagnose failures, but they do not replace or modify the official evaluation.
