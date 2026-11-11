# Task: Turning a Cube with the Fingers of One Hand

## Goal
With one hand, make the move I ask for on the 2×2×2 Rubik's cube: a quarter turn of one of its layers, or a quarter turn of the whole cube, with your fingers, holding the cube the whole time and without breaking it.

## Deployment
Your hand starts in whatever pose you choose. Then I set the cube in the palm, roughly in the middle, with any side up, in whatever state it happens to be. Then I ask for one move, and your policy is told which:
* a quarter turn, clockwise or counterclockwise, of one layer: one of the faces you can reach as the cube sits in your hand (you say which in your criteria; at least the face on top and the face toward your fingertips); or
* a quarter turn of the whole cube about one of its axes, so that another face ends up on top or toward your fingertips.

Make the move with your fingers and end with every layer aligned and the cube resting in your hand. It should work for every move you list and however I set the cube down, not just the way it was in my video.

Keep in mind that the real cube won't behave exactly like the one in your simulation, and I won't always set it down exactly the way I said.

## The Demonstration
The video in `demo/` shows me solving the cube once. This run is only about the single moves I make with my fingers: each turn of a layer, and each time I turn the whole cube in my hand. Find them in the video and in your reconstruction.
* Your robot hand should make them the way I do: with its fingers, the wrist posed like mine.
* Pushing the cube against anything but your hand, or turning it with the wrist alone, is not the same skill.
* Where the video doesn't show what a layer did, say so, and take the move from this goal.
* Getting the job done comes first, but not with a different way of doing it.

## Task Understanding and Decomposition
Before building your training simulation and policy:
* Find the moves in the video, and measure in your reconstruction how the cube turns relative to the hand where it can be measured.
* When you design a move in your simulation, use three things together: the video (how the fingers move and where they touch), your reconstruction (how far, about which axis, how fast) and this goal (the move asked for, layers aligned, cube held). Where they disagree, or where the robot hand can't do what mine does, the goal decides, and you write down the deviation.
* Separate what the video shows from what you infer.
* Turn this into your verification criteria (`demo2sim/VERIFICATION.md`), and revise it as you learn more.

## What You Deliver
* A policy that makes the requested move in the deployment setting, in your simulation, using only the observations `demo2sim/LEARNING.md` allows plus the requested move.
* What I need to run it: the hand's starting pose, the cube's mesh, parts and their state frames, how the requested move is given to the policy, and its observation and action interface.
* Your verification criteria (`demo2sim/VERIFICATION.md`), and the evidence that your policy meets them.
* Each move as a skill in your skill library (`demo2sim/LEARNING.md` section 2), so that the moves can be used to solve the cube later.

Write down how you understand the task and how you plan to do it, and update it as you learn more. How you get there is up to you.

## Resources
* Human demonstration: `demo/`
* Task configuration: `TASK_CONFIG.md`
* Verification: `demo2sim/VERIFICATION.md`
