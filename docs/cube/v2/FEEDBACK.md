# Feedback Protocol v2: Cameras, Sensor Verifier, Records

Task: One-handed 2x2x2 Rubik's Cube Solving. Everything in this document describes data returned by `fetch`, `frames` and `history`
(`REMOTE_API.md`). The policy's observation and action interface (`CONTRACT.md`) is unchanged.

## 1. Cameras

Three fixed, hardware-synchronized RGB-D cameras (global shutter, 848 × 480, pinhole without distortion,
D405-class depth). All three views show the same instant in frame k.

| View | Purpose |
|---|---|
| `top` | from above: contacts on the palm side, headings, rotations about +Z, the cube's U face |
| `left` | from the hand's left (+Y), nearly level: heights, toss trajectory, grasp and fingers |
| `right` | from the hand's right (−Y) and the fingertip side, elevated: complementary view for 3D pose |

`calibration.json` gives, per view, `K` (3×3), `T_world_cam` (camera → world) and `T_cam_world`, plus:

- **World frame:** `hardware/SPECS.md` (X forward, Y left, Z up, metres).
- **Camera frame:** OpenCV (x right, y down, z forward); pixel (0, 0) is the centre of the top-left pixel.
- **Time:** `t` in seconds since control step 0; `control_step = round(t × 500)`; `video/frames.json` lists both per frame.
- **Depth:** z along the optical axis; 16-bit PNG in 0.1 mm units in frame queries, 0 = no return; noise σ = 1 mm × (z / 0.5 m)².
- **Video:** 25 fps, H.264, real time, covering the whole policy phase.

## 2. Sensor-based verifier (`sensor/sensor_report.json`)

A deterministic program scores the trial against `SUCCESS.md` using only the camera frames, your robot log
(`logs/trial_0.npz`), the public robot model and mount (`hardware/`) and the object's public dimensions
(`object/SPECS.md`). It never reads simulator state. Fields:

| Field | Meaning |
|---|---|
| `status` | `success`, `failure` or `unknown` (rule in `status_rule`); `task_status`: the same for the task alone |
| `score`, `score_bounds` | total progress 0–1 (`SUCCESS.md` stages: first turn, turning, solving, hold); the interval covers moments that could not be observed and measurement error near thresholds |
| `progress`, `reward` (+ `_bounds`) | the same quantity as `score`: the official per-trial progress and reward |
| `confidence` | 0–1: observed fraction × (1 − interval width) |
| `stages` | per-stage score and score bounds; every milestone: reached (point), `reached_bounds`, `certain`, time, label |
| `unobservable` | quantities in `SUCCESS.md` that the sensors cannot observe for this task, and what that means for the score |
| `events` | timestamped observations (release, landing, rest, rotation milestones, layer turns, loss of retention, ...) |
| `object_motion` | measured summary quantities (see §3) |
| `hardware` | `measured` (joint positions and speeds vs the URDF limits) and `estimated` (torque demand from the PD law) |
| `runtime` | steps run vs expected, finite actions, policy errors, inference time |
| `observability` | frames, visibility fractions, margins used (`tolerances`), and what is not observable |
| `version`, `rubric_version`, `rig_version`, `code_sha256` | exact versions; identical inputs give identical reports |

Status rule: `success` only if the score is 1.0 even when every unobservable or near-threshold moment counts against the
policy, hardware is compliant and the run is valid; `failure` if the score is below 1.0 even when they all count for it,
or a hardware limit is measurably exceeded, or the run is invalid; otherwise `unknown`.

The verifier states what happened, never why. It is an independent sensor reading, not the cell's internal judgement:
official success remains as defined in `SUCCESS.md` (score 1.0 with every physical, hardware and runtime requirement in
every required trial), and the cell's internal validity checks have no sensor equivalent.

### Hardware

Judged by the authoritative rules of `hardware/SPECS.md` section 6 (`hardware/hardware_spec.json`) with the same code as
`HARDWARE_CHECK.md`, applied to your robot log:

- **Measured:** joint positions (against the URDF limits with the published 0.02 rad allowance) and joint speeds. Each gets
  `violation`, `compliant` or `uncertain` from the documented encoder noise (σ 0.002 rad, 0.05 rad/s): `violation` if a
  measured value, or the mean of 10 or 50 consecutive values, lies beyond a limit by more than k·σ/√window; `compliant` if
  every value lies inside by more than k·σ; otherwise `uncertain`. A clear violation makes the trial status `failure`; an
  uncertain decision makes it at best `unknown`.
- **Commanded:** action validity (finite, correctly shaped; targets outside the limits are clipped).
- **Estimated:** torque demand. Nothing measures torque on this hand; `estimated.joint_torque_demand` applies the PD law of
  `hardware/SPECS.md` to the measured state and your targets. Above the effort limit the actuator saturates: reported,
  not a violation (the applied torque never exceeds the limit on the target).

## 3. What is measured, and how

The margin is how far a measurement must clear a `SUCCESS.md` threshold before the score interval treats the milestone
as certain (`observability.tolerances`); the point score uses the thresholds exactly.

| Quantity | How | Margin |
|---|---|---|
| Sticker colours and cubie orientations | colour segmentation, 3D sticker planes, cube model with one moving layer | - |
| Layer turns (which layer, direction, angle) | continuous layer angle; a turn is complete when the turned layer is stably aligned (within 10°, moving less than 5°) for 0.1 s, so a continuous half turn is one turn | one frame (40 ms) |
| Cube state and distance to solved | tracked from the scramble you are given; distance to solved is read only at settled, aligned states | - |
| Cube centre and drop | from the identified cubies | 3 mm |
| Mechanism deviation (jam) | orientation residuals of cubies seen with two or more stickers | values within 4 deg of the 15 deg limit are uncertain |
| Hand contact | object surface within 4 mm of the robot model at the measured joint angles | gaps 2.5–5.5 mm count as uncertain |
| Environment contact | object surface within 3 mm of the floor | gaps 1.5–4.5 mm count as uncertain |

Not observable: the cell's internal validity checks; contact forces; joint torque; for the pen, its rotation about the
long axis while both roll markers are hidden (then only a lower bound on its angular speed is known).
An object hidden from all three cameras for longer than 0.5 s is treated as not retained in the point estimate and as
unknown in the interval. The point score credits only what was observed; `score_bounds` gives the range.

`sensor/sensor_tracks.npz` holds the per-frame tracks: `t`, `hand_contact`, `environment_contact`,
`hand_contact_uncertain`, `environment_contact_uncertain`, `hand_gap_m`, and cube_centre_z (n,) [m], aligned (n,), distance_to_solved (n,), solved (n,), layer_angle_deg (n,), layer_axis (n,), mechanism_deviation_deg (n,), state_key (n,) opaque state id. NaN means not observed.

## 4. Segmentation masks (`masks/`)

For every frame and view, the object's pixels in that camera image, derived from the cameras: the object's
camera-estimated 3D pose rendered with its public geometry, kept where the observed depth agrees with the model
surface (within 8 mm). Pixels hidden behind something nearer (fingers) are not part of the mask. Masks are pixel-aligned
with the RGB and depth images of the same view and share `video/frames.json` timestamps.

`masks/<view>.npz`: `rle_counts`, `rle_offsets` (mask k = run lengths `counts[offsets[k]:offsets[k+1]]` over the
row-major H × W image, alternating background/object, starting with background), `frame_index`, `t`, `control_step`,
`valid` (a camera pose estimate existed), `area`, `model_area` (unoccluded silhouette), `visible_fraction`,
`colour_agreement`, `occluded_px`, `shape`, `label`. The `masks` command returns selected frames as PNG.

## 5. What a submission returns, and what is on request

| Information | Returned automatically by `fetch` | On request |
|---|---|---|
| RGB video, three views | `video/*.mp4` | single frames: `frames` |
| Depth | – | `frames ... depth` (16-bit PNG, 0.1 mm) |
| Joint positions and velocities, measured | `logs/trial_0.npz` (`q`, `qd`) | – |
| Submitted actions | `logs/trial_0.npz` (`q_target`, `qd_target`) | – |
| Execution result, runtime diagnostics | `sensor_report.json` `runtime`; `status` command | – |
| Task success / failure / unknown | `sensor_report.json` | `history` |
| Reward and progress, stage scores, uncertainty | `sensor_report.json` | `history` (summary) |
| Events, hardware (measured / estimated), confidence | `sensor_report.json` | – |
| Segmentation masks | `masks/*.npz` | selected frames: `masks` |
| Perceived object tracks | `sensor/sensor_tracks.npz` | – |
| Calibration, timestamps | `calibration.json`, `video/frames.json` | – |
| Your package, records, best policy | – | `package`, `history`, `note`; `r2s2r-harness` |

Timestamps: frame k of every view, every mask k and `control_step` k describe the same instant; log row s is control
step s (the action at s and the state measured before it); the last frame is the state after the last logged step.

## 6. Frame queries

`frames sNN <view|all> <t1,...> [depth]` returns PNG frames rendered by the same cameras at any instant of the trial
(nearest 1 ms), with `frames/frames.json` giving the exact time and control step. Use it to inspect moments between video
frames, to get depth, or to check events reported by the verifier.

## 7. Experiment records

`history` keeps an immutable record of every submission (package, archive and feedback SHA-256; state; sensor summary)
and your `note` entries (hypothesis → change → evidence → decision, diagnostic or improvement, with your own local-simulation
result if you provide one), so you can compare local predictions with SuperDex observations across iterations.
Feedback bundles of finished submissions never change.
