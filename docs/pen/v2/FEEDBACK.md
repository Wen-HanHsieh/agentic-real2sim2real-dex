# Feedback Protocol v2: Cameras, Sensor Verifier, Records

Task: Pen Spinning. Everything in this document describes data returned by `fetch`, `frames` and `history`
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
- **Video:** 100 fps, H.264, real time, covering the whole policy phase.

## 2. Sensor-based verifier (`sensor/sensor_report.json`)

A deterministic program scores the trial against `SUCCESS.md` using only the camera frames, your robot log
(`logs/trial_0.npz`), the public robot model and mount (`hardware/`) and the object's public dimensions
(`object/SPECS.md`). It never reads simulator state. Fields:

| Field | Meaning |
|---|---|
| `status` | `success`, `failure` or `unknown` (rule in `status_rule`) |
| `score`, `score_bounds` | total progress 0–1 (`SUCCESS.md` stages: spin-up, sustain, hold); the interval covers moments that could not be observed and measurement error near thresholds |
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

- **Measured:** joint positions and speeds against the URDF limits exactly as published (`hardware/SPECS.md`); no
  tolerance is added. Each gets one of three decisions from the documented encoder noise (σ 0.002 rad, 0.05 rad/s):
  `violation` if a measured value, or the mean of 10 or 50 consecutive measured values, lies beyond a limit by more than
  k·σ/√window; `compliant` if every measured value lies inside by more than k·σ; otherwise `uncertain` (the joint was within
  measurement noise of a limit). k (in the report) makes a wrong clear decision at most 1 % likely over all joints, steps
  and windows. A clear violation makes the trial status `failure`; an uncertain decision makes it at best `unknown`.
- **Estimated:** torque. Nothing measures torque on this hand; `estimated.joint_torque_demand` applies the PD law of
  `hardware/SPECS.md` to the measured state and your commanded targets. Above the effort limit the motor saturates, so this
  is a demand, not a measured torque.

## 3. What is measured, and how

The margin is how far a measurement must clear a `SUCCESS.md` threshold before the score interval treats the milestone
as certain (`observability.tolerances`); the point score uses the thresholds exactly.

| Quantity | How | Margin |
|---|---|---|
| Pen axis and heading (back end to red tip) | multi-view RGB-D line fit; the red tip gives the direction | - |
| Signed cumulative heading rotation | unwrapped heading from step 0 | 1 deg |
| Pen centre, horizontal travel, drop | from the tip band and the known 140 mm length | 3 mm |
| Tilt of the long axis | from the 3D axis | 1.5 deg |
| Centre speed (hold) | time derivative of the centre (0.1 s window) | 0.005 m/s |
| Angular speed (hold) | not fully observable: rotation about the pen's own long axis cannot be seen; the swing rate of the long axis is a lower bound | a swing rate ≥ 0.6 rad/s proves 'angular speed < 0.5 rad/s' fails; otherwise the condition is unknown |
| Hand contact | object surface within 4 mm of the robot model at the measured joint angles | gaps 2.5–5.5 mm count as uncertain |
| Environment contact | object surface within 3 mm of the floor | gaps 1.5–4.5 mm count as uncertain |

Not observable: the cell's internal validity checks; contact forces; joint torque; for the pen, rotation about its own long
axis (so its hold milestones can be disproven but not confirmed, and a sensor `success` cannot be concluded for the pen).
An object hidden from all three cameras for longer than 0.5 s is treated as not retained in the point estimate and as
unknown in the interval. The point score credits only what was observed; `score_bounds` gives the range.

`sensor/sensor_tracks.npz` holds the per-frame tracks: `t`, `hand_contact`, `environment_contact`,
`hand_contact_uncertain`, `environment_contact_uncertain`, `hand_gap_m`, and pen_axis (n,3) unit vector back->tip, pen_centre (n,3) [m], pen_speed (n,) [m/s], pen_swing_rate (n,) [rad/s]. NaN means not observed.

## 4. Frame queries

`frames sNN <view|all> <t1,...> [depth]` returns PNG frames rendered by the same cameras at any instant of the trial
(nearest 1 ms), with `frames/frames.json` giving the exact time and control step. Use it to inspect moments between video
frames, to get depth, or to check events reported by the verifier.

## 5. Experiment records

`history` keeps an immutable record of every submission (package, archive and feedback SHA-256; state; sensor summary)
and your `note` entries (hypothesis → change → evidence → decision, diagnostic or improvement, with your own local-simulation
result if you provide one), so you can compare local predictions with SuperDex observations across iterations.
Feedback bundles of finished submissions never change.
