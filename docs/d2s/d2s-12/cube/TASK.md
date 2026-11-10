# Task: One-Handed Rubik's Cube

## Goal
Solve the 2×2×2 Rubik's cube with one hand, without breaking it.

## Deployment
I'll scramble the cube a little, just a few turns away from solved, and differently each time. Your hand starts in whatever pose you choose, and then I'll set the cube in the palm, roughly in the middle, with any side up. Pick a starting pose that keeps the cube there wherever I set it. Then turn its layers until it's solved, holding it in one hand the whole time. It should work for any such scramble and however I set the cube down, not just the way it was in my video.

Keep in mind that the real cube won't behave exactly like the one in your simulation, and I won't always set it down exactly the way I said.

## The Demonstration
The video in `demo/` shows me doing this once. It's one example, not the situation your policy will face, but it shows how I want the skill done.
* Your robot hand should move like mine: its wrist pose, finger motion and the cube's motion, especially the wrist pose.
* Where the cube is scrambled or set down differently from my video, adapt the same motion to it.
* Getting the job done in the deployment setting comes first, but not with a different way of doing it.

## Task Understanding and Decomposition
Before building your training simulation and policy:
* Identify the goal, the objects, their interactions and the final outcome from this file and the video.
* Note how my wrist moves and is oriented throughout the skill.
* Break the demonstration into an ordered list of manipulation subgoals, with the object motions and contact transitions of each.
* Separate what the video shows from what you infer.
* Turn this into your verification criteria (`demo2sim/VERIFICATION.md`), and revise it as you learn more.

Treat the list as a high-level plan, not a prescribed robot trajectory or control strategy.

## What You Deliver
* A policy that does this in the deployment setting, in your simulation, using only the observations `demo2sim/LEARNING.md` allows.
* What I need to run it: the hand's starting pose (wrist pose and finger joint positions), each object's mesh and state frame (and, for an object with parts that move relative to each other, its parts and their frames), the policy's observation and action interface, and, if the number of objects can change, how the policy handles that.
* Your verification criteria (`demo2sim/VERIFICATION.md`), which decide whether the job is done in the deployment setting, and the evidence that your policy meets them.

Write down how you understand the task and how you plan to do it, and update it as you learn more. How you get there is up to you. Whatever you do, make sure your policy works in the deployment setting.

## Resources
* Human demonstration: `demo/`
* Task configuration: `TASK_CONFIG.md`
* Verification: `demo2sim/VERIFICATION.md`
