# Object Specification: Tennis Ball

## 1. Geometry and Physical Properties

| Parameter | Value |
|---|---|
| Object | `tennis_ball` |
| Geometry | Sphere |
| Diameter | 0.065 m (±2 mm) |
| Mass | 0.0577 kg |
| Mass distribution | Hollow, approximately thin spherical shell |
| Moment of inertia | ≈ 4.1 × 10⁻⁵ kg·m² about any axis |
| Surface | Uniform yellow-green felt, unmarked |

- **Diameter:** Estimated from the demonstration video.
- **Mass:** Based on standard tennis-ball specifications, not measured from video.
- **Inertia:** Thin-shell approximation, `I = (2/3)mr²`; actual inertia may be approximately 20% lower.
- **Unspecified:** Friction, restitution, contact compliance, and aerodynamic properties.

## 2. Object State Frame (`objstate-1`)

- **Object index:** `0 = tennis_ball`
- **Origin:** Ball center (center of mass).
- **Axes:** Fixed to the ball, initially aligned with world axes at the beginning of the settle phase.
- **Rotation:** Although the ball is unmarked, its orientation and angular velocity are defined by the simulated state frame.
