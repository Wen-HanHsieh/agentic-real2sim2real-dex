# Task: Plug Handling on a Table (criteria not yet defined)

**No task objective, success criteria, placement targets or required sequence have been defined for this task yet** (`SUCCESS.md`). This document describes the human demonstration and what the target environment supports, so that you can prepare; the official evaluation of every rollout reports `status: criteria_undefined` until criteria are published.

## The Demonstration

In the human video (`demo/`), two two-blade charger plugs, a white one and a black one, lie on their sides on a white desk. A right hand enters from the near-right corner, palm down, with the fingers pointing forward-left. It picks up the white plug with a pinch grasp (thumb on one side face, index and middle finger on the opposite one), turns it in the fingertips until the blades point up, carries it about 25 cm to the left and stands it on the desk on the face opposite the blades. It then returns to the black plug, picks it up the same way, reorients it blades-up in the hand, and stands it beside the white one. Both plugs end standing side by side with their blades up; the hand withdraws. The clip lasts 14.5 s.

## The Target Scene

The target environment reproduces this scene (`object/SPECS.md`, `TASK_CONFIG.md` section 3): a flat tabletop (the plane z = 0), the white plug and the black plug lying on it at rest in the arrangement of the demonstration's first frame, and the Wuji Hand 2 on a free-floating wrist starting palm down above the near-right side of the table, 9 cm above it, with open fingers and touching nothing. The episode lasts 15 s (7,500 control steps); the policy observes the exact pose and velocities of both plugs at every step and commands the fingers and the wrist (`CONTRACT.md`).

## What the Environment Supports

- The wrist can move anywhere inside the workspace box of `TASK_CONFIG.md` section 3, which covers the table region around both plugs; its height is limited so that the wrist frame never goes below 3 cm above the tabletop.
- The hand can approach either plug from any direction, push it, grasp it, lift it, reorient it in the hand, carry it, release it, and set it down anywhere on the table, in any order and any number of times. Both plugs can be handled in the same episode.
- The plugs are free rigid bodies: they slide, tip over, fall, and collide with the table, with the hand and with each other. A plug that leaves the table falls to the floor 0.75 m below and is not retrieved.
- Nothing has to be inserted anywhere: the scene has no socket, outlet or cable.
- The observation's goal block (`goal_defined`, `goal_position`, `goal_orientation`, `goal_free_axis`) is a reserved place for per-plug targets; it currently reports no goal for either plug (`goal_defined` all 0, NaN values). Criteria published later may define goals there; until then the policy should not rely on it.

The feedback of every rollout (`FEEDBACK.md`) contains the exact trajectories of the hand and both plugs and the contact flags hand–plug, plug–table and plug–plug, so that any behaviour you train can be checked against the target record even before the criteria exist.

- **Human demonstration:** `demo/`
- **Target environment:** `target/screenshot.png`
- **Success criteria:** `SUCCESS.md` (not yet defined)
