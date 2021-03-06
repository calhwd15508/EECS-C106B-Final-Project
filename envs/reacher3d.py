import numpy as np
from gym import utils
from gym.envs.mujoco import mujoco_env
import os


class Reacher3dEnv(mujoco_env.MujocoEnv, utils.EzPickle):
    def __init__(self):
        self.goal = np.array([0.8, -0.6, 0.6])
        utils.EzPickle.__init__(self)
        mujoco_env.MujocoEnv.__init__(self, os.path.join(os.path.dirname(__file__), 'assets/reacher3d.xml'), 4)
        self.max_episode_steps = 500
        self.reward_threshold = -200

    def step(self, a):
        vec = self.get_body_com("fingertip") - self.get_body_com("target")
        reward_dist = - np.linalg.norm(vec)
        reward_ctrl = - np.square(a).sum() * 0.01
        reward = reward_dist + reward_ctrl
        self.do_simulation(a, self.frame_skip)
        ob = self._get_obs()
        s = self.state_vector()
        # print(reward_dist)
        # done = not (np.isfinite(s).all() and (-reward_dist > 0.1))
        done = False
        return ob, reward, done, dict(reward_dist=reward_dist, reward_ctrl=reward_ctrl)

    def viewer_setup(self):
        self.viewer.cam.trackbodyid = 0
        self.viewer.cam.distance = 5
        self.viewer.cam.lookat[2] += .8
        self.viewer.cam.elevation = -20

    def reset(self):
        """
        Trying to figure out which state is white
        Box(21)
        get_obs gives
            np.cos(theta), angle
            np.sin(theta), angle
            self.goal, pos
            self.sim.data.qvel.flat[:5], joint vel
            self.get_body_com("fingertip") - self.goal, distance/reward metric
        """
        qpos = self.np_random.uniform(low=-0.01, high=0.01, size=self.model.nq) + self.init_qpos
        while True:
            self.goal = self.np_random.uniform(low=-.5, high=.5, size=3)
            if np.linalg.norm(self.goal) < 1.5:
                break
        qpos[-3:] = self.goal
        qvel = self.init_qvel + self.np_random.uniform(low=-.01, high=.01, size=self.model.nv)
        qvel[-3:] = 0
        self.set_state(qpos, qvel)
        return self._get_obs()

    def _get_obs(self):
        theta = self.sim.data.qpos.flat[:5]
        return np.concatenate([
            np.cos(theta),
            np.sin(theta),
            self.goal,
            self.sim.data.qvel.flat[:5],
            self.get_body_com("fingertip") - self.goal
        ])
