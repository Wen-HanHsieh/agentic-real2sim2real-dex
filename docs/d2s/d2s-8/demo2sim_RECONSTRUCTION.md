# Reconstruction Workflow (Demo-to-Sim, Stage 1)

This document is the default workflow for reconstructing your task's demonstration into the outputs of `REFERENCE.md`. It is the starting point, not an immutable algorithm: you may change any step, replace any tool or add your own, as long as the outputs and the validation of `REFERENCE.md` are delivered and every deviation is recorded with its reason. The tools and models it names are pre-installed (`TOOLS.md` section 2). When something is ambiguous, decide, and record the decision and the reason in `<recon>/NOTES.md` (`<recon>` is the reconstruction directory of `REFERENCE.md`).

**Time:** Stage 1 lasts the full **60 minutes of wall-clock time**, including scene analysis, reconstruction, hand fitting, validation and output preparation. Use all of it: record the first VALID reconstruction, then keep refining its weakest parts (for example hand–object contact, depth, object pose and invalid frames) and record each better version. If any requirement remains incomplete at the deadline, deliver the available artifacts and explicitly document the missing work and validation failures. Do not fabricate results or claim completion.

## The task

Reconstruct and track the objects and the hands in your task's demonstration video, and turn them into simulation-ready assets:

1. **Understand the scene.** From the video, work out what happens in each sub-event, which objects and hands take part, how they must move relative to each other, and what kind of physical thing each object is, how it is built and how it is attached to or rests on the others (see Scene analysis, below). The reconstructed dynamics scene (geometry, parts, joints, physical properties) and its motion must agree with your answers.
2. Reconstruct and track every object involved in the manipulation, including objects that take part passively, such as a table under an object.
3. Reconstruct the hands in 3D on every frame where they are visible, with the hand-fitting method of section 3, against your object scene.
4. **A physically sensible kinematic reference.** The tracked poses and joint values over the clip (`scene/replay.json`, `pose6d/<object>/`) are the scene's kinematic reference. It must match the video (replay IoU against your own masks) and also obey your common-sense understanding of each event (section Scene analysis). Don't raise the IoU with motion that could not happen: an object that jumps, spins or changes size between frames, a resting object that sinks into or floats above its support, an object that should stay still but drifts, a piece that moves before it has been separated or stops following what carries it, an object in free flight that does not follow gravity, or objects and hands that pass through each other. Where the masks and common sense pull apart, model the motion that really happened, keep the IoU about the same (slightly lower is acceptable), and record the trade-off in the analysis.
5. Estimate each object's physical properties and export simulation models (real2sim).
6. For every tracked pose, give its uncertainty and an importance score between 0 and 1 for how crucial that pose is to the task's success. Importance depends on the task: contact-rich interactions and task-critical free-space motion, such as object flight during tossing, may both be highly important.
7. Each task is one scene. All objects and hands of a task share one world frame and one metric scale, and every fit is judged on all of them together: which object occludes which, which rests on which, and whether anything passes through anything else. A result that matches each object's silhouette on its own but puts objects or hands at inconsistent depths or scales scores poorly. A single still camera cannot separate an object's size from its distance; the known object dimensions (`object/SPECS.md`), the support surface, the contacts between objects and hands and the objects' plausible real-world sizes are what pin that down.

**Cube exception (Stage 1):** Demo-to-Sim reconstruction does not require recovering individual cubie rotations or reconstructing the cube's layer-turn mechanism from the video. Reconstruct the observable whole-cube motion and hand interactions. The Stage 2 training simulation must separately support the articulated cube mechanics specified in `object/SPECS.md`.

Blender is your modelling tool; the rest of the object method is yours. Build and edit every object's model in Blender. Tools for segmentation, camera calibration, 6D tracking, rendering and validation are provided (`TOOLS.md` section 2); use them, combine them with your own code, or design the rest of the pipeline yourself (segmentation, cameras, pose estimation and tracking, optimisation). You may use open-source code and pretrained models from the internet (section 2).

The hands use a given method. `tools/recon/mano_fit/` (read its `README.md`) is a MANO hand-pose optimisation: initialised from HaWoR, it fits the visible hand(s), jointly when multiple hands are present, over all frames to 2-D hand masks, HaWoR's relative articulation, a pose prior, temporal smoothness and hand–object terms against your MuJoCo object scene. You produce its inputs from the video (frames, cameras, hand masks, a HaWoR run, your object scene posed per frame, contact events from your analysis) and run `handlib/fit.py` (section 3).

The rules below fix the remaining details.

## Scene analysis

Before you build anything, watch the video (frame by frame where things happen fast) and write `<recon>/analysis/analysis.json` in the format below. It answers four questions for every sub-event of the clip:

1. **What happens?** Split the clip into sub-events, each one physical event: a grasp, a lift, a carry, a throw, a capture in the hand, a turn, a regrasp, a placement, a release. Give each its video frames.
2. **Which objects and hands take part?** Every object, part or hand that moves, touches, holds, supports or is acted on in that sub-event, and what acts on each object.
3. **Is their relative motion physically sensible?** State how the participating objects and hands must move relative to each other in this event: what stays attached and what separates (and when), what rests on what, what slides along or turns about what, what stays still, what is in free flight. Then check your kinematic reference against that. Where it disagrees with the video or with common sense, fix it (geometry, part structure, per-part poses, hand fit) until it agrees, keeping the replay IoU about the same (matching it is enough; slightly lower is acceptable), and record each fix with the IoU before and after.
4. **What kind of physical thing is each object?** Its physical type (rigid, articulated, cut into pieces, pressed in, screwed on or off, soft, flowing or granular, a container, fixed), its structure (its parts and how they are joined or attached to each other), its physical relations to the other objects and the hands (rests on, stands in, is held by, is attached to, leans against), and the hidden parameters the video implies (material, mass, friction). Infer them from what the video shows and `object/SPECS.md`, and say how your scene models each one (parts, joints, collision geometry, physical properties).

The analysis is your plan, and your reconstruction must follow it: the scene and its kinematic reference must make your answers to 3 and 4 true, subject to the Cube Stage 1 exception above.

Iterate until the reconstruction satisfies the analysis, then keep improving it until the 60 minutes are over. Check every relation of question 3 in the kinematic reference (the poses along the clip do what the relation says, on every frame), and every object answer of question 4 in `scene.xml` (the parts, joints and collision geometry exist; a short MuJoCo simulation of a resting object leaves it resting, nothing starts interpenetrating). Where a check fails, change what causes it and check again, keeping the replay IoU about the same. Record each check's result and evidence in the analysis. If a check cannot be made to pass, say why and what the scene does instead.

Write the analysis first, keep it up to date as you learn more, and log what changed and why. Its final version must describe the delivered scene.

```json
{
  "schema": "scene.analysis/v1",
  "events": [{
    "id": "ev1",
    "frames": [0, 32],
    "what": "what happens, in one or two sentences",
    "acted_on_by": "what moves the objects in this event (a hand, gravity)",
    "objects": ["<object>", "<object>__<part>", "right_hand"],
    "relations": [{
      "between": ["<object, part or hand>", "<object, part or hand>"],
      "expected": "how the first must move relative to the second in this event",
      "reconstruction_ok": false,
      "problem": "what the reconstruction got wrong, or null",
      "fix": "what you changed, or null",
      "iou_before": 0.71,
      "iou_after": 0.74,
      "check": {
        "reference": "pass",
        "evidence": "the test and its numbers"
      }
    }]
  }],
  "objects": {
    "<object>": {
      "type": ["rigid"],
      "structure": "its parts and how they are joined or attached",
      "relations": "its physical relations to the other objects and the hands over the clip",
      "parameters": "material, mass, friction ..., each with its evidence",
      "modelled_as": "how the scene models it: parts, joints, collision geometry, physics",
      "check": {
        "simulation": "pass",
        "evidence": "the test that shows the scene behaves as described"
      }
    }
  },
  "log": [{
    "minutes": 12,
    "change": "what changed in the analysis, and why"
  }]
}
```

- `events`: one entry per sub-event, in time order, covering the whole clip.
- `type`: any of rigid, articulated, cut, pressed, screwed, soft, flowing, container, fixed.
- `iou_before`, `iou_after`: the replay IoU (against your own masks) of the event's frames before and after the fix (`null` when nothing was fixed).
- `check`: pass or fail, with the evidence; a fail in the final version needs its reason in `<recon>/NOTES.md`.

## How you work

- **Time management:** Track elapsed wall-clock time. Stage 1 lasts 60 minutes: reach a VALID reconstruction first, then spend the remaining time refining it. You choose how to allocate the time; prioritize the deliverable contract and task-critical interactions.
- **Long computations:** Start them in the background with a log when useful (`nohup <command> > <log> 2>&1 &`). Record their process IDs, use bounded polling with a deadline, and stop unnecessary jobs or watchers. Never leave infinite polling loops running.
- **Process control:** Stop processes only by the process IDs you started. Never kill by name or pattern: no `pkill -f`, `killall` or `ps | grep | xargs kill`.
- **Consistent outputs:** Keep `<recon>` in a consistent state: write new results elsewhere and move them into place when they are complete.
- **Deadline:** At 60 minutes, stop further refinement, preserve completed outputs, run the remaining feasible checks, and report incomplete or failed requirements honestly. Do not extend the deadline silently.

## 1. Scope and input data

One task, one demonstration video, one scene. Your inputs are the task documents:

| Document | What it gives |
|---|---|
| `demo/README.md` | The demonstration file(s), the time base (frame rate, any re-timing), the image grid and the metric scale anchor |
| `object/SPECS.md` | The objects' geometry, mass and state frames: given information you may use |
| `TASK_CONFIG.md` | The object and part names (section 3) and the robot hand variant |
| `hardware/` | The robot hand the reconstruction is meant for (context only; the demonstrator's own hands are reconstructed as they are) |

Use the demonstration file named in `demo/README.md` as the image input; every per-frame output covers every one of its frames, in time order.

### About the video

- **Source.** Expect compression and motion blur. It was filmed by one camera; whether it moves is for you to find out.
- **Available information.** Nothing else is given. There are no masks, camera intrinsics, camera poses, gravity directions, depth maps, hand annotations or scorer. You estimate all of them from the video. The object dimensions in `object/SPECS.md` are the metric anchors (`demo/README.md`); a single still camera cannot otherwise separate an object's size from its distance.
- **Handedness.** Left and right are the demonstrator's anatomical hands as seen in the video. Reconstruct the hand(s) the demonstrator actually uses, even where the robot hand of `TASK_CONFIG.md` is the other side; never mirror a hand.

## 2. Rules for the method

**Object models in Blender.** Build and edit every object's geometry in Blender through its Python API (`bpy`), run headless:

`blender -b --factory-startup --python <script.py> -- <args>`

You may start from geometry made with other tools, such as a pretrained image-to-3D model, the dimensions in `object/SPECS.md` or your own fitting code, but import it into Blender and do the editing there. Export the meshes that go into `scene.xml` and `objects/<object>/mesh.obj` from Blender. Blender can also render your models from your cameras (EEVEE) so you can compare them with the masks.

**Hands with the given fitting method.** Reconstruct the visible hands with `tools/recon/mano_fit/`: HaWoR (installed; `tools/recon/hawor_cam.py` runs it in your camera frame) for the initialisation, then `handlib/fit.py` with its default configuration against your object scene, MANO from `$MANO_DIR`. As its README intends, you supervise the fit through its config (for example `fix_scale`, `sil_off`, `hawor_off`, `contact_off`); record every non-default setting and why in `<recon>/hand/method.json` and `<recon>/NOTES.md`. Keep the package's code unchanged; if you must change it, copy it into your own workspace, change the copy, and record the change and the reason. Mark a hand valid only where the video supports it (its README, section 5) and convert the result to `hand/hand_world.npz` (`tools/recon/handfit_export.py`).

**Everything else is yours to design:** masks, cameras, pose estimation and tracking, optimisation, uncertainty, importance and real2sim, using any tool.

**Camera focal length.** Monocular intrinsics (MoGe, `tools/recon/moge_intrinsics.py`) are a prior only: on untextured or synthetic images they can be far off. Calibrate the focal length against known geometry (`tools/recon/camera_calib.py pnp`, from image points of an object of known size, or the scene's other known dimensions), and explain any large disagreement with the prior (the validation flags one above 1.25×). No scorer is provided: measure your replay IoU against your own masks with your own code. Then run the validation of `REFERENCE.md` (`tools/recon/validate_reconstruction.py`).

**Object orientation and asymmetric features.** An object's silhouette can look the same in two orientations while the object itself does not. Before you accept an object's pose, list the features that break its symmetry (from `object/SPECS.md` and the video) and check, at the first frame and before and after each contact phase, that the reconstructed pose puts each of them where the video shows it. A high mask IoU does not choose between such orientations. Record each check and its image evidence in the analysis.

**Open-source code and pretrained models.** You may search the web, read papers and documentation, clone open-source repositories, install packages and download public pretrained model weights. Run every model yourself, on your machine and your GPUs. The models this workflow names are already installed (`TOOLS.md` section 2).

**Read-only:** the installed reconstruction environment (`$R2S2R_RECON_HOME`) and the task documents. Put your code, environments, caches and intermediate files in your own workspace.

## 3. The hand method, step by step

The default sequence, with the provided entry points (`TOOLS.md` section 2):

1. **Frames:** `frames.py` decodes the demonstration on its display-orientation grid.
2. **Hand masks:** `sam3_seg.py --prompt hand=hand` keeps every hand instance per frame.
3. **Initialisation:** `hawor_cam.py` detects the hands (hand detector) and runs HaWoR's temporal model in the camera frame with your focal length; HaWoR's own SLAM and infiller are not used, so the hands share your object scene's camera and metric world.
4. **Fit inputs:** `handfit_inputs.py` assigns each hand instance to left or right (by the detector's box, or by image side where the hands never cross), marks the forearm beyond the wrist plane as don't-care, moves HaWoR into your world frame, adds your `scene/scene.xml` + `replay.json` posed per frame and expands every contact phase of your analysis into single-frame events.
5. **Fit:** `mano_fit/handlib/fit.py --inputs … --out … [--config …]`, then `handlib/score.py`. Supervise it through its config: for example, a hand pushed behind a support needs `depth_order`, contact misses need `contact` and its cap, a scale that drifts needs `fix_scale`.
6. **Export:** `handfit_export.py` applies the validity rule and writes `hand/`.
7. **Check:** Check the hand against the object scene with `validate_reconstruction.py`: fingertip distances in every contact phase, the thumb and an opposing finger in grasps, hands passing into objects or fingers into each other (intersection depth), continuity, handedness and size. A small intersection depth or a high mask IoU does not show correct contact. Where a check fails, refine (masks, scene, contact phases, config, local refits with `freeze_frames`) and check again; record what you could not fix.

## 4. Environment

The reconstruction environment is pre-installed and read-only:

`source $R2S2R_RECON_HOME/env.sh`

This puts Blender 4.2 LTS (headless `bpy`, EEVEE), `uv`, `micromamba` and `recon-python` (the Python environment with SAM 3, HaWoR with its hand detector, MANO, MuJoCo, PyTorch, trimesh and python-fcl) on PATH and sets the model paths (`MANO_DIR`, `SAM3_CHECKPOINT`, `HAWOR_*`).

Its versions and checksums are in `$R2S2R_RECON_HOME/manifest.json`. Install anything else into environments in your own workspace.

## 5. Output contract and validation

Write the outputs exactly as `REFERENCE.md` specifies, in its conventions (section 1), and check them with `tools/recon/check_reference.py <recon>`. The method's own files go with them:

- `analysis/analysis.json`: the scene analysis (Scene analysis), kept up to date.
- `scene/scene.xml`: MJCF of the whole scene (meshes beside it).
- `scene/replay.json`: per-frame joint values that replay the clip.
- `scene/replay_iou.json`: your replay IoU per object and frame against your own masks.
- `pose6d/<object>/`: per-frame pose, uncertainty, importance.
- `physics/<object>.json`: physical properties.
- `hand/`: the hand fit (`hand_world.npz`, the config used, `fit_log.json`, `score.py` output).

### scene.xml and replay.json

- **scene.xml:** Loads with `mujoco.MjModel.from_xml_path`, with mesh paths relative to the file.
- **World frame:** The gravity-aligned world frame of `REFERENCE.md` section 1, in metres, +Z up (the same as `T_world_obj` and `T_world_cam`).
- **Objects:** Each object is one body subtree. Give a moving object a free joint on its root body. Articulations such as rotating layers or hinged parts are further joints or bodies inside the subtree. Static support (a table) is a fixed body.
- **Cube Stage 1 exception:** Whole-cube rigid-body reconstruction is sufficient for Demo-to-Sim; reconstructing its articulated layer-turn mechanism is not required at this stage.
- **Geometry:** Visual geoms (groups 0–2) are your reconstruction, in metres. Every object also needs collision geometry, plus the mass and inertia from its `physics/<object>.json`. Put collision-only geoms in group 3 or higher.
- **replay.json:** `{"objects": {"<object>": "<root body>"}, "frames": [{"frame": <k>, "qpos": {"<joint>": [values]}}]}`, one entry per video frame k (the format `handlib/geom.py` reads as `replay_hand_frames.json`). A free joint takes the body's world pose `[x, y, z, qw, qx, qy, qz]`; a hinge takes radians, a slide metres.

### Pose uncertainty and importance (`pose6d/<object>/traj_world.npz`)

One entry for every frame of the demonstration.

- **Pose:** A pose maps points in the object's canonical frame (metres) to the target frame. The canonical frame is the frame of the object's root body in `scene.xml` and of `objects/<object>/`. `T_world_obj` must agree with that body's pose in `replay.json`; `T_cam_obj` is in that frame's OpenCV camera frame.
- **`std_trans_mm` / `std_rot_deg`:** The 1-σ uncertainty of the object's position (mm) and orientation (deg), combined over the three axes as the square root of the summed variances.
- **`confidence`:** Your normalised scalar in [0, 1] (1 = fully determined). Define it in `<recon>/NOTES.md`.
- **`importance`:** A score in [0, 1] for how crucial this frame's pose is to task success: high for task-critical contact or free-space motion, low for less consequential motion. Define it in `<recon>/NOTES.md`.

### physics/<object>.json

Required keys: `mass_kg`, `com_m` (in the object frame), `inertia_com_kgm2` (3×3, about the COM), `friction` (static and sliding coefficients), `restitution`, `dominant_material`, `size_m` (bounding-box extents). Where `object/SPECS.md` gives a value, use it and say so.

### What the validation covers

`validate_reconstruction.py` writes `validation/report.json`; it is part of the reconstruction, and every fail or warn needs its explanation in `<recon>/NOTES.md`:

- **Objects:** Geometry against the known geometry of `object/SPECS.md`; the per-frame poses projected into the video against your segmentations, on every frame and with all objects and hands together; tracking failures and orientation flips. Image agreement alone is not evidence of 3D correctness.
- **Hands:** The share of frames with a valid hand, and the projected hands against the video.
- **Hand–object interaction:** 3D distances in the contact phases you report, intersection depth, and whether contacts agree with the video (the thumb and an opposing finger in a grasp).
- **Temporal consistency:** Smoothness, discontinuities, implausible speeds.
- **Physical plausibility:** Gravity (free flight, the tabletop, resting objects), objects that sink, float, drift, jump or pass through each other. Motion that improves image agreement but could not happen counts against the reconstruction.
- **Honesty:** Unobservable quantities marked as such, invalid frames flagged. Invented motion or states count against the reconstruction. For example, the spin of an unmarked tennis ball may be indeterminate from video; report its uncertainty rather than inventing a precise rotation.

**Deadline rule:** Have a validated reconstruction within the 60 minutes and keep refining it until they are over. If the deadline is reached with unresolved failures, preserve the available outputs and evidence, report the incomplete requirements, and stop further reconstruction work. An incomplete reconstruction must not be reported as passing the output contract.
