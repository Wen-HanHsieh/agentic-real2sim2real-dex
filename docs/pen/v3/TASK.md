# Task: Pen Spinning

Reproduce the dexterous manipulation skill demonstrated in the human video using the Wuji Hand 2: **spin a pen end over end around the fingers, counterclockwise viewed from above, for three full revolutions, keep it in the hand throughout, and hold it at rest**.

Rotation is the heading of the pen (back end to red tip) about the world vertical axis; rotating the pen about its own long axis does not count.

The hand starts palm up with the pen lying across the fingers, and its wrist is free to move within the workspace of `hardware/SPECS.md` section 3. The policy observes the exact position, orientation and velocities of the pen (`CONTRACT.md`).

Develop your policy in your own simulation and evaluate it in the provided target environment.

- **Human demonstration:** `demo/`
- **Target environment:** `target/screenshot.png`
- **Success criteria:** `SUCCESS.md` (provisional)
