# Object Specification: 2×2×2 Cube

The cube is the 2×2×2 puzzle seen in the human demonstration (`demo/`), reconstructed from the video; the edge length is the reconstruction's estimate (± 0.006 m).

- **Geometry:** Cube, edge 0.050 m, made of 8 corner cubies on a 0.025 m pitch. Each cubie is a 0.0246 m cube (0.2 mm gap on every cubie face) with its edges and corners bevelled by 1.5 mm; the three outward faces carry square stickers 19.6 mm on a side, 0.2 mm proud of the face, leaving a black border around each sticker. Contact geometry: the 0.0246 m cubie cubes.
- **Mass:** 0.060 kg; 8 equal cubies, uniform
- **Colours (solved):** U white, D yellow, F green, B blue, R red, L orange (`TASK.md`); black cubie bodies. The demonstration cube uses the same standard scheme.

## Mechanism

- Every cubie can only rotate about the cube centre; the cube has no fixed centre pieces.
- A layer of 4 cubies turns about one of the three axes through the centre. A layer can turn only while the other layers are aligned; one layer may be part-way through a turn at a time.
- A released layer settles back to the nearest aligned position by itself.
- Forcing the cubies more than 15° away from a configuration the mechanism allows jams the cube (`SUCCESS.md`).

Turning resistance and surface properties are not given.
