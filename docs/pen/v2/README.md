# Wuji Hand 2: Pen Spinning

Learn the dexterous manipulation skill demonstrated in the human video, train a policy in your own simulation, and iteratively improve it through SuperDex evaluation feedback.

## Resources

| Path | Description |
|---|---|
| `TASK.md` | Task objective |
| `SUCCESS.md` | Success criteria and task progress rubric |
| `CONTRACT.md` | Policy observations, actions, and timing |
| `hardware/SPECS.md` | Robot specifications, initial pose, and mount |
| `hardware/wuji_hand2_right/` | Robot URDF and meshes |
| `object/SPECS.md` | Object geometry and mass |
| `demo/` | Human demonstration video and sampled frames |
| `target/screenshot.png` | Target environment at episode start |
| `PACKAGE.md` | Policy packaging and deployment runtime |
| `REMOTE_API.md` | Submission and feedback API (protocol v2: three cameras, sensor report, frame queries, records) |
| `FEEDBACK.md` | Cameras, calibration, sensor-based verifier report, experiment records |
| `HARDWARE_CHECK.md` | Hardware validation tool for your own trajectories (`tools/hwcheck/`) |
| `example_package/` | Reference policy package |

## Roles

- **SuperDex (real side)** executes your policy, records cameras, joint states and actions, and determines the official
  task result: success / failure / unknown, reward and progress, events, hardware compliance and their uncertainty
  (`FEEDBACK.md`). It does not use your simulation.
- **You (sim side)** build and improve your own simulation, choose your methods, generate local rollouts, analyse the
  feedback and the differences between simulation and SuperDex, and decide what to try next.
- **The research harness** keeps your experiment records and best policy and offers optional analysis tools
  (`TOOLS.md`). It measures and records; it does not decide your research direction.

You may analyse the videos and masks yourself, build your own metrics and question measurements that are uncertain,
but your analyses do not replace or overwrite the official SuperDex results.
