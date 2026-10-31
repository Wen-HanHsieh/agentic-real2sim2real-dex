# Object Specification: Tennis Ball

- **Geometry:** Sphere, diameter 0.065 m (radius 0.0325 m). The diameter was measured from the demonstration video (the ball's free-fall acceleration in pixels against its pixel radius); uncertainty about ±2 mm on the diameter (±0.9 mm on the radius). A standard tennis ball is 65.4–68.6 mm.
- **Mass:** 0.0577 kg (standard tennis-ball range 56.0–59.4 g; the mass is not measurable from the video).
- **Mass distribution:** Hollow ball (thin rubber shell under felt), centred at the geometric centre; moment of inertia about any axis ≈ 4.1 × 10⁻⁵ kg·m² (thin-shell value 2/3 · m · r²; a real ball with a thick shell may be up to about 20 % lower).
- **Surface:** Felt, uniform yellow-green, no markings. The ball's rotation is not part of the task; the observation nevertheless reports it exactly.
- **Initial state:** the ball rests in the cupped palm of the hand at its initial pose (`TASK_CONFIG.md` section 3); the exact initial state is the observation of step 0.

Other surface and contact properties are not given.

## State Frame (object state `objstate-1`)

The state frame is the frame whose pose and velocities the observation and the feedback report for this object (`CONTRACT.md` section 2, `FEEDBACK.md` section 3).

Objects (order): `0 = tennis_ball`.

- **Origin:** the ball's centre (also its centre of mass).
- **Axes:** a frame fixed to the ball, aligned with the world axes at the start of the episode's settle phase. The ball is unmarked, so the axes have no visible reference; `object_orientation` and `object_angular_velocity` still report the ball's exact rotation and spin.
