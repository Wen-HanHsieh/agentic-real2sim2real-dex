# Training Simulation (Demo-to-Sim, Stage 2)

Build the simulation in which you train and verify your policy. Build it only after your reconstruction is recorded (`demo2sim/RECORDS.md`); the reconstruction is the reference of the skill.

## 1. What the Simulation Models

| Component | Source | Notes |
|---|---|---|
| Robot hand | `hardware/SPECS.md`, your hand file (`TASK_CONFIG.md` section 1), `hardware/wuji_hand2_<side>/` | The variant of your task; joint order, limits and actuator parameters from the hand file |
| Wrist | `hardware/SPECS.md` sections 3–4 | A free-floating 6-DoF wrist: position and orientation are **free** (no workspace box, no pose constraint) |
| Fingers | `hardware/SPECS.md` sections 5–7 | Joint PD controller, effort and speed limits, encoder noise, and the finger hardware rules |
| Objects | `object/SPECS.md` | Geometry, mass, inertia and, where there is one, the mechanism |
| Scene | `TASK_CONFIG.md` section 2 | Floor or table, world frame |
| Reference | your recorded reconstruction | The demonstrated hand and object motion, contact phases and the reconstruction's `scene.xml` |

**Wrist.** The wrist is free: your policy may move it to any position and orientation. Model how the policy drives it; the wrist controller of `hardware/SPECS.md` section 4 is the hand's reference actuator model (impedance gains, force and torque limits, target speed limits). The manipulation should resemble the demonstration, especially the wrist pose (`TASK.md`), so derive the reference wrist motion from your reconstruction (the demonstrator's wrist retargeted to the robot's wrist frame).

**Fingers.** The finger hardware is not free: keep the joint position, velocity and effort limits and the controller of `hardware/SPECS.md` sections 5–7 in your simulation, and do not train a policy that relies on violating them.

**Initial conditions.** No initial wrist pose, finger configuration or object placement is prescribed. Choose them from your reconstruction (for example the demonstrator's hand and object at the start of the skill, retargeted to the robot) and state your choice and its reason in the simulation record. You may randomize them during training.

**Episode.** Choose the episode length, control rate and termination conditions; state them in the record.

## 2. Validating the Simulation

Before training, check that the simulation is a faithful setting for the skill, and record what you checked, for example:

- the hand's joint limits, masses and controller response against `hardware/SPECS.md` and the hand file;
- the objects' geometry, mass and contact behavior against `object/SPECS.md`;
- a kinematic replay of the reconstructed demonstration (the demonstrator's motion retargeted to the robot, the objects on their reconstructed trajectories) in the simulation, rendered next to the demonstration video.

## 3. What You Record (`r2s2r-d2s sim`)

| Item | Content |
|---|---|
| Simulator | Name and version, physics settings (time step, solver, contact model and parameters) |
| Scene | The scene files you train in (sha256 of each), the robot and object models used |
| Reference | The reconstruction version it uses and how: retargeting method, what is tracked or used in the reward |
| Wrist and fingers | How the wrist is driven; the finger controller and limits as implemented |
| Initial conditions | The initial wrist pose, finger configuration and object placement, and why |
| Episode | Length, control rate, termination conditions |
| Validation | What you checked (section 2) and the results |
| Media | A rendered image of the initial scene and the replay video of section 2 |

A changed simulation is recorded again as a new version with what changed and why.
