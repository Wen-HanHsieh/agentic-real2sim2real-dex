# Task: Turning a Plug in One Hand

## Goal
Turn a plug you are already holding until its blades point up, with your fingers, without putting it down.

## Deployment
I'll put one plug in your hand, already picked up, held the way I hold it in my video just before I turn it. It is like the white or the black plug, and I'll never put it in your hand exactly the same way twice. Your hand starts in the pose you choose for holding it. Turn the plug in your hand until its blades point up, and keep holding it there, steady. Nothing but your hand should touch it. It should work for both plugs and however the plug sits in that grasp, not just the way it was in my video.

Keep in mind that the real plugs won't behave exactly like the ones in your simulation, and I won't always put them in your hand exactly the way I said.

## The Demonstration
The video in `demo/` shows me doing a whole job once: picking up two plugs and standing them up. This run is only about one part of it: how I turn each plug in my hand after I pick it up. Find that part in the video and in your reconstruction.
* Your robot hand should turn the plug the way I do: with its fingers, the plug turning relative to the hand, the wrist posed like mine.
* Turning the wrist alone, or letting the plug slip or pivot in a grip that doesn't move, is not the same skill.
* Getting the job done comes first, but not with a different way of doing it.

## Task Understanding and Decomposition
Before building your training simulation and policy:
* Find where in the video each plug turns in my hand, and measure in your reconstruction how far and about which axis it turns relative to the hand.
* When you design the motion in your simulation, use three things together: the video (how the fingers move and where they touch), your reconstruction (how far, about which axis, how fast) and this goal (blades up, still held). Where they disagree, or where the robot hand can't do what mine does, the goal decides, and you write down the deviation.
* Separate what the video shows from what you infer.
* Turn this into your verification criteria (`demo2sim/VERIFICATION.md`), and revise it as you learn more.

## What You Deliver
* A policy that does this in the deployment setting, in your simulation, using only the observations `demo2sim/LEARNING.md` allows.
* What I need to run it: the hand's starting pose, how the plug starts in it (the starts you trained and verified on), the plug's mesh and state frame, and the policy's observation and action interface.
* Your verification criteria (`demo2sim/VERIFICATION.md`), and the evidence that your policy meets them.
* The motion as a skill in your skill library (`demo2sim/LEARNING.md` section 2), so that it can be used in the whole task later.

Write down how you understand the task and how you plan to do it, and update it as you learn more. How you get there is up to you.

## Resources
* Human demonstration: `demo/`
* Task configuration: `TASK_CONFIG.md`
* Verification: `demo2sim/VERIFICATION.md`
