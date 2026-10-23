# Object Specification: Pen

- **Geometry:** Capsule (cylinder with hemispherical ends), total length 0.140 m, diameter 0.009 m
- **Mass:** 0.010 kg
- **Mass distribution:** Uniform, centered; both ends identical

The red tip is a visual marker only; it defines the heading direction used in `SUCCESS.md`.

## Visual Markings (cameras)

Visual only: they change no physical property (mass, inertia, and collision geometry are as above).

- **Red tip:** the last 18 mm at the heading end.
- **White band:** 8 mm wide at the centre.
- **Roll markers:** two longitudinal stripes along the barrel on opposite sides, each 70° of the circumference: yellow
  and green. They make the pen's rotation about its own long axis visible, so its full 3D orientation and angular
  velocity can be measured from the cameras (`FEEDBACK.md`).
