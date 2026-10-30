# Task: Tennis Ball Toss and Catch

Reproduce the dexterous manipulation skill demonstrated in the human video using the Wuji Hand 2: **toss a tennis ball upward from the palm, catch it, toss and catch it again, and keep it in the hand**.

A toss is a release followed by contact-free flight with an apex at least 5 cm above the release point; a catch is a flight that ends on the hand with the ball retained afterwards. Two complete toss-and-catch cycles are required; the ball's rotation is not part of the task.

The hand starts palm up with the ball resting in it, and its wrist is free to move within the workspace of `hardware/SPECS.md` section 3. The policy observes the exact position, orientation and velocities of the ball (`CONTRACT.md`).

Develop your policy in your own simulation and evaluate it in the provided target environment.

- **Human demonstration:** `demo/`
- **Target environment:** `target/screenshot.png`
- **Success criteria:** `SUCCESS.md` (provisional)
