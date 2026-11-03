# Object Specification: Two Charger Plugs

## 1. Geometry and Physical Properties

Two US Type-A, two-blade USB wall chargers reconstructed from the demonstration video.

| Parameter | White Plug (`plug_white`) | Black Plug (`plug_black`) |
|---|---|---|
| Body geometry | Rounded rectangular block | Rounded rectangular block |
| Body dimensions (X × Y × Z) | 29 × 43.1 × 58.5 mm | 31.8 × 35.8 × 64.5 mm |
| Edge radius (visual mesh) | ≈ 2 mm | ≈ 1 mm |
| Blade length | 16 mm | 18 mm |
| Total axial length | 74.5 mm | 82.5 mm |
| Mass | 0.075 kg | 0.055 kg |
| Center of mass | 2 mm toward blades from body center | 2 mm toward blades from body center |
| Surface | Glossy white plastic | Glossy black plastic |
| Blades | Dark metal-grey | Dark metal-grey |

**Shared blade geometry:**
- Two parallel flat blades, perpendicular to the body's end face.
- Blade width: 6.35 mm each.
- Blade thickness: 1.5 mm each.
- Blade center-to-center spacing: 12.7 mm.
- USB port recess on the face opposite the blades.

**Measurement and uncertainty:**
- Dimensions estimated from the demonstration video, using standard blade geometry for scale.
- White plug dimensions: approximately ±10% uncertainty; the 29 mm thickness was additionally refined using first-frame camera fitting.
- Masses are estimates, not directly measurable from video.
- Collision shapes are sharp-edged boxes; the edge radii apply to the visual mesh only.
- **Unspecified:** Moment of inertia, friction, restitution, and contact compliance.

## 2. Object State Frame (`objstate-1`)

**Object ordering:**
- `0 = plug_white`
- `1 = plug_black`

Both plugs use the same state-frame convention:

- **Origin:** Center of the rectangular body, not the center of mass.
- **+Z:** Blade axis, pointing from the body toward the blades.
- **+Y:** Blade-gap axis, with blade centers at Y = ±6.35 mm.
- **+X:** `Y × Z`, along the blade width.
- **Upright orientation:** Local +Z points toward world +Z.
