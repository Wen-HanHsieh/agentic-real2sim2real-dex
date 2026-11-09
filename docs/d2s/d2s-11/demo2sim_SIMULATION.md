# Training Simulation (Demo-to-Sim, Stage 2)

Build the simulation in which you train and verify your policy. Build it only after your reconstruction is recorded (`demo2sim/RECORDS.md`); the reconstruction is the reference of the skill.

## 1. What the Simulation Models

| Component | Source | Notes |
|---|---|---|
| Robot hand | `hardware/SPECS.md`, your hand file (`TASK_CONFIG.md` section 1), `hardware/wuji_hand2_<side>/` | The variant of your task; joint order, limits and actuator parameters from the hand file |
| Wrist | `hardware/SPECS.md` sections 3–4 | A free-floating 6-DoF wrist, within the wrist workspace of `TASK_CONFIG.md` section 5 where your task sets one |
| Fingers | `hardware/SPECS.md` sections 5–7 | Joint PD controller, effort and speed limits, encoder noise, and the finger hardware rules |
| Objects | your recorded reconstruction and the object information you identify and look up | Geometry, mass, inertia and, where there is one, the mechanism |
| Scene | `TASK_CONFIG.md` section 2 | Floor or table, world frame |
| Reference | your recorded reconstruction | The demonstrated hand and object motion, contact phases and the reconstruction's `scene.xml` |

**Wrist.** The wrist is free-floating: your policy may move it to any position and orientation within that workspace. Model how the policy drives it; the wrist controller of `hardware/SPECS.md` section 4 is the hand's reference actuator model (impedance gains, force and torque limits, target speed limits).

**Fingers.** The finger hardware is not free: keep the joint position, velocity and effort limits and the controller of `hardware/SPECS.md` sections 5–7 in your simulation, and do not train a policy that relies on violating them.

**Objects.** Where your reconstruction does not resolve part of an object, your simulation must still model it, from the information you identify and look up; record its source.

**Initial conditions.** The hand's start pose (wrist pose and finger positions) is yours to choose. The objects start as `TASK.md` (Deployment) describes. Cover those starts in training and verification as you see fit, and state your choices and their reasons in the simulation record. You may randomize them during training.

**Episode.** Choose the episode length, control rate and termination conditions, unless `TASK_CONFIG.md` sets them; state them in the record.

## 2. Validating the Simulation

Before training, check that the simulation is a faithful setting for the skill, and record what you checked, for example:

- the hand's joint limits, masses and controller response against `hardware/SPECS.md` and the hand file;
- the objects' geometry, mass and contact behavior against the object information you identify and look up;
- a kinematic replay of the reconstructed demonstration (the demonstrator's motion retargeted to the robot, the objects on their reconstructed trajectories) in the simulation, rendered next to the demonstration video;
- the robot hand and the objects do not pass into each other, in the retargeted replay of the demonstration and in your policy's rollouts; report the deepest penetration.

## 3. What You Record (`r2s2r-d2s sim`)

| Item | Content |
|---|---|
| Simulator | Name and version, physics settings (time step, solver, contact model and parameters) |
| Scene | The scene files you train in (sha256 of each), the robot and object models used |
| Reference | The reconstruction version it uses and how: retargeting method, what is tracked or used in the reward |
| Wrist and fingers | How the wrist is driven; the finger controller and limits as implemented |
| Initial conditions | The hand's start pose, how the object starts are generated in training, and why |
| Episode | Length, control rate, termination conditions |
| Validation | What you checked (section 2) and the results |
| Media | A rendered image of the initial scene and the replay video of section 2 |

A changed simulation is recorded again as a new version with what changed and why.
