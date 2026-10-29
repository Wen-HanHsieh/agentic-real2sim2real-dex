# Object Specification: Pen

The pen is the pen-spinning mod seen in the human demonstration (`demo/`), reconstructed from the video: a long, thin body of revolution with thicker end pieces. Dimensions are the reconstruction's estimates (length ± 0.015 m).

- **Geometry:** Body of revolution, total length 0.195 m. Barrel diameter 0.009 m. Back end: a cap piece 0.0095 m in diameter over the first 14 mm, ending in a rounded dome, with a short 0.0085 m neck where it meets the barrel. Heading end: a grip piece 0.0112 m in diameter from 173 mm to 187 mm, stepping down to 0.0085 m and tapering to the tip at 195 mm.
- **Mass:** 0.022 kg
- **Mass distribution:** Uniform over the body; centre of mass at mid-length. Moments of inertia about the centre: 2.2 × 10⁻⁷ kg·m² about the long axis, 7.3 × 10⁻⁵ kg·m² about any transverse axis.

| Distance from the back end (mm) | 0 | 0.8 | 2.3 | 13.7 | 14.8 | 16 | 171.6 | 172.6 | 187.2 | 188.8 | 194 | 195 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Diameter (mm) | 0 | 7.6 | 9.5 | 9.5 | 8.5 | 9.0 | 9.0 | 11.2 | 11.2 | 8.5 | 2.6 | 0 |

The profile is linear between the listed points. The red tip is a visual marker only; it defines the heading direction used in `SUCCESS.md`.

## Visual Markings (cameras)

Visual only: they change no physical property (mass, inertia, and collision geometry are as above). The demonstration pen is white with grey end pieces and red and blue rings; the target pen carries these markings instead:

- **Blue body:** everything that is not a marking below.
- **Red tip:** the last 18 mm at the heading end.
- **White band:** 8 mm wide at the centre.
- **Roll markers:** two longitudinal stripes along the barrel on opposite sides, each 70° of the circumference: yellow
  and green. They make the pen's rotation about its own long axis visible, so its full 3D orientation and angular
  velocity can be measured from the cameras (`FEEDBACK.md`).
