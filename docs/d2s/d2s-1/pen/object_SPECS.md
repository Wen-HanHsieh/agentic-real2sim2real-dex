# Object Specification: Pen

## 1. Geometry and Physical Properties

A pen-spinning mod reconstructed from the demonstration video, consisting of a long cylindrical barrel with thicker end pieces.

| Parameter | Value |
|---|---|
| Object | `pen` |
| Geometry | Body of revolution with thicker end pieces |
| Total length | 0.195 m (±0.015 m) |
| Barrel diameter | 0.009 m |
| Maximum diameter | 0.0112 m |
| Mass | 0.022 kg |
| Center of mass | Mid-length (97.5 mm from either end) |
| Mass distribution | Uniform along the body |
| Axial moment of inertia | 2.2 × 10⁻⁷ kg·m² |
| Transverse moment of inertia | 7.3 × 10⁻⁵ kg·m² |

### Geometry Profile

Diameter along the pen's longitudinal axis, measured from the back end:

| Distance (mm) | Diameter (mm) |
|---:|---:|
| 0 | 0 |
| 0.8 | 7.6 |
| 2.3 | 9.5 |
| 13.7 | 9.5 |
| 14.8 | 8.5 |
| 16.0 | 9.0 |
| 171.6 | 9.0 |
| 172.6 | 11.2 |
| 187.2 | 11.2 |
| 188.8 | 8.5 |
| 194.0 | 2.6 |
| 195.0 | 0 |

- The profile is linearly interpolated between the listed points.
- Dimensions are estimated from the demonstration video.
- **Unspecified:** Surface friction, restitution, and contact compliance.

### Visual Appearance

- **Body:** Blue.
- **Tip:** Red, covering the last 18 mm at the heading end.
- **Center band:** White, 8 mm wide.
- **Roll markers:** Yellow and green longitudinal stripes on opposite sides of the barrel, each covering 70° of its circumference.
- **Visual only:** Markings do not affect mass, inertia, or collision geometry.

The demonstration pen has different colors (white body, grey ends, red/blue rings); the specifications above describe this task's pen.

## 2. Object State Frame (`objstate-1`)

- **Object index:** `0 = pen`
- **Origin:** Geometric center, 97.5 mm from either end.
- **+X:** Along the pen's longitudinal axis toward the red tip.
- **+Y:** Perpendicular to the longitudinal axis, toward the center of the yellow stripe.
- **+Z:** `X × Y`, completing the right-handed frame.
- **Heading direction:** Projection of local +X onto the world horizontal plane.
