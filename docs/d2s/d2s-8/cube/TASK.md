# Task: One-Handed Rubik's Cube

Solve the 2×2×2 Rubik's cube with one hand.

The trained policy should move like the human hand in the video: its wrist pose, its finger motion and the object's motion, especially the wrist pose. Looking similar is good, but your goal is to finish the task, not to copy the motion exactly.

## Task Understanding and Decomposition

Before building your training simulation and policy:

1. Understand the task.
   * Identify the intended manipulation goal from the instruction above and the human video in `demo/`.
   * Identify the objects involved, their interactions, and the desired final outcome.
   * Note how the demonstrator's wrist moves and is oriented throughout the skill.
2. Decompose the task.
   * Break down the demonstrated task into a clear, ordered TODO list of meaningful manipulation subgoals.
   * Identify the key actions, object motions, contact transitions, and intermediate outcomes.
   * Distinguish what is directly observed in the video from what is inferred or stated in the instruction.
3. Turn it into your verification criteria (`demo2sim/VERIFICATION.md`).
4. Document and refine.
   * Record your task understanding and TODO list in your research workspace.
   * Identify ambiguities and assumptions.
   * Revise your task decomposition as new evidence becomes available.

Treat the TODO list as a high-level task plan, not a prescribed robot trajectory or control strategy. Independently determine how to achieve each subgoal with the robot.

## Resources

* Human demonstration: `demo/`
* Task configuration: `TASK_CONFIG.md`
* Object specifications: `object/SPECS.md`
* Verification: `demo2sim/VERIFICATION.md`
