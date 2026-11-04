# Learning Rules (Demo-to-Sim, Stage 3)

The policy is learned with **reinforcement learning** in your training simulation. The demonstration and your reconstruction may guide learning in many ways, but the final policy must be a closed-loop policy whose actions come from a network trained by reinforcement learning.

## 1. What Counts

**Allowed:**

- **PPO only** (Schulman et al., 2017, https://arxiv.org/abs/1707.06347): every reinforcement-learning stage of your policy, including a teacher or a residual, is trained with PPO; other RL algorithms (for example SAC, TD3, model-based RL) are not allowed. Massively parallel simulation is allowed.
- Rewards built from the demonstration: tracking the reconstructed object and hand (wrist and fingertip) motion, contact-phase rewards, task-progress terms you define.
- Initial states sampled from the reconstruction, curricula, demonstration-augmented RL.
- Imitation or behavior-cloning **pre-training followed by reinforcement-learning fine-tuning**.
- Reference controllers and residual PPO: a closed-loop residual learned with PPO on top of a reference trajectory or a base controller.
- Teacher–student distillation, provided the teacher is trained with PPO.
- Domain randomization of physics, initial conditions, observation noise and delays.

**A scripted controller that fully solves the task must not be presented as a learned PPO solution.** Report how any reference or base controller you use performs on its own.

**Not allowed as the final policy:**

- Scripted or hand-designed controllers.
- Open-loop replay of the reconstructed or retargeted demonstration, with or without time scaling.
- Trajectory optimization or sampling-based planning at execution time (for example MPC, CEM, MPPI).
- Behavior cloning or imitation learning without a reinforcement-learning stage.

Such methods may be used for analysis, for building a reference, or as baselines, but they are not the reported policy. If you are unsure whether a method qualifies, record the method and your reasoning in a note before relying on it.

**The final policy must be deployable.** At each control step it may observe only:

- **Proprioception:** finger joint positions and velocities with encoder noise (`hardware/SPECS.md`), its own previous finger and wrist targets, and the wrist pose and velocity.
- **Object states:** position, orientation, linear and angular velocity of each object's state frame (`object/SPECS.md`).
- The step index and constant task settings.

It must not observe contacts or contact forces, joint torques or motor currents, physical parameters (mass, friction, inertia, damping), images, rewards, or any other simulator internal. It outputs finger position targets (optionally velocity targets) and a wrist pose target (optionally feed-forward velocities) through the controllers of `hardware/SPECS.md`. A teacher may use more information during training, but the policy you verify and report is the deployable one; state its observation and action spaces in every iteration record.

**Label every iteration** with `policy_observations`: `"deployable"` (it observes only the set above) or `"privileged"` (it observes anything more, for example a teacher). The website shows the rollouts of the two kinds separately.

## 2. What You Record for Each Iteration (`r2s2r-d2s iter`)

Record every training iteration you evaluate (a training run, or a checkpoint you compare against others).

| Item | Content |
|---|---|
| Simulation | The simulation record version it was trained in |
| Algorithm | Algorithm and its main hyperparameters, policy architecture, observation and action spaces, number of environments, seeds |
| Reward | Every reward term with its formula or description and its weight |
| Domain randomization | Every randomized quantity with its range and distribution, or "none" |
| Curriculum | Stages and switching rules, or "none" |
| Training curves | Per training step: total reward and each reward term, episode length, and your verification metrics where you compute them during training (a CSV file) |
| Compute | Wall-clock time, GPU hours |
| Evaluation | The result against your current criteria on a fixed set of evaluation episodes (number of episodes, success rate, per-criterion values) |
| Rollout videos | A representative rollout from the top, left and right views of your simulation (mp4) |
| Reflection | What changed from the previous iteration, what worked, what failed, the next hypothesis |
