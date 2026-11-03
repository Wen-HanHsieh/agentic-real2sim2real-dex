# Reconstruction Reference

This document is the output contract of the Demo-to-Sim stage: what a reconstruction of the human demonstration consists of. Reconstructing the demonstration into these outputs, and validating them, is required before you build your simulator; how you reconstruct is your decision. The default workflow is `demo2sim/RECONSTRUCTION.md`, and the provided tools and models are listed in section 3 and `TOOLS.md` section 2. Use them, replace them or add your own: every artifact states the method that produced it, so any stage can be swapped without changing the layout. No reconstruction of the demonstration is provided: you produce it from the inputs of section 1.

**Time limit:** Complete the entire Demo-to-Sim Stage 1, including reconstruction, hand fitting, validation and output preparation, within the 60-minute wall-clock budget defined in `demo2sim/RECONSTRUCTION.md`. If the deadline is reached with incomplete artifacts or failed checks, preserve the available results and document the failures. Incomplete outputs must not be reported as passing this contract.

## 1. Inputs and Conventions

**Inputs.** The demonstration file and its time base (frame rate, duration, any re-timing) are in `demo/README.md`. The object geometry is given: `object/SPECS.md` states the dimensions, mass and mass distribution of every object of the task (names in `TASK_CONFIG.md` section 3), and `demo/README.md` names the metric scale anchor. Target-environment data (screenshots, rollout records, feedback) describes the robot's environment, not the demonstration, and is not ground truth for the reconstruction.

**Conventions.** Units: metres, seconds, radians. Rotations are right-handed. Quaternions are (w, x, y, z). A pose `T_a_b` is the 4 × 4 homogeneous transform that maps coordinates in frame b to frame a (`p_a = T_a_b · p_b`).

- **Frame index k.** Frame k (from 0) of the demonstration file. Every per-frame output covers every frame, in order, including frames where nothing could be estimated (marked invalid).
- **Time.** `t_real = k / 30` for every task: the real-time frame rate is 30 fps (`demo/README.md` states any re-timing of the file). Hands and objects are synchronised: the same k is the same instant.
- **Image.** The demonstration's pixel grid in display orientation at its native resolution. Pixel (u, v): u right, v down, (0, 0) the centre of the top-left pixel.
- **Camera frame.** OpenCV: origin at the optical centre, x right, y down, z forward. Pinhole intrinsics `K = [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]` on the image grid; state the distortion model (none = ideal pinhole).
- **World frame W.** One metric frame for the hands and the objects, fixed in the scene: origin at the camera's optical centre at frame 0; +z up, opposite to gravity as you estimate it (gravity is (0, 0, −9.81) m/s² in W); +x the frame-0 viewing direction projected on the horizontal plane; +y = z × x. If the camera moves, W stays attached to the frame-0 camera pose and `T_world_cam` varies per frame. (The world frame of `hardware/SPECS.md` belongs to the robot's environment; it is not this frame.)
- **Object frame.** The object's state frame of `object/SPECS.md`. Where the demonstration object does not show a feature that defines an axis, choose a frame consistent with the stated origin and geometry, and list the unobservable rotations.
- **Hands.** left and right are the demonstrator's anatomical hands as seen in the video; a hand is never mirrored. Hand geometry is the MANO model: 778 vertices, 1538 faces, 21 joints in OpenPose order (wrist; then thumb, index, middle, ring, little, each from the base to the tip).
- **Labels.** For every quantity you output, label how it was obtained: measured (read directly from the video, e.g. masks, timestamps), estimated (fitted to observations, e.g. poses, a fitted focal length), inferred (derived from priors, assumptions or physical reasoning, e.g. an assumed focal length, contact under occlusion) or unobservable (not determined by the video, e.g. the spin of an unmarked sphere, a pose while fully hidden). Never fill an unobservable quantity with invented motion: use `valid = false` or an explicit status instead.

## 2. Output Contract

A reconstruction is one directory `<recon>`. Required parts must exist and pass `tools/recon/check_reference.py <recon> --task-dir <task bundle> --video <demonstration file>`; recommended parts are additional artifacts that support the default workflow. Every required part directory has a `provenance.json`: method (tool or your own method), command, inputs (paths with SHA-256), and the code version.

| Part | Files | Contents | Status |
|---|---|---|---|
| Manifest | `reconstruction.json` | `schema = reconstruction/1`, task, demo (file, sha256, frames, fps_file, fps_real, retime_factor, image_size), objects (the names of `TASK_CONFIG.md` section 3), articulated (object → part names, `TASK_CONFIG.md` section 3), demo_hands (the demonstrator's hand(s) seen in the video: left, right or both) | required |
| Notes | `<recon>/NOTES.md` | Decisions and their reasons; what is measured, estimated, inferred or unobservable; known failures and their frames; the explanation of every validation warn or fail | required |
| Scene analysis | `analysis/analysis.json` | `scene.analysis/v1` (`demo2sim/RECONSTRUCTION.md`, Scene analysis): events with frames, participants, relations and their checks; objects with type, structure, relations, parameters and how they are modelled | required |
| Camera | `transforms/camera_intrinsics.json`, `transforms/camera_poses.npz` | K (3 × 3), image_size, distortion, labels (focal, principal_point); T_world_cam (T, 4, 4) per frame, with zero translation at frame 0 (the origin of W); optional per-frame K (T, 3, 3) | required |
| World frame | `transforms/world_frame.json` | definition, gravity_cam0 (unit gravity direction in the frame-0 camera), camera_static, metric_scale_source (what fixed the metric scale), labels (gravity, camera_motion, metric_scale) | required |
| Time | `transforms/time.json` | fps_real, retime_factor, t_real (the mapping), frames, synchronisation offsets (0 when hands and objects come from the same frames) | required |
| Object geometry | `objects/<object>/geometry.json` + mesh | source (specs_model: modelled from `object/SPECS.md`; provided: a provided model; reconstructed), mesh (metric, object frame; watertight if you can), frame_matches_specs (+ frame_note), scale_source; articulated objects normally add part_meshes, except for the Cube Stage 1 exception below | required |
| Object 6D motion | `pose6d/<object>/traj_world.npz`, `pose6d/<object>/method.json` | frame, t_real (T); T_world_obj, T_cam_obj (T, 4, 4); quat_wxyz (T, 4); valid (T, bool); status (T: 0 estimated from the frame, 1 estimated but uncertain, 2 not visible: held or interpolated, 3 lost, −1 not estimated); confidence (T, [0, 1]); std_trans_mm, std_rot_deg (T: the 1-σ uncertainty, combined over the three axes); importance (T, [0, 1], required). method.json: method, unobservable (pose components), labels (translation, rotation, …) | required |
| Articulation | `articulation/<object>.npz`, `articulation/<object>.json` | The part states of an articulated object of `TASK_CONFIG.md` section 3, if you reconstruct them: part_T_world (T, P, 4, 4), part_valid (T, P), part_confidence (T, P); parts, reconstructed (true), events (the detected articulation changes, e.g. part rotations {k0, k1, axis, quarter_turns}), labels (part_state); mark unresolved frames invalid and say why. Not required: the object's 6D motion above is the required part for every object, articulated or not. When present it must be complete (part_T_world for every part, reconstructed true, events) and is checked | optional |
| Hand motion | `hand/hand_world.npz`, `hand/method.json` | In W: t_real (T); sides = [left, right]; joints (2, T, 21, 3); vertices (2, T, 778, 3); faces (1538, 3); wrist_T_world (2, T, 4, 4); valid (2, T); confidence (2, T); MANO parameters mano_global_orient (2, T, 3), mano_hand_pose (2, T, 45), mano_betas (2, 10), mano_transl (2, T, 3), mano_scale (2). method.json: method, validity_rule, mano_convention, labels (joints, wrist_pose, shape, scale). The demonstrating hand(s) must have valid frames; an absent hand retains its slot but is marked invalid | required |
| Hand–object interaction | `interaction/contacts.json` | method; phases: {hand, object, frames: [k0, k1] (inclusive), t_real, label, evidence} for every contact of every hand with every object | required |
| Validation | `validation/report.json` | The output of `tools/recon/validate_reconstruction.py`: every check of section 4 with its status (pass, warn, fail, not_applicable), numbers and flagged frames | required |
| Comparison video | `compare/compare.mp4`, `compare/compare.json` | The demonstration and the reconstruction side by side at real time, frame k beside frame k (section 4) | required |
| Simulation scene | `scene/scene.xml`, `scene/replay.json`, `scene/replay_iou.json` | MuJoCo scene of the demonstration and the per-frame joint values that replay it (`demo2sim/RECONSTRUCTION.md`, section 5), with per-frame replay IoU against the reconstruction's segmentation masks | required |
| Segmentation | `seg/masks/<object>/%05d.png`; hands as objects named `hand_left`, `hand_right` | Binary masks per object and hand (used by the validation's image checks) | recommended |
| Physics | `physics/<object>.json` | mass_kg, com_m, inertia_com_kgm2, friction, restitution, dominant_material, size_m; values supplied by `object/SPECS.md` must be preserved, and other values labeled as inferred or estimated | required |
| Simulation hand-off | `sim/` | What your simulator consumes, produced from pose6d/ and hand/ (and articulation/ where you provide it) | optional |

**Cube Stage 1 exception.** For the Cube task, whole-cube rigid-body geometry and per-frame 6D motion are sufficient for Demo-to-Sim. Individual cubie trajectories, cubie part meshes, and articulated layer-turn reconstruction are not required. The `articulated` manifest field still records the cubie names specified by `TASK_CONFIG.md`; this does not make articulation reconstruction mandatory. The Stage 2 training simulator must support the articulated Cube mechanics defined in `object/SPECS.md`.

**Segmentation and image validation.** The default `seg/masks/` layout is recommended, but the required image-agreement checks must have access to the masks used for evaluation, either through this layout or through an explicitly supported validator input. The absence of saved masks does not waive required validation. If the available implementation cannot validate image agreement, report the check as incomplete rather than passing it.

**Pose importance.** Every `pose6d/<object>/traj_world.npz` must include an `importance` array with one value in [0, 1] for each frame. Importance is task-dependent: contact-rich events and task-critical free-space motion, including ball flight during tossing, may receive high importance. Define the scoring convention in `<recon>/NOTES.md`.

**Reproducibility.** `reconstruction.json` and the `provenance.json` files must let someone else rerun each stage: the commands, the input files and their SHA-256, the tool versions (the reconstruction environment's `manifest.json` checksum when you use it) and every non-default setting.

## 3. Tools and Models Provided

The tools are scripts under `tools/recon/`, the read-only installed copy (`$R2S2R_RECON_HOME/tools/recon`; your workspace's `tools/recon` links to it), and run in the pre-installed, read-only reconstruction environment (`source $R2S2R_RECON_HOME/env.sh`; versions and checksums in `$R2S2R_RECON_HOME/manifest.json`). Entry points, inputs and outputs: `TOOLS.md` section 2.

| Tool | Purpose | Output |
|---|---|---|
| `frames.py` | Frames of the demonstration on its display-orientation grid | `%06d.jpg`, `frames.json` |
| `sam3_seg.py` (SAM 3) | Object and hand masks on every frame from text (and optional box) prompts; every hand instance kept | masks per prompt |
| `sam2_video_seg.py` (SAM 2.1) | Object and hand masks propagated through the video from a few point prompts | `seg/` |
| `moge_intrinsics.py` (MoGe) | Focal length and metric pointmaps from single frames | `transforms/moge/` |
| `camera_calib.py` | Focal length and pose from 2D–3D correspondences of known geometry, focal sensitivity, camera rotation from background flow, the world frame W | `transforms/` |
| `pose_track.py` | 6D tracking of a rigid object of known geometry from its masks | per-frame poses |
| `objpose_track.py`, `objpose_validate.py` | Known-geometry render-and-compare 6D tracking in the camera frame (`T_cam_obj`; pair it with `transforms/` for `T_world_obj`, as `pose_track.py` does) and its checks | `objects/<object>/` |
| `hawor_cam.py` (hand detector + HaWoR) | Hand detection and HaWoR hand initialisation in the camera frame with your intrinsics | `hawor_cam.npz` |
| `mano_fit/` | The MANO hand fit against your object scene (`handlib/fit.py`, `score.py`, `views.py`; README) | fit result |
| `handfit_inputs.py`, `handfit_export.py` | Builds the fit's input folder from your reconstruction; writes `hand/` with the validity rule | `hand/` |
| `render_compare.py` | The comparison video | `compare/` |
| `validate_reconstruction.py` | The validation of section 4 | `validation/` |
| `check_reference.py` | The format check of section 2 | findings |
| `export_reference.py` | Converts the per-task file layout of the default workflow into this layout | `<recon>` |
| `build_viewer.py` | A local interactive 3D viewer of hands, objects and fingertip distances, synchronised with the video | static web page |

Models: SAM 3, SAM 2.1, MoGe, HaWoR with its hand detector, MANO (left and right) and Blender 4.2 LTS with headless `bpy`. Nothing in the tools contacts a remote service.

## 4. Validation and Comparison

**Validation (`validation/report.json`, required).** Run `validate_reconstruction.py` on the finished reconstruction; explain every warn and fail in `<recon>/NOTES.md`. The checks: reprojection of objects and hands against your masks; fingertip-to-object distances in every contact phase; anatomical plausibility of each grasp (the thumb and an opposing finger in contact, on opposite sides of the object); hand–object intersection depth; finger–finger and hand–hand intersection; temporal continuity (jumps, speeds, bone flips); gravity in free flight, drift and sinking at rest; handedness and hand size; synchronisation of the time base, the comparison video and the projected objects; the calibrated focal length against a monocular prior (a disagreement above 1.25× is flagged: monocular intrinsics are a prior, not a calibration). A small intersection depth or a high mask IoU never counts as correct contact on its own: a contact phase is supported only when fingers touch the object as the video shows.

For Cube Stage 1, validate the reconstructed whole-cube motion and its hand interactions without requiring per-cubie articulation outputs. If optional articulation data is supplied, validate it under the existing articulation contract.

**Comparison video (`compare/compare.mp4`, required).** Three panels of equal height at real time: the demonstration frame with its time label; the reconstruction rendered from the reconstructed camera (objects at their poses and MANO hands; nothing drawn where a pose is invalid); the reconstruction over the demonstration. `compare.json` lists the panels, the frames, the frame rate, the objects and hands shown and the method of each part. `render_compare.py` writes both.

**Viewer.** `build_viewer.py` writes a local 3D viewer (hands, objects, fingertip distances and continuity flags per frame, synchronised with the video) for inspecting your reconstruction.

**Deadline and validity.** The 60-minute Stage 1 limit does not lower validation standards. If the deadline is reached with missing required artifacts, uncompleted checks or failed validation, the agent must report the available evidence and unresolved requirements. It must not claim that the reconstruction passed the output contract.
