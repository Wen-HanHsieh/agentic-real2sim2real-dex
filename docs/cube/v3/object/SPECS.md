# Object Specification: 2×2×2 Cube

The cube is the 2×2×2 puzzle seen in the human demonstration (`demo/`), reconstructed from the video; the edge length is the reconstruction's estimate (± 0.006 m).

- **Geometry:** Cube, edge 0.050 m, made of 8 corner cubies on a 0.025 m pitch. Each cubie is a 0.0246 m cube (0.2 mm gap on every cubie face) with its edges and corners bevelled by 1.5 mm; the three outward faces carry square stickers 19.6 mm on a side, 0.2 mm proud of the face, leaving a black border around each sticker. Contact geometry: the 0.0246 m cubie cubes.
- **Mass:** 0.060 kg; 8 equal cubies, uniform
- **Colours (solved):** U white, D yellow, F green, B blue, R red, L orange (`TASK.md`); black cubie bodies. The demonstration cube uses the same standard scheme.
- **Initial state:** the scrambled cube rests in the cupped palm of the hand at its initial pose (`hardware/SPECS.md` section 3), U face up, F face toward the fingertips (`TASK.md`); the exact initial state is the observation of step 0.

## Mechanism

- Every cubie can only rotate about the cube centre; the cube has no fixed centre pieces.
- A layer of 4 cubies turns about one of the three axes through the centre. A layer can turn only while the other layers are aligned; one layer may be part-way through a turn at a time.
- A released layer settles back to the nearest aligned position by itself.
- Forcing the cubies more than 15° away from a configuration the mechanism allows jams the cube (`SUCCESS.md`).

Turning resistance and surface properties are not given.

## State Frame (object state `objstate-1`)

The state frame is the frame whose pose and velocities the observation and the feedback report for this object (`CONTRACT.md` section 2, `FEEDBACK.md` section 3).

Object (order): `0 = cube`. Parts (order): `0..7 = cubie0 … cubie7`, all belonging to object 0 (`part_object`).

- **Cube (root) frame:** origin = the cube's centre, defined as the point fixed to cubie 0 at its home offset from the centre (−e/4, −e/4, +e/4 in cubie 0's frame, e = 50 mm edge); in every legal configuration it coincides with the mean of the eight cubie centres. Axes = cubie 0's axes. With the cube solved: +x points to the B face, +y to the L face, +z to the U face; cubie 0 is the D-B-L corner piece. A layer turn that moves cubie 0 turns this frame with it (a 2×2×2 cube has no fixed centre pieces).
- **Cubie frames:** origin = the cubie's centre; axes = the cubie's own axes, aligned with the cube frame when the cube is solved.
- **Home slots** of cubie `j` (solved, in the cube frame, units of e/4): 0 `(+,+,−)`, 1 `(−,+,−)`, 2 `(+,−,−)`, 3 `(−,−,−)`, 4 `(+,+,+)`, 5 `(−,+,+)`, 6 `(+,−,+)`, 7 `(−,−,+)`.
- **`cube_relative_orientation`** `(8, 4)`: each cubie's orientation relative to cubie 0, `q₀⁻¹ ⊗ q_j` `(w, x, y, z)` (row 0 is the identity), sign-continuous over time.
- **`cube_configuration`** `(8,)` int64: for each cubie, the index of the nearest of the 24 cube rotations (largest `trace(Gᵀ R)`) to its relative orientation `R`. The table of the 24 rotations `G` (3 × 3 matrices with entries in {−1, 0, 1}, determinant +1) is sorted lexicographically by the nine row-major entries; index 0 is the first. Solved = every index equal to the identity's index (23). The full table is in `object/rotations24.json`.
- **`scramble`** `(3, 2)`: unchanged meaning (`TASK.md`).
- Feedback adds the complete layer turns, the distance to solved and the mechanism deviation (`FEEDBACK.md` section 1, `measurements`).
