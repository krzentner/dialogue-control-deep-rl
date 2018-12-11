from lagom.envs import Env
from lagom.envs.spaces import Box, Discrete, Tuple
from dial_control_rl import game
import numpy as np


class CraftingEnv(Env):

    def __init__(self, init_seed=None):
        self.seed(init_seed)

    def _step_player(self):
        self.current_player = ((self.current_player + 1) % 2) + 1

    def step(self, action):
        player = self.current_player
        action = game.action_for_player(player, action)
        _, reward, discount = self.game.play(action)
        obs = self.game.render_observation()

        self._step_player()

        obs = game.observations_for_player(obs, self.current_player)
        obs = self.actual_observation_space.flatten(obs)
        return (obs, reward, self.game.game_over, {
                'goals': self.game.goals(),
                'player': player,
                })

    def seed(self, seed):
        self.last_seed = seed
        self.current_player = 1
        self.random_state = np.random.RandomState(seed)
        self.game = game.make_game(seed)
        self.game.its_showtime()
        self.actual_observation_space = Tuple((
            Box(0, 255, dtype=np.uint8,
                shape=(game.MAP_HEIGHT, game.MAP_WIDTH)),
            Box(0, 255, dtype=np.uint8,
                shape=(3,)),
            Box(0, 255, dtype=np.uint8,
                shape=(3,)),
            Box(0, 1, dtype=np.uint8,
                shape=(game.MAP_HEIGHT, game.MAP_WIDTH)),
            Box(0, 1, dtype=np.uint8,
                shape=(game.MAP_HEIGHT, game.MAP_WIDTH)),
            Box(0, 1, dtype=np.uint8, shape=(game.GOAL_LEN,))))

    def render(self, mode='human'):
        if mode == 'human':
            return self.game.render_human()
        elif mode == 'rgb_array':
            return self.game.render_array()

    def close(self):
        pass

    @property
    def observation_space(self):
        flat_dim = self.actual_observation_space.flat_dim
        return Box(0, 255, dtype=np.uint8, shape=(flat_dim,))

    @property
    def action_space(self):
        return Discrete(8)

    @property
    def T(self):
        # We probably don't need one this long, but we should be able to handle
        # it, so whatever.
        return 100

    @property
    def max_episode_reward(self):
        return 100

    @property
    def reward_range(self):
        return (-200.0, 100.0)

    def observation_to_goal(self, observation):
        completed_goals = observation[1]
        indices = list(range(game.GOAL_LEN))
        self.random_state.shuffle(indices)
        result = np.zeros(game.GOAL_LEN)
        for i in indices:
            if completed_goals[i] == 1.0:
                result[i] = 1.0
                return result
        return None

    def reset(self):
        self.seed(self.last_seed)
        obs = self.game.render_observation()
        obs = game.observations_for_player(obs, self.current_player)
        obs = self.actual_observation_space.flatten(obs)
        assert obs.shape == self.observation_space.shape
        return obs
