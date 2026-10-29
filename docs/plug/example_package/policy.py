"""Minimal example policy package: holds the start pose. Shows the package format only."""

import numpy as np


class HoldPolicy:
    def reset(self):
        self.hold = None

    def act(self, obs):
        if self.hold is None:
            self.hold = np.array(obs["prev_q_target"][-1], dtype=np.float64)  # start pose (CONTRACT.md)
        return self.hold.copy(), None


def load_policy(path):
    return HoldPolicy()
