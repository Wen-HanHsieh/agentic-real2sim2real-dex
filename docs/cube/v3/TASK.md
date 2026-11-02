# Task: One-Handed Rubik's Cube Manipulation

Analyze the human demonstration in `demo/` and the success criteria in `SUCCESS.md`.

Your goal is to understand and reproduce the demonstrated manipulation task using the Wuji Hand 2 in the target environment.

## Task Understanding and Decomposition

Before developing your training simulation and policy:

1. Understand the task.
   * Identify the intended manipulation goal from the human video.
   * Identify the objects involved, their interactions, and the desired final outcome.
   * Use `SUCCESS.md` to understand the evaluation requirements.
2. Decompose the task.
   * Break down the demonstrated task into a clear, ordered TODO list of meaningful manipulation subgoals.
   * Identify the key actions, object motions, contact transitions, and intermediate outcomes.
   * Distinguish what is directly observed in the video from what is inferred or specified by `SUCCESS.md`.
3. Document and refine.
   * Record your task understanding and TODO list in your research workspace.
   * Identify ambiguities and assumptions.
   * Revise your task decomposition as new evidence becomes available.

Treat the TODO list as a high-level task plan, not a prescribed robot trajectory or control strategy. Independently determine how to achieve each subgoal with the robot.

## Resources

* Human demonstration: `demo/`
* Success criteria: `SUCCESS.md`
* Target environment: `target/`
* Task configuration: `TASK_CONFIG.md`
* Object specifications: `object/SPECS.md`
