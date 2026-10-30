# Target Environment: Success Criteria

**Task success criteria are not yet defined for this task.**

The tabletop environment with two plugs is new, and no success criteria, task progress rubric, placement targets or required sequence have been published for it. Until they are, the official evaluation of every rollout reports `status: criteria_undefined` with `success: null`, `progress: null`, no milestones and no stages (`FEEDBACK.md` section 1); `criteria.id` and `criteria.rubric` are `null` and `criteria.status` is `undefined`. The validity of the run (policy runtime, hardware compliance, the target's run checks) is still reported. Nothing is scored, nothing is ranked in `history`, and the target makes no comparison between submissions (`REMOTE_API.md` section 5).

When criteria are published, they will appear here with a criteria id, a rubric version and a status (`provisional` or `approved`); from then on every report names them, and the records evaluated under them form their own comparison group. Records made before that are never re-scored.

- **Episode:** 15 s (7,500 control steps at 500 Hz). The episode length is provisional and may change together with the criteria.
- **Validity:** a valid run executes all 7,500 steps without a policy failure, with hardware compliance (`hardware/SPECS.md` section 7) and with the target's run checks passed (`FEEDBACK.md` section 1).

## 1. What Is Recorded

Every rollout's feedback contains the exact trajectory of the wrist and of both plugs at every control step and the contact flags hand–plug, plug–table and plug–plug of every control interval (`FEEDBACK.md` section 3). Any criteria published later will be scored from this record; the record of a rollout made now is not re-scored.

## 2. Research Freedom

No training reward is prescribed. You may design your own objectives, rewards, intermediate goals, curricula, optimization methods, simulators, and policy architectures; your own metrics are not official results, and no official score exists for this task until criteria are published.
