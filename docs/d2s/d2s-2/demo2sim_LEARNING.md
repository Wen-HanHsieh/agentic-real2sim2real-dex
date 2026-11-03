# Learning Rules (Demo-to-Sim, Stage 3)

The policy is learned with **reinforcement learning** in your training simulation. The demonstration and your reconstruction may guide learning in many ways, but the final policy must be a closed-loop policy whose actions come from a network trained by reinforcement learning.

## 1. What Counts

**Allowed:**

- Any reinforcement-learning algorithm: on-policy (for example PPO), off-policy (for example SAC), model-based RL, massively parallel simulation.
- Rewards built from the demonstration: tracking the reconstructed object and hand (wrist and fingertip) motion, contact-phase rewards, task-progress terms you define.
- Initial states sampled from the reconstruction, curricula, demonstration-augmented RL.
- Imitation or behavior-cloning **pre-training followed by reinforcement-learning fine-tuning**.
- Residual reinforcement learning on top of a reference trajectory or a base controller, provided the residual is learned by RL and the policy is closed-loop.
- Teacher–student distillation, provided the teacher is trained by RL.
- Domain randomization of physics, initial conditions, observation noise and delays.

**Not allowed as the final policy:**

- Scripted or hand-designed controllers.
- Open-loop replay of the reconstructed or retargeted demonstration, with or without time scaling.
- Trajectory optimization or sampling-based planning at execution time (for example MPC, CEM, MPPI).
- Behavior cloning or imitation learning without a reinforcement-learning stage.

Such methods may be used for analysis, for building a reference, or as baselines, but they are not the reported policy. If you are unsure whether a method qualifies, record the method and your reasoning in a note before relying on it.

## 2. Resembling the Demonstration

The manipulation should resemble the demonstration, especially the wrist pose (`TASK.md`). Your reward, your verification criteria (`demo2sim/VERIFICATION.md`) or both should measure how closely the policy's wrist motion follows the demonstrator's wrist motion, retargeted to the robot, and you report that measure for every iteration.

## 3. What You Record for Each Iteration (`r2s2r-d2s iter`)

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
| Evaluation | The result against your current criteria on a fixed set of evaluation episodes (number of episodes, success rate, per-criterion values), including the wrist-pose similarity of section 2 |
| Rollout videos | A representative rollout from the top, left and right views of your simulation (mp4) |
| Reflection | What changed from the previous iteration, what worked, what failed, the next hypothesis |
