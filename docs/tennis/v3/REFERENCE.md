# Reconstruction Reference (provisional)

**Status: provisional.** This document states what a reconstruction of the human demonstration consists of (the output contract of the Demo-to-Sim stage) and which reconstruction tools are provided to you. It is a contract for the artifacts, not a prescribed method: how you reconstruct, and whether you use the provided tools or your own, is your decision. The contract is modular: every artifact carries a `method` field naming how it was produced, so that a stage can be replaced or added without changing the layout. Two points marked **TODO** await a decision of the maintainers of the target environment; everything else describes what exists today.

## 1. Inputs

The demonstration files and their time bases are listed in `demo/README.md` (an original 30 fps capture, 10.50 s). The object geometry is given: `object/SPECS.md` states the dimensions, mass and mass distribution of `tennis_ball`, and the metric scale anchor (the ball diameter). Reconstructing the object geometry from the video is not required; a reconstruction estimates the object's and the hand's motion in a metric frame.

## 2. Output Contract

A complete reconstruction is a directory with the parts below. Time is always physical time `t_real` in seconds (`demo/README.md`: frame `k` at `t_real = k / 30`). The camera frame is OpenCV (x right, y down, z forward); the reconstruction world frame is the metric world of the hand reconstruction's camera trajectory (the first camera pose defines it; for this demonstration the camera is fixed, so the world frame is the camera frame; a gravity-aligned frame is planned, `transforms/world_frame.json`). Every part carries a `provenance.json` with a `method` field (the tool or your own method), its version, the command line and the input file's SHA-256.

| Part | Files | Contents | Status of the provided tools |
|---|---|---|---|
| Frames and masks | `seg/frames/%05d.jpg`, `seg/masks/<object>/%05d.png`, `seg/objects.json`, `seg/stats.json`, `seg/overlay.mp4` | Decoded frames in display orientation, every frame; binary masks per tracked object (`tennis_ball`) and per hand; per-object visibility statistics; an overlay video | implemented |
| Camera intrinsics | `transforms/moge/intrinsics.json` | Focal length, principal point, field of view, image size, orientation | implemented |
| Hand motion | `hand/<video>/tracks_*/` (hand boxes and handedness per frame), `hand/<video>/SLAM/*.npz` (camera poses per frame, metric scale), `hand/<video>/hawor_world_*.npz` (world-frame hand fits: translation, rotation, pose, shape, validity for two hands), `hand/hand_world.npz`: `t_real` (T,), `joints` (2, T, 21, 3) world-frame keypoints of both hands and their vertices; `hand/<video>/vis_cam/overlay.mp4` | The demonstrator's hand motion per frame and the camera trajectory | implemented |
| Object geometry | `object/SPECS.md` (given: the dimensions, mass and mass distribution; no mesh files are shipped, model the object from the dimensions) ; optionally `object3d/<object>/` a reconstructed shape with its own `method`, if you use a shape model | The known geometry; a reconstructed shape is optional and not required | given |
| Object 6D motion | `pose6d/<object>/traj_world.npz`: `t_real` (T,), `T_world_obj` (T, 4, 4), `quat_wxyz` (T, 4), `valid` (T,), `status` (0 ok, 1 uncertain, 2 occluded, 3 lost), `confidence` (0–1), `iou`, `occlusion_frac`, `depth_locked`, `axis_sign_confidence`, `T_cam_obj`, `method`, `mesh`, `source_video_sha256`; `pose6d/<object>/method.json` (`method`, `status` ok/partial, `note`, `producer`, `mesh`, `frame_convention`, `unobservable`); the tracking tool's own `objects/<object>/` (trajectory, `trajectory_meta.json`, `metrics.json`, `REPORT.md`, `overlay.mp4`, overlay sheets) | The object's pose per frame in the world frame, with validity, status and confidence per frame and the method used; occluded or lost frames carry held or extrapolated poses, so use `valid`, `status` and `confidence` | implemented (known-geometry 6D tracking, section 3) |
| Frames and time | `transforms/camera_intrinsics.json`, `transforms/world_frame.json`, `transforms/time.json` | The world-frame definition and the camera pose of frame 0, the frame-to-time mapping, trimming, and the hand/object synchronization (0 by construction when both come from the same frames) | planned |
| Validation | `hand/<video>/metrics.json` (detection coverage, re-projection agreement of the fitted hands with the hand masks, jitter, handedness, camera-trajectory scale and drift); `metrics/*.json` for the objects (per-frame mask agreement of the re-projected object with the segmentation, hand–object contact consistency, gravity consistency of free flight where the task has one) | What a reconstruction reports about its own quality | hand metrics implemented; object metrics in the tracking tool's `objects/<object>/metrics.json` and `REPORT.md` |
| Comparison videos | `seg/overlay.mp4`, `hand/<video>/vis_cam/overlay.mp4` (+ `vis_cam/tile.jpg`, `vis_cam/stats.json`), `compare/compare.mp4`, `compare/compare.json` | The comparison videos of section 4 | implemented (the three-panel video is being run) |
| Simulation hand-off | `sim/trajectory_<name>.csv` (`t_real, x, y, z, qw, qx, qy, qz` in the world frame), `sim/hand_keypoints.csv` | What your simulator consumes | producible from `pose6d/` and `hand/` (the export is yours) |

Quaternions are `(w, x, y, z)` throughout, as in `CONTRACT.md`; positions in metres. The names `<object>` are those of `object/SPECS.md` (`tennis_ball`).

**TODO (maintainer decision):** whether the reconstruction artifacts are produced by you from the inputs above, or whether a reference reconstruction is delivered with the bundle; and which parts of this contract are required for a submission's research record versus recommended.

## 3. Tools Provided

Only tools that exist are listed as provided; entry points are in `TOOLS.md` section 3.

| Tool | Purpose | Output | Status |
|---|---|---|---|
| Video segmentation (SAM 2.1 video predictor) | Object and hand masks on every frame from a few point prompts on one frame | `seg/` | implemented, verified on all four demonstrations |
| Camera intrinsics (MoGe) | Focal length, principal point and a metric-scale pointmap from single frames | `transforms/moge/intrinsics.json` | implemented, verified on all four |
| Hand motion (HaWoR) | Hand detection and tracking, per-frame hand fits, a masked camera trajectory with metric scale, world-frame hand motion, overlay rendering | `hand/` | installed and running; detection and camera-frame fits verified on all four demonstrations, world-frame stages verified on one and in progress on the others |
| Known-geometry 6D object tracking (render-and-compare v1) | The object's pose per frame by rendering its known geometry (`object/SPECS.md` frame) and comparing with the object and hand masks; depth from the known size and the intrinsics (no depth sensor; no learned pose model); the world frame from the hand reconstruction's camera poses | `objects/<object>/`, exported to `pose6d/` | implemented, verified on all four demonstrations (ball mask agreement median 0.96, 99 % of frames tracked; the ball's orientation is unobservable (reported as identity); free flights fit gravity within 7 % in the camera frame) |
| Comparison video | Three panels: input, hand overlay, 3D view in the reconstruction world with the camera path (objects drawn once `pose6d/` exists) | `compare/compare.mp4`, `compare/compare.json` | implemented, not yet run |
| Object shape model (SAM 3D Objects) | A reconstructed object shape | `object3d/` | optional, **not provided** (gated model weights); the object geometry is the published one |

Known limitations of the tracking tool: monocular depth comes from the known size over the apparent size and scales with the focal length, and the metric scale of the hand reconstruction's world disagrees with it by 10–60 % depending on the clip (reported, not resolved); occluded or lost frames carry held or extrapolated poses (`status`, `confidence`); symmetric objects are tracked on one symmetry branch kept by continuity; hand checks use the wrist position only. Not done: fingertip-level contact checks. Any method of your own is acceptable as long as its artifacts follow section 2 and state their `method`.

**TODO (maintainer decision):** whether you receive the tools themselves (with their environments) or only their outputs for this task's demonstration.

## 4. Comparison Artifacts

A reconstruction is accompanied by comparison videos that show, at the same instants, the input and what was reconstructed from it; they are what the research record publishes next to your target rollouts. All run at real time, 30 fps.

1. `seg/overlay.mp4`: the input video with the object and hand masks overlaid, one colour per object id (`seg/objects.json` maps ids to names).
2. `hand/<video>/vis_cam/overlay.mp4`: the input video with the fitted hand meshes projected on every frame (left hand light blue, right hand orange); `vis_cam/tile.jpg` shows five sampled frames and `vis_cam/stats.json` the rendering statistics. The data the video was rendered from is `hand/<video>/hand_world.npz`.
3. `compare/compare.mp4` with `compare/compare.json` (task, frames, real-time fps, panels, objects shown, the `method` of each part): three panels of equal height (720 px), left to right: the input frame with its time label; the hand meshes projected on the frame; a 3D view of the reconstruction world from a fixed viewpoint with the camera path, the current camera, the hand meshes, and the object meshes at their estimated poses once `pose6d/` exists (until then the panel says `objects: pending`). Nothing is cut; frames without a valid hand fit are shown without a hand.
4. `compare/sim_replay.mp4`: the input video side by side with your simulated replay of the reconstruction (`r2s2r-calib video` makes such a file from two videos).
