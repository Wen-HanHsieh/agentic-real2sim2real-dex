# Object Specification: 2×2×2 Rubik's Cube

## 1. Geometry and Physical Properties

| Parameter | Value |
|---|---|
| Object | `cube` |
| Geometry | 2×2×2 cube with 8 corner cubies |
| Edge length | 0.050 m (±0.006 m) |
| Cubie dimensions | 0.0246 × 0.0246 × 0.0246 m |
| Cubie pitch | 0.025 m |
| Edge bevel | 1.5 mm |
| Stickers | 19.6 mm square, protruding 0.2 mm |
| Total mass | 0.060 kg |
| Mass distribution | 8 equal, uniform cubies |
| Collision geometry | Cubie cubes, without visual bevels or stickers |

**Colors (solved):**
- U: White
- D: Yellow
- F: Green
- B: Blue
- R: Red
- L: Orange
- Cubie bodies: Black

**Unspecified:** Turning resistance, friction, restitution, and contact compliance.

## 2. Mechanics

- The cube consists of 8 corner cubies rotating about the cube center, with no fixed center pieces.
- Each layer contains 4 cubies and rotates about one of the three principal axes.
- Turning a second layer while another is not aligned is resisted by the mechanism; the interlock is elastic, so the deflection grows with the applied torque and disappears after release.
- A released layer close to an aligned position (within about 20°) settles into it; released farther away, it stays where it is.
- Forcing cubies more than 15° away from a mechanically allowed configuration does not jam the mechanism, but counts as breaking the cube.

## 3. Object State Frame (`objstate-1`)

**Object and part ordering:**
- Object `0 = cube`
- Parts `0–7 = cubie0 … cubie7`, all belonging to object 0.

### Cube Root Frame

- **Origin:** Cube center, defined relative to cubie 0 at offset `(−e/4, −e/4, +e/4)` in cubie 0's frame, where `e = 0.050 m`.
- **Axes:** Follow cubie 0. The root frame rotates when cubie 0 participates in a layer turn.
- **Solved orientation:**
  - +X → Back (B)
  - +Y → Left (L)
  - +Z → Up (U)
- **Cubie 0:** Down–Back–Left corner.

In every legal configuration, the cube center coincides with the mean position of the eight cubie centers.

### Cubie Frames

- **Origin:** Each cubie's geometric center.
- **Axes:** Fixed to each cubie, aligned with the cube root frame in the solved configuration.

**Home slots (solved):**

Coordinates are expressed in cube-frame units of `e/4`.

| Cubie | X | Y | Z |
|---|---|---|---|
| `cubie0` | + | + | − |
| `cubie1` | − | + | − |
| `cubie2` | + | − | − |
| `cubie3` | − | − | − |
| `cubie4` | + | + | + |
| `cubie5` | − | + | + |
| `cubie6` | + | − | + |
| `cubie7` | − | − | + |

### Configuration Encoding

- **Relative orientation:** Each cubie's orientation relative to cubie 0, `q₀⁻¹ ⊗ qⱼ` (wxyz); cubie 0 is the identity.
- **Cube configuration:** Each relative orientation is mapped to the nearest of 24 valid cube rotations, using maximum `trace(GᵀR)`.
- **Rotation table:** `object/rotations24.json`, sorted lexicographically by the nine row-major entries of each rotation matrix.
- **Rotation matrices:** 3×3 matrices with entries in `{−1, 0, 1}` and determinant +1.
- **Solved configuration:** All eight rotation indices equal `23` (identity rotation).
