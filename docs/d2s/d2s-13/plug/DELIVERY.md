# Delivering Your Policy

This file says what I need from you to run your policy, and, for tasks with target rounds (`TASK_CONFIG.md` section 1), how a delivery is run and what you get back. Whatever is not stated here is up to you.

## 1. What You Deliver

1. **A policy package** that runs on the target: the interface of section 2, the package format and runtime limits of section 3.
2. **A start pose file** (section 4): the hand pose the target moves the hand to before the objects are placed, and, for in-hand tasks, where the object sits in that hand.

Everything you deliver must come from your own work in your simulation. The target runs your package as it is; it does not tune, retrain or adapt it.

## 2. Policy Interface (contract `v2`)

### 2.1 Control

- **Robot:** the hand of `TASK_CONFIG.md` section 1 on a free-floating 6-DoF wrist (`hardware/SPECS.md`): 20 finger joints in the vendor URDF order plus the wrist pose.
- **Policy frequency:** 500 Hz (one `act()` call per 2 ms step). The finger PD controller and the wrist controller run at 1 kHz and hold each command for two ticks.
- **Episode:** `N` steps; `N` and the episode length of your task are in `TASK_CONFIG.md` section 5. The episode is not ended by task events (dropping an object, finishing early); it ends early only on a policy failure (section 2.4).
- **Units:** SI (m, kg, s, rad). Quaternions are `(w, x, y, z)`.

### 2.2 Frames and Time

- **World frame:** `TASK_CONFIG.md` section 2.
- **Wrist frame:** the URDF root link of the hand, `r_mount` or `l_mount` (`hardware/SPECS.md` section 3).
- **Object state frames:** the target reports each object by a frame fixed to it, defined geometrically in `TASK_CONFIG.md` section 5. It is the target's frame, not the one you chose for your reconstruction: map between the two yourself.
- **Orientation:** a unit quaternion that rotates frame vectors into the world frame. Quaternion streams are sign-continuous (at step 0 `w ≥ 0`, afterwards the sign with a non-negative dot product with the previous value).
- **Velocities:** linear velocity of the frame origin and angular velocity, both in the world frame.
- **Time:** step `k` is at `t = 0.002 k` s. `t = 0` is the first policy step, after the placement and settle phase of section 4.3, which the policy does not control. All state in the observation of step `k` is sampled at one instant: after the last controller tick of command `k − 1` (for `k = 0`: at the end of the settle phase).

### 2.3 Observations

`act(obs)` receives a dictionary; arrays are NumPy `float64` unless stated. `O` is the number of objects (`TASK_CONFIG.md` section 3; it can change between trials when the task says so).

| Key | Shape | Description |
|---|---|---|
| `q` | `(20,)` | Finger joint positions [rad], with encoder noise (`hardware/SPECS.md` section 6) |
| `qd` | `(20,)` | Finger joint velocities [rad/s], with encoder noise |
| `prev_q_target` | `(3, 20)` | Previous three finger position targets as commanded, oldest first |
| `prev_qd_target` | `(3, 20)` | Previous three finger velocity targets, oldest first (`None` recorded as zeros) |
| `wrist_position` | `(3,)` | Wrist-frame origin in the world [m] |
| `wrist_orientation` | `(4,)` | Wrist-frame orientation |
| `wrist_linear_velocity` | `(3,)` | World frame [m/s] |
| `wrist_angular_velocity` | `(3,)` | World frame [rad/s] |
| `prev_wrist_position_target` | `(3, 3)` | Previous three **executed** wrist position targets (after the limits of section 2.4), oldest first |
| `prev_wrist_orientation_target` | `(3, 4)` | Previous three executed wrist orientation targets, oldest first |
| `step` | int | Control step, 0 to `N` − 1 |
| `object_position` | `(O, 3)` | State-frame origin of each object in the world [m] |
| `object_orientation` | `(O, 4)` | State-frame orientation |
| `object_linear_velocity` | `(O, 3)` | World frame [m/s] |
| `object_angular_velocity` | `(O, 3)` | World frame [rad/s] |

Your task's additional keys, if any, are in `TASK_CONFIG.md` section 5. At step 0 the target histories hold three copies of your start pose's finger positions and wrist pose (zeros for `prev_qd_target`). The wrist and object states are exact; the finger encoders are noisy.

**Not observed:** images or depth, contacts or contact forces, joint torques, the target's physical parameters, and any evaluation result. You may use any subset of the observation. The policy may keep internal state; `reset()` initializes it.

### 2.4 Actions

`act(obs)` returns a dictionary:

| Key | Shape | Required | Description |
|---|---|---|---|
| `q_target` | `(20,)` | yes | Absolute finger position targets [rad], clipped to the URDF joint limits |
| `qd_target` | `(20,)` | no (`None` = zero) | Finger velocity targets [rad/s] |
| `wrist_position_target` | `(3,)` | yes | Wrist-frame origin target in the world [m] |
| `wrist_orientation_target` | `(4,)` | yes | Norm within [0.9, 1.1], normalized before use; either sign |
| `wrist_linear_velocity_target` | `(3,)` | no (`None` = zero) | Feed-forward, world frame [m/s] |
| `wrist_angular_velocity_target` | `(3,)` | no (`None` = zero) | Feed-forward, world frame [rad/s] |

Values must be finite; unknown keys are refused.

**Wrist limits** (every step; `hardware/SPECS.md` section 4): the executed position target moves toward your target by at most `V_MAX` = 2.5 m/s × 2 ms and is then clipped to the wrist workspace box of `TASK_CONFIG.md` section 5; the executed orientation target turns toward yours along the shortest arc by at most `W_MAX` = 6.0 rad/s × 2 ms; the feed-forward velocities are clipped to norms of 2.5 m/s and 6.0 rad/s. Commands beyond the limits are not a failure; the executed targets and the limit flags are in the trial log (section 6).

**Policy failure:** a missing, non-finite or wrongly shaped action value, an unknown key, a wrist orientation norm outside [0.9, 1.1], an exception, or no answer within 5 s ends the trial. A dropped object or a failed task does not end the trial.

**Determinism:** for identical observation histories after `reset()`, `act()` must return bit-identical actions.

## 3. Package

A directory with `policy.py`, `manifest.json` and optional weight and configuration files. `policy.py` defines `load_policy(path)`, returning an object with `reset()` and `act(obs)`.

```json
{
  "name": "my_policy",
  "contract_version": "v2",
  "entry": "policy.py:load_policy",
  "files": {"policy.py": "<sha256 hex>", "weights.npz": "<sha256 hex>"}
}
```

`files` lists every file except `manifest.json`, each with its SHA-256.

**Runtime on the target**

| Requirement | Limit |
|---|---|
| Python | 3.12 (3.12.3) |
| Libraries | standard library, NumPy 2.5.4, PyTorch 2.14.1 (CPU build); nothing else |
| Threads | BLAS and PyTorch pools limited to 1 thread |
| GPU | none |
| Memory | ≤ 8 GB address space |
| CPU time | ≤ 600 s per trial |
| `act()` time | 2 ms target (500 Hz); 5 s hard timeout; 60 s for `load_policy()` and `reset()` |
| Writable storage | `TMPDIR` only, ≤ 64 MB |

The package runs in a sandbox: the package directory is read-only, there is no network, no subprocess and no compiled code from the package.

**Check before you deliver:** `r2s2r-d2s validate <package_dir>` runs the target's checks locally: manifest and hashes, contract version, `load_policy()` and `reset()`, `act()` calls on observations with exactly your task's keys and shapes (1000 steps by default, `--steps N`), with your start pose when you give it (`r2s2r-d2s validate <package_dir> <start_pose.json>`), determinism and inference time. It does not tell you whether the policy will succeed.

## 4. Start Pose File

### 4.1 Format

```json
{
  "start_pose": {
    "wrist_frame": "r_mount",
    "wrist_position": [0.0, 0.0, 0.30],
    "wrist_orientation": [1.0, 0.0, 0.0, 0.0],
    "fingers": {"r_thumb_cmc_flex": 0.3, "...": 0.0},
    "<object>_nominal": {"position": [0.0, 0.0, -0.10], "orientation": [1.0, 0.0, 0.0, 0.0]}
  }
}
```

- `wrist_frame`: `r_mount` / `l_mount` (or `r_wrist` / `l_wrist`, converted by the fixed URDF offset).
- `wrist_position`, `wrist_orientation`: that frame's pose in the target's world frame (`TASK_CONFIG.md` section 2), inside the wrist workspace box (section 5 of `TASK_CONFIG.md`).
- `fingers`: all 20 finger joints by name [rad]. These are both the joint positions the hand is moved to and the finger targets it holds until your policy's first command.
- `<object>_nominal`: for in-hand tasks, where the object sits in this hand, as the object's state frame (`TASK_CONFIG.md` section 5) in the wrist frame: `position` [m] and, where `TASK_CONFIG.md` asks for it, `orientation`. The key name for your task is in `TASK_CONFIG.md` section 5. Tasks whose objects start away from the hand have no nominal.

### 4.2 Checks before a round

The target refuses a start pose, and runs nothing, if the file is malformed, the wrist pose is outside the workspace box, the hand touches the table or floor, or (in-hand tasks) the object placed exactly at the nominal does not come to rest on the hand as described in 4.3. The reason is written to `start_pose_rejected.json` (section 6).

### 4.3 How each trial starts

1. The hand is moved to your start pose and holds it (the fingers at your `fingers` values).
2. The objects are placed: in-hand objects near your nominal, never in exactly the same spot (how far, in which directions and how they are turned is described in everyday words in `TASK.md`, Deployment); other objects as `TASK.md` describes. An object that would overlap the hand is first shifted a few millimetres away from it.
3. The objects are released at rest and the hand holds still for 1.0 s. Then the objects must be at rest (speed below 0.02 m/s) and touching the hand (in-hand tasks) or resting on the table and not touching the hand (other tasks).
4. The hand holds still for another 0.5 s; in that time no object may move more than 3 mm.
5. Your policy starts (`t = 0`).

If step 3 or 4 fails, the trial is a **placement failure**: your policy is not run, and the trial is not repeated. A start pose that only holds the object when the fingers close after the object is in place does not pass: choose finger values that catch the object as it is placed, wherever it is placed.

Simulate this sequence yourself before you deliver.

## 5. Delivering to the Target (tasks with target rounds)

```bash
r2s2r-d2s submit <package_dir> <start_pose.json> --gate <gate record ID>
```

`--gate` names a gate of your task suite whose candidate is this package (the SHA-256 of its `manifest.json`) and that made it the incumbent (`demo2sim/VERIFICATION.md` section 3). A policy does not need to pass your own verification to be delivered. `submit` refuses a delivery without such a gate, and a new delivery while your judgment or your replay of the previous round is not recorded. It first runs `validate` and the start pose checks of 4.2 (a refused delivery is not a round), then hands the delivery to the target and waits until the round is done. If your command time limit ends the wait, it returns `still running`; run `r2s2r-d2s submit --wait` to keep waiting. The round's results are written to `target_feedback/round_<n>/` in your workspace. `r2s2r-d2s time` shows which phase you are in and how much time you have left.

One delivery is one round. A round runs a fixed number of trials (`TASK_CONFIG.md` section 1), each from a new start drawn by the target (new placement, and for tasks that have it a new object count, layout or scramble). Starts are never reused, and the target never retries a trial.

## 6. What You Get Back

`target_feedback/round_<n>/`:

- `start_pose_rejected.json`: only if the start pose was refused; then nothing else ran.
- `trial_<i>/start_state.json`: the measured start state at `t = 0` (object poses, object count and kinds, scramble where the task has one, wrist pose, the start pose you requested), and a note if the trial was a placement failure.
- `trial_<i>/trial.json`: trial metadata (round, trial, steps executed, timestamps).
- `trial_<i>/policy_log_trial_0.npz`: every observation's finger encoders and every command: finger targets, commanded and executed wrist targets, wrist limit flags.
- `trial_<i>/state_trial_0.npz`: per step the wrist and object states and contact flags (hand–object, object–environment, object–object, per-finger contact).
- `trial_<i>/video/`: the trial from three cameras, from the release of the objects to the end.
- `trial_<i>/measurements.json`: the standard measurements of `d2s_measures.py` (meas-2), computed by the target from the trial's state log and finger joint positions, the same code the gate uses on your simulation: for each object how high it rose, how long it touched the hand, was held and was held in an opposed grip, its largest rotation and displacement relative to the hand within one opposed grip, the part of its relative rotation that happened while the finger joints were almost still, its final pose, speed and contacts, how long it rests at the end; for the wrist its path length and rotation. They are exact; they are not a score and not a verdict.

There is no score and no success or failure verdict: judge each trial yourself from these records and the video, against your verification criteria (`demo2sim/VERIFICATION.md`), and record your judgment of every trial with `r2s2r-d2s judge` (`demo2sim/RECORDS.md`) before your next delivery.

## 7. Rounds and Time

- **Deliver early.** The first round tells you more about the target than further training in your own simulation. Deliver as soon as your task suite has an incumbent that passes `validate`, even when it often fails.
- **Time:** the budget of `TASK_CONFIG.md` section 1 in total; the time `submit` waits for the target does not count. Your first delivery must come within the first-delivery limit given there, or the run ends without a target round.
- **Rounds:** deliver as often as you like; record your judgment of every trial of a round and your replay of it (section 8) before the next delivery.
- **Stop** when your own verification passes (a `verify` record that names a final gate) and you judge every trial of your latest round successful, or when the time is up.

## 8. Replay Before You Repair

After you judge a round and before you change your simulation or policy for the next one:
- **Replay every trial** in your simulation: start from the trial's measured start state (`start_state.json`) and apply the target's recorded commands (`policy_log_trial_0.npz`), open loop. Save your replay's state log in the standard format of `d2s_measures.py`.
- **Find what makes the replay differ** from the target's state log (`state_trial_0.npz`), before you repair anything: an observation mismatch (frames, timing, what the policy saw) or a dynamics mismatch (contact, friction, mass, controller response). Test a few hypotheses in the replay and keep the change that makes it reproduce what the target did.
- **Record it:** `r2s2r-d2s replay <round> replay.json --sim trial_0=replay_0.npz ...` (`demo2sim/RECORDS.md`). The command computes for every trial the residual of your replay against the target (object and wrist position and orientation errors over time, and when they first exceed 2 cm). `submit` refuses your next delivery until the round's replay is recorded.
