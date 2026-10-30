"""Minimal example policy package (contract v2): holds the start pose of the fingers and the wrist. Shows the
package format only."""

import numpy as np


class HoldPolicy:
    def reset(self):
        self.hold = None

    def act(self, obs):
        if self.hold is None:  # start pose (CONTRACT.md): the newest entries of the target histories at step 0
            self.hold = {"q_target": np.array(obs["prev_q_target"][-1], dtype=np.float64),
                         "wrist_position_target": np.array(obs["prev_wrist_position_target"][-1], dtype=np.float64),
                         "wrist_orientation_target": np.array(obs["prev_wrist_orientation_target"][-1], dtype=np.float64)}
        return {k: v.copy() for k, v in self.hold.items()}


def load_policy(path):
    return HoldPolicy()
