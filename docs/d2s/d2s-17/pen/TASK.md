# Task: Pen Spinning

## Goal
Spin the pen clockwise in four 180° turns, passing it between finger pairs: index–middle → middle–ring → ring–pinky → middle–ring → index–middle. Then hold it.

## Deployment
Your hand starts in whatever pose you choose, and then I'll slide the pen between the index and middle fingers, with the same end toward the thumb as in my video. I'll put it in roughly at its middle, but not always exactly there and not always perfectly straight. Pick a starting pose that holds the pen however I slide it in. It should work however I put the pen in, not just the way it was in my video.

Keep in mind that the real pen won't behave exactly like the one in your simulation, and I won't always put it in exactly the way I said.

## The Demonstration
The video in `demo/` shows me doing this once. It's one example, not the situation your policy will face, but it shows how I want the skill done.
* Your robot hand should move like mine: its wrist pose, finger motion and the pen's motion, especially the wrist pose.
* Where the pen sits differently from my video, adapt the same motion to it.
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
