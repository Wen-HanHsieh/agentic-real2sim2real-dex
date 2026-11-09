# Task: Plug Manipulation

## Goal
Stand the plugs up on the left side of the table, blades pointing up.

## Deployment
I'll leave two or three plugs lying on the right side of the table, wherever they happen to land; sometimes they'll touch or lean on each other. Each one is like the white or the black plug in my video. Your hand starts in whatever pose you choose. Pick the plugs up one at a time, in any order, and stand each one up on the left side, blades up, until the right side is clear. It should work however the plugs are lying, not just the way they were in my video.

Keep in mind that the real plugs won't behave exactly like the ones in your simulation, and they won't always be lying exactly the way I described.

## The Demonstration
The video in `demo/` shows me doing this once. It's one example, not the situation your policy will face, but it shows how I want the skill done.
* Your robot hand should move like mine: its wrist pose, finger motion and the plugs' motion, especially the wrist pose.
* Where a plug lies differently from my video, adapt the same motion to it.
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
