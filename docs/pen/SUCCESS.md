# Success Criteria: Pen Spinning

Complete all stages in order within **12 s (6000 steps at 500 Hz)**. Total progress score: 0–1.

Rotation is the signed cumulative change of the pen's heading (the direction from its back end to its red tip, projected on the horizontal plane) about world +Z, measured from step 0. Counterclockwise from above is positive; clockwise motion subtracts. Rotation of the pen about its own long axis does not change the heading and does not count.

### 1. Spin-up (0–0.30)
- **0:** Heading rotation < 90°, or the pen is lost before reaching it.
- **0.10:** Net rotation ≥ 90°.
- **0.20:** Net rotation ≥ 180°.
- **0.30:** First revolution: net rotation reaches +360° within 3.0 s of step 0.

### 2. Sustain (0–0.45)
- **0:** First revolution not completed.
- **0.15:** Net rotation ≥ +540°.
- **0.25:** Second revolution: +720° reached within 3.0 s of the first.
- **0.35:** Net rotation ≥ +900°.
- **0.45:** Third revolution: +1080° reached within 3.0 s of the second.

### 3. Hold (0–0.25)
- **0:** Third revolution incomplete, or the pen not retained.
- **0.10:** After +1080°, the pen touches the hand with centre speed < 0.02 m/s and angular speed < 0.5 rad/s for ≥ 0.25 s.
- **0.15:** The same throughout the final 0.5 s.
- **0.25:** Throughout the final 1.0 s: net rotation ≥ +1080° (the third revolution is never undone), centre speed < 0.02 m/s, angular speed < 0.5 rad/s, and hand contact at every step.

All milestones require the pen retained up to that moment: it touches nothing but the hand, contact interruptions < 0.10 s, its centre stays within 8 cm horizontally of its step-0 position and never drops more than 3 cm below it, and its long axis never tilts more than 45° from horizontal.

**Scoring:** Award the highest satisfied milestone per stage. Later-stage scores require full completion of preceding stages. Back-and-forth motion nets to zero; a revolution that takes longer than 3.0 s after the previous one does not count toward the next milestone.

**Official success:** Score = 1.0, with all physical, hardware, and runtime requirements satisfied in every required evaluation trial.
