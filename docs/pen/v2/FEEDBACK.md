# Target Evaluation Feedback

The target environment evaluates each rollout from sensor-observable evidence: three cameras, the robot's joint log, and the public robot and object specifications. Official success criteria are in `SUCCESS.md`. Feedback exists only after the rollout; the deployed policy never receives camera images (`CONTRACT.md`).

## 1. Cameras

Three fixed, synchronized RGB-D cameras (global shutter, 848 × 480, pinhole without distortion):

| View | Perspective |
|---|---|
| `top` | Above the hand |
| `left` | From the hand's left (+Y), nearly level |
| `right` | From the hand's right (−Y) and the fingertip side, elevated |

- **RGB video:** 100 fps, H.264, real time, covering the whole rollout (1,201 frames per view).
- **Calibration:** `calibration.json`: per view `K`, `T_world_cam`, `T_cam_world`; world frame as in `hardware/SPECS.md`; OpenCV camera frame, pixel (0, 0) at the centre of the top-left pixel.
- **Timestamps:** `video/frames.json` gives each frame's time `t` (s since control step 0) and `control_step = round(t × 500)`, the same for all views. Row `s` of `logs/trial_0.npz` is control step `s` (the state measured before the action at `s`).
- **Depth:** 16-bit PNG in 0.1 mm units (0 = no return), noise σ = 1 mm × (z / 0.5 m)², through the `frames ... depth` query only.

## 2. Official Evaluation

`sensor/sensor_report.json`:

| Field | Description |
|---|---|
| `status` | Official result: `success`, `failure`, or `unknown` (rule below and in `status_rule`) |
| `task_status` | The same decision for the task rubric alone |
| `score`, `score_bounds` | Task progress 0–1 (stages: spin-up, sustain, hold) and its uncertainty interval |
| `progress`, `reward` (and `_bounds`) | The same quantity as `score` |
| `stages` | Per-stage scores; per milestone `reached`, `reached_bounds`, `certain`, time |
| `events` | Timestamped observations (rotation milestones, loss of retention) |
| `object_motion` | Measured summary quantities |
| `hardware` | Joint position and speed compliance (measured), action validity, PD torque demand (estimated) |
| `runtime` | `valid` / `invalid`, steps run and expected, policy error, inference time |
| `confidence`, `observability`, `unobservable` | Observed fraction, measurement margins, what cannot be observed |
| `version`, `rubric_version`, `rig_version`, `code_sha256` | Evaluation versions (`REMOTE_API.md` section 7) |

**Status rule:**

- `success`: the score is 1.0 even when every unobservable or near-threshold moment counts against the policy, the hardware is compliant, and the run is valid.
- `failure`: the score is below 1.0 even when all of them count for the policy, a hardware limit is clearly exceeded, or the run is invalid (policy failure or missing steps).
- `unknown`: otherwise; the evidence cannot decide.

**Sensor estimates, not ground truth.** Every value is measured from the cameras and the joint log; the target's internal state is never read or returned. A joint measurement within encoder noise of a limit is `uncertain`; torque is only estimated (`hardware/SPECS.md` section 6). The evaluation reports what happened, not why; diagnosing causes is your task.

## 3. Object Tracking and Segmentation

**Measurements**

| Quantity | How it is measured | Margin |
|---|---|---|
| Pen axis and heading (back end → red tip) | multi-view RGB-D line fit; the red tip gives the direction | – |
| Signed cumulative heading rotation | unwrapped heading from step 0 | 1° |
| Pen centre, horizontal travel, drop | bounded by the visible red tip, white centre band and visible length; when they are hidden the centre is known only within an interval along the axis, used as the worst case in `score_bounds` | 3 mm plus the along-axis interval |
| Centre speed (hold) | derivative of the smoothest centre path consistent with the per-frame intervals (0.1 s window) | 0.005 m/s |
| Tilt of the long axis | from the 3D axis | 1.5° |
| Angular speed (hold) | full 3D orientation from the yellow and green roll markers (0.2 s window); where both markers are hidden, the swing rate of the long axis is only a lower bound | 0.15 rad/s |
| Hand contact | object surface within 4 mm of the robot model at the measured joint angles | gaps 2.5–5.5 mm are uncertain |
| Environment contact | object surface within 3 mm of the floor | gaps 1.5–4.5 mm are uncertain |

A milestone is certain only when the measurement clears the `SUCCESS.md` threshold by the margin; the point score uses the thresholds exactly. An object hidden from all cameras for more than 0.5 s counts as not retained in the point score and as unknown in `score_bounds`. Not observable: contact forces and joint torques; the pen's rotation about its own long axis while both roll markers are hidden (then only a lower bound on its angular speed is known, so a hold milestone can be disproven but not confirmed).

**Object tracks** (`sensor/sensor_tracks.npz`, one row per video frame): `t`, `hand_contact`, `environment_contact` (1 / 0 / NaN), `hand_contact_uncertain`, `environment_contact_uncertain`, `hand_gap_m`, and `pen_axis` (n, 3) unit vector back end → tip, `pen_centre` (n, 3) [m], `pen_speed` (n,) [m/s], `pen_angular_speed` (n,) [rad/s, full 3D, where the roll markers are visible], `pen_swing_rate` (n,) [rad/s, swing of the long axis]. NaN means not observed.

**Segmentation masks** (`masks/<view>.npz`): the `pen` mask of every frame and view, pixel-aligned with the RGB and depth images and indexed like `video/frames.json`. Each is the object's camera-estimated pose rendered with its public geometry, kept where the observed depth agrees within 8 mm; pixels hidden by the hand are excluded. Run-length encoded, with per-frame `valid`, `visible_fraction`, `colour_agreement`, and other fields described in `masks/masks.json`. A mask can be invalid or partly occluded.

## 4. Standard Feedback

Produced and stored after every completed rollout, never changed afterwards. They are not pushed to you; retrieve them with `fetch sNN` (`REMOTE_API.md`).

| File | Contents |
|---|---|
| `feedback.json` | Protocol, task, policy SHA-256, target model version and robot revision, evaluation versions, and the SHA-256 of every file |
| `calibration.json` | Camera intrinsics, extrinsics, conventions, depth model |
| `logs/trial_0.npz` | `joint_names`; measured `q`, `qd`; commanded `q_target`, `qd_target` (6,000 rows) |
| `video/top.mp4`, `video/left.mp4`, `video/right.mp4` | Synchronized RGB videos |
| `video/frames.json`, `video/video.json` | Per-frame time and control step; video metadata |
| `sensor/sensor_report.json` | Official evaluation (section 2) |
| `sensor/sensor_tracks.npz` | Sensor-estimated object tracks and contact (section 3) |
| `masks/top.npz`, `masks/left.npz`, `masks/right.npz`, `masks/masks.json` | Segmentation masks and their encoding (section 3) |

## 5. Optional Queries and Tools

| Command or tool | Use |
|---|---|
| `frames` | RGB frames at any instant of a finished rollout, optionally with depth |
| `masks` | Selected masks as PNG |
| `history`, `note`, `package` | Experiment records, your research notes, exact past packages |
| `r2s2r-maskiou`, `r2s2r-hwcheck`, `r2s2r-harness` | Local tools (`TOOLS.md`) |

None of them changes official results. Syntax and limits: `REMOTE_API.md`.

## 6. Research Use

You may use videos, joint logs, object tracks, masks, and official results to diagnose failures and improve your simulation and policy. Your own diagnostic metrics do not replace the official evaluation.
