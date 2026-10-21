# Success Criteria: One-handed 2×2×2 Rubik's Cube Solving

Complete the stages within **40 s (20000 steps at 500 Hz)**. Total progress score: 0–1.

A layer turn is complete when the turned layer is aligned again (within about 10°) a quarter or half turn from where it started. Distance to solved is the smallest number of face turns that solves the cube (a 180° turn counts as one); the start state is 3 turns from solved, and the policy receives the scramble in every observation (`CONTRACT.md`). Solved means every face shows one colour and every layer is aligned: any two cubies' orientations differ by less than 10°, whatever the whole cube's orientation.

### 1. First turn (0–0.15)
- **0:** No layer turned.
- **0.05:** A layer rotated ≥ 45° about its axis.
- **0.15:** One complete layer turn.

### 2. Turning (0–0.15)
- **0:** Fewer than two complete layer turns.
- **0.05:** Two complete layer turns.
- **0.15:** Three or more complete layer turns.

### 3. Solving (0–0.50)
- **0:** Distance to solved never below 3.
- **0.15:** Distance to solved reaches 2.
- **0.30:** Distance to solved reaches 1.
- **0.50:** The cube is solved at some moment.

### 4. Hold (0–0.20)
- **0:** Not solved at the end.
- **0.10:** Solved and touching the hand at the final step.
- **0.20:** Solved throughout the final 1.0 s and touching the hand at the final step.

All milestones require the cube retained and intact up to that moment: it touches nothing but the hand, its centre never drops more than 5 cm below its step-0 height, and the cubies are never forced more than 15° away from a configuration the mechanism allows (all layers aligned, or exactly one layer part-way through a turn).

**Scoring:** Stage scores are additive; award the highest satisfied milestone per stage. Stages 1 and 2 count every complete layer turn, solving or not. Stage 3 requires Stage 1 complete but not Stage 2, and scores the smallest distance reached at any moment. Stage 4 requires Stage 3 complete. Reorienting the whole cube in the hand is allowed and is not a turn. Examples: one wrong turn 0.15; one correct turn 0.30; two correct turns 0.50; solved and held to the end 1.0.

**Official success:** Score = 1.0, with all physical, hardware, and runtime requirements satisfied in every required evaluation trial.
