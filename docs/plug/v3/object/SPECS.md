# Object Specification: Two Charger Plugs and the Table

The scene holds the two two-blade (US type A) USB wall chargers of the human demonstration, reconstructed from the video, lying on a tabletop. Their dimensions were measured from the demonstration video, scaled by the standard blade geometry (6.35 mm wide blades 12.7 mm apart). Objects (order): `0 = plug_white`, `1 = plug_black`.

## White Plug (`plug_white`, object 0)

- **Body:** Rectangular block, 29 × 43.1 × 58.5 mm: 29 mm thick along the blade width, 43.1 mm wide along the blade gap, 58.5 mm long along the blade axis; rounded edges (radius about 4 mm), glossy white plastic; a small port recess on the face opposite the blades. The width and length are the reconstruction's estimates (±10 %); the thickness was re-measured by fitting the demonstration camera and the body's per-axis dimensions to 17 annotated image points of the first frame, with the black plug as the metric reference (28.6–29.4 mm, stated as 29 ± 3 mm). It replaces an earlier square-section estimate.
- **Blades:** Two, each 6.35 mm wide, 1.5 mm thick, and 16 mm long, standing perpendicular to the 29 × 43.1 mm face with their centres 12.7 mm apart (blade faces parallel to each other, across the gap); overall length 74.5 mm along the blade axis.
- **Mass:** 0.075 kg (typical for this class of adapter; not measurable from the video), centre of mass 2 mm from the body centre toward the blades.
- **Colours (videos):** White body, dark metal-grey blades.

## Black Plug (`plug_black`, object 1)

- **Body:** Rectangular block, 31.8 × 35.8 × 64.5 mm (31.8 mm along the blade width, 35.8 mm along the blade gap, 64.5 mm along the blade axis), rounded edges (radius about 2 mm), glossy black plastic; a port recess on the face opposite the blades.
- **Blades:** Two, each 6.35 mm wide, 1.5 mm thick, and 18 mm long, standing perpendicular to the 31.8 × 35.8 mm face with their centres 12.7 mm apart; overall length 82.5 mm along the blade axis.
- **Mass:** 0.055 kg (not measurable from the video), centre of mass 2 mm from the body centre toward the blades.
- **Colours (videos):** Black body, dark metal-grey blades.

Surface and contact properties of the plugs and the table are not given.

## Table

- **Tabletop:** the plane z = 0 (world frame, `hardware/SPECS.md` section 3), the top face of a static block 1.20 × 1.20 m and 0.03 m thick centred at (0.10, 0.00); matte white laminate (videos). It is large enough that neither plug nor the hand reaches an edge within the wrist workspace.
- **Floor:** z = −0.75 m. A plug pushed off the table falls to it and is not retrieved.

## Initial Arrangement

Both plugs lie at rest on the table in the arrangement of the demonstration's first frame; the exact initial states are the observation of step 0. Approximately (positions ±2 cm, yaw angles ±10°, from the video; the white plug's position and yaw come from the same first-frame camera fit as its thickness):

| Object | Body centre (m) | Resting face | Blade axis | Blades |
|---|---|---|---|---|
| `plug_white` | (0.042, 0.031, 0.015) | its wide face (body +x face, the 29 mm thickness axis, down) | horizontal, yaw +24° from world +X (forward-left) | side by side (gap axis horizontal) |
| `plug_black` | (−0.043, −0.041, 0.018) | the body +y face down (a face normal to the blade-gap axis) | horizontal, yaw −109° from world +X (to the right, slightly backward) | stacked one above the other |

The hand starts 0.2–0.3 m behind the plugs on the −X, −Y side (`hardware/SPECS.md` section 3) and touches neither.

## State Frame (object state `objstate-1`)

The state frame is the frame whose pose and velocities the observation and the feedback report for this object (`CONTRACT.md` section 2, `FEEDBACK.md` section 3).

Objects (order): `0 = plug_white`, `1 = plug_black`; every `object_*` array carries both in this order.

- **Origin:** the body centre of the plug (the centre of its rectangular body, not the centre of mass, which lies 2 mm toward the blades).
- **+z:** the blade axis, from the body centre through the blades (upright = +z pointing to world +Z).
- **+y:** from one blade to the other (the blade-gap axis; the two blades stand at y = ±6.35 mm).
- **+x:** `y × z`, along the blade width.
- The angle between the blade axis and world +Z is `acos` of the third component of the rotated +z axis.

## Goal Block (`goal_defined`, `goal_position`, `goal_orientation`, `goal_free_axis`)

The observation and the state record carry a per-plug goal block (`CONTRACT.md` section 3): `goal_defined` `(2,)` int64, `goal_position` `(2, 3)` (goal of the state-frame origin), `goal_orientation` `(2, 4)` `(w, x, y, z)`, `goal_free_axis` `(2, 3)` (a state-frame axis about which rotation is ignored; zeros = none). It is configurable per experiment, and it is **currently undefined**: `goal_defined` is `[0, 0]`, `goal_position` and `goal_orientation` are NaN, `goal_free_axis` is zero, constant through the episode. Criteria published later may define goals; until then there is none (`SUCCESS.md`).
