# Success Criteria: Ball Toss, Catch, and Spin

Complete all stages in order within **10 s (5000 steps at 500 Hz)**. Total progress score: 0–1.

### 1. Toss (0–0.25)
- **0:** No release.
- **0.10:** Upward release with ≥ 0.05 s contact-free flight.
- **0.25:** Upward release, ≥ 0.10 s contact-free flight, apex ≥ 20 cm above release, and a physically consistent free-fall arc.

### 2. Catch (0–0.30)
- **0:** No valid toss or recontact.
- **0.10:** Hand recontacts the ball after a valid toss, before any environment contact.
- **0.30:** Ball lands on the hand, touches nothing else afterward, and maintains speed < 0.02 m/s for ≥ 0.10 s while touching the hand. Define the first qualifying moment as `t_rest`.

### 3. Spin (0–0.30)
- **0:** < 90°
- **0.10:** ≥ 90°
- **0.15:** ≥ 180°
- **0.20:** ≥ 360°
- **0.25:** ≥ 540°
- **0.30:** ≥ 720°

Measure signed net rotation about world +Z after `t_rest` (counterclockwise from above is positive). All milestones require contact gaps < 0.10 s and ball-center displacement ≤ 3 cm from its position at `t_rest`.

### 4. Hold (0–0.15)
- **0:** Required spin incomplete or ball not retained.
- **0.05:** After the spin, maintain hand contact and speed < 0.02 m/s for ≥ 0.10 s.
- **0.10:** Maintain ≥ 720° net rotation, hand contact, and speed < 0.02 m/s throughout the final 0.15 s.
- **0.15:** Maintain ≥ 720° net rotation and speed < 0.02 m/s throughout the final 0.30 s; hand contact at the final step.

**Scoring:** Award the highest satisfied milestone per stage. Later-stage scores require full completion of preceding stages. Earlier hops and regrasps before the qualifying toss are allowed.

**Official success:** Score = 1.0, with all physical, hardware, and runtime requirements satisfied in every required evaluation trial.
