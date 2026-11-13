# Learning Rules (Demo-to-Sim, Stage 3)

The policy is learned with **reinforcement learning** in your training simulation. The demonstration and your reconstruction may guide learning in many ways, but the final policy must be a closed-loop policy whose actions come from a network trained by reinforcement learning.

## 1. What Counts

**Algorithm**
- **PPO only** (Schulman et al., 2017, https://arxiv.org/abs/1707.06347): every reinforcement-learning stage of your policy, including a teacher or a residual, is trained with PPO.
- Other RL algorithms (for example SAC, TD3, model-based RL) are not allowed.
- Massively parallel simulation is allowed.

**Not allowed as the final policy**
- Scripted or hand-designed controllers.
- Open-loop replay of the reconstructed or retargeted demonstration, with or without time scaling.
- Trajectory optimization or sampling-based planning at execution time (for example MPC, CEM, MPPI).
- Behavior cloning or imitation learning without a reinforcement-learning stage.

**Allowed**
- The methods above for analysis, for building a reference, or as baselines, but not as the reported policy.
- A reference that does not stay kinematic: first optimize it in your simulation into one the hand can execute and that moves the objects along their reconstructed trajectories.
- **Skills learned separately**, for example one PPO policy per subgoal of your decomposition, composed into one policy (section 2). Report each skill's own performance (its skill suite) as well as the composed policy's.
- **A discrete decision layer** inside the final policy: a lookup table, rule or search over a finite set of high-level steps (for example which object to handle next, or which part to move and in which direction), computed only from the allowed observations.
  - Every motion command still comes from the PPO-trained network.
  - The decision layer may not simulate physics, optimize trajectories or sample rollouts at execution time.
  - Record it with your iteration.

**Honesty rules**
- A scripted controller that fully solves the task must not be presented as a learned PPO solution.
- Report how any reference or base controller you use performs on its own.
- If you are unsure whether a method qualifies, record the method and your reasoning in a note before relying on it.

**The final policy must be deployable.** At each control step it may observe only:
- **Proprioception:** finger joint positions and velocities with encoder noise (`hardware/SPECS.md`), its own previous finger and wrist targets, and the wrist pose and velocity.
- **Object states:** position, orientation, linear and angular velocity of each object's state frame (the one you define and record with your reconstruction).
  - **Parts:** for an object with parts that move relative to each other, also the state of each part: its pose and velocity relative to the object's state frame, or its joint position and velocity (the parts and their frames you define and record with your reconstruction).
  - Where your task has target rounds, the target reports objects and their parts in its own frames (`DELIVERY.md` section 2.2).
- The step index and constant task settings.
- **History:** any of the above from earlier control steps of the same episode (for example a stack of recent steps, or the state of a recurrent network).

**It must not observe**
- Contacts or contact forces.
- Joint torques or motor currents.
- Physical parameters (mass, friction, inertia, damping).
- Images, rewards, or any other simulator internal.

**Actions**
- Finger position targets (optionally velocity targets) and a wrist pose target (optionally feed-forward velocities), through the controllers of `hardware/SPECS.md`.

**Teacher and labels**
- A teacher may use more information during training, but the policy you verify and report is the deployable one.
- State the policy's observation and action spaces in every iteration record.
- **Label every iteration** with `policy_observations`: `"deployable"` (it observes only the set above) or `"privileged"` (it observes anything more, for example a teacher).
- Deployable and privileged rollouts are reported separately.

## 2. Building the Policy from Skills

What has worked for long, contact-rich tasks: learn each skill on its own starts until it is reliable, then compose. A whole task trained at once tends to fail a little at every stage.

**Prove each primitive first.** Reinforcement learning rarely discovers a contact-rich motion it has never seen succeed: a policy that keeps failing at one stage usually settles on the safe part of the task (holding on) instead. So before you train the whole task:
- **Chain the primitives** in your task suite (`demo2sim/VERIFICATION.md` section 3): every link from the deployment start to the goal. That is the entry from the start (for example a capture, or a settle into a grip), each contact-rich motion, and a transition wherever one link ends in a state the next does not start from.
- **A skill that works only from starts nothing in the chain produces does not help the task.** Check where each link actually ends and whether the next one works from there; the gate tests every link from the end states of the links before it.
- **Design each one from three sources together:** the demonstration video (how the fingers move, where they touch, what the reconstruction cannot see), your reconstruction (how far and about which axis the object turns relative to the hand, how fast, in which interval) and `TASK.md` (what must hold when the motion is done). Where they disagree, or where the robot hand cannot do what the human hand does, the task decides; write the deviation into the `primitive_spec`.
- **Build any controller that performs each one** in your simulation, within the hardware limits of `hardware/SPECS.md`: scripted, from trajectory optimization or search, from your reconstruction, using privileged state. It need not be deployable.
- **Gate it in a feasibility suite** for that link. When it meets the suite's pass rate from the handoff states, the link is proven; until every link of the chain is proven, the task suite does not gate. Prove the links in chain order: a link's handoff states exist only once the links before it have an incumbent.
- **Master it with a deployable policy.** Train from the proven controller: a teacher with privileged state, then a deployable student (`/usr/local/lib/r2s2r-v3/tools/d2s_teacher.py`: PPO teacher, optional residual over your controller or behavior-cloning from it, DAgger student, numpy export), or residual PPO over the controller. Widen the starts and goals step by step (for example with support, then without; small angles, then the full angle; narrow starts, then the deployment's). Gate the policy in a skill suite for the link until its incumbent reaches 0.8 from the handoff states: the link is **mastered**. The controller itself is never the reported policy (section 1), and you report how it performs on its own.
- **Primitives first.** Spend the first 60% of your budget on the links of the chain: until then, the task suite gates only when every link is mastered.
- **If you cannot prove a primitive**, find out why: forces, joint limits, contact geometry, the simulation of the object. Record the evidence in a note (`--kind blocker`) instead of continuing to train around it.
- `r2s2r-d2s status` shows which primitives are proven and mastered, and it points out a stage that stays (almost) never reached for six gates in a row: such a stage needs a proven motion and a teacher, not another reward setting.

**Training at scale**
- **A GPU simulation is worth it, once it matches your evaluator.** Contact-rich skills usually need tens to hundreds of millions of simulation steps. On one L40S, MuJoCo Warp runs the hand with one object at about 20,000–50,000 policy steps per second (4,096 worlds, 50 Hz policy, 1 kHz physics); one CPU core runs about 200.
- **One model on both sides.** Build your scene with `d2s_warp_scene.py` (`HandScene`) or load your own, and give the same compiled model to your evaluator and to `mujoco_warp.put_model`. Change no option or parameter on one side only.
  - Run the hand's controllers the same way on both sides (`CpuHand` / `WarpHandEnv`). If your evaluator has its own loop, check it against `CpuHand` with the same commands.
  - A force you compute yourself (a spring, a mechanism) must be computed and applied the same way on both sides. Prefer MuJoCo's own joint springs, damping and friction loss.
- **Check parity before you rely on GPU training** (`/usr/local/lib/r2s2r-v3/tools/d2s_parity.py`, with your own Python):
  - `static`: the models and options are the same. Save the exact model you pass to `put_model` (`mujoco.mj_saveModel`) and compare it with your evaluator's; `compare_warp_opt` catches changes made after `put_model`.
  - `states`: CPU and GPU agree contact by contact on states from your own rollouts, and no contact or constraint buffer overflows. `python d2s_parity.py snippet` prints the code that records the states and the per-seed results.
  - `outcome`: the same policy, scored by your evaluator's judge on at least 128 seeds under each simulation, gives the same success, hardware-violation and drop rates within its tolerance. This is the check that counts.
  - Matching trajectories is the wrong test: MuJoCo Warp is not exactly repeatable even against itself.
  - Compare the per-seed agreement with that of two CPU runs, one from float32-rounded starts: closed-loop contact rollouts never agree seed by seed, even on the CPU.
  - For an articulated object, include its internal state (how its parts moved) in the judge you check parity with: whole-object outcomes can agree while part-part contacts do not.
  - Run `outcome` again on the checkpoint you keep. Record each result with the simulation version.
- **Settings that break parity** (`d2s_warp_scene.py check` lists them):
  - Linesearch iterations below 20. The CPU solver stops early in tight grasps and returns wrong accelerations: objects spin or fly out of the hand and joints exceed their speed limits, on the CPU only. Keep `ls_iterations` 50 and `iterations` 100.
  - Box–box contacts between geoms that matter. Use convex meshes made from the box's 8 vertices (`add_box`).
  - Parts of one articulated object that touch at rest. CPU and GPU disagree about which part-part contacts exist, with or without a contact margin. Leave about 0.2 mm per face between parts and let joint springs, limits, damping and friction loss hold the rest configuration.
  - Buffer overflow. A contact or constraint overflow drops contacts without an error: size the buffers from your own starts and treat an overflow as an error (`WarpHandEnv.raise_on_overflow`).
- **Measure training honestly.**
  - Success is the first episode of each environment after a reset. The mean of recently finished episodes over-counts short failures and changes with the number of environments.
  - Hardware violations are counted per episode.
  - Score checkpoints on your evaluator (64–128 seeds) while you train, and keep the best by that score. `d2s_teacher.py` does all of this.
- **Make sure training moves the policy.** Watch the policy change per update (KL, parameter change). A learning rate or action noise so small that the policy does not change wastes the run; `d2s_teacher.py` warns about it.
- **A student rarely beats its teacher.** Distil only from a teacher that succeeds at least 0.9 on the student's starts. Improve the teacher first; `d2s_teacher.py` refuses a weaker one unless you override it.
- **Focus compute.** Run a few experiments at a time, each with enough samples to learn, rather than many runs that each stop early.

**Rewards and curricula**
- **Reward what your suite judges.** For each stage: a progress term (how much the stage's error to its goal shrank since the previous step, in the units of your criteria) and a bonus when the stage's criteria hold, judged the way your evaluator judges them.
- **Holding still must not pay.** If per-step rewards for keeping the object (alive, contact or grasp terms) add up to more than finishing the stage, the policy learns to hold on and stop. Keep such terms small or zero. End the episode on an unrecoverable failure (the object dropped or out of reach), with a penalty no larger than the success bonus.
- **Regularize lightly.** Action-rate, joint-limit and hardware-limit terms keep the motion executable. Together they should stay a small part (about 10% or less) of a successful episode's return.
- **Check the reward before you train.** Score three policies with your reward (`d2s_teacher.evaluate`): your proven controller, a policy that holds still, and random actions. The controller must earn the highest return; if holding still earns more, fix the reward first.
- **Start the curriculum where the motion already works.**
  - Begin at the starts and goals where your proven controller or teacher succeeds.
  - Widen one range at a time (goal, start spread, randomization). Move up a level when the evaluator's success stays above about 0.8.
  - Keep drawing some starts (20–30%) from earlier levels, so the policy does not forget them.
  - The last level is the deployment's ranges, which your suites gate. `d2s_teacher.Curriculum` does the switching.
- **Give the deployable policy a history.** The hand has no tactile or force sensing (`hardware/SPECS.md`), so slip, contact and changes in the object's motion show only over time, in how the joints and the object move. Give the student several recent steps (`DistillConfig.history`, 3–8 is a common start) or a recurrent network, and compare it on your evaluator with one that sees a single step.

**Skills**
- **Decompose** the task into skills in the order of your criteria's stages (`TASK.md`, Task Understanding and Decomposition).
- **One suite per skill.** Before you train a skill separately, register its skill suite (`demo2sim/VERIFICATION.md` section 3): where it starts, what completes it, and the pass rate you require, with the reason for that number.
- **Starts come from the previous skill.** A skill's starts are the end states the previous skill's incumbent actually reaches, with randomization, not only states you construct by hand. For the links of the chain the gate hands these states over (handoff states); train from them too.
- **A skill is in the library when its suite's incumbent meets its pass rate** without a hardware violation. Freeze it. `r2s2r-d2s status` lists the library.
- **Compose** the library into one policy and train the transitions; the task suite judges the composed policy.
- **Changing a skill** in the library needs a new gate of every suite that depends on it.

## 3. Changes and When to Switch Methods

- **Every change you keep goes through a gate** with its hypothesis, the stage it should improve and its method class (for example reward, curriculum, action space, observations, simulation, algorithm settings, architecture). The gate records are your changelog.
- **Look before you change.** Open the failure montages of your latest gate (`failures/` in its output) and find the first thing that goes wrong; name it with `--observed`. A change aimed at a failure you have seen is worth more than a setting you have not tried.
- **Change one thing at a time** where you can; when you batch changes, say so in the hypothesis.
- **Decide in advance when to give up on a method.** When the same method class is rejected three times in a row, record a decision note and try a different class rather than another setting of the same one. `r2s2r-d2s status` reports such streaks.
- **Plan the budget.** Keep a budget plan in `PROGRESS.md`: what each remaining block of time is for. Time without a stated purpose is usually wasted.

## 4. What You Record for Each Iteration (`r2s2r-d2s iter`)

Record every training iteration you evaluate (a training run, or a checkpoint you compare against others).

| Item | Content |
|---|---|
| Simulation | The simulation record version it was trained in; the simulation it ran in (CPU MuJoCo, or MuJoCo Warp with the `d2s_parity.py` results of that version) |
| Algorithm | Algorithm and its main hyperparameters, policy architecture, observation and action spaces (with the history length), number of environments, seeds |
| Reward | Every reward term with its formula or description and its weight |
| Domain randomization | Every randomized quantity with its range and distribution, or "none" |
| Curriculum | Stages and switching rules, or "none" |
| Training curves | Per training step: total reward and each reward term, episode length, success (first episode per environment), hardware violations per episode, the policy change per update, and your verification metrics where you compute them during training (a CSV file) |
| Compute | Wall-clock time, GPU hours |
| Evaluation | The result against your current criteria on a fixed set of evaluation episodes (number of episodes, success rate, per-criterion values), and the ID of its gate where it had one |
| Rollout videos | A representative rollout from the top, left and right views of your simulation (mp4) |
| Reflection | What changed from the previous iteration, what worked, what failed, the next hypothesis |
